import json
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from .manifest import load_manifest, ManifestError

class PackManager:
    def __init__(self, packs_dir: Path, data_dir: Path):
        self.packs_dir = Path(packs_dir)
        self.data_dir = Path(data_dir)
        self.state_file = self.data_dir / "pack_state.json"
        self.packs_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state = self._load_state()

    def _load_state(self):
        if not self.state_file.exists():
            return {}
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_state(self):
        temp = self.state_file.with_suffix(".tmp")
        temp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.state_file)

    def discover(self):
        packs, errors = [], []
        for folder in sorted(self.packs_dir.iterdir()):
            if not folder.is_dir():
                continue
            try:
                manifest = load_manifest(folder)
                manifest["_folder"] = folder.name
                manifest["_path"] = str(folder)
                manifest["_enabled"] = bool(self.state.get(manifest["id"], False))
                packs.append(manifest)
            except ManifestError as exc:
                errors.append(f"{folder.name}: {exc}")
        return packs, errors

    def set_enabled(self, pack_id: str, enabled: bool):
        self.state[pack_id] = bool(enabled)
        self._save_state()

    def find_pack(self, pack_id: str):
        for pack in self.discover()[0]:
            if pack["id"] == pack_id:
                return Path(pack["_path"]), pack
        raise ValueError(f"Không tìm thấy pack: {pack_id}")

    def import_pack(self, archive: Path):
        archive = Path(archive)
        if not zipfile.is_zipfile(archive):
            raise ValueError("Tệp được chọn không phải ZIP hợp lệ")
        temp_dir = self.data_dir / "import_tmp"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        try:
            with zipfile.ZipFile(archive) as zf:
                for info in zf.infolist():
                    name = info.filename.replace("\\", "/")
                    parts = PurePosixPath(name).parts
                    if not parts or name.startswith("/") or ".." in parts:
                        raise ValueError("ZIP chứa đường dẫn không an toàn")
                    target = (temp_dir / Path(*parts)).resolve()
                    if temp_dir.resolve() not in target.parents and target != temp_dir.resolve():
                        raise ValueError("ZIP chứa đường dẫn vượt khỏi thư mục giải nén")
                zf.extractall(temp_dir)
            manifests = list(temp_dir.rglob("manifest.json"))
            if len(manifests) != 1:
                raise ValueError("ZIP phải chứa đúng một manifest.json")
            source_dir = manifests[0].parent
            manifest = load_manifest(source_dir)
            pack_id = manifest["id"]
            if any(p["id"] == pack_id for p in self.discover()[0]):
                raise ValueError(f"Đã tồn tại pack có ID: {pack_id}")
            safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", pack_id).strip(".-")
            if not safe_name:
                raise ValueError("ID pack không hợp lệ")
            destination = self.packs_dir / safe_name
            if destination.exists():
                raise ValueError("Thư mục đích đã tồn tại")
            shutil.copytree(source_dir, destination)
            return manifest
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def export_pack(self, pack_id: str, destination: Path):
        folder, manifest = self.find_pack(pack_id)
        destination = Path(destination)
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in folder.rglob("*"):
                if file.is_file():
                    zf.write(file, Path(folder.name) / file.relative_to(folder))
        return destination

    def create_pack(self, name: str, app: str, description: str, author: str):
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        if not slug:
            raise ValueError("Tên pack không hợp lệ")
        pack_id = f"{app}.{slug}"
        if any(p["id"] == pack_id for p in self.discover()[0]):
            raise ValueError("Pack có ID này đã tồn tại")
        folder = self.packs_dir / f"{app}-{slug}"
        if folder.exists():
            raise ValueError("Thư mục pack đã tồn tại")
        folder.mkdir(parents=True)
        manifest = {
            "id": pack_id, "name": name.strip(), "app": app,
            "version": "1.0.0", "description": description.strip(),
            "author": author.strip() or "Local user", "assets": ["theme.css"],
            "kind": "live-css-theme",
            "compatibility": {"status": "cdp-css-injection"}
        }
        css = ":root {\n  --diamonda-background: #171923;\n  --diamonda-foreground: #f1f2f8;\n  --diamonda-accent: #858bea;\n}\n"
        (folder / "theme.css").write_text(css, encoding="utf-8")
        (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest

    def backup(self, destination: Path):
        destination = Path(destination)
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as zf:
            if self.state_file.exists():
                zf.write(self.state_file, "data/pack_state.json")
            for folder in self.packs_dir.iterdir():
                if folder.is_dir():
                    for file in folder.rglob("*"):
                        if file.is_file():
                            zf.write(file, Path("resources/packs") / folder.name / file.relative_to(folder))
            info = {"created_at": datetime.now().isoformat(timespec="seconds"), "format": 1}
            zf.writestr("backup_info.json", json.dumps(info, indent=2))
        return destination

    def restore(self, archive: Path):
        archive = Path(archive)
        if not zipfile.is_zipfile(archive):
            raise ValueError("Tệp backup không phải ZIP hợp lệ")
        staging = self.data_dir / "restore_tmp"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        try:
            with zipfile.ZipFile(archive) as zf:
                for info in zf.infolist():
                    name = info.filename.replace("\\", "/")
                    parts = PurePosixPath(name).parts
                    if name.startswith("/") or ".." in parts:
                        raise ValueError("Backup chứa đường dẫn không an toàn")
                zf.extractall(staging)
            pack_root = staging / "resources" / "packs"
            if pack_root.exists():
                for folder in pack_root.iterdir():
                    if not folder.is_dir():
                        continue
                    manifest = load_manifest(folder)
                    destination = self.packs_dir / folder.name
                    if destination.exists():
                        continue
                    shutil.copytree(folder, destination)
            state_backup = staging / "data" / "pack_state.json"
            if state_backup.exists():
                data = json.loads(state_backup.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("File trạng thái trong backup không hợp lệ")
                self.state = data
                self._save_state()
        finally:
            shutil.rmtree(staging, ignore_errors=True)
