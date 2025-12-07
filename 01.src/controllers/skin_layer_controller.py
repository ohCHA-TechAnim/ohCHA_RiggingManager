# ohCHA_RigManager/01/src/controllers/skin_layer_controller.py
# Description: [v20.97] FULL CODE.
#              - UPDATED: Uses 'find_script_path' to support .mse/.ms/.txt loading.
#              - INTEGRITY: Preserved all Layer/Mask/Paint logic.

import os
import json
import re
import traceback
import collections
import copy
import shutil
from pymxs import runtime as rt

try:
    from utils.paths import get_project_root, find_script_path
    from utils.ohcha_max_utils import UndoContext, get_selected_skin_vert_indices, get_skin_bone_data
except ImportError:
    rt.print("❌ [SkinController] 'utils' 임포트 실패")
    get_project_root = lambda: ""
    find_script_path = lambda x: None
    get_selected_skin_vert_indices = lambda m: []
    get_skin_bone_data = lambda m: []


    class UndoContext:
        def __init__(self, name, *args): pass

        def __enter__(self): pass

        def __exit__(self, *args): pass


def _load_data_manager():
    """Loads ohcha_data_utils using flexible extension check."""
    path = find_script_path("ohcha_data_utils")
    if path:
        try:
            rt.fileIn(path)
            return rt.globalVars.get("ohCHA_DataUtil") != rt.undefined
        except Exception as e:
            rt.print(f"❌ [SkinController] DataUtil Load Error: {e}")
            return False
    return False


DEFAULT_SKIN_DATA = {
    "version": "1.6",
    "bones": [],
    "layers": [
        {
            "name": "Base Weights",
            "opacity": 1.0,
            "enabled": True,
            "mask": None,
            "mask_enabled": True,
            "blend_mode": "Overwrite",
            "weights": {}
        }
    ]
}


