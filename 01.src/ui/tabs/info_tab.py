# ohCHA_RigManager/01/src/ui/tabs/info_tab.py
# Description: [v21.46] INFO TAB UPDATE.
#              - UPDATED: Clickable links, Layout adjustment.

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QDesktopServices
from PySide6.QtCore import QUrl

try:
    from utils.paths import get_icon_path
    from utils.translator import translator
    from utils.config import VERSION, CONTACT_EMAIL, LINKEDIN_URL, TUTORIAL_URL
except ImportError:
    def get_icon_path(name):
        return None


    class TempTranslator:
        def get(self, key): return f"<{key}>"


    translator = TempTranslator()
    VERSION = "0.90_Beta"
    CONTACT_EMAIL = "ckekdnlt@naver.com"
    LINKEDIN_URL = "https://www.linkedin.com/in/ohcha"
    TUTORIAL_URL = ""


class InfoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = get_icon_path("ohCHA_RigManager_Logo.png")
        if logo_path:
            pixmap = QPixmap(logo_path).scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        else:
            self.logo_label.setText("ohCHA Rig Manager")
            self.logo_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #DDD;")

        # Version
        self.version_label = QLabel()
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet("color: #AAA; font-size: 14px;")

        # How to Use (Link)
        self.how_to_use_title = QLabel()
        self.how_to_use_title.setObjectName("InfoTitle")
        self.how_to_use_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #007ACC; margin-top: 10px;")

        self.how_to_use_link = QLabel()
        self.how_to_use_link.setOpenExternalLinks(True)
        self.how_to_use_link.setWordWrap(True)
        self.how_to_use_link.setStyleSheet("color: #AAA; font-size: 13px;")

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #444;")

        # Copyright
        self.copyright_label = QLabel()
        self.copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.copyright_label.setStyleSheet("color: #666; font-size: 11px;")

        # Contact
        self.contact_label = QLabel()
        self.contact_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.contact_label.setStyleSheet("color: #888; font-size: 12px;")
        self.contact_label.setOpenExternalLinks(True)

        # Layout Assembly
        main_layout.addStretch(1)
        main_layout.addWidget(self.logo_label)
        main_layout.addWidget(self.version_label)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.how_to_use_title)
        main_layout.addWidget(self.how_to_use_link)
        main_layout.addStretch(2)
        main_layout.addWidget(line)
        main_layout.addWidget(self.contact_label)
        main_layout.addWidget(self.copyright_label)

        self.retranslate_ui()

    def retranslate_ui(self):
        # Version
        self.version_label.setText(f"Version {VERSION}")

        # Tutorial
        self.how_to_use_title.setText(translator.get("info_how_to_use_title"))
        link_text = translator.get("info_how_to_use_content")
        self.how_to_use_link.setText(
            f'<a href="{TUTORIAL_URL}" style="color:#4DA6FF; text-decoration:none;">▶ {link_text}</a>')

        # Copyright
        self.copyright_label.setText(translator.get("info_copyright"))

        # Contact (Email + LinkedIn)
        contact_title = translator.get("info_contact")
        self.contact_label.setText(
            f"{contact_title}: {CONTACT_EMAIL}<br>"
            f'<a href="{LINKEDIN_URL}" style="color:#AAA; text-decoration:none;">LinkedIn: ohcha</a>'
        )