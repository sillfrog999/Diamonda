import json
from pathlib import Path

REQUIRED_FIELDS = ("id", "name", "app", "version", "description", "author")
ALLOWED_APPS = {"youtube", "facebook", "discord", "spotify"}

class ManifestError(ValueError):
    pass

def load_manifest(pack_dir: Path) -> dict:
    pack_dir = Path(pack_dir).resolve()
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ManifestError("Thiếu manifest.json")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ManifestError(f"Không đọc được manifest: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("Manifest phải là JSON object")
    missing = [field for field in REQUIRED_FIELDS if not isinstance(data.get(field), str) or not data[field].strip()]
    if missing:
        raise ManifestError("Thiếu hoặc sai kiểu trường: " + ", ".join(missing))
    if data["app"] not in ALLOWED_APPS:
        raise ManifestError(f"Ứng dụng không được hỗ trợ: {data['app']}")
    assets = data.get("assets", [])
    if not isinstance(assets, list) or any(not isinstance(x, str) for x in assets):
        raise ManifestError("Trường assets phải là danh sách chuỗi")
    for item in assets:
        rel = Path(item)
        if rel.is_absolute() or ".." in rel.parts:
            raise ManifestError(f"Đường dẫn asset không hợp lệ: {item}")
        asset_path = (pack_dir / rel).resolve()
        if pack_dir not in asset_path.parents or not asset_path.is_file():
            raise ManifestError(f"Không tìm thấy asset hoặc đường dẫn không an toàn: {item}")
    features = data.get("features", [])
    if not isinstance(features, list) or any(not isinstance(x, str) for x in features):
        raise ManifestError("Trường features phải là danh sách chuỗi")
    return data
