# ohCHA_RigManager/01/src/rig_manager_core.py
# Description: [v21.56] CORE FIX.
#              - FIX: Added missing import 'get_selected_skin_vert_indices'.
#              - This fixes 'Find Bone' and 'Transfer' crashes.

import os
import sys
import importlib
import json
import traceback
from pymxs import runtime as rt
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

rt.print("✅ [Import Check] Loading rig_manager_core...")

try:
    import utils.translator
    importlib.reload(utils.translator)
    translator = utils.translator.translator

    # ⭐️ [FIX] Added 'get_selected_skin_vert_indices' to imports
    from utils.ohcha_max_utils import OchaError, get_selected_skin_vert_indices
    
    from controllers import main_logic, edit_mesh_logic, skinning_logic, commands
    from controllers.skin_layer_controller import skin_controller_instance
    from controllers.group_controller import group_controller_instance
    from controllers import rigging_controller
    importlib.reload(rigging_controller)

    from utils.paths import get_project_root, get_icon_path
    from utils.config import (
        TABS_CONFIG,
        DEFAULT_TAB_ID,
        SIDEBAR_EXPANDED_WIDTH,
        SIDEBAR_COLLAPSED_WIDTH,
        VERSION
    )
    from ui.ohcha_ui_base import OchaBaseWindow, show_tool_instance
    from ui.ohcha_ui_widgets import OchaLanguageMenu

except ImportError as e:
    rt.print(f"❌ [Import Error] CRITICAL: A module failed to load: {e}")
    traceback.print_exc()
    raise


def import_class_from_path(path):
    module_name, class_name = path.rsplit('.', 1)
    module = importlib.import_module(module_name)
    importlib.reload(module)
    return getattr(module, class_name)


