# ohCHA_RigManager/01/src/ui/tabs/skinning_tab.py
# Description: [v22.05] CRASH FIX.
#              - FIX: Explicit parenting (QWidget(self)) to prevent early Garbage Collection.
#              - FIX: Stabilized layout assignment logic.

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import functools
import os

try:
    from utils.translator import translator
    from ui.ohcha_ui_widgets import (
        OchaCollapsibleGroup,
        OchaAnimatedToggle,
        BaseTreeItemWidget,
        LayerTreeItemWidget,
        MaskTreeItemWidget,
        OchaBoneListExplorer,
        OchaWeightToolWidget
    )
    from utils.paths import get_icon_path
    from controllers.skin_layer_controller import skin_controller_instance
except ImportError:
    class T: get = lambda s, k: k
    translator = T(); get_icon_path = lambda n: None
    class OchaCollapsibleGroup(QGroupBox):
        def __init__(self, t, e=True): super().__init__(t); self.setContentLayout = self.setLayout
        def setHeaderText(self, t): self.setTitle(t)
    class OchaAnimatedToggle(QCheckBox): pass
    class BaseTreeItemWidget(QWidget): pass
    class LayerTreeItemWidget(QWidget): pass
    class MaskTreeItemWidget(QWidget): pass
    class OchaBoneListExplorer(QWidget): pass
    class OchaWeightToolWidget(QWidget): pass
    skin_controller_instance = None


