# ohCHA_RigManager/01/src/ui/tabs/rigging_tab.py
# Description: [v21.46] RIGGING TAB FULL.
#              - FIXED: retranslate_ui refreshes names properly.

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QCheckBox, QTabWidget, QGridLayout, QMessageBox, QScrollArea,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QAbstractItemView, QSplitter,
    QLineEdit, QFrame, QGroupBox, QRadioButton, QButtonGroup, QColorDialog,
    QSizePolicy, QAbstractSpinBox, QComboBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QCursor

try:
    from ui.ohcha_ui_widgets import OchaCollapsibleGroup, OchaAnimatedToggle, OchaControllerInspector, OchaStyledButton
except ImportError:
    # Dummy classes
    class OchaAnimatedToggle(QCheckBox):
        pass


    class OchaStyledButton(QPushButton):
        pass


    class OchaCollapsibleGroup(QGroupBox):
        def setHeaderText(self, t): self.setTitle(t)

        def setContentLayout(self, l): self.setLayout(l)


    class OchaControllerInspector(QWidget):
        pass

try:
    from ui.tabs.layer_tool import LayerToolWidget
except ImportError:
    LayerToolWidget = None

try:
    from ui.tabs.naming_tool import NamingToolWidget
except ImportError:
    NamingToolWidget = None

from controllers.rigging_controller import rigging_controller_instance
from pymxs import runtime as rt
from utils.translator import translator


