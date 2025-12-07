# ohCHA_RigManager/01/src/utils/paths.py
# Description: [v20.96] Added 'find_script_path' for multi-format support.

import os
from pymxs import runtime as rt


def get_project_root() -> str | None:
    """
    이 스크립트(paths.py)의 위치를 기준으로 프로젝트 루트 폴더
    (ohCHA_RigManager)의 절대 경로를 찾습니다.
    """
    try:
        try:
            current_file_path = os.path.abspath(__file__)
        except NameError:
            current_file_path = rt.getThisScriptFilename()

        if not current_file_path:
            return None

        utils_dir = os.path.dirname(current_file_path)
        src_dir = os.path.dirname(utils_dir)
        root_dir = os.path.dirname(src_dir)

        if os.path.isdir(src_dir):
            return root_dir
        else:
            rt.print(f"❌ [paths.py] 예상 경로에 '01.src' 폴더가 없습니다: {src_dir}")
            return None

    except Exception as e:
        rt.print(f"❌ [paths.py] get_project_root() 오류: {e}")
        return None


def get_icon_path(n: str) -> str | None:
    """ '03.assets/icons' 폴더의 아이콘 경로를 반환합니다. """
    root = get_project_root()
    if root:
        p = os.path.normpath(os.path.join(root, "03.assets", "icons", n))
        if os.path.exists(p):
            return p
    return None


def find_script_path(script_name_no_ext: str) -> str | None:
    """
    '01.src/scripts' 폴더에서 해당 이름의 스크립트를 찾습니다.
    우선순위: .mse (Encrypted) > .ms (Script) > .txt (Text)
    """
    root = get_project_root()
    if not root: return None

    scripts_dir = os.path.join(root, "01.src", "scripts")

    # Priority Order
    extensions = [".mse", ".ms", ".txt"]

    for ext in extensions:
        full_path = os.path.join(scripts_dir, f"{script_name_no_ext}{ext}")
        if os.path.exists(full_path):
            return full_path

    return None