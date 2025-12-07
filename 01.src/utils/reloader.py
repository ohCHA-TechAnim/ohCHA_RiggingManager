# ohCHA_RigManager/01.src/utils/reloader.py
# Description: [변경 없음] 개발용 리로더 유틸리티

import sys
import importlib
from pymxs import runtime as rt


def reload_modules(package_name: str):
    """
    지정된 패키지 이름으로 시작하는 모든 모듈을 재귀적으로 리로드합니다.
    3ds Max, Maya와 같은 DCC 환경에서 개발 시 매우 유용합니다.
    """
    loaded_modules = list(sys.modules.keys())

    for module_name in loaded_modules:
        if module_name.startswith(package_name):
            try:
                module = sys.modules[module_name]
                importlib.reload(module)
                rt.print(f" > Reloaded: {module_name}")
            except Exception as e:
                rt.print(f" > Failed to reload {module_name}: {e}")