class SkinLayerController:
    def __init__(self):
        self.node = None
        self.native_skin_mod = None
        self.is_manager_loaded = _load_data_manager()

        # Session State
        self.is_painting = False
        self.is_editing_manually = False
        self.editing_layer_index = -1

        # Data Cache (RAM)
        self.cached_data = None
        self.backup_weights = None
        self.clipboard_weights = {}
        self.topology_cache = {}
        self.cached_node_handle = None

    def set_current_node(self, node):
        if self.is_painting or self.is_editing_manually: return

        self.node = None
        self.native_skin_mod = None
        self.cached_data = None
        self.topology_cache = {}
        self.cached_node_handle = None

        if node and rt.isValidNode(node):
            self.node = node
            self.native_skin_mod = self._find_native_skin_mod_mxs()
            if self.native_skin_mod:
                self.cached_node_handle = str(node.handle)
                self.cached_data = self._load_data_from_disk()
                rt.print(f"✅ [SkinController] Node Set: {node.name} (Data Loaded)")
            else:
                rt.print(f"⚠️ [SkinController] No Skin Modifier: {node.name}")

    def _ui_to_data_index(self, ui_index: int, total_layers: int) -> int:
        return total_layers - 1 - ui_index

    def _get_sidecar_file_path(self):
        if not self.node or not rt.isValidNode(self.node): return None
        project_root = get_project_root()
        if not project_root: return None
        cache_dir = os.path.join(project_root, "data", "skin_cache")
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except Exception:
            return None

        node_name_safe = re.sub(r'[\\/*?:"<>|]', "_", self.node.name).replace(" ", "_")
        return os.path.join(cache_dir, f"{node_name_safe}.ohchaSkin")

    def _load_data_from_disk(self) -> dict:
        sidecar_path = self._get_sidecar_file_path()
        if not sidecar_path or not os.path.exists(sidecar_path):
            return copy.deepcopy(DEFAULT_SKIN_DATA)
        try:
            with open(sidecar_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "layers" in data:
                    for layer in data["layers"]:
                        if "enabled" not in layer: layer["enabled"] = True
                        if "mask_enabled" not in layer: layer["mask_enabled"] = True
                return data
        except Exception:
            return copy.deepcopy(DEFAULT_SKIN_DATA)

    def get_layer_data_from_scene(self) -> dict:
        if self.cached_data is None:
            self.cached_data = self._load_data_from_disk()
        return self.cached_data

    def save_layer_data_to_scene(self, py_data: dict) -> bool:
        self.cached_data = py_data

        sidecar_path = self._get_sidecar_file_path()
        if not sidecar_path: return False
        try:
            if self.native_skin_mod:
                try:
                    bones_data = get_skin_bone_data(self.native_skin_mod)
                    py_data["bones"] = [b['name'] for b in bones_data]
                except:
                    pass

            with open(sidecar_path, 'w', encoding='utf-8') as f:
                json.dump(py_data, f, indent=4)
            return True
        except Exception:
            return False

    def export_skin_data(self, target_path: str) -> bool:
        if self.cached_data:
            self.save_layer_data_to_scene(self.cached_data)

        source_path = self._get_sidecar_file_path()
        if not source_path or not os.path.exists(source_path): return False
        try:
            shutil.copy2(source_path, target_path)
            return True
        except Exception as e:
            rt.print(f"❌ Export Failed: {e}")
            return False

    def import_skin_data(self, source_path: str) -> dict:
        if not self.native_skin_mod: return None
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            bone_names = data.get("bones", [])
            if bone_names:
                mxs_names = rt.Array(*(str(n) for n in bone_names))
                rt.ohCHA_SkinLogic.addBonesToSkin(mxs_names)

            self.save_layer_data_to_scene(data)
            return data
        except Exception as e:
            rt.print(f"❌ Import Failed: {e}")
            return None

    def inject_weights_to_native_skin(self, final_weights: dict, undo_name="ohCHA Skin Inject"):
        if not self.native_skin_mod or final_weights is None: return

        # Note: We rely on memory cache. No explicit save here for performance.
        rt.disableSceneRedraw()

        vert_ids = []
        bone_ids_list = []
        weights_list = []

        for vert_index, (bone_indices, weights) in final_weights.items():
            if not bone_indices: continue
            vert_ids.append(int(vert_index))
            bone_ids_list.append(rt.Array(*(int(b) for b in bone_indices)))
            weights_list.append(rt.Array(*(float(w) for w in weights)))

        mxs_vert_ids = rt.Array(*vert_ids)
        mxs_bone_list = rt.Array(*bone_ids_list)
        mxs_weight_list = rt.Array(*weights_list)

        with UndoContext(undo_name):
            try:
                # Calls optimized Bulk Injector
                rt.ohCHA_SkinLogic.applyBulkSkinData(self.native_skin_mod, mxs_vert_ids, mxs_bone_list, mxs_weight_list)
            except Exception as e:
                rt.print(f"❌ [Inject] 웨이트 주입 중 오류: {e}")
                traceback.print_exc()
            finally:
                rt.enableSceneRedraw()
                rt.forceCompleteRedraw()
                rt.gc(light=True)

    def flatten_layers_to_weights(self, up_to_ui_index: int = -1) -> dict | None:
        layer_data = self.get_layer_data_from_scene()
        layers = layer_data.get("layers", [])

        if not layers: return None

        num_layers_to_process = len(layers)
        if up_to_ui_index != -1:
            data_index_to = self._ui_to_data_index(up_to_ui_index, len(layers))
            num_layers_to_process = data_index_to + 1

        target_layers = layers[:num_layers_to_process]
        if not target_layers: return None

        start_index = -1
        for i, layer in enumerate(target_layers):
            if layer.get("enabled", True):
                start_index = i
                break

        if start_index == -1:
            return {}

        base_layer = target_layers[start_index]
        base_weights = base_layer.get("weights", {})

        final_weights_map = {
            int(v_idx): collections.defaultdict(float, zip(bones, weights))
            for v_idx, (bones, weights) in base_weights.items()
        }

        for layer in target_layers[start_index + 1:]:
            if not layer.get("enabled", True): continue
            if not layer.get("weights"): continue

            opacity = layer.get("opacity", 1.0)
            blend_mode = layer.get("blend_mode", "Overwrite")
            mask = layer.get("mask")
            mask_enabled = layer.get("mask_enabled", True)

            layer_data_map = {int(v_idx): dict(zip(bones, weights)) for v_idx, (bones, weights) in
                              layer.get("weights", {}).items()}

            masked_verts = set()
            if mask and mask_enabled:
                for v_list in mask.values(): masked_verts.update(v_list)

            for v_idx, vert_weights in layer_data_map.items():
                if mask and mask_enabled and v_idx not in masked_verts: continue
                current_weights = final_weights_map.setdefault(v_idx, collections.defaultdict(float))

                if blend_mode == "Overwrite":
                    if opacity >= 0.999:
                        current_weights.clear()
                        current_weights.update(vert_weights)
                    else:
                        for b_id in set(current_weights.keys()) | set(vert_weights.keys()):
                            old_w = current_weights.get(b_id, 0.0)
                            new_w = vert_weights.get(b_id, 0.0)
                            current_weights[b_id] = old_w * (1.0 - opacity) + new_w * opacity

                elif blend_mode == "Add":
                    for b_id, w in vert_weights.items(): current_weights[b_id] += w * opacity

                elif blend_mode == "Subtract":
                    for b_id, w in vert_weights.items(): current_weights[b_id] -= w * opacity

                elif blend_mode == "Normal":
                    for b_id in set(current_weights.keys()) | set(vert_weights.keys()):
                        old_w = current_weights.get(b_id, 0.0)
                        new_w = vert_weights.get(b_id, 0.0)
                        current_weights[b_id] = old_w * (1.0 - opacity) + new_w * opacity

        injectable_weights = {}
        for v_idx, blended_weights_map in final_weights_map.items():
            final_bone_weights = {b: w for b, w in blended_weights_map.items() if w > 1e-6}
            total_weight = sum(final_bone_weights.values())
            if total_weight < 1e-6: continue

            scale_factor = 1.0 / total_weight
            final_bones = []
            final_weights = []
            for b, w in final_bone_weights.items():
                final_bones.append(b)
                final_weights.append(w * scale_factor)

            injectable_weights[v_idx] = (final_bones, final_weights)
        return injectable_weights

    def toggle_layer_visibility(self, ui_index: int, state: bool) -> dict:
        d = self.get_layer_data_from_scene()
        idx = self._ui_to_data_index(ui_index, len(d['layers']))
        if 0 <= idx < len(d['layers']):
            d['layers'][idx]['enabled'] = state
            self.save_layer_data_to_scene(d)
        return d

    def toggle_mask_visibility(self, ui_index: int, state: bool) -> dict:
        d = self.get_layer_data_from_scene()
        idx = self._ui_to_data_index(ui_index, len(d['layers']))
        if 0 <= idx < len(d['layers']):
            d['layers'][idx]['mask_enabled'] = state
            self.save_layer_data_to_scene(d)
        return d

    def _sync_layer_from_viewport_selection(self):
        if not self.node or not self.native_skin_mod: return
        try:
            sel_verts = get_selected_skin_vert_indices(self.native_skin_mod)
        except:
            return
        if not sel_verts: return

        all_data = self.get_layer_data_from_scene()
        layers = all_data.get("layers", [])
        target_ui_index = self.editing_layer_index if self.editing_layer_index != -1 else 0
        data_index = self._ui_to_data_index(target_ui_index, len(layers))
        if data_index < 0 or data_index >= len(layers): return

        target_layer = layers[data_index]
        layer_weights = target_layer.get("weights", {})

        mxs_verts = rt.Array(*(int(v) for v in sel_verts))
        bulk_data = rt.ohCHA_DataUtil.getBulkVertexWeights(self.node, mxs_verts)

        if bulk_data:
            for entry in bulk_data:
                v_idx = int(entry[0])
                v_str = str(v_idx)
                bones = list(entry[1])
                weights = list(entry[2])

                valid_bones = []
                valid_weights = []
                for b, w in zip(bones, weights):
                    if w > 0.0001:
                        valid_bones.append(int(b))
                        valid_weights.append(round(float(w), 6))

                if valid_bones:
                    layer_weights[v_str] = [valid_bones, valid_weights]
                else:
                    if v_str in layer_weights: del layer_weights[v_str]

        target_layer["weights"] = layer_weights
        self.cached_data = all_data

    def save_bone_list_json(self, file_path: str) -> bool:
        if not self.native_skin_mod: return False
        try:
            bones_data = get_skin_bone_data(self.native_skin_mod)
            bone_names = [b['name'] for b in bones_data]
            data = {"version": "1.0", "count": len(bone_names), "bones": bone_names}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            rt.print(f"❌ Save Bone List Error: {e}")
            return False

    def load_bone_list_json(self, file_path: str) -> int:
        if not self.native_skin_mod: return 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            bone_names = data.get("bones", [])
            if not bone_names: return 0
            mxs_names = rt.Array(*(str(n) for n in bone_names))
            added_count = rt.ohCHA_SkinLogic.addBonesToSkin(mxs_names)
            return added_count
        except Exception as e:
            rt.print(f"❌ Load Bone List Error: {e}")
            return 0

    def apply_smooth_to_active_layer(self, ui_layer_index: int = -1, strength: float = 1.0, bone_limit: int = 4,
                                     prune_threshold: float = 0.02) -> bool:
        if not self.node or not self.native_skin_mod: return False
        sel_verts = get_selected_skin_vert_indices(self.native_skin_mod)
        if not sel_verts: return False
        if ui_layer_index != -1: self.editing_layer_index = ui_layer_index

        if not self.topology_cache:
            mxs_topo = rt.ohCHA_DataUtil.getMeshTopology(self.node)
            if not mxs_topo: return False
            self.topology_cache = [list(adj) for adj in mxs_topo]

        self._sync_layer_from_viewport_selection()
        all_data = self.get_layer_data_from_scene()
        layers = all_data.get("layers", [])
        data_index = self._ui_to_data_index(self.editing_layer_index, len(layers))
        target_layer = layers[data_index]
        layer_weights = target_layer.get("weights", {})
        layer_mask = target_layer.get("mask")
        mask_enabled = target_layer.get("mask_enabled", True)

        valid_mask_verts = None
        if layer_mask and mask_enabled: valid_mask_verts = set(sum(layer_mask.values(), []))

        new_weights_map = {}
        for v_idx in sel_verts:
            v_str = str(v_idx)
            if valid_mask_verts is not None and v_idx not in valid_mask_verts: continue
            my_data = layer_weights.get(v_str, [[], []])
            my_weights = collections.defaultdict(float, zip(my_data[0], my_data[1]))
            if v_idx > len(self.topology_cache): continue
            neighbors = self.topology_cache[v_idx - 1]
            if not neighbors: continue

            sum_weights = collections.defaultdict(float)
            valid_cnt = 0
            for n_idx in neighbors:
                n_str = str(n_idx)
                if n_str in layer_weights:
                    for b, w in zip(layer_weights[n_str][0], layer_weights[n_str][1]): sum_weights[b] += w
                    valid_cnt += 1
            if valid_cnt == 0: continue

            avg_weights = {b: w / valid_cnt for b, w in sum_weights.items()}
            final_bone_weights = collections.defaultdict(float)
            all_bones = set(my_weights.keys()) | set(avg_weights.keys())

            for b_id in all_bones:
                val_new = (my_weights[b_id] * (1.0 - strength)) + (avg_weights.get(b_id, 0.0) * strength)
                if val_new > prune_threshold: final_bone_weights[b_id] = val_new

            sorted_items = sorted(final_bone_weights.items(), key=lambda x: x[1], reverse=True)[:bone_limit]
            total_w = sum(val for _, val in sorted_items)
            if total_w > 1e-6:
                factor = 1.0 / total_w
                new_weights_map[v_str] = [[b for b, _ in sorted_items], [round(w * factor, 6) for _, w in sorted_items]]
            else:
                if v_str in new_weights_map: del new_weights_map[v_str]

        if new_weights_map:
            layer_weights.update(new_weights_map)
            target_layer["weights"] = layer_weights

            self.cached_data = all_data
            final_result = self.flatten_layers_to_weights()
            self.inject_weights_to_native_skin(final_result)

            rt.print(f"✅ [Smooth] Relaxed {len(new_weights_map)} vertices.")
            return True
        return False

    def apply_smart_heal_to_active_layer(self, ui_layer_index: int = -1, tolerance: float = 0.05) -> bool:
        if not self.node or not self.native_skin_mod: return False
        sel_verts = get_selected_skin_vert_indices(self.native_skin_mod)
        if not sel_verts:
            rt.print("⚠️ No vertices selected to heal.")
            return False

        if ui_layer_index != -1: self.editing_layer_index = ui_layer_index

        if not self.topology_cache:
            mxs_topo = rt.ohCHA_DataUtil.getMeshTopology(self.node)
            if not mxs_topo: return False
            self.topology_cache = [list(adj) for adj in mxs_topo]

        process_verts = set(sel_verts)
        for v_idx in sel_verts:
            if v_idx <= len(self.topology_cache):
                neighbors = self.topology_cache[v_idx - 1]
                process_verts.update(neighbors)

        self._sync_layer_from_viewport_selection()
        all_data = self.get_layer_data_from_scene()
        layers = all_data.get("layers", [])
        data_index = self._ui_to_data_index(self.editing_layer_index, len(layers))
        target_layer = layers[data_index]
        layer_weights = target_layer.get("weights", {})

        layer_mask = target_layer.get("mask")
        mask_enabled = target_layer.get("mask_enabled", True)
        valid_mask_verts = None
        if layer_mask and mask_enabled: valid_mask_verts = set(sum(layer_mask.values(), []))

        changes_count = 0
        new_weights_map = {}

        for v_idx in process_verts:
            if valid_mask_verts is not None and v_idx not in valid_mask_verts: continue
            v_str = str(v_idx)
            my_data = layer_weights.get(v_str, [[], []])
            my_weights = dict(zip(my_data[0], my_data[1]))
            if not my_weights: continue

            if v_idx > len(self.topology_cache): continue
            neighbors = self.topology_cache[v_idx - 1]
            if not neighbors: continue

            neighbor_accum = collections.defaultdict(float)
            valid_neighbors = 0
            for n_idx in neighbors:
                n_str = str(n_idx)
                if n_str in layer_weights:
                    for b, w in zip(layer_weights[n_str][0], layer_weights[n_str][1]):
                        neighbor_accum[b] += w
                    valid_neighbors += 1

            if valid_neighbors == 0: continue
            neighbor_avg = {b: w / valid_neighbors for b, w in neighbor_accum.items()}
            filtered_bones = {}
            is_dirty = False

            for b_id, my_w in my_weights.items():
                n_avg = neighbor_avg.get(b_id, 0.0)
                if n_avg < tolerance:
                    is_dirty = True
                else:
                    filtered_bones[b_id] = my_w

            if not is_dirty: continue

            final_bones_list = []
            final_vals_list = []
            if not filtered_bones:
                for b, w in neighbor_avg.items(): filtered_bones[b] = w

            total_w = sum(filtered_bones.values())
            if total_w > 1e-6:
                factor = 1.0 / total_w
                sorted_items = sorted(filtered_bones.items(), key=lambda x: x[1], reverse=True)
                for b, w in sorted_items:
                    new_w = w * factor
                    if new_w > 0.001:
                        final_bones_list.append(b)
                        final_vals_list.append(round(new_w, 6))

            new_weights_map[v_str] = [final_bones_list, final_vals_list]
            changes_count += 1

        if changes_count > 0:
            layer_weights.update(new_weights_map)
            target_layer["weights"] = layer_weights

            self.cached_data = all_data
            final_result = self.flatten_layers_to_weights()
            self.inject_weights_to_native_skin(final_result)

            rt.print(f"✅ [Heal] Expanded Area Processed: {changes_count} vertices corrected.")
            return True
        rt.print("ℹ️ [Heal] Area is clean.")
        return False

    def apply_weight_to_active_layer(self, target_bone_id: int, value: float, operation: str = "set",
                                     ui_layer_index: int = -1) -> bool:
        if not self.node or not self.native_skin_mod: return False
        if ui_layer_index != -1: self.editing_layer_index = ui_layer_index
        success = rt.ohCHA_SkinLogic.applyWeightOperation(target_bone_id, value, operation)
        if success:
            self._sync_layer_from_viewport_selection()
            return True
        return False

    def copy_vertex_weights(self):
        if not self.native_skin_mod: return
        try:
            sel_verts = get_selected_skin_vert_indices(self.native_skin_mod)
            if not sel_verts: return
            vert_id = sel_verts[0]
            count = rt.skinOps.GetVertexWeightCount(self.native_skin_mod, vert_id)
            self.clipboard_weights = {}
            for i in range(1, count + 1):
                self.clipboard_weights[
                    rt.skinOps.GetVertexWeightBoneID(self.native_skin_mod, vert_id, i)] = rt.skinOps.GetVertexWeight(
                    self.native_skin_mod, vert_id, i)
            rt.print(f"📋 Copied from {vert_id}")
        except:
            pass

    def paste_vertex_weights(self, ui_layer_index: int = -1) -> bool:
        if not self.clipboard_weights: return False
        if not self.native_skin_mod: return False
        if ui_layer_index != -1: self.editing_layer_index = ui_layer_index
        bones = list(self.clipboard_weights.keys())
        weights = list(self.clipboard_weights.values())
        mxs_bones = rt.Array(*(int(b) for b in bones))
        mxs_weights = rt.Array(*(float(w) for w in weights))
        success = rt.ohCHA_SkinLogic.pasteWeightData(mxs_bones, mxs_weights)
        if success:
            self._sync_layer_from_viewport_selection()
            rt.print("📋 Pasted")
            return True
        return False

    def transfer_weights_on_layer(self, source_id: int, target_id: int, ui_layer_index: int) -> bool:
        if not self.node or not self.native_skin_mod: return False
        if ui_layer_index != -1: self.editing_layer_index = ui_layer_index
        success = rt.ohCHA_SkinLogic.transferWeights(source_id, target_id)
        if success:
            self._sync_layer_from_viewport_selection()
            return True
        return False

    def start_painting_session(self, ui_index: int, selected_bone_id: int | None = None) -> bool:
        if self.is_painting or self.is_editing_manually or not self.node: return False
        rt.print(f"🔥 [Paint] UI Layer {ui_index}")
        self.backup_weights = self.flatten_layers_to_weights() or {}
        current_layer_state = self.flatten_layers_to_weights(up_to_ui_index=ui_index)
        if current_layer_state is None: return False
        self.inject_weights_to_native_skin(current_layer_state)
        if not rt.ohCHA_PaintSession.start(self.node, selected_bone_id):
            self.inject_weights_to_native_skin(self.backup_weights)
            return False
        self.editing_layer_index = ui_index
        self.is_painting = True
        return True

    def commit_painting_session(self) -> dict:
        if not self.is_painting: return self.get_layer_data_from_scene()
        rt.ohCHA_PaintSession.commit()
        try:
            mxs_weight_data = rt.ohCHA_PaintSession.getPaintedWeights(self.node)
        except:
            return self.get_layer_data_from_scene()
        captured = {str(i[0]): [list(i[1]), [round(w, 6) for w in i[2]]] for i in mxs_weight_data}
        all_data = self.get_layer_data_from_scene()
        layers = all_data['layers']
        target_layer = layers[self._ui_to_data_index(self.editing_layer_index, len(layers))]
        mask = target_layer.get("mask")
        mask_enabled = target_layer.get("mask_enabled", True)

        if mask and mask_enabled:
            valid = set(sum(mask.values(), []))
            curr = target_layer.get("weights", {}).copy()
            for k, v in captured.items():
                if int(k) in valid: curr[k] = v
            target_layer['weights'] = curr
        else:
            target_layer['weights'] = captured

        self.save_layer_data_to_scene(all_data)
        self.is_painting = False
        self.editing_layer_index = -1
        self.backup_weights = None
        return all_data

    def enter_manual_edit_mode(self, ui_index: int) -> bool:
        if self.is_painting or self.is_editing_manually or not self.node: return False
        target = self.flatten_layers_to_weights(up_to_ui_index=ui_index)
        if not target: return False
        self.inject_weights_to_native_skin(target)
        if not rt.ohCHA_PaintSession.enterManualEditMode(self.node): return False
        self.editing_layer_index = ui_index
        self.is_editing_manually = True
        return True

    def commit_manual_edit_session(self) -> dict:
        if not self.is_editing_manually: return self.get_layer_data_from_scene()
        res = self.capture_and_save_to_layer(
            self._ui_to_data_index(self.editing_layer_index, len(self.get_layer_data_from_scene()['layers'])), True)
        self.is_editing_manually = False
        self.editing_layer_index = -1
        return res

    def capture_and_save_to_layer(self, data_index: int, do_save: bool = True) -> dict:
        if not self.is_manager_loaded: return {}
        try:
            w_data = rt.ohCHA_DataUtil.getAllVertexWeights(self.node)
        except:
            return {}
        proc = {str(i[0]): [list(i[1]), [round(w, 6) for w in i[2]]] for i in w_data}
        d = self.get_layer_data_from_scene()
        d['layers'][data_index]['weights'] = proc
        if do_save: self.save_layer_data_to_scene(d)
        return d

    def add_new_layer(self, name="New Layer") -> dict:
        d = self.get_layer_data_from_scene()
        n = name
        c = 1
        names = {l['name'] for l in d['layers']}
        while n in names: n = f"{name} {c}"; c += 1
        d['layers'].append(
            {"name": n, "opacity": 1.0, "enabled": True, "mask": None, "mask_enabled": True, "blend_mode": "Overwrite",
             "weights": {}})
        self.save_layer_data_to_scene(d)
        return d

    def remove_layer(self, ui_index: int) -> dict:
        d = self.get_layer_data_from_scene()
        idx = self._ui_to_data_index(ui_index, len(d['layers']))
        if idx != 0:
            d['layers'].pop(idx)
            self.save_layer_data_to_scene(d)
        return d

    def move_layer(self, f, t) -> dict:
        d = self.get_layer_data_from_scene()
        df = self._ui_to_data_index(f, len(d['layers']))
        dt = self._ui_to_data_index(t, len(d['layers']))
        if df != 0 and dt != 0:
            l = d['layers'].pop(df)
            d['layers'].insert(dt, l)
            self.save_layer_data_to_scene(d)
        return d

    def collapse_all_layers(self) -> dict:
        w = self.flatten_layers_to_weights()
        if not w: return self.get_layer_data_from_scene()
        new_w = {str(k): [v[0], v[1]] for k, v in w.items()}

        d = copy.deepcopy(DEFAULT_SKIN_DATA)
        d["layers"][0]["weights"] = new_w

        self.save_layer_data_to_scene(d)
        return d

    def add_mask_to_layer(self, ui_index: int) -> dict:
        d = self.get_layer_data_from_scene()
        idx = self._ui_to_data_index(ui_index, len(d['layers']))
        if 0 <= idx < len(d['layers']) and d['layers'][idx].get('mask') is None:
            d['layers'][idx]['mask'] = {}
            d['layers'][idx]['mask_enabled'] = True
            self.save_layer_data_to_scene(d)
        return d

    def remove_mask_from_layer(self, ui_index: int) -> dict:
        d = self.get_layer_data_from_scene()
        idx = self._ui_to_data_index(ui_index, len(d['layers']))
        if 0 <= idx < len(d['layers']) and 'mask' in d['layers'][idx]:
            d['layers'][idx]['mask'] = None
            d['layers'][idx]['mask_enabled'] = True
            self.save_layer_data_to_scene(d)
        return d

    def update_mask_data(self, ui_index: int, bid: int, verts: list, remove=False) -> dict:
        d = self.get_layer_data_from_scene()
        idx = self._ui_to_data_index(ui_index, len(d['layers']))
        if 0 <= idx < len(d['layers']):
            l = d['layers'][idx]
            m = l.get('mask')
            if m is None:
                if remove: return d
                l['mask'] = {}
                l['mask_enabled'] = True
                m = l['mask']
            sid = str(bid)
            s = set(m.get(sid, []))
            if remove:
                s.difference_update(verts)
            else:
                s.update(verts)
            if s:
                m[sid] = sorted(list(s))
            elif sid in m:
                del m[sid]
            self.save_layer_data_to_scene(d)
        return d

    def get_mask_verts_for_bone(self, ui_index: int, bid: int) -> list:
        d = self.get_layer_data_from_scene()
        idx = self._ui_to_data_index(ui_index, len(d['layers']))
        if 0 <= idx < len(d['layers']): return d['layers'][idx].get('mask', {}).get(str(bid), [])
        return []

    def set_layer_blend_mode(self, ui_index: int, mode: str) -> dict:
        d = self.get_layer_data_from_scene()
        idx = self._ui_to_data_index(ui_index, len(d['layers']))
        if 0 <= idx < len(d['layers']):
            d['layers'][idx]['blend_mode'] = mode
            self.save_layer_data_to_scene(d)
        return d

    def _find_native_skin_mod_mxs(self):
        if not self.is_manager_loaded or not self.node: return None
        try:
            return rt.ohCHA_DataUtil._findNativeSkinModifier(self.node)
        except:
            return None

    def get_skin_bone_data_for_ui(self):
        from utils.ohcha_max_utils import get_skin_bone_data
        return get_skin_bone_data(self.native_skin_mod)


skin_controller_instance = SkinLayerController()