# ============================================================================
# [1] Skin Hide Widget (Mesh Visibility)
# ============================================================================
class SkinHideWidget(QWidget):
    hideFaceRequested = Signal(bool)
    hideElementRequested = Signal(bool)
    unhideAllRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Header Info & Toggle
        header_layout = QHBoxLayout()
        # ⭐️ [FIX] Explicit parent 'self' to prevent GC
        self.lbl_info = QLabel(self)
        self.lbl_info.setObjectName("DescLabel")
        
        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(8)
        self.lbl_unselected = QLabel(self)
        self.lbl_unselected.setObjectName("ToggleLabel")
        self.toggle_unselected = OchaAnimatedToggle(width=46, height=24, parent=self)
        
        toggle_layout.addWidget(self.lbl_unselected)
        toggle_layout.addWidget(self.toggle_unselected)
        
        header_layout.addWidget(self.lbl_info, 1)
        header_layout.addLayout(toggle_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_face = QPushButton(self)
        self.btn_element = QPushButton(self)
        
        blue_style = "background-color: #03A9F4; color: white; padding: 8px; font-weight: bold; border-radius: 4px;"
        green_style = "background-color: #2ECC71; color: white; padding: 8px; font-weight: bold; border-radius: 4px;"
        
        self.btn_face.setStyleSheet(blue_style)
        self.btn_element.setStyleSheet(blue_style)
        
        btn_layout.addWidget(self.btn_face)
        btn_layout.addWidget(self.btn_element)

        self.btn_unhide = QPushButton(self)
        self.btn_unhide.setStyleSheet(green_style)

        # Assembly
        layout.addLayout(header_layout)
        line = QFrame(self)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        layout.addLayout(btn_layout)
        layout.addWidget(self.btn_unhide)

        # Connections
        self.btn_face.clicked.connect(lambda: self.hideFaceRequested.emit(self.toggle_unselected.isChecked()))
        self.btn_element.clicked.connect(lambda: self.hideElementRequested.emit(self.toggle_unselected.isChecked()))
        self.btn_unhide.clicked.connect(self.unhideAllRequested.emit)

        self.retranslate_ui()

    def retranslate_ui(self):
        # ⭐️ Safely update text
        if hasattr(self, 'lbl_info'):
            self.lbl_info.setText(f"ℹ️ {translator.get('skin_hide_info_lbl')}")
            self.lbl_unselected.setText(translator.get("skin_lbl_hide_unselected"))
            self.toggle_unselected.setToolTip(translator.get("tip_hide_invert"))
            self.btn_face.setText(f"▣ {translator.get('skin_btn_face')}")
            self.btn_element.setText(f"❒ {translator.get('skin_btn_element')}")
            self.btn_unhide.setText(f"👁️ {translator.get('skin_btn_unhide')}")


# ============================================================================
# [2] Skin Utilities Widget (Tools & Weight Operations)
# ============================================================================
class SkinUtilsWidget(QWidget):
    # Signals
    removeUnusedRequested = Signal()
    findBoneRequested = Signal()
    clearFilterRequested = Signal()
    transferRequested = Signal()
    pruneRequested = Signal()
    saveListRequested = Signal()
    loadListRequested = Signal()
    saveSkinRequested = Signal()
    loadSkinRequested = Signal()
    exportDataRequested = Signal()
    importDataRequested = Signal()
    
    # Weight Tool Signals
    weightSelectionRequested = Signal(str)
    weightPresetRequested = Signal(float)
    weightMathRequested = Signal(str, float)
    weightClipboardRequested = Signal(str)
    weightSmoothRequested = Signal()
    weightHealRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(6)

        def mk_btn(obj_name="UtilBtn", style=""):
            b = QPushButton(self) # ⭐️ Explicit Parent
            b.setObjectName(obj_name)
            if style: b.setStyleSheet(style)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.setMinimumHeight(24)
            return b

        # Row 1
        row1 = QHBoxLayout()
        row1.setSpacing(2)
        self.btn_rem_unused = mk_btn()
        self.btn_find_bone = mk_btn()
        self.btn_clear = mk_btn()
        self.btn_transfer = mk_btn(style="background-color: #D35400; color: white;")
        for b in [self.btn_rem_unused, self.btn_find_bone, self.btn_clear, self.btn_transfer]:
            row1.addWidget(b)

        # Row 2
        row2 = QHBoxLayout()
        row2.setSpacing(2)
        self.btn_prune = mk_btn()
        self.btn_save_list = mk_btn()
        self.btn_load_list = mk_btn()
        self.btn_save_env = mk_btn(style="background-color: #27AE60; color: white;")
        self.btn_load_env = mk_btn(style="background-color: #27AE60; color: white;")
        for b in [self.btn_prune, self.btn_save_list, self.btn_load_list, self.btn_save_env, self.btn_load_env]:
            row2.addWidget(b)

        # Row 3
        row3 = QHBoxLayout()
        row3.setSpacing(2)
        self.btn_export = mk_btn()
        self.btn_import = mk_btn(style="background-color: #8E44AD; color: white;")
        row3.addWidget(self.btn_export)
        row3.addWidget(self.btn_import)

        # Weight Tool
        self.weight_tool = OchaWeightToolWidget(self)

        # Assembly
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)
        layout.addSpacing(4)
        layout.addWidget(self.weight_tool)

        # Connections
        self.btn_rem_unused.clicked.connect(self.removeUnusedRequested.emit)
        self.btn_find_bone.clicked.connect(self.findBoneRequested.emit)
        self.btn_clear.clicked.connect(self.clearFilterRequested.emit)
        self.btn_transfer.clicked.connect(self.transferRequested.emit)
        self.btn_prune.clicked.connect(self.pruneRequested.emit)
        self.btn_save_list.clicked.connect(self.saveListRequested.emit)
        self.btn_load_list.clicked.connect(self.loadListRequested.emit)
        self.btn_save_env.clicked.connect(self.saveSkinRequested.emit)
        self.btn_load_env.clicked.connect(self.loadSkinRequested.emit)
        self.btn_export.clicked.connect(self.exportDataRequested.emit)
        self.btn_import.clicked.connect(self.importDataRequested.emit)

        # Weight Tool Pass-through
        self.weight_tool.selectionChanged.connect(self.weightSelectionRequested.emit)
        self.weight_tool.presetClicked.connect(self.weightPresetRequested.emit)
        self.weight_tool.mathClicked.connect(self.weightMathRequested.emit)
        self.weight_tool.clipboardClicked.connect(self.weightClipboardRequested.emit)
        self.weight_tool.smoothClicked.connect(self.weightSmoothRequested.emit)
        self.weight_tool.healClicked.connect(self.weightHealRequested.emit)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.btn_rem_unused.setText(translator.get("btn_rem_useless"))
        self.btn_rem_unused.setToolTip(translator.get("tip_rem_useless"))
        self.btn_find_bone.setText(translator.get("btn_bnlist_vert"))
        self.btn_find_bone.setToolTip(translator.get("tip_bnlist_vert"))
        self.btn_clear.setText(translator.get("btn_clear_filter"))
        self.btn_clear.setToolTip(translator.get("tip_clear_filter"))
        self.btn_transfer.setText(translator.get("btn_transfer"))
        self.btn_transfer.setToolTip(translator.get("tip_transfer"))
        self.btn_prune.setText(translator.get("btn_rem_zero"))
        self.btn_prune.setToolTip(translator.get("tip_rem_zero"))
        self.btn_save_list.setText(translator.get("btn_save_bnlist"))
        self.btn_save_list.setToolTip(translator.get("tip_save_bnlist"))
        self.btn_load_list.setText(translator.get("btn_load_bnlist"))
        self.btn_load_list.setToolTip(translator.get("tip_load_bnlist"))
        self.btn_save_env.setText(translator.get("btn_save_skin"))
        self.btn_save_env.setToolTip(translator.get("tip_save_skin"))
        self.btn_load_env.setText(translator.get("btn_load_skin"))
        self.btn_load_env.setToolTip(translator.get("tip_load_skin"))
        self.btn_export.setText(translator.get("btn_export_skindata"))
        self.btn_export.setToolTip(translator.get("tip_export_skindata"))
        self.btn_import.setText(translator.get("btn_import_skindata"))
        self.btn_import.setToolTip(translator.get("tip_import_skindata"))
        self.weight_tool.retranslate_ui()