class GuideExplorerWidget(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._current_guide_name = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        self.lbl_title = QLabel()
        self.lbl_title.setStyleSheet("color: #DDD; font-weight: bold; font-size: 12px;")

        self.search_bar = QLineEdit()
        self.search_bar.setStyleSheet(
            "background-color: #222; border: 1px solid #444; padding: 4px; border-radius: 3px;")
        self.search_bar.textChanged.connect(self._filter_list)

        header_layout.addWidget(self.lbl_title)
        header_layout.addWidget(self.search_bar)
        layout.addLayout(header_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(15)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setStyleSheet(
            "QTreeWidget { background-color: #2b2b2b; border: 1px solid #444; border-radius: 3px; } QTreeWidget::item { padding: 4px; } QTreeWidget::item:selected { background-color: #007ACC; }")
        layout.addWidget(self.tree)

        tools_layout = QVBoxLayout()
        tools_layout.setSpacing(4)

        self.btn_snap = QPushButton()
        self.btn_snap.setStyleSheet(
            "QPushButton { background-color: #8E44AD; color: white; font-weight: bold; padding: 8px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #9B59B6; }")

        self.btn_mirror = QPushButton()
        self.btn_mirror.setStyleSheet(
            "QPushButton { background-color: #2980B9; color: white; font-weight: bold; padding: 8px; border-radius: 4px; border: none; } QPushButton:hover { background-color: #3498DB; }")

        tools_layout.addWidget(self.btn_snap)
        tools_layout.addWidget(self.btn_mirror)
        layout.addLayout(tools_layout)

        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.btn_mirror.clicked.connect(self._on_mirror_clicked)
        self.btn_snap.clicked.connect(self._on_snap_clicked)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.lbl_title.setText(translator.get("rig_lbl_guide_expl"))
        self.search_bar.setPlaceholderText(translator.get("rig_ph_search"))
        self.btn_snap.setText(translator.get("rig_btn_snap"))
        self.btn_mirror.setText(translator.get("rig_btn_mirror"))

    def refresh_list(self):
        data = self.controller.get_guide_data()
        self.tree.clear()
        self.search_bar.clear()
        lookup = {}

        for g in data:
            item = QTreeWidgetItem([g['name']])
            item.setData(0, Qt.ItemDataRole.UserRole, g['name'])
            lookup[g['handle']] = item
            if g['parent_handle'] == "0":
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
                item.setForeground(0, QColor("#3498DB"))

        for g in data:
            if g['handle'] not in lookup: continue
            item = lookup[g['handle']]
            parent_handle = g.get('parent_handle')
            if parent_handle and parent_handle in lookup:
                lookup[parent_handle].addChild(item)
            else:
                self.tree.addTopLevelItem(item)
        self.tree.expandAll()

    def _filter_list(self, text):
        search_text = text.lower()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._apply_filter_recursive(root.child(i), search_text)

    def _apply_filter_recursive(self, item, text):
        name = item.text(0).lower()
        match = text in name
        child_match = False
        for i in range(item.childCount()):
            if self._apply_filter_recursive(item.child(i), text):
                child_match = True
        should_show = match or child_match
        item.setHidden(not should_show)
        if should_show: item.setExpanded(True)
        return should_show

    def _on_item_clicked(self, item, column):
        self._current_guide_name = item.data(0, Qt.ItemDataRole.UserRole)

    def _on_item_double_clicked(self, item, column):
        name = item.data(0, Qt.ItemDataRole.UserRole)
        if name:
            try:
                node = rt.getNodeByName(name)
                if node: rt.select(node)
            except:
                pass

    def _on_mirror_clicked(self):
        self.controller.mirror_guides()

    def _on_snap_clicked(self):
        if not self._current_guide_name:
            QMessageBox.warning(self, "Snap", "Please select a guide first.")
            return
        if not self.controller.snap_guide_to_selection(self._current_guide_name):
            QMessageBox.warning(self, "Snap Failed", "Select Mesh Vertices first.")


class RiggingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = rigging_controller_instance
        self.col_start = QColor(255, 0, 0)
        self.col_end = QColor(0, 0, 255)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; top: -1px; background-color: #2b2b2b; }
            QTabBar::tab { background: #333; color: #AAA; padding: 8px 12px; border: 1px solid #222; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #444; color: white; font-weight: bold; border-bottom: 1px solid #444; }
            QTabBar::tab:hover { background: #3E3E3E; }
        """)

        self.tab_biped = QWidget()
        self.tab_bone = QWidget()
        self.tab_layers = QWidget()
        self.tab_naming = QWidget()
        self.tab_picker = QWidget()
        self.tab_pose = QWidget()

        self.tabs.addTab(self.tab_biped, "Biped")
        self.tabs.addTab(self.tab_bone, "Bone")
        self.tabs.addTab(self.tab_layers, "Layers")
        self.tabs.addTab(self.tab_naming, "Naming")
        self.tabs.addTab(self.tab_picker, "Picker")
        self.tabs.addTab(self.tab_pose, "Pose")

        self._init_biped_tab()
        self._init_bone_tab()
        self._init_layers_tab()
        self._init_naming_tab()
        self._init_pose_tab()
        self._init_placeholder(self.tab_picker, "Anim Picker")

        main_layout.addWidget(self.tabs)
        self.retranslate_ui()

    def retranslate_ui(self):
        # [FIX] Tabs Names are now translated properly
        self.tabs.setTabText(0, translator.get("rig_tab_biped"))
        self.tabs.setTabText(1, translator.get("rig_tab_bone"))
        self.tabs.setTabText(2, translator.get("rig_tab_layers"))
        self.tabs.setTabText(3, translator.get("rig_tab_naming"))
        self.tabs.setTabText(4, translator.get("rig_tab_picker"))
        self.tabs.setTabText(5, translator.get("rig_tab_pose"))

        # Biped Tab
        self.grp_struct.setHeaderText(translator.get("rig_grp_struct"))
        self.lbl_spine.setText(translator.get("rig_lbl_spine"))
        self.lbl_neck.setText(translator.get("rig_lbl_neck"))
        self.chk_tri_pelvis.setText(translator.get("rig_chk_tripelvis"))
        self.chk_tri_neck.setText(translator.get("rig_chk_trineck"))
        self.lbl_finger.setText(translator.get("rig_lbl_fingers"))
        self.lbl_flink.setText(translator.get("rig_lbl_flinks"))
        self.lbl_toe.setText(translator.get("rig_lbl_toes"))
        self.lbl_tlink.setText(translator.get("rig_lbl_tlinks"))
        self.lbl_leglink.setText(translator.get("rig_lbl_leglinks"))
        self.lbl_tail.setText(translator.get("rig_lbl_tail"))
        self.lbl_pony1.setText(translator.get("rig_lbl_pony1"))
        self.lbl_pony2.setText(translator.get("rig_lbl_pony2"))

        self._update_workflow_header(self.grp_work.btn.isChecked())
        self.btn_step1.setText(translator.get("rig_btn_create_guides"))
        self.btn_step2.setText(translator.get("rig_btn_align_short"))
        self.btn_step3.setText(translator.get("rig_btn_gen_biped"))
        self.guide_explorer.retranslate_ui()

        # Bone Tab
        self.grp_create.setHeaderText(translator.get("bone_grp_create"))
        self.lbl_bname.setText(translator.get("bone_lbl_base"))
        self.lbl_cnt.setText(translator.get("bone_lbl_cnt"))
        self.btn_create_bone.setText(translator.get("bone_btn_create"))

        self.grp_opt.setHeaderText(translator.get("bone_grp_opt"))
        self.lbl_wh.setText(translator.get("bone_lbl_wh"))
        self.lbl_taper.setText(translator.get("bone_lbl_taper"))
        self.btn_fin_side.setText(translator.get("bone_btn_fin_side"))
        self.btn_fin_front.setText(translator.get("bone_btn_fin_front"))
        self.btn_fin_back.setText(translator.get("bone_btn_fin_back"))

        self.grp_mirror.setHeaderText(translator.get("bone_grp_mirror"))
        self.lbl_axis.setText(translator.get("bone_lbl_axis"))
        self.lbl_flip.setText(translator.get("bone_lbl_flip"))
        self.lbl_offset.setText(translator.get("bone_lbl_offset"))
        self.lbl_gizmo.setText(translator.get("bone_lbl_gizmo_size"))
        self.btn_mirror_helper.setText(translator.get("bone_btn_helper"))
        self.btn_mirror_run.setText(translator.get("bone_btn_mirror"))

        self.grp_color.setHeaderText(translator.get("bone_grp_color"))
        self.btn_grad.setText(translator.get("bone_chk_grad"))
        self.btn_apply_col.setText(translator.get("bone_btn_color_apply"))

        self.grp_stretch.setHeaderText(translator.get("bone_grp_stretch"))
        self.lbl_stretch_hint.setText(translator.get("bone_lbl_stretch_hint"))
        self.btn_apply_stretch.setText(translator.get("bone_btn_apply_stretch"))

        self.grp_ctrl.setHeaderText(translator.get("bone_grp_ctrl"))

        self.grp_twist.setHeaderText(translator.get("rig_grp_twist"))
        self.lbl_twist_cnt.setText(translator.get("rig_lbl_twist_count"))
        self.lbl_mode.setText(translator.get("rig_lbl_twist_mode"))
        self.lbl_mode_parent.setText(translator.get("rig_mode_parent"))
        self.lbl_mode_child.setText(translator.get("rig_mode_child"))
        self.btn_create_twist.setText(translator.get("rig_btn_create_twist_run"))

        self.grp_inspector.setHeaderText(translator.get("rig_grp_inspector"))
        if hasattr(self, "inspector_widget"):
            self.inspector_widget.retranslate_ui()

        # Pose Tab
        self.grp_pose.setHeaderText(translator.get("rig_grp_transform"))
        self.btn_copy.setText(translator.get("rig_btn_copy_pose"))
        self.btn_paste.setText(translator.get("rig_btn_paste_pose"))
        self.btn_mirror_paste.setText(translator.get("rig_btn_mirror_paste"))
        self.chk_pos.setText(translator.get("rig_chk_pos"))
        self.chk_rot.setText(translator.get("rig_chk_rot"))

        if hasattr(self, "layer_tool_widget") and self.layer_tool_widget:
            self.layer_tool_widget.retranslate_ui()
        if hasattr(self, "naming_tool_widget") and self.naming_tool_widget:
            self.naming_tool_widget.retranslate_ui()

    def _init_biped_tab(self):
        main_tab_layout = QHBoxLayout(self.tab_biped)
        main_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.biped_splitter = QSplitter(Qt.Orientation.Horizontal)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setStyleSheet("QScrollArea { background-color: #2b2b2b; }")

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(15)

        self.grp_struct = OchaCollapsibleGroup("1. Structure Settings", expanded=True)
        gl = QGridLayout()
        gl.setSpacing(10)
        gl.setContentsMargins(10, 15, 10, 15)
        gl.setColumnStretch(1, 1)
        gl.setColumnStretch(3, 1)

        self.spn_spine, self.lbl_spine = self._add_spin(gl, 0, 0, "Spine:", 4, 1, 4)
        self.spn_neck, self.lbl_neck = self._add_spin(gl, 0, 2, "Neck:", 1, 1, 2)
        self.spn_finger, self.lbl_finger = self._add_spin(gl, 1, 0, "Fingers:", 5, 0, 5)
        self.spn_flink, self.lbl_flink = self._add_spin(gl, 1, 2, "F. Links:", 3, 1, 3)
        self.spn_toe, self.lbl_toe = self._add_spin(gl, 2, 0, "Toes:", 1, 1, 5)
        self.spn_tlink, self.lbl_tlink = self._add_spin(gl, 2, 2, "T. Links:", 1, 1, 3)
        self.spn_leglink, self.lbl_leglink = self._add_spin(gl, 3, 0, "Leg Links:", 3, 3, 4)
        self.spn_tail, self.lbl_tail = self._add_spin(gl, 3, 2, "Tail:", 0, 0, 5)
        self.spn_pony1, self.lbl_pony1 = self._add_spin(gl, 4, 0, "Pony 1:", 0, 0, 5)
        self.spn_pony2, self.lbl_pony2 = self._add_spin(gl, 4, 2, "Pony 2:", 0, 0, 5)

        self.chk_tri_pelvis = OchaStyledButton("Tri Pelvis")
        self.chk_tri_neck = OchaStyledButton("Tri Neck")
        self.chk_tri_neck.setChecked(True)
        gl.addWidget(self.chk_tri_pelvis, 5, 0, 1, 2)
        gl.addWidget(self.chk_tri_neck, 5, 2, 1, 2)

        self.grp_struct.setContentLayout(gl)
        left_layout.addWidget(self.grp_struct)

        self.grp_work = OchaCollapsibleGroup("2. Workflow", expanded=True)
        self.grp_work.btn.toggled.connect(self._update_workflow_header)

        vl = QVBoxLayout()
        vl.setSpacing(10)
        vl.setContentsMargins(5, 5, 5, 5)

        self.btn_step1 = QPushButton("1. Create Guides")
        self.btn_step1.clicked.connect(self._on_create_guides)
        self.btn_step1.setStyleSheet(self._get_workflow_button_style("#C0392B", "#E74C3C", "#922B21"))

        self.btn_step2 = QPushButton("2. Align")
        self.btn_step2.clicked.connect(self._on_align_guides)
        self.btn_step2.setStyleSheet(self._get_workflow_button_style("#D35400", "#E67E22", "#A04000"))

        self.btn_step3 = QPushButton("3. Finalize")
        self.btn_step3.clicked.connect(self._on_finalize)
        self.btn_step3.setStyleSheet(self._get_workflow_button_style("#27AE60", "#2ECC71", "#1E8449"))

        vl.addWidget(self.btn_step1)
        vl.addWidget(self.btn_step2)
        vl.addWidget(self.btn_step3)
        self.grp_work.setContentLayout(vl)
        left_layout.addWidget(self.grp_work)
        left_layout.addStretch()

        left_scroll.setWidget(left_widget)

        self.guide_explorer_container = QWidget()
        right_layout = QVBoxLayout(self.guide_explorer_container)
        right_layout.setContentsMargins(5, 5, 5, 5)
        self.guide_explorer = GuideExplorerWidget(self.controller)
        right_layout.addWidget(self.guide_explorer)
        self.guide_explorer_container.setVisible(False)

        self.biped_splitter.addWidget(left_scroll)
        self.biped_splitter.addWidget(self.guide_explorer_container)
        self.biped_splitter.setStretchFactor(0, 1)
        self.biped_splitter.setStretchFactor(1, 0)
        main_tab_layout.addWidget(self.biped_splitter)

    def _init_bone_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        l = QVBoxLayout(content)
        l.setSpacing(10)
        l.setContentsMargins(10, 10, 10, 10)

        # 1. Creation
        self.grp_create = OchaCollapsibleGroup("Creation", expanded=True)
        gc = QVBoxLayout()
        gc.setSpacing(8)

        row1 = QHBoxLayout()
        self.lbl_bname = QLabel("Name:")
        self.txt_bname = QLineEdit("Bone")
        self.lbl_cnt = QLabel("Count:")
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 100)
        self.spin_count.setValue(1)
        row1.addWidget(self.lbl_bname)
        row1.addWidget(self.txt_bname)
        row1.addWidget(self.lbl_cnt)
        row1.addWidget(self.spin_count)

        row2 = QHBoxLayout()
        self.lbl_wh = QLabel("W/H:")
        self.spin_width = QSpinBox()
        self.spin_width.setValue(4)
        self.spin_width.setRange(1, 1000)
        self.spin_height = QSpinBox()
        self.spin_height.setValue(4)
        self.spin_height.setRange(1, 1000)
        self.lbl_taper = QLabel("Taper:")
        self.spin_taper = QSpinBox()
        self.spin_taper.setValue(90)
        self.spin_taper.setRange(0, 100)
        for sp in [self.spin_width, self.spin_height, self.spin_taper]:
            sp.setStyleSheet("background-color:#333; color:#EEE;")
        row2.addWidget(self.lbl_wh)
        row2.addWidget(self.spin_width)
        row2.addWidget(self.spin_height)
        row2.addWidget(self.lbl_taper)
        row2.addWidget(self.spin_taper)

        row3 = QHBoxLayout()
        self.btn_fin_side = OchaStyledButton("Side Fin")
        self.btn_fin_front = OchaStyledButton("Front Fin")
        self.btn_fin_back = OchaStyledButton("Back Fin")
        row3.addWidget(self.btn_fin_side)
        row3.addWidget(self.btn_fin_front)
        row3.addWidget(self.btn_fin_back)

        self.btn_create_bone = QPushButton("Create Bone Chain")
        self.btn_create_bone.setFixedHeight(35)
        self.btn_create_bone.setStyleSheet(
            "background-color: #27AE60; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_create_bone.clicked.connect(self._on_create_bone)

        gc.addLayout(row1)
        gc.addLayout(row2)
        gc.addLayout(row3)
        gc.addWidget(self.btn_create_bone)
        self.grp_create.setContentLayout(gc)
        l.addWidget(self.grp_create)

        # 2. Options
        self.grp_opt = OchaCollapsibleGroup("Options", expanded=False)
        go = QGridLayout()
        self.grp_opt.setContentLayout(go)

        # 3. Mirror
        self.grp_mirror = OchaCollapsibleGroup("Mirror Tool", expanded=False)
        gm = QVBoxLayout()
        hbox1 = QHBoxLayout()
        self.combo_axis = QComboBox()
        self.combo_axis.addItems(["X", "Y", "Z", "XY", "YZ", "ZX"])
        self.combo_axis.setCurrentText("X")
        self.combo_axis.setStyleSheet(
            "QComboBox { background-color: #333; border: 1px solid #555; padding: 4px; border-radius: 4px; }")
        self.lbl_axis = QLabel("Axis:")
        hbox1.addWidget(self.lbl_axis)
        hbox1.addWidget(self.combo_axis)

        hbox2 = QHBoxLayout()
        self.rad_fy = QRadioButton("Y")
        self.rad_fz = QRadioButton("Z")
        self.rad_fn = QRadioButton("None")
        self.rad_fn.setChecked(True)
        self.grp_flip = QButtonGroup()
        self.grp_flip.addButton(self.rad_fy)
        self.grp_flip.addButton(self.rad_fz)
        self.grp_flip.addButton(self.rad_fn)
        self.lbl_flip = QLabel("Flip:")
        hbox2.addWidget(self.lbl_flip)
        hbox2.addWidget(self.rad_fy)
        hbox2.addWidget(self.rad_fz)
        hbox2.addWidget(self.rad_fn)

        hbox3 = QHBoxLayout()
        self.spin_offset = QSpinBox()
        self.spin_offset.setRange(-1000, 1000)
        self.spin_gizmo = QSpinBox()
        self.spin_gizmo.setValue(20)
        self.spin_gizmo.setRange(1, 1000)
        self.lbl_offset = QLabel("Offset:")
        self.lbl_gizmo = QLabel("Gizmo Size:")
        hbox3.addWidget(self.lbl_offset)
        hbox3.addWidget(self.spin_offset)
        hbox3.addWidget(self.lbl_gizmo)
        hbox3.addWidget(self.spin_gizmo)

        hbox4 = QHBoxLayout()
        self.btn_mirror_helper = QPushButton("Create Gizmo")
        self.btn_mirror_helper.clicked.connect(lambda: self.controller.create_mirror_gizmo(self.spin_gizmo.value()))
        self.btn_mirror_run = QPushButton("Mirror Bones")
        self.btn_mirror_run.setStyleSheet("background-color: #8E44AD; color: white; font-weight: bold;")
        self.btn_mirror_run.clicked.connect(self._on_mirror)
        hbox4.addWidget(self.btn_mirror_helper)
        hbox4.addWidget(self.btn_mirror_run)

        gm.addLayout(hbox1)
        gm.addLayout(hbox2)
        gm.addLayout(hbox3)
        gm.addLayout(hbox4)
        self.grp_mirror.setContentLayout(gm)
        l.addWidget(self.grp_mirror)

        # 4. Colorize
        self.grp_color = OchaCollapsibleGroup("Colorize", expanded=False)
        gcol = QHBoxLayout()
        self.btn_col1 = QPushButton()
        self.btn_col1.setFixedSize(40, 26)
        self.btn_col1.setStyleSheet(f"background-color: {self.col_start.name()}; border: 1px solid #555;")
        self.btn_col1.clicked.connect(lambda: self._pick_color(True))

        self.btn_col2 = QPushButton()
        self.btn_col2.setFixedSize(40, 26)
        self.btn_col2.setStyleSheet(f"background-color: {self.col_end.name()}; border: 1px solid #555;")
        self.btn_col2.clicked.connect(lambda: self._pick_color(False))

        self.btn_grad = OchaStyledButton("Gradient")
        self.btn_grad.setFixedWidth(80)
        self.btn_apply_col = QPushButton("Apply")
        self.btn_apply_col.setStyleSheet("background-color: #555; color: white;")
        self.btn_apply_col.clicked.connect(self._on_color_apply)

        gcol.addWidget(self.btn_col1)
        gcol.addWidget(self.btn_col2)
        gcol.addWidget(self.btn_grad)
        gcol.addWidget(self.btn_apply_col)
        self.grp_color.setContentLayout(gcol)
        l.addWidget(self.grp_color)

        # 5. Stretch
        self.grp_stretch = OchaCollapsibleGroup("Stretch Tool", expanded=False)
        gs = QVBoxLayout()
        self.btn_apply_stretch = QPushButton("Apply Stretch to Selection")
        self.btn_apply_stretch.setFixedHeight(30)
        self.btn_apply_stretch.setStyleSheet("background-color: #D35400; color: white; font-weight: bold;")
        self.btn_apply_stretch.clicked.connect(self._on_apply_stretch)
        self.lbl_stretch_hint = QLabel("Select bones and click Apply.")
        gs.addWidget(self.lbl_stretch_hint)
        gs.addWidget(self.btn_apply_stretch)
        self.grp_stretch.setContentLayout(gs)
        l.addWidget(self.grp_stretch)

        # 6. Controllers
        self.grp_ctrl = OchaCollapsibleGroup("Create Controllers", expanded=False)
        gctrl = QHBoxLayout()
        for shp in ["Pin", "Box", "Circle"]:
            b = QPushButton(shp)
            b.setStyleSheet("background-color: #444; color: white;")
            b.clicked.connect(lambda c=False, s=shp: self.controller.create_controller(s))
            gctrl.addWidget(b)
        self.grp_ctrl.setContentLayout(gctrl)
        l.addWidget(self.grp_ctrl)

        # 7. Twist (Updated to Collapsible)
        self.grp_twist = OchaCollapsibleGroup("Twist Bone Tool", expanded=False)
        gt = QVBoxLayout()

        row_cnt = QHBoxLayout()
        self.lbl_twist_cnt = QLabel("Count:")
        self.spin_twist_cnt = QSpinBox()
        self.spin_twist_cnt.setRange(2, 10)
        self.spin_twist_cnt.setValue(2)
        row_cnt.addWidget(self.lbl_twist_cnt)
        row_cnt.addWidget(self.spin_twist_cnt)

        row_mode = QHBoxLayout()
        self.lbl_mode = QLabel("Mode:")
        self.lbl_mode_parent = QLabel("Parent")
        self.toggle_mode = OchaAnimatedToggle()
        self.lbl_mode_child = QLabel("Child")
        row_mode.addWidget(self.lbl_mode)
        row_mode.addWidget(self.lbl_mode_parent)
        row_mode.addWidget(self.toggle_mode)
        row_mode.addWidget(self.lbl_mode_child)

        self.btn_create_twist = QPushButton("Create Twist Bones")
        self.btn_create_twist.setStyleSheet("background-color: #8E44AD; color: white; font-weight: bold;")
        self.btn_create_twist.clicked.connect(self._on_create_twist_batch)

        gt.addLayout(row_cnt)
        gt.addLayout(row_mode)
        gt.addWidget(self.btn_create_twist)

        self.grp_twist.setContentLayout(gt)
        l.addWidget(self.grp_twist)

        # 8. Inspector (Updated to Collapsible)
        self.grp_inspector = OchaCollapsibleGroup("Controller Inspector", expanded=False)
        gi = QVBoxLayout()
        gi.setContentsMargins(0, 0, 0, 0)
        self.inspector_widget = OchaControllerInspector(self.controller)
        gi.addWidget(self.inspector_widget)
        self.grp_inspector.setContentLayout(gi)
        l.addWidget(self.grp_inspector)

        l.addStretch()
        scroll.setWidget(content)
        tab_l = QVBoxLayout(self.tab_bone)
        tab_l.setContentsMargins(0, 0, 0, 0)
        tab_l.addWidget(scroll)

    def _on_create_bone(self):
        name = self.txt_bname.text()
        cnt = self.spin_count.value()
        w = self.spin_width.value()
        h = self.spin_height.value()
        t = self.spin_taper.value()
        fin_flags = {"side": self.btn_fin_side.isChecked(), "front": self.btn_fin_front.isChecked(),
                     "back": self.btn_fin_back.isChecked()}
        self.controller.create_bone_chain(name, cnt, w, h, t, fin_flags)

    def _on_apply_stretch(self):
        self.controller.apply_stretch_to_selection()

    def _on_mirror(self):
        axis = self.combo_axis.currentText()
        flip = "None"
        if self.rad_fy.isChecked(): flip = "Y"
        if self.rad_fz.isChecked(): flip = "Z"
        self.controller.mirror_bones(axis, flip, self.spin_offset.value())

    def _pick_color(self, is_start):
        c = QColorDialog.getColor()
        if c.isValid():
            if is_start:
                self.col_start = c; self.btn_col1.setStyleSheet(
                    f"background-color: {c.name()}; border: 1px solid #555;")
            else:
                self.col_end = c; self.btn_col2.setStyleSheet(f"background-color: {c.name()}; border: 1px solid #555;")

    def _on_color_apply(self):
        self.controller.color_bones(self.col_start, self.col_end, self.btn_grad.isChecked())

    def _on_create_twist_batch(self):
        count = self.spin_twist_cnt.value();
        is_child = self.toggle_mode.isChecked()
        if not self.controller.create_twist_bones_batch(count, is_child): QMessageBox.warning(self, translator.get(
            "title_error"), "Selection is empty or invalid.")

    def _init_layers_tab(self):
        l = QVBoxLayout(self.tab_layers)
        l.setContentsMargins(0, 0, 0, 0)
        if LayerToolWidget:
            self.layer_tool_widget = LayerToolWidget()
            l.addWidget(self.layer_tool_widget)
        else:
            l.addWidget(QLabel("Layer Tool Missing"))

    def _init_naming_tab(self):
        l = QVBoxLayout(self.tab_naming)
        l.setContentsMargins(0, 0, 0, 0)
        if NamingToolWidget:
            self.naming_tool_widget = NamingToolWidget()
            l.addWidget(self.naming_tool_widget)
        else:
            l.addWidget(QLabel("Naming Tool Missing"))

    def _init_pose_tab(self):
        l = QVBoxLayout(self.tab_pose)
        l.setContentsMargins(10, 10, 10, 10)
        self.grp_pose = OchaCollapsibleGroup("Pose", expanded=True)
        vl = QVBoxLayout()
        vl.setSpacing(8)
        row1 = QHBoxLayout()
        self.btn_copy = QPushButton("Copy")
        self.btn_copy.setStyleSheet("padding: 8px; font-weight: bold; border: none;")
        self.btn_copy.clicked.connect(self.controller.copy_pose)
        self.btn_paste = QPushButton("Paste")
        self.btn_paste.setStyleSheet("padding: 8px; font-weight: bold; border: none;")
        self.btn_paste.clicked.connect(
            lambda: self.controller.paste_pose(self.chk_pos.isChecked(), self.chk_rot.isChecked()))
        row1.addWidget(self.btn_copy)
        row1.addWidget(self.btn_paste)
        row_opt = QHBoxLayout()
        self.chk_pos = QCheckBox("Pos")
        self.chk_pos.setChecked(True)
        self.chk_rot = QCheckBox("Rot")
        self.chk_rot.setChecked(True)
        row_opt.addStretch()
        row_opt.addWidget(self.chk_pos)
        row_opt.addWidget(self.chk_rot)
        self.btn_mirror_paste = QPushButton("Mirror Paste")
        self.btn_mirror_paste.setStyleSheet("padding: 8px; font-weight: bold; background-color: #555; border: none;")
        self.btn_mirror_paste.clicked.connect(lambda: self.controller.mirror_paste_pose("X"))
        vl.addLayout(row1)
        vl.addLayout(row_opt)
        vl.addWidget(self.btn_mirror_paste)
        self.grp_pose.setContentLayout(vl)
        l.addWidget(self.grp_pose)
        l.addStretch()

    def _get_workflow_button_style(self, base_color, hover_color, press_color):
        return f"""QPushButton {{ background-color: {base_color}; color: white; font-weight: bold; font-size: 14px; padding: 12px; border-radius: 6px; border-bottom: 3px solid rgba(0,0,0,0.3); }} QPushButton:hover {{ background-color: {hover_color}; margin-top: 1px; border-bottom: 2px solid rgba(0,0,0,0.3); }} QPushButton:pressed {{ background-color: {press_color}; margin-top: 3px; border-bottom: none; }}"""

    def _add_spin(self, layout, row, col, label_text, val, min_v, max_v):
        lbl = QLabel(label_text);
        lbl.setStyleSheet("color: #BBB; font-size: 13px; margin-right: 5px;");
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter);
        lbl.setFixedWidth(80)
        spn = QSpinBox();
        spn.setRange(min_v, max_v);
        spn.setValue(val);
        spn.setAlignment(Qt.AlignmentFlag.AlignCenter);
        spn.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons);
        spn.setStyleSheet(
            "QSpinBox { background-color: #3A3A3A; border: 1px solid #555; padding: 4px; border-radius: 4px; color: #EEE; font-weight: bold; min-width: 50px; } QSpinBox:hover { border: 1px solid #777; background-color: #444; } QSpinBox:focus { border: 1px solid #007ACC; }")
        layout.addWidget(lbl, row, col);
        layout.addWidget(spn, row, col + 1);
        return spn, lbl

    def _update_workflow_header(self, checked):
        base = translator.get("rig_grp_work");
        hint = translator.get("rig_grp_work_hint");
        self.grp_work.setHeaderText(f"{base}{hint}" if checked else base)

    def _on_create_guides(self):
        self.controller.create_guide_skeleton(self._get_config())
        if not self.guide_explorer_container.isVisible(): self.guide_explorer_container.setVisible(
            True); win = self.window();
        if win: win.resize(win.width() + 280, win.height()); self.biped_splitter.setSizes([win.width(), 280])
        self.guide_explorer.refresh_list()

    def _on_align_guides(self):
        self.controller.auto_align_guides()

    def _on_finalize(self):
        self.controller.finalize_biped(self._get_config())
        if self.guide_explorer_container.isVisible(): self.guide_explorer_container.setVisible(
            False); win = self.window();
        if win and win.width() > 600: win.resize(win.width() - 280, win.height())

    def _get_config(self):
        return {'spine': self.spn_spine.value(), 'neck': self.spn_neck.value(),
                'triPelvis': self.chk_tri_pelvis.isChecked(), 'triNeck': self.chk_tri_neck.isChecked(),
                'fingers': self.spn_finger.value(), 'fingerlinks': self.spn_flink.value(), 'toes': self.spn_toe.value(),
                'toelinks': self.spn_tlink.value(), 'leglinks': self.spn_leglink.value(), 'tail': self.spn_tail.value(),
                'pony1': self.spn_pony1.value(), 'pony2': self.spn_pony2.value()}

    def _init_placeholder(self, widget, title):
        l = QVBoxLayout(widget);
        lbl = QLabel(f"🚧 {title} (Coming Soon)");
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter);
        lbl.setStyleSheet("color: #666; font-style: italic;");
        l.addWidget(lbl)