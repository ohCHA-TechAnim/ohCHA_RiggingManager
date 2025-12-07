# ohCHA_RigManager/01/src/ui/ohcha_ui_base.py
from pymxs import runtime as rt
import sys
from PySide6.QtWidgets import QApplication, QDialog, QWidget
from PySide6.QtCore import Qt
import importlib

try:
    from ui import ohcha_ui_styles

    importlib.reload(ohcha_ui_styles)
    from ui.ohcha_ui_styles import get_current_theme_style, set_current_theme

    rt.print("✅ [PySide] 'ohcha_ui_styles' 모듈 강제 리로드 성공.")
except ImportError as e:
    rt.print(f"❌ [PySide] 테마 관리자('ohcha_ui_styles') 임포트 실패: {e}")
    raise


def get_max_main_window():
    try:
        return QWidget.find(rt.windows.getMAXHWND())
    except Exception:
        return None


class OchaBaseWindow(QDialog):
    # ⭐️ [FIX] init -> __init__ (매우 중요)
    def __init__(self, parent=None):
        if parent is None:
            parent = get_max_main_window()
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.Tool)
        self.setObjectName("ohCHA_Base_Window")

        # [UI FIX] Force dark theme as default for consistent look
        set_current_theme("dark")
        self.apply_theme()

    def apply_theme(self):
        importlib.reload(ohcha_ui_styles)
        style_sheet = ohcha_ui_styles.get_current_theme_style()
        self.setStyleSheet(style_sheet)

    def closeEvent(self, event):
        self.hide()
        event.ignore()


def show_tool_instance(window_class):
    if not hasattr(rt, "ohCHA_Tool_Instances"):
        rt.ohCHA_Tool_Instances = {}

    instance_key = window_class.__name__

    try:
        if instance_key in rt.ohCHA_Tool_Instances and rt.ohCHA_Tool_Instances[instance_key]:
            try:
                # 기존 인스턴스가 유효한지(삭제되지 않았는지) 확인
                if not rt.ohCHA_Tool_Instances[instance_key].isVisible():
                    rt.ohCHA_Tool_Instances[instance_key].show()

                rt.print(f"💡 [PySide] 기존 '{instance_key}' 인스턴스를 포커싱합니다.")
                existing_instance = rt.ohCHA_Tool_Instances[instance_key]
                existing_instance.apply_theme()
                existing_instance.show()
                existing_instance.raise_()
                existing_instance.activateWindow()
            except RuntimeError:
                # C++ 객체가 삭제된 경우 새로 생성
                rt.print(f"⚠️ [PySide] 기존 인스턴스가 만료되어 새로 생성합니다.")
                app = QApplication.instance()
                if not app: app = QApplication(sys.argv)
                new_instance = window_class()
                rt.ohCHA_Tool_Instances[instance_key] = new_instance
                new_instance.show()
        else:
            rt.print(f"🚀 [PySide] 새 '{instance_key}' 인스턴스를 생성하고 'rt'에 등록합니다.")
            app = QApplication.instance()
            if not app:
                app = QApplication(sys.argv)
            new_instance = window_class()
            rt.ohCHA_Tool_Instances[instance_key] = new_instance
            new_instance.show()

    except Exception as e:
        rt.print(f"❌ [PySide] 툴 런처 실행 중 치명적 오류: {e}")
        import traceback
        rt.print(traceback.format_exc())