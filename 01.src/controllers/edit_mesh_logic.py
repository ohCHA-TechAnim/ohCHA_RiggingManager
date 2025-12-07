# ohCHA_RigManager/01/src/controllers/edit_mesh_logic.py
# Description: [Refactored] Cleaned up imports, removed mock classes, and added type hinting.
#              Ensures strict dependency on 'utils.ohcha_max_utils'.

import textwrap
from pymxs import runtime as rt

# ⭐️ Strict Import: 실제 유틸리티가 없으면 툴이 동작하지 않도록 명확히 에러를 띄웁니다.
try:
    from utils.ohcha_max_utils import (
        OchaError,
        execute_mxs_as_file,
        is_valid_mesh
    )
except ImportError as e:
    rt.print(f"❌ [edit_mesh_logic] Critical Import Error: {e}")
    raise


def check_identity_scale(node) -> dict:
    """
    노드의 스케일이 (1,1,1)인지 검사합니다.
    """
    scale_val = node.scale
    tolerance = 1e-5
    # Point3 비교 시 각 성분별 오차 체크
    has_issue = (
        abs(scale_val.x - 1.0) > tolerance or
        abs(scale_val.y - 1.0) > tolerance or
        abs(scale_val.z - 1.0) > tolerance
    )
    return {"has_issue": has_issue, "value": scale_val}


def check_existing_skin(node) -> dict:
    """
    노드에 이미 Skin 모디파이어가 존재하는지 검사합니다.
    """
    for mod in node.modifiers:
        if rt.isKindOf(mod, rt.Skin):
            return {"has_issue": True, "value": mod.name}
    return {"has_issue": False, "value": None}


def check_pivot_not_at_origin(node) -> dict:
    """
    피벗이 월드 원점(0,0,0)에 있는지 검사합니다.
    """
    pivot_pos = node.pivot
    tolerance = 1e-5
    dist = rt.distance(pivot_pos, rt.Point3(0, 0, 0))
    has_issue = dist > tolerance
    return {"has_issue": has_issue, "value": pivot_pos}


def get_scene_meshes() -> list[dict]:
    """
    씬 내의 유효한 지오메트리(숨김/동결 제외)를 수집합니다.
    """
    return [
        {"name": obj.name, "node": obj}
        for obj in rt.objects
        if is_valid_mesh(obj) and not obj.isHidden and not obj.isFrozen
    ]


def run_all_checks(node) -> dict:
    """
    특정 노드에 대해 모든 검사 로직을 수행합니다.
    """
    if not is_valid_mesh(node):
        return {}

    results = {
        "non_uniform_scale": check_identity_scale(node),
        "existing_skin": check_existing_skin(node),
        "pivot_not_at_origin": check_pivot_not_at_origin(node),
    }
    return results


# ----------------------------------------------------------------------------
# Fix Actions (Commands)
# ----------------------------------------------------------------------------

def apply_reset_xform(node) -> bool:
    """
    Reset XForm을 적용하고 스택을 합칩니다.
    """
    mxs_code = (
        "undo \"Apply Reset XForm\" on ("
        "ResetXForm ohCHA_Logic_TargetNode; "
        "maxOps.CollapseNodeTo ohCHA_Logic_TargetNode 1 true"
        ")"
    )
    result = execute_mxs_as_file(mxs_code, node=node)
    return result is not None


def lock_all_transforms(node) -> bool:
    """
    모든 트랜스폼(이동/회전/크기)을 잠급니다.
    """
    mxs_code = "undo \"Lock All Transforms\" on (setTransformLockFlags ohCHA_Logic_TargetNode #all)"
    result = execute_mxs_as_file(mxs_code, node=node)
    return result is not None


def delete_skin_modifier(node) -> bool:
    """
    모든 Skin 모디파이어를 삭제합니다.
    """
    mxs_code = (
        "undo \"Delete Skin Modifier\" on ("
        "for i = ohCHA_Logic_TargetNode.modifiers.count to 1 by -1 do ("
        "if isKindOf ohCHA_Logic_TargetNode.modifiers[i] Skin do ("
        "deleteModifier ohCHA_Logic_TargetNode i"
        ")))"
    )
    result = execute_mxs_as_file(mxs_code, node=node)
    return result is not None


def move_pivot_to_origin(node) -> bool:
    """
    피벗을 (0,0,0)으로 이동시킵니다.
    """
    mxs_code = "undo \"Move Pivot to Origin\" on (ohCHA_Logic_TargetNode.pivot = [0,0,0])"
    result = execute_mxs_as_file(mxs_code, node=node)
    return result is not None


def enable_all_inheritance(node) -> bool:
    """
    상속 플래그를 모두 켭니다 (R/S/T).
    """
    mxs_code = "undo \"Enable All Inheritance\" on (setInheritanceFlags ohCHA_Logic_TargetNode #all)"
    result = execute_mxs_as_file(mxs_code, node=node)
    return result is not None


def finalize_add_skin(node, bone_limit: int = 4, use_dq: bool = False) -> bool:
    """
    최종 단계: Skin 모디파이어를 추가하고 설정을 적용합니다.
    실패 시 OchaError를 발생시켜 상위 컨트롤러에서 잡도록 합니다.
    """
    mxs_bool = "on" if use_dq else "off"

    # textwrap을 사용하여 MaxScript 코드의 들여쓰기와 가독성을 유지
    mxs_code_configure = textwrap.dedent(f"""
    undo "Add and Configure Skin" on
    (
        try
        (
            addModifier ohCHA_Logic_TargetNode (Skin())

            if (ohCHA_Logic_TargetNode.modifiers[#Skin] != undefined) then
            (
                ohCHA_Logic_TargetNode.modifiers[#Skin].bone_Limit = {bone_limit}
                ohCHA_Logic_TargetNode.modifiers[#Skin].enableDQ = {mxs_bool}

                -- UI 갱신을 위해 선택 및 패널 활성화
                select ohCHA_Logic_TargetNode
                modPanel.setCurrentObject ohCHA_Logic_TargetNode.modifiers[#Skin]

                true 
            )
            else
            (
                false 
            )
        )
        catch
        (
            false 
        )
    )
    """)

    result = execute_mxs_as_file(mxs_code_configure, node=node)

    if result is not True:
        raise OchaError(f"Skin 모디파이어 추가/설정에 실패했습니다.\n(Node: {node.name})")

    return True