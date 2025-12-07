# ohCHA_RigManager/01.src/controllers/skinning_logic.py
# Description: [v20.96] Support .mse/.ms/.txt Loading.

import os
from pymxs import runtime as rt

try:
    from utils.paths import find_script_path
except ImportError:
    find_script_path = lambda x: None

def _ensure_script_loaded():
    """
    MaxScript 로직 파일을 찾아 로드합니다.
    우선순위: .mse > .ms > .txt
    """
    path = find_script_path("ohcha_skin_logic")
    if path:
        try:
            rt.fileIn(path)
            return True
        except Exception as e:
            rt.print(f"❌ [SkinLogic] MS Load Error: {e}")
            return False
    else:
        rt.print(f"❌ [SkinLogic] Script file missing: ohcha_skin_logic")
        return False

def hide_selection(hide_type: str, hide_unselected: bool):
    if not _ensure_script_loaded(): return
    try:
        res = rt.ohCHA_SkinLogic.hideSelection(hide_type, hide_unselected)
        if res: rt.print("✅ [SkinHide] 완료.")
    except Exception as e:
        rt.print(f"❌ [SkinHide] Execution Error: {e}")

def unhide_all():
    if not _ensure_script_loaded(): return
    try:
        res = rt.ohCHA_SkinLogic.unhideAll()
        if res: rt.print("✅ [SkinHide] Unhide 완료.")
    except Exception as e:
        rt.print(f"❌ [SkinHide] Execution Error: {e}")