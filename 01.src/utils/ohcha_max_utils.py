# ohCHA_RigManager/01/src/utils/ohcha_max_utils.py
# Description: [v1.9.2] Added 'world_pos' parsing to get_skin_bone_data for Hybrid Mapping.

import pymxs
from pymxs import runtime as rt
import traceback, textwrap, tempfile, os


class OchaError(Exception): pass


class UndoContext:
    def __init__(self, name="ohCHA Undo"):
        self.name = name

    def __enter__(self):
        if not rt.theHold.Holding(): rt.theHold.Begin()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            rt.theHold.Cancel(); rt.print(f"⚠️ [Undo] Error occurred, operation cancelled: {exc_val}")
        else:
            rt.theHold.Accept(self.name)


def execute_mxs_as_file(mxs_code: str, node=None):
    if node and not rt.isValidNode(node): raise OchaError(f"Invalid Node: {node}")
    temp_file_path = ""
    try:
        node_name = node.name if node else ""
        safe_mxs_code = mxs_code
        full_mxs_code = textwrap.dedent(f"""
        (
            local ohCHA_Logic_TargetNode = getNodeByName "{node_name}"
            local result = undefined
            try ( result = ( {safe_mxs_code} ) ) 
            catch ( format "MXS_ERROR: %\\n" (getCurrentException()); result = undefined )
            result
        )
        """)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ms', encoding='utf-8') as f:
            f.write(full_mxs_code);
            temp_file_path = f.name
        result = rt.fileIn(temp_file_path)
        return result
    except Exception as e:
        rt.print(f"--- PYTHON ERROR ---");
        rt.print(traceback.format_exc());
        raise OchaError(f"Script Error: {e}")
    finally:
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass


def is_valid_mesh(node) -> bool:
    if not rt.isValidNode(node): return False
    if rt.isKindOf(node, rt.GeometryClass): return True
    return False


def get_selected_skin_node():
    if rt.selection.count != 1: raise OchaError("오브젝트를 하나만 선택해주세요.")
    node = rt.selection[0];
    skin_mod = None
    for mod in node.modifiers:
        if rt.isKindOf(mod, rt.Skin): skin_mod = mod; break
    if skin_mod is None: raise OchaError(f"'{node.name}'에 Skin 모디파이어가 없습니다.")
    return node, skin_mod


def get_selected_skin_single_vert_id(skin_mod) -> int | None:
    if skin_mod is None or skin_mod == rt.undefined: return None
    try:
        mxs_array = rt.skinOps.GetSelectedVertices(skin_mod)
        if mxs_array is None or mxs_array == rt.undefined:
            return None
        if mxs_array.count != 1:
            return None
        return int(mxs_array[0])
    except Exception as e:
        rt.print(f"❌ [MaxUtils] get_selected_skin_single_vert_id 오류: {e}");
        return None


def get_selected_skin_vert_indices(skin_mod) -> list[int]:
    if skin_mod is None or skin_mod == rt.undefined: return []
    try:
        mxs_array = rt.skinOps.GetSelectedVertices(skin_mod)
        if mxs_array is None: return []
        return [int(v) for v in mxs_array]
    except Exception as e:
        rt.print(f"❌ [MaxUtils] get_selected_skin_vert_indices 오류: {e}");
        return []


def select_skin_verts(skin_mod, vert_indices: list[int]):
    if skin_mod is None or skin_mod == rt.undefined: return
    try:
        rt.skinOps.selectVertices(skin_mod, rt.Array(*vert_indices))
    except Exception as e:
        rt.print(f"❌ [MaxUtils] select_skin_verts 오류: {e}")


# ⭐️ [v1.9.2] Updated to parse World Position from MS result
def get_skin_bone_data(skin_mod) -> list[dict]:
    if skin_mod is None or skin_mod == rt.undefined: return []
    try:
        owner_node = rt.refs.dependentNodes(skin_mod)[0]
        if not rt.isValidNode(owner_node): return []

        # MS returns: #(name, id, handle, parent_handle, layer_name, posX, posY, posZ)
        mxs_bone_data = rt.ohCHA_DataUtil.getBoneDataWithHierarchy(owner_node)

        bone_list = []
        for row in mxs_bone_data:
            # row is a PyMXS wrapper around MS array, accessible by index
            # Safety check for array length (Backward compatibility)
            world_pos = [0.0, 0.0, 0.0]
            if len(row) >= 8:
                world_pos = [float(row[5]), float(row[6]), float(row[7])]

            bone_list.append({
                "name": row[0],
                "id": row[1],
                "handle": str(row[2]),
                "parent_handle": str(row[3]),
                "layer_name": str(row[4]),
                "world_pos": world_pos # Added for Spatial Mapping
            })
        return bone_list
    except Exception as e:
        rt.print(f"❌ [MaxUtils] get_skin_bone_data 오류: {e}")
        return []