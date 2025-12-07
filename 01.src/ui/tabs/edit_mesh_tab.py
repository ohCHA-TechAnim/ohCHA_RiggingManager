# ohCHA_RigManager/01/src/ui/tabs/edit_mesh_tab.py
# Description: [v1.9.15] Fixed Table Column Widths (Action Column Stretch).

from pymxs import runtime as rt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QSplitter,
    QStackedWidget, QAbstractItemView, QApplication, QProgressDialog,
    QCheckBox, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
import functools

try:
    from utils.translator import translator
except ImportError:
    class TempTranslator:
        get = lambda s, k: f"<{k}>"


    translator = TempTranslator()
try:
    from ui.ohcha_ui_widgets import OchaAnimatedToggle
except ImportError:
    class OchaAnimatedToggle(QCheckBox):
        pass
try:
    from controllers import edit_mesh_logic
except ImportError:
    edit_mesh_logic = None

# Configuration
from utils.config import EDIT_MESH_CHECKS


class StatusCircleWidget(QWidget):
    def __init__(self, p=None):
        super().__init__(p)
        self.setFixedSize(12, 12)
        self._c = QColor("#BDC3C7")  # Default Gray

    def setStatus(self, s):
        cm = {"PASS": "#2ECC71", "FAIL": "#E74C3C", "WARN": "#F1C40F"}
        self._c = QColor(cm.get(s, "#BDC3C7"))
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(self._c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(self.rect())


class WelcomeDetailWidget(QWidget):
    def __init__(self, p=None):
        super().__init__(p)
        l = QVBoxLayout(self)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb = QLabel()
        self.lb.setStyleSheet("font-style:italic; color:#888;")
        l.addWidget(self.lb)

    def retranslate_ui(self):
        self.lb.setText(translator.get("em_welcome_msg"))


class DetailActionWidget(QWidget):
    actionRequested = Signal()

    def __init__(self, p=None):
        super().__init__(p)
        self._current_txt = None
        self._current_btn_key = None
        l = QVBoxLayout(self)
        self.info = QLabel()
        self.info.setWordWrap(True)  # 긴 텍스트 줄바꿈
        self.btn = QPushButton()
        self.btn.setVisible(False)
        l.addWidget(self.info)
        l.addWidget(self.btn)
        l.addStretch(1)
        self.btn.clicked.connect(self.actionRequested.emit)

    def update_info(self, txt=None, btn_key=None):
        self._current_txt = txt
        self._current_btn_key = btn_key
        self._refresh_text()

    def _refresh_text(self):
        # "Value: [1.0, 1.0, 1.0]" 형식 등
        val_lbl = translator.get("lbl_value")
        no_issue_lbl = translator.get("lbl_no_issues")

        if self._current_txt and hasattr(self._current_txt, 'x'):  # Point3 handling
            display_txt = f"{val_lbl} [{self._current_txt.x:.3f}, {self._current_txt.y:.3f}, {self._current_txt.z:.3f}]"
        elif self._current_txt:
            display_txt = f"{val_lbl} {self._current_txt}"
        else:
            display_txt = no_issue_lbl

        self.info.setText(display_txt)

        if self._current_btn_key:
            self.btn.setText(translator.get(self._current_btn_key))
            self.btn.setVisible(True)
        else:
            self.btn.setVisible(False)

    def retranslate_ui(self):
        self._refresh_text()


class EditMeshTab(QWidget):
    refreshRequested = Signal()
    fixScaleRequested = Signal(object)
    fixSkinRequested = Signal(object)
    fixPivotRequested = Signal(object)
    finalizeRequested = Signal(object, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logic = edit_mesh_logic
        self.status_widgets = {}
        self.detail_widgets = {}
        self.current_check_results = {}
        self.current_node = None
        self.inspector_checks_data = EDIT_MESH_CHECKS

        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

    def _create_widgets(self):
        self.refresh_btn = QPushButton()
        self.mesh_list = QListWidget()

        # Table Setup
        self.table = QTableWidget(0, 3)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)  # 깔끔하게
        header = self.table.horizontalHeader()

        # ⭐️ [v1.9.15 Fix] Action Column Stretch
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Check Item (Compact)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Status (Icon)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Action (Fill Space)

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)

        self.details_stack = QStackedWidget()
        self.welcome_detail = WelcomeDetailWidget()
        self.details_stack.addWidget(self.welcome_detail)

        for d in self.inspector_checks_data:
            w = DetailActionWidget()
            self.details_stack.addWidget(w)
            self.detail_widgets[d["id"]] = w

        # Finalize Controls
        self.toggles = {key: OchaAnimatedToggle(40, 20) for key in ["lock", "inherit", "skin", "dq"]}
        for key, toggle in self.toggles.items():
            if key != "dq": toggle.setChecked(True)

        self.spin_bone = QSpinBox()
        self.spin_bone.setRange(1, 100)
        self.spin_bone.setValue(4)

        self.finalize_btn = QPushButton()
        self.finalize_btn.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold; padding: 8px;")

        self.lbl_scene = QLabel()
        self.lbl_lock = QLabel()
        self.lbl_inherit = QLabel()
        self.lbl_skin = QLabel()
        self.lbl_dq = QLabel()
        self.lbl_bone = QLabel()

        self.grp_inspector = QGroupBox()
        self.grp_details = QGroupBox()
        self.grp_finalize = QGroupBox()

        self._on_toggle_skin_options(self.toggles["skin"].isChecked())

    def _setup_layout(self):
        main = QHBoxLayout(self)
        main.setContentsMargins(10, 10, 10, 10)

        # Left Panel (Mesh List)
        left_w = QWidget()
        left_w.setFixedWidth(130)
        left = QVBoxLayout(left_w)
        left.addWidget(self.lbl_scene)
        left.addWidget(self.refresh_btn)
        left.addWidget(self.mesh_list)

        # Right Panel (Splitter)
        right_split = QSplitter(Qt.Orientation.Vertical)

        l1 = QVBoxLayout(self.grp_inspector)
        l1.setSpacing(5);
        l1.setContentsMargins(5, 15, 5, 5)
        l1.addWidget(self.table)

        l2 = QVBoxLayout(self.grp_details)
        l2.setSpacing(5);
        l2.setContentsMargins(5, 15, 5, 5)
        l2.addWidget(self.details_stack)

        l3 = QVBoxLayout(self.grp_finalize)
        l3.setSpacing(8);
        l3.setContentsMargins(10, 20, 10, 10)

        # Finalize Rows
        rows = [
            (self.lbl_lock, self.toggles["lock"]),
            (self.lbl_inherit, self.toggles["inherit"]),
            (self.lbl_skin, self.toggles["skin"]),
            (self.lbl_dq, self.toggles["dq"]),
            (self.lbl_bone, self.spin_bone)
        ]
        for lb, w in rows:
            h = QHBoxLayout()
            h.addWidget(lb)
            h.addStretch(1)
            h.addWidget(w)
            l3.addLayout(h)

        l3.addStretch(1)
        l3.addWidget(self.finalize_btn)

        right_split.addWidget(self.grp_inspector)
        right_split.addWidget(self.grp_details)
        right_split.addWidget(self.grp_finalize)
        # Ratio 2:1:2
        right_split.setStretchFactor(0, 2)
        right_split.setStretchFactor(1, 1)
        right_split.setStretchFactor(2, 2)

        main.addWidget(left_w)
        main.addWidget(right_split, 1)

        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self.inspector_checks_data))
        for r, data in enumerate(self.inspector_checks_data):
            self.table.setItem(r, 0, QTableWidgetItem())  # Title

            # Status Widget
            st_w = StatusCircleWidget()
            c_w = QWidget();
            h = QHBoxLayout(c_w);
            h.setContentsMargins(0, 0, 0, 0);
            h.setAlignment(Qt.AlignmentFlag.AlignCenter);
            h.addWidget(st_w)
            self.table.setCellWidget(r, 1, c_w)
            self.status_widgets[data["id"]] = st_w

            # Detail Button
            btn = QPushButton()
            btn.clicked.connect(functools.partial(self._on_show_details, r))
            self.table.setCellWidget(r, 2, btn)

    def retranslate_ui(self):
        # Titles
        self.refresh_btn.setText(translator.get("em_refresh_btn"))
        self.lbl_scene.setText(translator.get("em_scene_meshes"))
        self.finalize_btn.setText(translator.get("em_btn_finalize"))

        # Group Boxes
        self.grp_inspector.setTitle(translator.get("em_grp_inspector"))
        self.grp_details.setTitle(translator.get("em_grp_details"))
        self.grp_finalize.setTitle(translator.get("em_grp_finalize"))

        # Finalize Options & Tooltips
        self.lbl_lock.setText(translator.get("em_opt_lock"));
        self.lbl_lock.setToolTip(translator.get("tip_em_lock"))
        self.lbl_inherit.setText(translator.get("em_opt_inherit"));
        self.lbl_inherit.setToolTip(translator.get("tip_em_inherit"))
        self.lbl_skin.setText(translator.get("em_opt_skin"));
        self.lbl_skin.setToolTip(translator.get("tip_em_skin"))
        self.lbl_dq.setText(translator.get("em_opt_dq"));
        self.lbl_dq.setToolTip(translator.get("tip_em_dq"))
        self.lbl_bone.setText(translator.get("em_opt_limit"));
        self.lbl_bone.setToolTip(translator.get("tip_em_limit"))

        # Table Headers
        self.table.setHorizontalHeaderLabels([
            translator.get("em_col_check"), translator.get("em_col_status"), translator.get("em_col_details")
        ])

        # Table Items
        btn_text = translator.get("btn_show_details")
        for r, data in enumerate(self.inspector_checks_data):
            # Check Name
            if self.table.item(r, 0):
                name_text = translator.get(data["label_key"])
                self.table.item(r, 0).setText(name_text)
                # Add tooltip for row based on 'info_key'
                self.table.item(r, 0).setToolTip(translator.get(data.get("info_key", "")))

            btn = self.table.cellWidget(r, 2)
            if btn: btn.setText(btn_text)

        # Detail Widgets
        self.welcome_detail.retranslate_ui()
        for w in self.detail_widgets.values():
            w.retranslate_ui()

        # Mesh List Placeholder
        if self.mesh_list.count() == 0 or self.mesh_list.item(0).data(Qt.ItemDataRole.UserRole) is None:
            self.mesh_list.clear()
            self.mesh_list.addItem(translator.get("msg_no_mesh"))

    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.mesh_list.itemSelectionChanged.connect(self._on_select)
        self.finalize_btn.clicked.connect(self._on_finalize)
        self.toggles["skin"].toggled.connect(self._on_toggle_skin_options)

        # Hardcoded ID connections (mapped to config IDs)
        if "non_uniform_scale" in self.detail_widgets:
            self.detail_widgets["non_uniform_scale"].actionRequested.connect(
                lambda: self.fixScaleRequested.emit(self.current_node) if self.current_node else None)
        if "existing_skin" in self.detail_widgets:
            self.detail_widgets["existing_skin"].actionRequested.connect(
                lambda: self.fixSkinRequested.emit(self.current_node) if self.current_node else None)
        if "pivot_not_at_origin" in self.detail_widgets:
            self.detail_widgets["pivot_not_at_origin"].actionRequested.connect(
                lambda: self.fixPivotRequested.emit(self.current_node) if self.current_node else None)

    def _on_toggle_skin_options(self, on):
        self.toggles["dq"].setEnabled(on)
        self.spin_bone.setEnabled(on)

    def _on_finalize(self):
        if not self.current_node:
            return QMessageBox.warning(self, translator.get("title_error"), translator.get("msg_select_mesh"))
        opts = {
            "lock_transforms": self.toggles["lock"].isChecked(),
            "enable_inheritance": self.toggles["inherit"].isChecked(),
            "add_skin": self.toggles["skin"].isChecked(),
            "use_dq": self.toggles["dq"].isChecked(),
            "bone_limit": self.spin_bone.value()
        }
        self.finalizeRequested.emit(self.current_node, opts)

    def _on_show_details(self, r):
        self.table.selectRow(r)
        data = self.inspector_checks_data[r]
        w = self.detail_widgets.get(data["id"])
        if w:
            self.details_stack.setCurrentWidget(w)
            res = self.current_check_results.get(data["id"])

            if res and res.get("has_issue"):
                fix_key = data.get("fix_key")
                value = res.get("value")
            else:
                fix_key = None
                value = None

            w.update_info(value, fix_key)

    def _on_refresh(self):
        # Preserve selection logic omitted for brevity, essentially full refresh
        self.mesh_list.clear()
        self._reset_inspector()
        meshes = self.logic.get_scene_meshes()

        if not meshes:
            self.mesh_list.addItem(translator.get("msg_no_mesh"))
            return

        pd = QProgressDialog(translator.get("msg_scanning"), translator.get("btn_cancel"), 0, len(meshes), self)
        pd.setMinimumDuration(0)
        pd.setWindowModality(Qt.WindowModality.WindowModal)

        for i, m in enumerate(meshes):
            pd.setValue(i)
            QApplication.processEvents()
            if pd.wasCanceled(): break

            item = QListWidgetItem(m["name"])
            res = self.logic.run_all_checks(m["node"])
            if any(r and r.get("has_issue") for r in res.values()):
                item.setForeground(QColor("#E74C3C"))  # Issue Color
            item.setData(Qt.ItemDataRole.UserRole, {"node": m["node"], "results": res})
            self.mesh_list.addItem(item)

        pd.setValue(len(meshes))
        if self.mesh_list.count() > 0:
            self.mesh_list.setCurrentRow(0)

    def _on_select(self):
        self._reset_inspector()
        items = self.mesh_list.selectedItems()
        if not items:
            self.finalize_btn.setEnabled(False)
            return
        data = items[0].data(Qt.ItemDataRole.UserRole)
        if not data: return

        self.current_node = data["node"]
        self.current_check_results = data.get("results", {})
        self.finalize_btn.setEnabled(True)

        for cid, w in self.status_widgets.items():
            r = self.current_check_results.get(cid)
            w.setStatus("FAIL" if r and r.get("has_issue") else "PASS")

        if self.table.currentRow() >= 0:
            self._on_show_details(self.table.currentRow())
        else:
            self._on_show_details(0)

    def _reset_inspector(self):
        self.current_node = None
        self.current_check_results.clear()
        self.details_stack.setCurrentIndex(0)  # Welcome
        self.table.clearSelection()
        self.finalize_btn.setEnabled(False)
        for w in self.status_widgets.values():
            w.setStatus("NOT_CHECKED")


rt.print("✅ [Import Check] FINISHED loading ui.tabs.edit_mesh_tab.")