class RigManagerWindow(OchaBaseWindow):
    def __init__(self):
        # ⭐️ [INIT LANGUAGE] Load from settings.json or default to 'en'
        initial_lang = "en"
        try:
            root = get_project_root()
            if root:
                settings_path = os.path.join(root, "data", "settings.json")
                if os.path.exists(settings_path):
                    with open(settings_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        initial_lang = data.get("language", "en")
                        rt.print(f"🌍 Initial Language Loaded: {initial_lang}")
        except Exception as e:
            rt.print(f"⚠️ Failed to load settings.json: {e}")

        translator.__init__()
        translator.set_language(initial_lang)

        super().__init__()
        self.setWindowTitle(f"ohCHA Rig Manager v{VERSION}")

        self.resize(540, 600)
        self._is_sidebar_expanded = True

        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(200)
        self.sync_timer.timeout.connect(self._sync_max_selection_to_ui)
        self.sync_timer.start()
        self._last_selected_bone_id = -1

        self.logo = QLabel("ohCHA")
        self.logo.setObjectName("SidebarLogo")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.btn_hamburger = QPushButton("☰")
        self.btn_hamburger.setFixedSize(42, 42)
        self.btn_hamburger.setObjectName("HamburgerButton")

        self.lang_menu = OchaLanguageMenu()
        self.lang_menu.cur = initial_lang
        self.lang_menu._upd_btn()

        self.tabs = {}
        self.btns = {}
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        for t_config in TABS_CONFIG:
            tid = t_config["id"]
            try:
                TabClass = import_class_from_path(t_config["cls_path"])
                self.tabs[tid] = TabClass()
            except Exception as e:
                rt.print(f"❌ Failed to load tab '{tid}': {e}")
                traceback.print_exc()
                continue

            btn = QPushButton()
            btn.setCheckable(True)
            btn.setObjectName("SidebarButton")

            icon_path = get_icon_path(t_config["icon"])
            if icon_path:
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(33, 33))

            self.btns[tid] = btn
            self.btn_group.addButton(btn)

        self._setup_ui()
        self._connect()
        self.retranslate()

        if DEFAULT_TAB_ID in self.btns:
            self.btns[DEFAULT_TAB_ID].setChecked(True)
            self.stack.setCurrentWidget(self.tabs[DEFAULT_TAB_ID])
            QTimer.singleShot(100, lambda: self.adjustSize())

    def _setup_ui(self):
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(SIDEBAR_EXPANDED_WIDTH)

        side_l = QVBoxLayout(self.sidebar)
        side_l.setContentsMargins(5, 5, 5, 5)
        side_l.setSpacing(5)

        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(50)
        hl = QHBoxLayout(self.header_widget)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self.logo)
        hl.addStretch(1)
        hl.addWidget(self.btn_hamburger)

        side_l.addWidget(self.header_widget)
        side_l.addSpacing(10)

        for b in self.btns.values():
            side_l.addWidget(b)

        side_l.addStretch()

        lb = QHBoxLayout()
        lb.addStretch()
        lb.addWidget(self.lang_menu)
        lb.addStretch()

        side_l.addLayout(lb)
        side_l.addSpacing(10)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        for t in self.tabs.values():
            self.stack.addWidget(t)

        main_l = QHBoxLayout(self)
        main_l.setContentsMargins(0, 0, 0, 0)
        main_l.setSpacing(0)
        main_l.addWidget(self.sidebar)
        main_l.addWidget(self.stack, 1)

        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)

    def _connect(self):
        self.btn_hamburger.clicked.connect(self._toggle_side)
        self.lang_menu.languageChanged.connect(self.on_language_changed)

        for tid, btn in self.btns.items():
            btn.clicked.connect(lambda checked=False, widget=self.tabs[tid]: self._on_tab_changed(widget))
            if tid == "skinning":
                btn.clicked.connect(self._on_skin_tab_selected)

        # [1] Edit Mesh Tab Connections
        if "edit_mesh" in self.tabs:
            t = self.tabs["edit_mesh"]
            t.refreshRequested.connect(t._on_refresh)
            t.fixScaleRequested.connect(lambda n: self._run_command(commands.FixScaleCommand(n)))
            t.fixSkinRequested.connect(lambda n: self._run_command(commands.FixSkinCommand(n)))
            t.fixPivotRequested.connect(lambda n: self._run_command(commands.FixPivotCommand(n)))
            t.finalizeRequested.connect(self._on_edit_finalize)

        # [2] Skinning Tab Connections
        if "skinning" in self.tabs:
            t = self.tabs["skinning"]
            # Skin Hide Manager Signals
            t.hideSelectionRequested.connect(lambda type, uns: self._run_simple(commands.SkinHideCommand(type, uns)))
            t.unhideAllRequested.connect(lambda: self._run_simple(commands.SkinUnhideAllCommand()))
            
            # Utils Signals
            t.removeUnusedBonesRequested.connect(self._on_remove_unused_bones)
            t.findInfluencingBonesRequested.connect(self._on_find_influencing_bones)
            t.clearBoneFilterRequested.connect(lambda: self._update_bone_explorer(True))
            t.transferWeightsRequested.connect(self._on_transfer_weights)
            t.removeZeroWeightsRequested.connect(self._on_remove_zero_weights)
            t.saveSkinRequested.connect(self._on_save_skin)
            t.saveBoneListRequested.connect(self._on_save_bone_list)
            t.loadBoneListRequested.connect(self._on_load_bone_list)
            t.loadSkinRequested.connect(self._on_load_skin)
            
            # Weight Tool Signals
            t.weightSelectionRequested.connect(self._on_weight_selection)
            t.weightPresetRequested.connect(self._on_weight_preset)
            t.weightMathRequested.connect(self._on_weight_math)
            t.weightClipboardRequested.connect(self._on_weight_clipboard)
            t.weightSmoothRequested.connect(self._on_weight_smooth)
            t.weightHealRequested.connect(self._on_weight_heal)
            t.btn_export_skin.clicked.connect(self._on_export_skin_clicked)
            t.btn_import_skin.clicked.connect(self._on_import_skin_clicked)

            # Bone Explorer Signals
            if hasattr(t, "bone_explorer"):
                explorer = t.bone_explorer
                # Force viewport update on bone click
                explorer.boneClicked.connect(self._on_skin_select_envelope)
                explorer.viewOptionsChanged.connect(self._on_bone_explorer_view_changed)
                explorer.addGroupClicked.connect(self._on_add_group)
                explorer.removeGroupClicked.connect(self._on_remove_group)
                explorer.renameGroupClicked.connect(self._on_rename_group)
                explorer.assignBonesClicked.connect(self._on_assign_bones)
                explorer.removeInfluenceRequested.connect(self.tabs["skinning"]._on_remove_bone_influence)

            # Layer Manager Signals
            mgr = t.layer_manager_widget
            mgr.layer_tree.currentItemChanged.connect(self._on_skin_item_selection_changed)
            mgr.addLayerClicked.connect(self._on_skin_add_layer)
            mgr.removeLayerClicked.connect(self._on_skin_remove_layer)
            mgr.moveLayerUpClicked.connect(self._on_skin_move_layer_up)
            mgr.moveLayerDownClicked.connect(self._on_skin_move_layer_down)
            mgr.injectToSkinClicked.connect(self._on_skin_inject)
            mgr.importFromSelectionClicked.connect(self._on_skin_import_from_selection)
            mgr.manualEditClicked.connect(self._on_skin_manual_edit_commit_toggled)
            mgr.paintCommitClicked.connect(self._on_skin_paint_commit_toggled)
            mgr.paintOptionsClicked.connect(self._on_skin_paint_options_clicked)
            mgr.paintBlendToggled.connect(self._on_skin_paint_blend_toggled)
            mgr.blendModeChanged.connect(self._on_skin_blend_mode_changed)
            mgr.collapseLayersClicked.connect(self._on_skin_collapse_layers)
            mgr.addMaskToLayerClicked.connect(self._on_skin_add_mask_to_layer)
            mgr.removeMaskFromLayerClicked.connect(self._on_skin_remove_mask_from_layer)
            mgr.updateMaskDataClicked.connect(self._on_skin_update_mask_data)
            mgr.selectMaskVertsClicked.connect(self._on_skin_select_mask_verts)

            if hasattr(t, "bone_explorer"):
                t.bone_explorer.hide()

    def _on_tab_changed(self, widget):
        self.stack.setCurrentWidget(widget)
        QTimer.singleShot(50, lambda: self.adjustSize())

    def _toggle_side(self):
        self._is_sidebar_expanded = not self._is_sidebar_expanded
        self._update_side_text()

        target_w = SIDEBAR_EXPANDED_WIDTH if self._is_sidebar_expanded else SIDEBAR_COLLAPSED_WIDTH
        self.lang_menu.set_expanded_mode(self._is_sidebar_expanded)

        self.anim_group = QParallelAnimationGroup(self)

        anim_min = QPropertyAnimation(self.sidebar, b"minimumWidth")
        anim_min.setDuration(200)
        anim_min.setEndValue(target_w)
        anim_min.setEasingCurve(QEasingCurve.Type.InOutCubic)

        anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth")
        anim_max.setDuration(200)
        anim_max.setEndValue(target_w)
        anim_max.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.anim_group.addAnimation(anim_min)
        self.anim_group.addAnimation(anim_max)
        self.anim_group.start()

        for b in self.btns.values():
            b.setProperty("collapsed", not self._is_sidebar_expanded)
            b.style().unpolish(b)
            b.style().polish(b)

    def _update_side_text(self):
        if self._is_sidebar_expanded:
            self.logo.setVisible(True)
            self.logo.setText("ohCHA")
            for tid, btn in self.btns.items():
                t_key = next((t["trans_key"] for t in TABS_CONFIG if t["id"] == tid), "")
                btn.setText(translator.get(t_key))
        else:
            self.logo.setVisible(False)
            self.logo.setText("")
            for b in self.btns.values():
                b.setText("")

    def on_language_changed(self, lang_code):
        translator.set_language(lang_code)
        try:
            root = get_project_root()
            if root:
                data_dir = os.path.join(root, "data")
                if not os.path.exists(data_dir): os.makedirs(data_dir)
                settings_path = os.path.join(data_dir, "settings.json")
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump({"language": lang_code}, f)
        except:
            pass
        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(f"ohCHA Rig Manager v{VERSION}")
        for tid, btn in self.btns.items():
            t_key = next((t["trans_key"] for t in TABS_CONFIG if t["id"] == tid), "")
            btn.setText(translator.get(t_key))

        for page in self.tabs.values():
            if hasattr(page, 'retranslate_ui'):
                try:
                    page.retranslate_ui()
                except Exception as e:
                    rt.print(f"⚠️ [Retranslate] Error: {e}")

        self._update_side_text()
        QTimer.singleShot(50, lambda: self.adjustSize())

    def _sync_max_selection_to_ui(self):
        if not skin_controller_instance.node or self.stack.currentWidget() != self.tabs.get("skinning"):
            return
        try:
            if rt.modPanel.getCurrentObject() == skin_controller_instance.native_skin_mod:
                current_bone_id = rt.skinOps.GetSelectedBone(skin_controller_instance.native_skin_mod)
                if current_bone_id != self._last_selected_bone_id:
                    self._last_selected_bone_id = current_bone_id
                    if hasattr(self.tabs["skinning"], "bone_explorer"):
                        self.tabs["skinning"].bone_explorer.silent_select_bone(current_bone_id)
        except Exception:
            pass

    def _run_command(self, cmd):
        try:
            if cmd.execute():
                rt.print(f"✅ {cmd.name} OK")
            else:
                rt.print(f"⚠️ {cmd.name} Failed")
        except OchaError as e:
            QMessageBox.warning(self.window(), translator.get("title_error"), str(e))
        except Exception as e:
            QMessageBox.critical(self.window(), translator.get("title_error"), str(e))
            rt.print(traceback.format_exc())

        if "edit_mesh" in self.tabs and hasattr(self.tabs["edit_mesh"], '_on_refresh'):
            self.tabs["edit_mesh"]._on_refresh()

    def _run_simple(self, cmd):
        try:
            cmd.execute()
        except OchaError as e:
            QMessageBox.warning(self.window(), translator.get("title_error"), str(e))

    def _on_edit_finalize(self, node, opts):
        queue, log = [], []
        if opts["lock_transforms"]: queue.append(commands.LockTransformCommand(node))
        if opts["enable_inheritance"]: queue.append(commands.EnableInheritanceCommand(node))
        if opts["add_skin"]: queue.append(commands.AddSkinCommand(node, opts["bone_limit"], opts["use_dq"]))
        ok = True
        try:
            for c in queue:
                if c.execute():
                    log.append(f"✅ {c.name}")
                else:
                    ok = False
                    log.append(f"❌ {c.name}")
                    break
        except OchaError as e:
            ok = False
            QMessageBox.warning(self.window(), translator.get("title_error"), str(e))
        except Exception as e:
            ok = False
            QMessageBox.critical(self.window(), translator.get("title_error"), str(e))

        rt.print("\n".join(log))

        if ok:
            QMessageBox.information(self.window(), translator.get("msg_done"),
                                    translator.get("msg_finalize_comp") + "\n\n" + "\n".join(log))

        if "edit_mesh" in self.tabs:
            self.tabs["edit_mesh"]._on_refresh()

    def _get_selected_node(self):
        if rt.selection.count != 1:
            QMessageBox.warning(self.window(), translator.get("title_selection_error"),
                                translator.get("msg_selection_error"))
            return None
        node = rt.selection[0]
        if not rt.isKindOf(node, rt.GeometryClass) or not any(rt.isKindOf(m, rt.Skin) for m in node.modifiers):
            QMessageBox.warning(self.window(), translator.get("title_selection_error"),
                                translator.get("msg_selection_error"))
            return None
        return node

    def _update_skin_layer_ui(self, data: dict):
        skin_tab = self.tabs.get("skinning")
        if skin_tab:
            skin_tab.layer_manager_widget.refresh_ui(data)

    def _on_skin_tab_selected(self, checked=False):
        if skin_controller_instance.is_painting or skin_controller_instance.is_editing_manually:
            return
        skin_tab = self.tabs.get("skinning")
        if skin_tab:
            skin_controller_instance.set_current_node(None)
            group_controller_instance.set_current_node(None)
            self._on_skin_load_layers()
            skin_tab.layer_manager_widget.set_session_active(False)
            skin_tab.bone_explorer.clear_list()
            skin_tab.bone_explorer.hide()

    def _on_skin_load_layers(self):
        data = skin_controller_instance.get_layer_data_from_scene()
        self._update_skin_layer_ui(data)

    def _on_skin_import_from_selection(self):
        node = self._get_selected_node()
        if not node: return
        skin_tab = self.tabs.get("skinning")
        if not skin_tab: return
        skin_controller_instance.set_current_node(node)
        group_controller_instance.set_current_node(node)

        if QMessageBox.question(self.window(), translator.get("title_import_base"),
                                translator.get("msg_import_base").format(node.name),
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            rt.execute(f"select $'{node.name}'; max modify mode")
            data = skin_controller_instance.capture_and_save_to_layer(0)
            if data and data.get('layers'):
                self._update_skin_layer_ui(data)
                self._update_bone_explorer(show_on_update=True)
                skin_tab.layer_manager_widget.set_session_active(True)
                QMessageBox.information(self.window(), translator.get("title_save_complete"),
                                        translator.get("msg_save_complete").format(node.name))
            else:
                skin_tab.layer_manager_widget.set_session_active(False)
                QMessageBox.warning(self.window(), translator.get("title_error"), "Failed to capture skin weights.")

    def _update_bone_explorer(self, show_on_update=False):
        skin_tab = self.tabs.get("skinning")
        if not skin_tab or not skin_controller_instance.node:
            return
        sort_idx = skin_tab.bone_explorer.sort_combo.currentIndex()
        base_bone_data = skin_controller_instance.get_skin_bone_data_for_ui()
        if sort_idx == 3:
            bone_data = group_controller_instance.get_groups_for_ui(base_bone_data)
        else:
            bone_data = base_bone_data
        skin_tab.bone_explorer.populate_bones(bone_data)
        if show_on_update:
            skin_tab.bone_explorer.show()

    def _on_bone_explorer_view_changed(self):
        self._update_bone_explorer(show_on_update=True)

    def _on_add_group(self):
        text, ok = QInputDialog.getText(self, translator.get("pop_add_group_title"),
                                        translator.get("pop_add_group_label"))
        if ok and text:
            if not group_controller_instance.add_group(text):
                QMessageBox.warning(self, translator.get("title_error"),
                                    translator.get("pop_group_exists").format(text))
            self._update_bone_explorer(True)

    def _on_remove_group(self, group_name):
        if not group_name or group_name == "[Ungrouped]": return
        if QMessageBox.question(self, translator.get("pop_remove_group_title"),
                                translator.get("pop_remove_group_msg").format(
                                    group_name)) == QMessageBox.StandardButton.Yes:
            group_controller_instance.remove_group(group_name)
            self._update_bone_explorer(True)

    def _on_rename_group(self, old_name):
        if not old_name or old_name == "[Ungrouped]": return
        new_name, ok = QInputDialog.getText(self, translator.get("pop_rename_group_title"),
                                            translator.get("pop_rename_group_label"), text=old_name)
        if ok and new_name and new_name != old_name:
            if not group_controller_instance.rename_group(old_name, new_name):
                QMessageBox.warning(self, translator.get("title_error"), translator.get("pop_rename_fail"))
            self._update_bone_explorer(True)

    def _on_assign_bones(self, group_name):
        if not group_name or group_name == "[Ungrouped]":
            QMessageBox.information(self, translator.get("title_info"), translator.get("pop_assign_select_group"))
            return
        skin_tab = self.tabs.get("skinning")
        if not skin_tab: return
        selected_bone_ids = skin_tab.bone_explorer.get_selected_bone_ids()
        if not selected_bone_ids:
            QMessageBox.information(self, translator.get("title_info"), translator.get("pop_assign_select_bones"))
            return
        group_controller_instance.assign_bones_to_group(group_name, selected_bone_ids)
        self._update_bone_explorer(True)

    def _on_remove_unused_bones(self):
        if skin_controller_instance.node:
            try:
                if rt.ohCHA_SkinLogic.removeUnusedBones():
                    self._update_bone_explorer(True)
            except Exception as e:
                QMessageBox.critical(self, translator.get("title_error"), f"{e}")

    def _on_remove_zero_weights(self):
        if not skin_controller_instance.node: return
        try:
            if rt.ohCHA_SkinLogic.pruneWeights(0.001):
                rt.print("✅ Zero weights pruned.")
        except Exception as e:
            rt.print(f"❌ Prune Error: {e}")

    def _on_save_skin(self):
        if not skin_controller_instance.node: return
        if QMessageBox.question(self.window(), translator.get("title_confirm"),
                                translator.get("msg_save_skin_confirm"),
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                updated_data = skin_controller_instance.collapse_all_layers()
                self._update_skin_layer_ui(updated_data)
                self._on_skin_inject()
                if rt.ohCHA_SkinLogic.openSaveSkinDialog():
                    rt.print("✅ Save Dialog Opened.")
                else:
                    rt.print("⚠️ Save Dialog Command Failed.")
            except Exception as e:
                QMessageBox.critical(self.window(), translator.get("title_error"), f"Save Error: {e}")

    def _on_load_skin(self):
        if not skin_controller_instance.node: return
        try:
            if rt.ohCHA_SkinLogic.openLoadSkinDialog():
                rt.print("✅ Load Dialog Opened.")
        except Exception as e:
            rt.print(f"❌ Load Error: {e}")

    def _on_save_bone_list(self):
        if not skin_controller_instance.node: return
        default_name = f"{skin_controller_instance.node.name}_BoneList.json"
        path, _ = QFileDialog.getSaveFileName(self, translator.get("btn_save_bnlist"), default_name,
                                              "JSON Files (*.json)")
        if path:
            if skin_controller_instance.save_bone_list_json(path):
                QMessageBox.information(self, translator.get("title_save_complete"),
                                        translator.get("msg_bnlist_saved").format(os.path.basename(path)))

    def _on_load_bone_list(self):
        if not skin_controller_instance.node: return
        path, _ = QFileDialog.getOpenFileName(self, translator.get("btn_load_bnlist"), "", "JSON Files (*.json)")
        if path:
            count = skin_controller_instance.load_bone_list_json(path)
            if count > 0:
                QMessageBox.information(self, translator.get("title_complete"),
                                        translator.get("msg_bnlist_loaded").format(count))
                self._update_bone_explorer(True)
            else:
                rt.print("⚠️ No bones added (Duplicate or Missing).")

    def _on_find_influencing_bones(self):
        skin_tab = self.tabs.get("skinning")
        skin_mod = skin_controller_instance.native_skin_mod
        if not skin_tab or not skin_mod: return
        
        # ⭐️ [FIX] Ensure function is available
        try:
            vert_indices = get_selected_skin_vert_indices(skin_mod)
        except NameError:
            rt.print("❌ Critical Import Error: get_selected_skin_vert_indices not found.")
            return

        if not vert_indices:
            QMessageBox.information(self, translator.get("title_info"), translator.get("pop_find_bone_select_vert"))
            return
        try:
            all_influences = set()
            for v_id in vert_indices:
                influencing_ids = rt.ohCHA_DataUtil.getVertexInfluences(skin_mod, v_id)
                if influencing_ids:
                    all_influences.update(list(influencing_ids))
            if not all_influences:
                QMessageBox.information(self, translator.get("title_info"), translator.get("pop_find_bone_none"))
                return
            skin_tab.bone_explorer.filter_and_select_by_ids(list(all_influences))
        except Exception as e:
            QMessageBox.critical(self, translator.get("title_error"), f"{e}")
            traceback.print_exc()

    def _on_transfer_weights(self):
        skin_tab = self.tabs.get("skinning")
        if not skin_tab: return
        selected_bone_ids = skin_tab.bone_explorer.get_selected_bone_ids()
        if len(selected_bone_ids) != 1:
            QMessageBox.warning(self, translator.get("title_selection_error"),
                                translator.get("pop_transfer_select_source"))
            return
        source_bone_id = selected_bone_ids[0]
        
        # ⭐️ [FIX] Use imported function
        vert_indices = get_selected_skin_vert_indices(skin_controller_instance.native_skin_mod)
        
        if not vert_indices:
            QMessageBox.warning(self, translator.get("title_selection_error"),
                                translator.get("pop_transfer_select_verts"))
            return
        all_bones = skin_controller_instance.get_skin_bone_data_for_ui()
        target_candidates = [b for b in all_bones if b['id'] != source_bone_id]
        target_candidates.sort(key=lambda x: x['name'])
        items = [f"{b['name']}" for b in target_candidates]
        item, ok = QInputDialog.getItem(self, translator.get("pop_transfer_select_target_title"),
                                        translator.get("pop_transfer_select_target_label"), items, 0, False)
        if ok and item:
            target_bone = next((b for b in target_candidates if b['name'] == item), None)
            if target_bone:
                try:
                    layer_idx = self._get_active_layer_index()
                    res = skin_controller_instance.transfer_weights_on_layer(source_bone_id, target_bone['id'],
                                                                             layer_idx)
                    if not res:
                        QMessageBox.warning(self, translator.get("title_info"),
                                            translator.get("pop_transfer_no_change"))
                except Exception as e:
                    QMessageBox.critical(self, translator.get("title_error"), f"{e}")
                    traceback.print_exc()

    def _get_active_layer_index(self):
        skin_tab = self.tabs.get("skinning")
        if not skin_tab: return 0
        idx, _ = skin_tab.layer_manager_widget.get_selected_indices()
        if idx < 0: return 0
        return idx

    def _on_weight_selection(self, action):
        rt.print(f"🖱️ Button Clicked: {action}")
        try:
            res = rt.ohCHA_SkinLogic.modifySelection(action)
            if not res: rt.print("⚠️ Selection modification failed.")
        except Exception as e:
            rt.print(f"❌ Selection Error: {e}")

    def _on_weight_preset(self, value):
        skin_tab = self.tabs.get("skinning")
        if not skin_tab: return
        selected_bone_ids = skin_tab.bone_explorer.get_selected_bone_ids()
        if len(selected_bone_ids) != 1:
            rt.print("⚠️ Please select exactly ONE bone.")
            return
        target_bone_id = selected_bone_ids[0]
        layer_idx = self._get_active_layer_index()
        if skin_controller_instance.apply_weight_to_active_layer(target_bone_id, value, "set",
                                                                 ui_layer_index=layer_idx):
            rt.print(f"✅ Applied {value} to bone {target_bone_id}")

    def _on_weight_math(self, operation, value):
        skin_tab = self.tabs.get("skinning")
        if not skin_tab: return
        selected_bone_ids = skin_tab.bone_explorer.get_selected_bone_ids()
        if len(selected_bone_ids) != 1:
            rt.print("⚠️ Please select exactly ONE bone.")
            return
        target_bone_id = selected_bone_ids[0]
        layer_idx = self._get_active_layer_index()
        if skin_controller_instance.apply_weight_to_active_layer(target_bone_id, value, operation,
                                                                 ui_layer_index=layer_idx):
            op = "+" if operation == "add" else "-"
            rt.print(f"✅ {op} {value} to bone {target_bone_id}")

    def _on_weight_clipboard(self, action):
        layer_idx = self._get_active_layer_index()
        if action == "copy":
            skin_controller_instance.copy_vertex_weights()
        elif action == "paste":
            skin_controller_instance.paste_vertex_weights(ui_layer_index=layer_idx)

    def _on_weight_smooth(self):
        rt.print("🖱️ Button Clicked: Smooth")
        layer_idx = self._get_active_layer_index()
        skin_controller_instance.apply_smooth_to_active_layer(ui_layer_index=layer_idx)

    def _on_weight_heal(self):
        rt.print("🖱️ Button Clicked: Heal")
        layer_idx = self._get_active_layer_index()
        skin_controller_instance.apply_smart_heal_to_active_layer(ui_layer_index=layer_idx, tolerance=0.1)

    # ⭐️ [FIXED] Force Modify Panel and Select
    def _on_skin_select_envelope(self, bone_id: int):
        if skin_controller_instance.node:
            try:
                # Force MaxScript to handle selection regardless of current panel state
                rt.ohCHA_PaintSession.selectEnvelope(skin_controller_instance.node, bone_id)
                self._last_selected_bone_id = bone_id
            except Exception as e:
                rt.print(f"❌ Selection Error: {e}")

    def _on_skin_paint_commit_toggled(self, ui_index: int):
        skin_tab = self.tabs.get("skinning")
        if not skin_tab: return
        if skin_controller_instance.is_painting:
            updated_data = skin_controller_instance.commit_painting_session()
            self._update_skin_layer_ui(updated_data)
            skin_tab.layer_manager_widget.set_painting_mode(False)
            QMessageBox.information(self.window(), translator.get("title_save_complete"),
                                    translator.get("msg_paint_saved"))
        else:
            if ui_index < 0:
                QMessageBox.warning(self.window(), translator.get("title_layer_selection"),
                                    translator.get("msg_layer_selection_paint"))
                return
            selected_bone_ids = skin_tab.bone_explorer.get_selected_bone_ids()
            bone_id_to_select = selected_bone_ids[0] if selected_bone_ids else None
            if skin_controller_instance.start_painting_session(ui_index, bone_id_to_select):
                QTimer.singleShot(100, lambda: (skin_tab.layer_manager_widget.set_painting_mode(True),
                                                self._on_skin_paint_blend_toggled(
                                                    skin_tab.layer_manager_widget.chk_blend_mode.isChecked())))
            else:
                QMessageBox.warning(self.window(), translator.get("title_error"), translator.get("msg_error_paint"))

    def _on_skin_manual_edit_commit_toggled(self, ui_index: int):
        skin_tab = self.tabs.get("skinning")
        if not skin_tab: return
        if skin_controller_instance.is_editing_manually:
            updated_data = skin_controller_instance.commit_manual_edit_session()
            self._update_skin_layer_ui(updated_data)
            skin_tab.layer_manager_widget.set_manual_editing_mode(False)
            QMessageBox.information(self.window(), translator.get("title_save_complete"),
                                    translator.get("msg_manual_edit_saved"))
        else:
            if ui_index < 0:
                QMessageBox.warning(self.window(), translator.get("title_layer_selection"),
                                    translator.get("msg_layer_selection_manual_edit"))
                return
            if QMessageBox.question(self.window(), translator.get("title_enter_manual_edit"),
                                    translator.get("msg_enter_manual_edit"),
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                if skin_controller_instance.enter_manual_edit_mode(ui_index):
                    skin_tab.layer_manager_widget.set_manual_editing_mode(True)
                    selected_bone_ids = skin_tab.bone_explorer.get_selected_bone_ids()
                    if selected_bone_ids:
                        rt.ohCHA_PaintSession.selectEnvelope(skin_controller_instance.node, selected_bone_ids[0])
                else:
                    QMessageBox.warning(self.window(), translator.get("title_error"),
                                        translator.get("msg_error_manual_edit"))

    def _on_skin_item_selection_changed(self, current, previous):
        if current is None: return
        try:
            item_data = current.data(0, Qt.ItemDataRole.UserRole)
        except RuntimeError:
            return
        if not skin_controller_instance.node: return
        skin_tab = self.tabs.get("skinning")
        if not skin_tab: return
        rt.ohCHA_PaintSession.enterVertexSelectMode(skin_controller_instance.node)
        selected_bone_ids = skin_tab.bone_explorer.get_selected_bone_ids()
        if selected_bone_ids:
            rt.ohCHA_PaintSession.selectEnvelope(skin_controller_instance.node, selected_bone_ids[0])

    def _on_skin_add_layer(self):
        data = skin_controller_instance.add_new_layer()
        self._update_skin_layer_ui(data)

    def _on_skin_remove_layer(self, ui_index: int):
        data = skin_controller_instance.remove_layer(ui_index)
        self._update_skin_layer_ui(data)

    def _on_skin_move_layer_up(self, ui_index: int):
        data = skin_controller_instance.move_layer(ui_index, ui_index - 1)
        self._update_skin_layer_ui(data)

    def _on_skin_move_layer_down(self, ui_index: int):
        data = skin_controller_instance.move_layer(ui_index, ui_index + 1)
        self._update_skin_layer_ui(data)

    def _on_skin_inject(self):
        final_weights = skin_controller_instance.flatten_layers_to_weights()
        if final_weights is None:
            rt.print("⚠️ [Core] Flattening 결과가 없습니다.")
            return
        skin_controller_instance.inject_weights_to_native_skin(final_weights)

    def _on_skin_paint_blend_toggled(self, is_on: bool):
        if not skin_controller_instance.is_painting: return
        try:
            rt.execute(f"ohCHA_SetPaintBlend {'true' if is_on else 'false'}")
        except Exception as e:
            rt.print(f"❌ [Core] _on_skin_paint_blend_toggled 오류: {e}")

    def _on_skin_paint_options_clicked(self):
        if not skin_controller_instance.is_painting: return
        try:
            rt.execute("ohCHA_OpenPaintOptions()")
        except Exception as e:
            rt.print(f"❌ [Core] _on_skin_paint_options_clicked 오류: {e}")

    def _on_skin_blend_mode_changed(self, ui_index: int, mode: str):
        skin_controller_instance.set_layer_blend_mode(ui_index, mode)
        self._on_skin_inject()

    def _on_skin_collapse_layers(self):
        if QMessageBox.question(self.window(), translator.get("title_collapse_layers"),
                                translator.get("msg_collapse_layers"),
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            updated_data = skin_controller_instance.collapse_all_layers()
            self._update_skin_layer_ui(updated_data)
            self._on_skin_inject()
            QMessageBox.information(self.window(), translator.get("title_complete"),
                                    translator.get("msg_collapse_complete"))

    def _on_skin_add_mask_to_layer(self, ui_index: int):
        data = skin_controller_instance.add_mask_to_layer(ui_index)
        self._update_skin_layer_ui(data)

    def _on_skin_remove_mask_from_layer(self, ui_index: int):
        data = skin_controller_instance.remove_mask_from_layer(ui_index)
        self._update_skin_layer_ui(data)

    def _on_skin_update_mask_data(self, ui_index: int, is_remove: bool):
        if skin_controller_instance.native_skin_mod is None: return
        skin_tab = self.tabs.get("skinning")
        if not skin_tab: return
        selected_bone_ids = skin_tab.bone_explorer.get_selected_bone_ids()
        if not selected_bone_ids:
            QMessageBox.warning(self.window(), translator.get("title_bone_selection"),
                                translator.get("msg_bone_selection_mask"))
            return
        vert_indices = get_selected_skin_vert_indices(skin_controller_instance.native_skin_mod)
        if not vert_indices and not is_remove:
            QMessageBox.information(self.window(), translator.get("title_notification"),
                                    translator.get("msg_mask_select_success").format(0))
            return
        for b_id in selected_bone_ids:
            skin_controller_instance.update_mask_data(ui_index, b_id, vert_indices, remove=is_remove)
        self._update_skin_layer_ui(skin_controller_instance.get_layer_data_from_scene())

    def _on_skin_select_mask_verts(self, ui_index: int):
        if skin_controller_instance.native_skin_mod is None: return
        skin_tab = self.tabs.get("skinning")
        if not skin_tab: return
        selected_bone_ids = skin_tab.bone_explorer.get_selected_bone_ids()
        if not selected_bone_ids:
            QMessageBox.warning(self.window(), translator.get("title_bone_selection"),
                                translator.get("msg_bone_selection_check"))
            return
        all_mask_verts = set()
        for b_id in selected_bone_ids:
            all_mask_verts.update(skin_controller_instance.get_mask_verts_for_bone(ui_index, b_id))
        if not all_mask_verts:
            QMessageBox.information(self.window(), translator.get("title_notification"),
                                    translator.get("msg_no_mask_data"))
            select_skin_verts(skin_controller_instance.native_skin_mod, [])
        else:
            select_skin_verts(skin_controller_instance.native_skin_mod, list(all_mask_verts))
            rt.print(translator.get("msg_mask_select_success").format(len(all_mask_verts)))

    def _on_export_skin_clicked(self):
        if not skin_controller_instance.node: return
        default_name = f"{skin_controller_instance.node.name}_SkinData.ohchaSkin"
        path, _ = QFileDialog.getSaveFileName(self, translator.get("btn_export_skindata"), default_name,
                                              "ohCHA Skin Files (*.ohchaSkin)")
        if path:
            if skin_controller_instance.export_skin_data(path):
                QMessageBox.information(self, translator.get("title_save_complete"),
                                        translator.get("msg_save_complete").format(os.path.basename(path)))

    def _on_import_skin_clicked(self):
        if not skin_controller_instance.node: return
        if QMessageBox.warning(self, translator.get("title_warning"), translator.get("msg_import_warn"),
                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        path, _ = QFileDialog.getOpenFileName(self, translator.get("btn_import_skindata"), "",
                                              "ohCHA Skin Files (*.ohchaSkin)")
        if path:
            data = skin_controller_instance.import_skin_data(path)
            if data:
                self._update_skin_layer_ui(data)
                self.tabs["skinning"].layer_manager_widget.set_session_active(True)
                QMessageBox.information(self, translator.get("title_complete"), translator.get("msg_done"))


if __name__ == "__main__":
    try:
        from ui import ohcha_ui_base

        importlib.reload(ohcha_ui_base)
        ohcha_ui_base.show_tool_instance(RigManagerWindow)
    except Exception as e:
        rt.print(f"❌ [PySide] 툴 런처 실행 중 치명적 오류: {e}")
        rt.print(traceback.format_exc())