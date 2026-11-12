from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QTextEdit, QMessageBox,
    QComboBox, QFileDialog, QInputDialog, QLineEdit
)
from diamonda.core.pack_manager import PackManager
from diamonda.adapters.registry import AdapterRegistry
from diamonda.core.browser_injector import BrowserInjector

APP_LABELS = {"youtube": "YouTube", "facebook": "Facebook", "discord": "Discord", "spotify": "Spotify"}

class MainWindow(QMainWindow):
    def __init__(self, base_dir: Path):
        super().__init__()
        self.base_dir = Path(base_dir)
        self.manager = PackManager(self.base_dir / "resources" / "packs", self.base_dir / "data")
        self.adapters = AdapterRegistry()
        self.injector = BrowserInjector(self.base_dir, self._set_injection_status)
        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(1500)
        self.sync_timer.timeout.connect(self.injector.sync_once)
        self.packs = []
        self.setWindowTitle("Diamonda 0.4.0 — Functional Mods")
        self.resize(1180, 760)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(22, 18, 22, 18)
        outer.setSpacing(12)

        header = QHBoxLayout()
        brand = QVBoxLayout()
        title = QLabel("DIAMONDA")
        title.setObjectName("brand")
        subtitle = QLabel("Discover · Modify · Create · Share · Restore")
        subtitle.setObjectName("muted")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header.addLayout(brand)
        header.addStretch()
        self.filter_box = QComboBox()
        self.filter_box.addItems(["Tất cả ứng dụng", "YouTube", "Facebook", "Discord", "Spotify"])
        self.filter_box.currentTextChanged.connect(self.refresh)
        header.addWidget(self.filter_box)
        refresh_btn = QPushButton("Làm mới")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        outer.addLayout(header)

        toolbar = QHBoxLayout()
        for label, callback in [
            ("Tạo pack", self.create_pack), ("Nhập ZIP", self.import_pack),
            ("Xuất pack", self.export_pack), ("Backup", self.backup),
            ("Restore", self.restore), ("Kiểm tra xung đột", self.check_conflicts)
        ]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        outer.addLayout(toolbar)

        body = QHBoxLayout()
        self.pack_list = QListWidget()
        self.pack_list.setMinimumWidth(340)
        self.pack_list.currentRowChanged.connect(self.show_details)
        body.addWidget(self.pack_list, 1)

        right = QVBoxLayout()
        self.name_label = QLabel("Chọn một resource pack")
        self.name_label.setObjectName("pack_title")
        self.meta_label = QLabel(" ")
        self.meta_label.setObjectName("muted")
        self.description = QTextEdit()
        self.description.setReadOnly(True)
        self.description.setPlaceholderText("Thông tin resource pack sẽ xuất hiện ở đây.")
        self.action_btn = QPushButton("Bật pack")
        self.action_btn.setEnabled(False)
        self.action_btn.clicked.connect(self.toggle_selected)
        self.apply_btn = QPushButton("Apply trực tiếp lên website")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.apply_selected)
        self.unapply_btn = QPushButton("Gỡ pack khỏi website")
        self.unapply_btn.setEnabled(False)
        self.unapply_btn.clicked.connect(self.unapply_live)
        right.addWidget(self.name_label)
        right.addWidget(self.meta_label)
        right.addWidget(self.description, 1)
        right.addWidget(self.action_btn)
        right.addWidget(self.apply_btn)
        right.addWidget(self.unapply_btn)
        body.addLayout(right, 2)
        outer.addLayout(body, 1)

        footer = QLabel("MVP 0.4.0 · Live CSS + JavaScript mods · Direct CDP injection")
        footer.setObjectName("muted")
        outer.addWidget(footer)
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #11151d; color: #e8edf5; font-size: 14px; }
            QLabel#brand { font-size: 25px; font-weight: 800; letter-spacing: 3px; color: #a8c7ff; }
            QLabel#muted { color: #8c98aa; }
            QLabel#pack_title { font-size: 22px; font-weight: 700; }
            QListWidget, QTextEdit, QComboBox, QLineEdit {
                background: #1a2230; border: 1px solid #303b4d; border-radius: 9px;
                padding: 8px; selection-background-color: #315b91;
            }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #2a3444; }
            QPushButton { background: #315b91; color: white; border: 0; border-radius: 8px; padding: 9px 12px; font-weight: 600; }
            QPushButton:hover { background: #416fa9; }
            QPushButton:disabled { background: #303846; color: #7e8999; }
        """)

    def _selected_pack(self):
        row = self.pack_list.currentRow()
        if row < 0 or row >= len(self.packs):
            return None
        return self.packs[row]

    def refresh(self, *_):
        selected_filter = self.filter_box.currentText().lower()
        all_packs, errors = self.manager.discover()
        self.packs = all_packs if selected_filter == "tất cả ứng dụng" else [p for p in all_packs if p["app"] == selected_filter]
        self.pack_list.clear()
        for pack in self.packs:
            status = "● Đang bật" if pack["_enabled"] else "○ Đang tắt"
            item = QListWidgetItem(f'{pack["name"]}\n{APP_LABELS.get(pack["app"], pack["app"])} · {status}')
            item.setData(Qt.UserRole, pack["id"])
            self.pack_list.addItem(item)
        self.statusBar().showMessage(f"Tìm thấy {len(self.packs)} pack · {len(errors)} lỗi manifest")
        if self.packs:
            self.pack_list.setCurrentRow(0)
        else:
            self.name_label.setText("Không có resource pack")
            self.meta_label.setText(" ")
            self.description.setPlainText("Không tìm thấy pack phù hợp. Bạn có thể tạo pack mới hoặc nhập ZIP.")
            self.action_btn.setEnabled(False)

    def show_details(self, row):
        if row < 0 or row >= len(self.packs):
            return
        pack = self.packs[row]
        app_name = APP_LABELS.get(pack["app"], pack["app"])
        self.name_label.setText(pack["name"])
        self.meta_label.setText(f'{app_name} · v{pack["version"]} · Tác giả: {pack["author"]}')
        lines = [pack["description"], "", f'ID: {pack["id"]}', f'Ứng dụng: {app_name}',
                 f'Phiên bản: {pack["version"]}', f'Trạng thái quản lý: {"Đang bật" if pack["_enabled"] else "Đang tắt"}',
                 f'Adapter: {self.adapters.get(pack["app"]).status}', "", "Tệp đi kèm:"]
        lines.extend([f"  • {asset}" for asset in pack.get("assets", [])] or ["  (Không có asset)"])
        lines += ["", "MOD TÍNH NĂNG:"]
        lines.extend([f"  • {feature}" for feature in pack.get("features", [])] or ["  (Pack chỉ có thay đổi giao diện)"])
        lines += ["", "Live Injection: Diamonda inject CSS và JavaScript pack vào tab website qua CDP.", "JavaScript chỉ chạy khi người dùng chủ động Apply pack. Chỉ nhập pack từ nguồn đáng tin cậy. Unapply gọi cleanup để gỡ các tính năng đã đăng ký.", "Ứng dụng desktop gốc cần adapter riêng."]
        self.description.setPlainText("\n".join(lines))
        self.action_btn.setEnabled(True)
        self.apply_btn.setEnabled(any(str(a).lower().endswith((".css", ".js")) for a in pack.get("assets", [])))
        self.unapply_btn.setEnabled(bool(self.injector.css))
        self.action_btn.setText("Tắt pack" if pack["_enabled"] else "Bật pack")

    def _set_injection_status(self, message):
        self.statusBar().showMessage(message, 10000)

    def apply_selected(self):
        pack = self._selected_pack()
        if not pack:
            return
        try:
            folder, manifest = self.manager.find_pack(pack["id"])
            css_parts = []
            js_scripts = []
            for asset in manifest.get("assets", []):
                suffix = str(asset).lower()
                content = (folder / asset).read_text(encoding="utf-8")
                if suffix.endswith(".css"):
                    css_parts.append(content)
                elif suffix.endswith(".js"):
                    js_scripts.append((str(asset), content))
            css = "\n\n".join(css_parts)
            if not css.strip() and not js_scripts:
                raise ValueError("Pack không có CSS hoặc JavaScript mod.")
            if len(css.encode("utf-8")) > 512 * 1024:
                raise ValueError("CSS của pack vượt giới hạn 512 KB.")
            if sum(len(code.encode("utf-8")) for _, code in js_scripts) > 256 * 1024:
                raise ValueError("JavaScript mod vượt giới hạn 256 KB.")
            if js_scripts:
                answer = QMessageBox.warning(
                    self, "Xác nhận chạy mod JavaScript",
                    "Pack này chứa JavaScript có thể tương tác với nội dung trang web. "
                    "Chỉ tiếp tục nếu bạn tin tưởng nguồn pack. Bạn muốn thực thi mod này?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if answer != QMessageBox.Yes:
                    return
            url, count = self.injector.apply(pack["app"], pack["id"], css, js_scripts)
            self.sync_timer.start()
            if count:
                message = f"Đã inject {manifest['name']} vào {count} tab · {url}"
            else:
                message = f"Đã mở {url}; đang chờ trang tải xong để inject {manifest['name']}"
            self.statusBar().showMessage(message, 15000)
            QMessageBox.information(self, "Diamonda Direct Injection", message + "\n\n"
                "Diamonda đang dùng CDP trên hồ sơ trình duyệt riêng. CSS và mod JavaScript đã được gửi tới tab. "
                "Hãy giữ Diamonda mở để tự áp dụng lại sau khi tải lại tab.")
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Inject thất bại", str(exc))

    def unapply_live(self):
        self.sync_timer.stop()
        removed = self.injector.unapply()
        self.statusBar().showMessage(f"Đã gỡ pack khỏi {removed} tab.", 8000)
        self.refresh()

    def closeEvent(self, event):
        self.sync_timer.stop()
        self.injector.unapply()
        super().closeEvent(event)

    def toggle_selected(self):
        pack = self._selected_pack()
        if not pack:
            return
        self.manager.set_enabled(pack["id"], not pack["_enabled"])
        self.refresh()

    def create_pack(self):
        name, ok = QInputDialog.getText(self, "Tạo resource pack", "Tên pack:")
        if not ok or not name.strip():
            return
        app, ok = QInputDialog.getItem(self, "Ứng dụng", "Chọn ứng dụng:", list(APP_LABELS), 0, False)
        if not ok:
            return
        description, ok = QInputDialog.getText(self, "Mô tả", "Mô tả pack:")
        if not ok:
            return
        try:
            self.manager.create_pack(name, app, description or "Local resource pack", "Local user")
            self.refresh()
            QMessageBox.information(self, "Diamonda", "Đã tạo resource pack mẫu.")
        except Exception as exc:
            QMessageBox.critical(self, "Không thể tạo pack", str(exc))

    def import_pack(self):
        path, _ = QFileDialog.getOpenFileName(self, "Nhập resource pack", "", "ZIP archive (*.zip)")
        if not path:
            return
        try:
            pack = self.manager.import_pack(Path(path))
            self.refresh()
            QMessageBox.information(self, "Diamonda", f'Đã nhập: {pack["name"]}')
        except Exception as exc:
            QMessageBox.critical(self, "Nhập pack thất bại", str(exc))

    def export_pack(self):
        pack = self._selected_pack()
        if not pack:
            QMessageBox.warning(self, "Diamonda", "Hãy chọn một pack trước.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Xuất resource pack", f'{pack["id"]}.zip', "ZIP archive (*.zip)")
        if not path:
            return
        try:
            self.manager.export_pack(pack["id"], Path(path))
            QMessageBox.information(self, "Diamonda", "Đã xuất resource pack.")
        except Exception as exc:
            QMessageBox.critical(self, "Xuất pack thất bại", str(exc))

    def backup(self):
        path, _ = QFileDialog.getSaveFileName(self, "Tạo bản backup", "diamonda-backup.zip", "ZIP archive (*.zip)")
        if not path:
            return
        try:
            self.manager.backup(Path(path))
            QMessageBox.information(self, "Diamonda", "Đã tạo backup pack và trạng thái quản lý.")
        except Exception as exc:
            QMessageBox.critical(self, "Backup thất bại", str(exc))

    def restore(self):
        path, _ = QFileDialog.getOpenFileName(self, "Khôi phục backup", "", "ZIP archive (*.zip)")
        if not path:
            return
        answer = QMessageBox.question(self, "Xác nhận restore", "Khôi phục các pack chưa tồn tại và trạng thái từ backup? Pack trùng tên sẽ được giữ nguyên.")
        if answer != QMessageBox.Yes:
            return
        try:
            self.manager.restore(Path(path))
            self.refresh()
            QMessageBox.information(self, "Diamonda", "Đã khôi phục backup.")
        except Exception as exc:
            QMessageBox.critical(self, "Restore thất bại", str(exc))

    def check_conflicts(self):
        enabled, _ = self.manager.discover()
        enabled = [p for p in enabled if p["_enabled"]]
        groups = {}
        for pack in enabled:
            for asset in pack.get("assets", []):
                key = (pack["app"], Path(asset).name.lower())
                groups.setdefault(key, []).append(pack["name"])
        conflicts = [(app, asset, names) for (app, asset), names in groups.items() if len(names) > 1]
        if not conflicts:
            QMessageBox.information(self, "Kiểm tra xung đột", "Không phát hiện trùng tên asset giữa các pack đang bật.")
            return
        lines = ["Phát hiện các asset trùng tên (chỉ là cảnh báo tiềm năng; chưa có cài đặt vào ứng dụng):", ""]
        for app, asset, names in conflicts:
            lines.append(f'{APP_LABELS.get(app, app)} / {asset}: ' + ", ".join(names))
        QMessageBox.warning(self, "Xung đột tiềm năng", "\n".join(lines))
