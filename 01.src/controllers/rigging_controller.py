# ohCHA_RigManager/01/src/controllers/rigging_controller.py
# Description: [v21.36] DEBUG CONTROLLER.
#              - STRETCH: No changes, calling updated MS logic.

import pymxs
import importlib
import os
from pymxs import runtime as rt

try:
    from controllers import rigging_logic

    importlib.reload(rigging_logic)
except ImportError:
    rigging_logic = None
    print("❌ [RiggingController] Failed to import rigging_logic.py")

try:
    from utils.paths import get_project_root, find_script_path
except ImportError:
    get_project_root = lambda: ""
    find_script_path = lambda x: None


class RiggingController:
    def __init__(self):
        print("--- [RiggingController] Init ---")
        self._ensure_logic_loaded()

    def _ensure_logic_loaded(self):
        """Checks if MaxScript structs are loaded and prints status."""
        modules = [
            ("ohCHA_ShapeUtils", "ohcha_shape_utils"),
            ("ohCHA_BoneLogic", "ohcha_bone_logic"),
            ("ohCHA_BipedLogic", "ohcha_biped_logic"),
            ("ohCHA_ControlLogic", "ohcha_control_logic")
        ]

        for struct_name, file_base in modules:
            try:
                # Check if struct is loaded
                is_loaded = hasattr(rt, struct_name) and getattr(rt, struct_name) is not None

                if not is_loaded:
                    print(f"⚠️ [DEBUG] '{struct_name}' not found. Attempting load...")
                    path = find_script_path(file_base)

                    if path:
                        print(f"   -> Loading from: {path}")
                        rt.fileIn(path)

                        # Re-check
                        if hasattr(rt, struct_name):
                            print(f"   ✅ Loaded successfully: {struct_name}")
                        else:
                            print(f"   ❌ Failed to initialize struct: {struct_name}")
                    else:
                        print(f"   ❌ Script file missing: {file_base}")
                # else:
                #     print(f"   ✅ Already loaded: {struct_name}")

            except Exception as e:
                print(f"❌ [RiggingController] Load Error ({struct_name}): {e}")

    # =================================================================
    # [1] Biped
    # =================================================================
    def create_guide_skeleton(self, config_dict):
        if rigging_logic: rigging_logic.create_guide_skeleton(config_dict)

    def mirror_guides(self):
        if rigging_logic: rigging_logic.mirror_selected_guides()

    def auto_align_guides(self):
        if rigging_logic: rigging_logic.apply_guide_lookat()

    def finalize_biped(self, config_dict):
        self._ensure_logic_loaded()
        if hasattr(rt, "ohCHA_BipedLogic"):
            rt.ohCHA_BipedLogic.generateAndFitBiped(config_dict)
        else:
            print("❌ [Error] ohCHA_BipedLogic undefined.")

    def get_guide_data(self):
        if rigging_logic: return rigging_logic.get_guide_hierarchy_data()
        return []

    def snap_guide_to_selection(self, guide_name):
        if rigging_logic: return rigging_logic.snap_guide_to_vertex_center(guide_name)
        return False

    # =================================================================
    # [2] Twist
    # =================================================================
    def create_twist_bones_batch(self, count, is_child_driven):
        self._ensure_logic_loaded()
        sel = list(rt.selection)
        if not sel: return False
        cnt = 0
        for obj in sel:
            prefix = f"Twist_{obj.name}"
            try:
                if rt.ohCHA_BoneLogic.createTwistBoneChain(obj, count, prefix, is_child_driven): cnt += 1
            except:
                pass
        return cnt > 0

    # =================================================================
    # [3] Bone Tools
    # =================================================================
    def create_bone_chain(self, name, count, width, height, taper, fin_flags=None):
        self._ensure_logic_loaded()
        pos_list = []
        if rt.selection.count >= 2:
            for o in rt.selection: pos_list.append(o.pos)
        elif rt.selection.count == 1:
            start = rt.selection[0].pos
            for i in range(count + 1): pos_list.append(start + rt.point3(0, 0, i * 20.0))
        else:
            start = rt.point3(0, 0, 0)
            for i in range(count + 1): pos_list.append(start + rt.point3(0, 0, i * 20.0))

        side, front, back = False, False, False
        if fin_flags:
            side = fin_flags.get('side', False)
            front = fin_flags.get('front', False)
            back = fin_flags.get('back', False)

        try:
            mxs_pos_list = rt.Array(*(p for p in pos_list))
            rt.ohCHA_BoneLogic.createCustomBoneChain(
                mxs_pos_list, name,
                float(width), float(height), float(taper),
                side, front, back
            )
            print(f"✅ Bone Chain Created.")
        except Exception as e:
            print(f"❌ Bone Creation Error: {e}")

    def apply_stretch_to_selection(self, width=10.0):
        self._ensure_logic_loaded()
        if rt.selection.count == 0:
            print("⚠️ Select bones first.")
            return
        try:
            val = float(width) * 2.0
            rt.ohCHA_BoneLogic.applyStretchToSelection(val)
            print(f"✅ Stretch setup applied.")
        except Exception as e:
            print(f"❌ Stretch Error: {e}")

    def create_mirror_gizmo(self, size):
        """Creates Mirror Gizmo (Helper) via BoneLogic."""
        self._ensure_logic_loaded()
        if not hasattr(rt, "ohCHA_BoneLogic"): return
        try:
            result_node = rt.ohCHA_BoneLogic.createMirrorGizmo(float(size))
            if rt.isValidNode(result_node):
                print(f"✅ Mirror Gizmo created: {result_node.name}")
        except Exception as e:
            print(f"❌ Gizmo Error: {e}")

    def mirror_bones(self, axis_mode, flip_mode, offset):
        self._ensure_logic_loaded()
        helper = rt.getNodeByName("Helper_Mirror_Plane")
        if not helper:
            print("⚠️ [Mirror] Gizmo 'Helper_Mirror_Plane' not found.")
            return
        if rt.selection.count == 0:
            print("⚠️ [Mirror] No bones selected.")
            return
        mxs_nodes = rt.Array(*list(rt.selection))
        try:
            rt.ohCHA_BoneLogic.mirrorBonesAdvanced(mxs_nodes, helper, axis_mode, flip_mode, float(offset))
            print("✅ Bones mirrored successfully.")
        except Exception as e:
            print(f"❌ Mirror Error: {e}")

    def color_bones(self, col_start, col_end, use_gradient):
        self._ensure_logic_loaded()
        sel = list(rt.selection)
        if not sel: return
        c1 = rt.color(col_start.red(), col_start.green(), col_start.blue())
        c2 = rt.color(col_end.red(), col_end.green(), col_end.blue())
        if use_gradient:
            if len(sel) == 1:
                rt.ohCHA_BoneLogic.colorHierarchy(sel[0], c1, c2)
            else:
                rt.ohCHA_BoneLogic.colorNodeList(rt.Array(*sel), c1, c2)
        else:
            for o in sel: o.wirecolor = c1
        rt.redrawViews()

    def create_controller(self, shape_type):
        self._ensure_logic_loaded()
        rt.ohCHA_ShapeUtils.createCurveController(shape_type, 10.0)

    # =================================================================
    # [4] Controller Inspector
    # =================================================================
    def get_controller_hierarchy(self, node):
        self._ensure_logic_loaded()
        if not rt.isValidNode(node): return []
        try:
            raw = rt.ohCHA_ControlLogic.getControllerTree(node)
            parsed = []
            for row in raw:
                parsed.append({
                    "index": int(row[0]), "parent_index": int(row[1]),
                    "name": str(row[2]), "type": str(row[3]),
                    "depth": int(row[4]), "sub_id": int(row[5])
                })
            return parsed
        except:
            return []

    def get_node_info(self, node):
        self._ensure_logic_loaded()
        if not rt.isValidNode(node): return {}
        ht = rt.ohCHA_ControlLogic.getNodeInfo(node)
        if not ht: return {}
        return {
            "Name": ht.Item["Name"], "Class": ht.Item["Class"],
            "Handle": ht.Item["Handle"], "WireColor": ht.Item["WireColor"],
            "Pos": ht.Item["Pos"], "Rot": ht.Item["Rot"], "Scale": ht.Item["Scale"],
            "Parent": ht.Item["Parent"], "Children": ht.Item["Children"]
        }

    def get_controller_details(self, node, indices_path):
        self._ensure_logic_loaded()
        mxs_path = rt.Array(*(int(i) for i in indices_path))
        data = rt.ohCHA_ControlLogic.getControllerDetails(node, mxs_path)
        if not data: return None
        py_data = {
            "type": data.Item["type"], "is_script": data.Item["is_script"],
            "is_expr": data.Item["is_expr"], "is_constraint": data.Item["is_constraint"]
        }
        if py_data["is_script"]:
            py_data["code"] = data.Item["script"]
        elif py_data["is_expr"]:
            py_data["code"] = data.Item["expression"]
        elif py_data["is_constraint"]:
            t_list = []
            for item in data.Item["targets"]:
                parts = item.split("|")
                if len(parts) >= 2: t_list.append({"name": parts[0], "weight": float(parts[1])})
            py_data["targets"] = t_list
        return py_data

    def assign_controller(self, node, indices_path, type_str):
        self._ensure_logic_loaded()
        mxs_path = rt.Array(*(int(i) for i in indices_path))
        init_code = "0.0" if "Float" in type_str and "Script" in type_str else "[0,0,0]"
        return rt.ohCHA_ControlLogic.assignController(node, mxs_path, type_str, init_code)

    def apply_script_code(self, node, indices_path, code):
        self._ensure_logic_loaded()
        mxs_path = rt.Array(*(int(i) for i in indices_path))
        return rt.ohCHA_ControlLogic.applyScriptText(node, mxs_path, code)

    def add_constraint_target(self, node, indices_path):
        self._ensure_logic_loaded()
        if rt.selection.count != 1: return False
        target = rt.selection[0]
        mxs_path = rt.Array(*(int(i) for i in indices_path))
        return rt.ohCHA_ControlLogic.addConstraintTarget(node, mxs_path, target)

    def remove_constraint_target(self, node, indices_path, index):
        self._ensure_logic_loaded()
        mxs_path = rt.Array(*(int(i) for i in indices_path))
        return rt.ohCHA_ControlLogic.removeConstraintTarget(node, mxs_path, index)

    def set_constraint_weight(self, node, indices_path, index, weight):
        self._ensure_logic_loaded()
        mxs_path = rt.Array(*(int(i) for i in indices_path))
        return rt.ohCHA_ControlLogic.setConstraintWeight(node, mxs_path, index, weight)

    # [5] Placeholders
    def copy_pose(self):
        self._ensure_logic_loaded()
        sel = list(rt.selection);
        if not sel: return
        rt.ohCHA_BoneLogic.copyPose(rt.Array(*sel))

    def paste_pose(self, p, r):
        self._ensure_logic_loaded()
        sel = list(rt.selection);
        if not sel: return
        rt.ohCHA_BoneLogic.pastePose(rt.Array(*sel))

    def mirror_paste_pose(self, ax):
        self._ensure_logic_loaded()
        sel = list(rt.selection);
        if not sel: return
        rt.ohCHA_BoneLogic.pasteMirrorPose(rt.Array(*sel), ax)


rigging_controller_instance = RiggingController()