# ============================================================================
# [3] Layer Manager Widget
# ============================================================================
class OchaLayerManagerWidget(QFrame):
    addLayerClicked = Signal()
    removeLayerClicked = Signal(int)
    moveLayerUpClicked = Signal(int)
    moveLayerDownClicked = Signal(int)
    injectToSkinClicked = Signal()
    importFromSelectionClicked = Signal()
    manualEditClicked = Signal(int)
    paintCommitClicked = Signal(int)
    paintOptionsClicked = Signal()
    paintBlendToggled = Signal(bool)
    blendModeChanged = Signal(int, str)
    collapseLayersClicked = Signal()
    addMaskToLayerClicked = Signal(int)
    removeMaskFromLayerClicked = Signal(int)
    updateMaskDataClicked = Signal(int, bool)
    selectMaskVertsClicked = Signal(int)
    toggleLayerClicked = Signal(int, bool)
    toggleMaskClicked = Signal(int, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LayerManagerFrame")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(4)

        top_layout = QHBoxLayout()
        self.btn_import = QPushButton(self)
        self.btn_collapse = QPushButton(self)
        top_layout.addWidget(self.btn_import, 1)
        top_layout.addWidget(self.btn_collapse, 1)

        self.layer_tree = QTreeWidget(self)
        self.layer_tree.setHeaderHidden(True)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(2)
        ctrl_btn_style = "QPushButton { background-color: #444; color: #EEE; border-radius: 3px; font-weight: bold; font-size: 14px; border: 1px solid #555; } QPushButton:hover { background-color: #555; } QPushButton:pressed { background-color: #333; }"

        self.btn_add = QPushButton("+", self)
        self.btn_rem = QPushButton("-", self)
        self.btn_up = QPushButton("▲", self)
        self.btn_down = QPushButton("▼", self)

        for b in [self.btn_add, self.btn_rem, self.btn_up, self.btn_down]:
            b.setMinimumHeight(30)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.setStyleSheet(ctrl_btn_style)
            controls_layout.addWidget(b)

        line = QFrame(self)
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        controls_layout.addWidget(line)

        self.btn_manual_edit = QPushButton(self)
        self.btn_paint_commit = QPushButton(self)
        self.btn_paint_options = QPushButton(self)
        
        for b in [self.btn_manual_edit, self.btn_paint_commit, self.btn_paint_options]:
            b.setFixedHeight(30)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.btn_paint_options.setEnabled(False)

        self.lbl_blend = QLabel(self)
        self.chk_blend_mode = OchaAnimatedToggle(width=40, height=20, parent=self)
        self.chk_blend_mode.setChecked(False)
        self.chk_blend_mode.setEnabled(False)

        controls_layout.addWidget(self.btn_manual_edit)
        controls_layout.addWidget(self.btn_paint_commit)
        controls_layout.addWidget(self.btn_paint_options)

        blend_layout = QHBoxLayout()
        blend_layout.addWidget(self.lbl_blend)
        blend_layout.addWidget(self.chk_blend_mode)
        controls_layout.addLayout(blend_layout)

        self.btn_inject = QPushButton(self)
        self.btn_inject.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold; padding: 6px;")

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.layer_tree)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.btn_inject)

        # Connections
        self.btn_add.clicked.connect(lambda c=False: self.addLayerClicked.emit())
        self.btn_rem.clicked.connect(self._on_remove_clicked)
        self.btn_up.clicked.connect(self._on_move_up_clicked)
        self.btn_down.clicked.connect(self._on_move_down_clicked)
        self.btn_manual_edit.clicked.connect(self._on_manual_edit_clicked)
        self.btn_paint_commit.clicked.connect(self._on_paint_commit_clicked)
        self.btn_paint_options.clicked.connect(lambda c=False: self.paintOptionsClicked.emit())
        self.chk_blend_mode.toggled.connect(lambda v: self.paintBlendToggled.emit(v))
        self.btn_inject.clicked.connect(lambda c=False: self.injectToSkinClicked.emit())
        self.btn_import.clicked.connect(lambda c=False: self.importFromSelectionClicked.emit())
        self.btn_collapse.clicked.connect(lambda c=False: self.collapseLayersClicked.emit())
        self.layer_tree.currentItemChanged.connect(self._on_selection_changed)

        self.set_session_active(False)
        self.retranslate_ui()

    def set_session_active(self, is_active: bool):
        self.btn_import.setEnabled(True)
        self.btn_collapse.setEnabled(is_active and self.layer_tree.topLevelItemCount() > 1)
        self.layer_tree.setEnabled(is_active)
        self.btn_add.setEnabled(is_active)
        self.btn_inject.setEnabled(is_active)

        if is_active:
            self._on_selection_changed(self.layer_tree.currentItem(), None)
        else:
            self.btn_rem.setEnabled(False)
            self.btn_up.setEnabled(False)
            self.btn_down.setEnabled(False)
            self.btn_manual_edit.setEnabled(False)
            self.btn_paint_commit.setEnabled(False)

    def retranslate_ui(self):
        self.btn_import.setText(translator.get("skin_btn_import"))
        self.btn_collapse.setText(translator.get("skin_btn_collapse"))
        self.btn_manual_edit.setText(translator.get("skin_btn_manual_edit"))
        self.btn_paint_commit.setText(translator.get("skin_btn_paint"))
        self.btn_paint_options.setText(translator.get("skin_btn_paint_options"))
        self.lbl_blend.setText(translator.get("skin_lbl_blend_mode"))
        self.btn_inject.setText(f"🔥 {translator.get('skin_btn_inject')}")

        self.btn_import.setToolTip(translator.get("tooltip_import"))
        self.btn_collapse.setToolTip(translator.get("tooltip_collapse"))
        self.btn_add.setToolTip(translator.get("tooltip_add_layer"))
        self.btn_rem.setToolTip(translator.get("tooltip_rem_layer"))
        self.btn_up.setToolTip(translator.get("tooltip_move_up"))
        self.btn_down.setToolTip(translator.get("tooltip_move_down"))
        self.btn_manual_edit.setToolTip(translator.get("tooltip_manual_edit"))
        self.btn_paint_commit.setToolTip(translator.get("tooltip_paint"))
        self.btn_paint_options.setToolTip(translator.get("skin_btn_paint_options_tip"))
        self.btn_inject.setToolTip(translator.get("tooltip_inject"))

    def get_selected_indices(self) -> (int, bool):
        item = self.layer_tree.currentItem()
        if not item or not item.data(0, Qt.ItemDataRole.UserRole): return -1, False
        data = item.data(0, Qt.ItemDataRole.UserRole)
        return data.get("layer_index", -1), data.get("is_mask", False)

    def _on_remove_clicked(self):
        self.removeLayerClicked.emit(self.get_selected_indices()[0])

    def _on_move_up_clicked(self):
        self.moveLayerUpClicked.emit(self.get_selected_indices()[0])

    def _on_move_down_clicked(self):
        self.moveLayerDownClicked.emit(self.get_selected_indices()[0])

    def _on_manual_edit_clicked(self):
        self.manualEditClicked.emit(self.get_selected_indices()[0])

    def _on_paint_commit_clicked(self):
        self.paintCommitClicked.emit(self.get_selected_indices()[0])

    def _on_selection_changed(self, current, previous):
        layer_index, is_mask = self.get_selected_indices()
        cnt = self.layer_tree.topLevelItemCount()
        is_base = (layer_index == cnt - 1) and (cnt > 0)
        has_selection = layer_index >= 0

        self.btn_paint_commit.setEnabled(has_selection and not is_base and not is_mask)
        self.btn_manual_edit.setEnabled(has_selection and not is_mask)
        self.btn_rem.setEnabled(has_selection and not is_base and not is_mask)
        self.btn_up.setEnabled(has_selection and not is_base and not is_mask and layer_index > 0)
        self.btn_down.setEnabled(has_selection and not is_base and not is_mask and layer_index < cnt - 2)
        self.btn_collapse.setEnabled(cnt > 1)

    def refresh_ui(self, layer_data: dict):
        self.layer_tree.blockSignals(True)
        current_selection_index, _ = self.get_selected_indices()
        self.layer_tree.clear()

        layers = layer_data.get("layers", [])
        item_to_select = None

        for ui_index in range(len(layers)):
            data_index = len(layers) - 1 - ui_index
            layer_info = layers[data_index]

            name = layer_info.get("name", "Unnamed")
            enabled = layer_info.get("enabled", True)
            blend_mode = layer_info.get("blend_mode", "Overwrite")
            mask = layer_info.get("mask")
            mask_enabled = layer_info.get("mask_enabled", True)
            is_base = (data_index == 0)

            item = QTreeWidgetItem()
            item.setData(0, Qt.ItemDataRole.UserRole, {"layer_index": ui_index, "is_mask": False})

            if is_base:
                item_widget = BaseTreeItemWidget(name=name, enabled=enabled)
                item_widget.btn_vis.setEnabled(False)
            else:
                item_widget = LayerTreeItemWidget(name=name, enabled=enabled, blend_mode=blend_mode,
                                                  has_mask=(mask is not None))
                item_widget.visibilityToggled.connect(functools.partial(self.toggleLayerClicked.emit, ui_index))
                item_widget.blendModeChanged.connect(functools.partial(self.blendModeChanged.emit, ui_index))
                item_widget.addMaskClicked.connect(functools.partial(self.addMaskToLayerClicked.emit, ui_index))
                item_widget.removeMaskClicked.connect(functools.partial(self.removeMaskFromLayerClicked.emit, ui_index))

            self.layer_tree.addTopLevelItem(item)
            self.layer_tree.setItemWidget(item, 0, item_widget)

            if mask is not None and not is_base:
                mask_item = QTreeWidgetItem(item)
                mask_item.setData(0, Qt.ItemDataRole.UserRole, {"layer_index": ui_index, "is_mask": True})

                mask_widget = MaskTreeItemWidget(enabled=mask_enabled)
                mask_widget.visibilityToggled.connect(functools.partial(self.toggleMaskClicked.emit, ui_index))
                mask_widget.addToMaskClicked.connect(
                    functools.partial(self.updateMaskDataClicked.emit, ui_index, False))
                mask_widget.removeFromMaskClicked.connect(
                    functools.partial(self.updateMaskDataClicked.emit, ui_index, True))
                mask_widget.selectMaskClicked.connect(functools.partial(self.selectMaskVertsClicked.emit, ui_index))
                self.layer_tree.setItemWidget(mask_item, 0, mask_widget)

            if ui_index == current_selection_index:
                item_to_select = item

        if item_to_select: self.layer_tree.setCurrentItem(item_to_select)
        self.layer_tree.expandAll()
        self.layer_tree.blockSignals(False)
        self._on_selection_changed(self.layer_tree.currentItem(), None)

    def set_painting_mode(self, is_painting):
        self.btn_paint_options.setEnabled(is_painting)
        self.chk_blend_mode.setEnabled(is_painting)
        self.lbl_blend.setEnabled(is_painting)
        is_idle = not is_painting
        self.btn_import.setEnabled(is_idle)
        self.btn_add.setEnabled(is_idle)
        self.btn_collapse.setEnabled(is_idle)
        self.btn_rem.setEnabled(is_idle)
        self.btn_up.setEnabled(is_idle)
        self.btn_down.setEnabled(is_idle)
        self.btn_inject.setEnabled(is_idle)
        self.layer_tree.setEnabled(is_idle)
        self.btn_manual_edit.setEnabled(is_idle)

        if is_painting:
            self.btn_paint_commit.setText("Commit")
            self.btn_paint_commit.setStyleSheet("background-color: #2ECC71;")
            self.btn_paint_commit.setEnabled(True)
        else:
            self.btn_paint_commit.setText(translator.get("skin_btn_paint"))
            self.btn_paint_commit.setStyleSheet("")
            self._on_selection_changed(self.layer_tree.currentItem(), None)

    def set_manual_editing_mode(self, is_editing):
        is_idle = not is_editing
        self.btn_import.setEnabled(is_idle)
        self.btn_add.setEnabled(is_idle)
        self.btn_rem.setEnabled(is_idle)
        self.btn_collapse.setEnabled(is_idle)
        self.btn_up.setEnabled(is_idle)
        self.btn_down.setEnabled(is_idle)
        self.btn_inject.setEnabled(is_idle)
        self.layer_tree.setEnabled(is_idle)
        self.btn_paint_commit.setEnabled(is_idle)
        self.btn_paint_options.setEnabled(is_idle)
        self.chk_blend_mode.setEnabled(is_idle)
        self.lbl_blend.setEnabled(is_idle)

        if is_editing:
            self.btn_manual_edit.setText("Commit")
            self.btn_manual_edit.setStyleSheet("background-color: #2ECC71;")
        else:
            self.btn_manual_edit.setText(translator.get("skin_btn_manual_edit"))
            self.btn_manual_edit.setStyleSheet("")
            self._on_selection_changed(self.layer_tree.currentItem(), None)


# ============================================================================
# [4] Main Skinning Tab (Assembler)
# ============================================================================
class SkinningTab(QWidget):
    # Signals (Must match existing core connections exactly)
    hideSelectionRequested = Signal(str, bool)
    unhideAllRequested = Signal()
    removeUnusedBonesRequested = Signal()
    findInfluencingBonesRequested = Signal()
    clearBoneFilterRequested = Signal()
    transferWeightsRequested = Signal()
    removeZeroWeightsRequested = Signal()
    saveBoneListRequested = Signal()
    loadBoneListRequested = Signal()
    saveSkinRequested = Signal()
    loadSkinRequested = Signal()
    weightSelectionRequested = Signal(str)
    weightPresetRequested = Signal(float)
    weightMathRequested = Signal(str, float)
    weightClipboardRequested = Signal(str)
    weightSmoothRequested = Signal()
    weightHealRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QPushButton#UtilBtn { background-color: #555; color: white; border-radius: 3px; padding: 4px; font-size: 10px; }
            QPushButton#UtilBtn:hover { background-color: #666; }
            QLabel#DescLabel { color: #888; font-size: 12px; padding-bottom: 5px; }
            QLabel#ToggleLabel { color: #D0D0D0; font-weight: bold; font-size: 12px; }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Left Panel (Splitter Left) ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # 1. Hide Group
        self.g_hide = OchaCollapsibleGroup("Mesh Hide", False)
        # ⭐️ Fix: Add widget to collapsible using a wrapper layout
        self.hide_widget = SkinHideWidget(self)
        gh_layout = QVBoxLayout()
        gh_layout.setContentsMargins(0,0,0,0)
        gh_layout.addWidget(self.hide_widget)
        self.g_hide.setContentLayout(gh_layout)

        # 2. Layer Group
        self.g_layer = OchaCollapsibleGroup("Layer Skinning", True)
        self.layer_manager_widget = OchaLayerManagerWidget(self)
        gl_layout = QVBoxLayout()
        gl_layout.setContentsMargins(0,0,0,0)
        gl_layout.addWidget(self.layer_manager_widget)
        self.g_layer.setContentLayout(gl_layout)

        # 3. Utils Group
        self.g_utils = OchaCollapsibleGroup("Utilities & Tools", True)
        self.utils_widget = SkinUtilsWidget(self)
        gu_layout = QVBoxLayout()
        gu_layout.setContentsMargins(0,0,0,0)
        gu_layout.addWidget(self.utils_widget)
        self.g_utils.setContentLayout(gu_layout)

        # Add to Left Panel
        left_layout.addWidget(self.g_hide)
        left_layout.addWidget(self.g_layer)
        left_layout.addWidget(self.g_utils)
        left_layout.addStretch(1)

        # --- Right Panel (Bone Explorer) ---
        self.bone_explorer = OchaBoneListExplorer(self)

        # Splitter Assembly
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.bone_explorer)
        splitter.setSizes([340, 200])

        main_layout.addWidget(splitter)

        # --- Signal Wiring ---
        self.hide_widget.hideFaceRequested.connect(lambda inv: self.hideSelectionRequested.emit("face", inv))
        self.hide_widget.hideElementRequested.connect(lambda inv: self.hideSelectionRequested.emit("element", inv))
        self.hide_widget.unhideAllRequested.connect(self.unhideAllRequested.emit)

        self.utils_widget.removeUnusedRequested.connect(self.removeUnusedBonesRequested.emit)
        self.utils_widget.findBoneRequested.connect(self.findInfluencingBonesRequested.emit)
        self.utils_widget.clearFilterRequested.connect(self.clearBoneFilterRequested.emit)
        self.utils_widget.transferRequested.connect(self.transferWeightsRequested.emit)
        self.utils_widget.pruneRequested.connect(self.removeZeroWeightsRequested.emit)
        self.utils_widget.saveListRequested.connect(self.saveBoneListRequested.emit)
        self.utils_widget.loadListRequested.connect(self.loadBoneListRequested.emit)
        self.utils_widget.saveSkinRequested.connect(self.saveSkinRequested.emit)
        self.utils_widget.loadSkinRequested.connect(self.loadSkinRequested.emit)
        
        # Aliases for core connection
        self.btn_export_skin = self.utils_widget.btn_export
        self.btn_import_skin = self.utils_widget.btn_import

        self.utils_widget.weightSelectionRequested.connect(self.weightSelectionRequested.emit)
        self.utils_widget.weightPresetRequested.connect(self.weightPresetRequested.emit)
        self.utils_widget.weightMathRequested.connect(self.weightMathRequested.emit)
        self.utils_widget.weightClipboardRequested.connect(self.weightClipboardRequested.emit)
        self.utils_widget.weightSmoothRequested.connect(self.weightSmoothRequested.emit)
        self.utils_widget.weightHealRequested.connect(self.weightHealRequested.emit)

        if skin_controller_instance:
            self.layer_manager_widget.toggleLayerClicked.connect(
                lambda i, s: self.layer_manager_widget.refresh_ui(
                    skin_controller_instance.toggle_layer_visibility(i, s)
                )
            )
            self.layer_manager_widget.toggleMaskClicked.connect(
                lambda i, s: self.layer_manager_widget.refresh_ui(
                    skin_controller_instance.toggle_mask_visibility(i, s)
                )
            )

        self.bone_explorer.removeInfluenceRequested.connect(self._on_remove_bone_influence)
        self.retranslate_ui()

    def retranslate_ui(self):
        self.g_hide.setHeaderText(translator.get("skin_grp_mesh_hide"))
        self.hide_widget.retranslate_ui()
        self.g_layer.setHeaderText(translator.get("skin_grp_layers"))
        self.layer_manager_widget.retranslate_ui()
        self.g_utils.setHeaderText("Utilities & Tools")
        self.utils_widget.retranslate_ui()
        self.bone_explorer.retranslate_ui()

    def _on_remove_bone_influence(self, bone_id):
        if not skin_controller_instance: return
        idx, _ = self.layer_manager_widget.get_selected_indices()
        if idx < 0: idx = 0
        skin_controller_instance.apply_weight_to_active_layer(bone_id, 0.0, "set", ui_layer_index=idx)