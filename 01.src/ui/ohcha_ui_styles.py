# ohCHA_RigManager/01/src/ui/ohcha_ui_styles.py
from pymxs import runtime as rt

LIGHT_STYLE = """
/* This theme is incomplete and needs design refinement. */
QDialog#ohCHA_Base_Window, QWidget { background-color: #F0F0F0; }
QLabel { color: #333333; }
/* ... other partial styles ... */
"""

DARK_STYLE = """
QWidget, QDialog#ohCHA_Base_Window {
    background-color: #3c3c3c;
    color: #D0D0D0;
    font-size: 14px;
}
QLabel {
    background-color: transparent;
}
/* Sidebar */
QWidget#Sidebar {
    background-color: #2b2b2b;
    border-right: 1px solid #4A4C5F;
}
QLabel#SidebarLogo {
    color: #FFFFFF;
    font-weight: bold;
    font-size: 20px;
    padding: 5px 0px 5px 15px;
}
QPushButton#SidebarButton {
    background-color: transparent;
    color: #D0D0D0;
    border: none;
    padding: 15px;
    border-radius: 4px;
    font-weight: bold;
    text-align: left;
    font-size: 16px;
    margin: 2px 5px;
}
QPushButton#SidebarButton[collapsed="true"] {
    text-align: center;
    padding: 15px 0px;
}
QPushButton#SidebarButton:hover {
    background-color: #4a4a4a;
}
QPushButton#SidebarButton:checked {
    background-color: #007ACC;
    color: #FFFFFF;
}
QPushButton#HamburgerButton {
    background-color: transparent;
    border: none;
    padding: 8px;
    color: #D0D0D0;
    font-size: 24px;
}
QPushButton#HamburgerButton:hover { background-color: #4a4a4a; }
/* Language Menu */
QPushButton#MainLangButtonExpanded {
    background-color: #3c3c3c; color: #D0D0D0; border: 1px solid #555;
    padding: 8px 10px; border-radius: 4px; text-align: left;
}
QPushButton#MainLangButton {
    background-color: #3c3c3c;
    padding: 0px;
    border: none;
}
QPushButton#LangChoiceButton {
    background-color: #4a4a4a; color: #FFFFFF; border: none; border-radius: 4px;
    padding: 8px 10px; text-align: left;
}
/* General Widgets */
QPushButton {
    background-color: #007ACC; color: #FFFFFF; border: none;
    padding: 8px 12px; border-radius: 4px; font-weight: bold;
    min-height: 18px; /* Ensure button height is sufficient */
}
QPushButton:hover { background-color: #008ae6; }
QPushButton:pressed { background-color: #005c99; }
QPushButton:disabled { background-color: #555; color: #888; }

QGroupBox {
    background-color: #333333;
    border: 1px solid #555555;
    border-radius: 4px;
    margin-top: 1em; /* Provide space for the title */
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center; /* Centered title */
    padding: 5px 10px; /* Vertical and horizontal padding */
    background-color: #4a4a4a;
    border-radius: 4px;
}
QListWidget, QTableWidget, QTreeWidget { /* QTreeWidget 추가 */
    background-color: #2b2b2b;
    border: 1px solid #555;
    border-radius: 4px;
}
QTableWidget::item { 
    padding: 8px; /* Increased padding for table cells */
    border-bottom: 1px solid #3c3c3c;
}
QTableWidget::item:selected, QListWidget::item:selected, QTreeWidget::item:selected { background-color: #007ACC; }
QHeaderView::section {
    background-color: #4a4a4a;
    color: #D0D0D0;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #555;
    font-weight: bold;
}
QSplitter::handle {
    background-color: #4a4a4a;
    height: 4px;
}
QSpinBox, QLineEdit { /* QLineEdit 추가 */
    background-color: #2b2b2b;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 4px;
}
QComboBox {
    background-color: #2b2b2b;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 4px;
}
QComboBox::drop-down { border: none; }

/* ⭐️ [UX 개선] 정렬 순서 버튼을 위한 커스텀 스타일 */
QPushButton#BoneSortOrderButton {
    background-color: #5A5A5A;
    font-weight: bold;
    font-size: 16px;
    min-width: 30px;
    max-width: 30px;
    padding: 4px;
}
QPushButton#BoneSortOrderButton:checked {
    background-color: #007ACC;
    color: white;
}
QPushButton#BoneSortOrderButton:hover {
    background-color: #6E6E6E;
}
"""

THEMES = {"light": LIGHT_STYLE, "dark": DARK_STYLE}
THEME_STORAGE_KEY = "ohCHA_Current_Theme"

def set_current_theme(theme_name: str):
    if theme_name in THEMES:
        setattr(rt, THEME_STORAGE_KEY, theme_name)
    else:
        rt.print(f"⚠️ [Theme] '{theme_name}'은(는) 유효하지 않은 테마입니다.")

def get_current_theme_style() -> str:
    current_theme_name = getattr(rt, THEME_STORAGE_KEY, "dark")
    return THEMES.get(current_theme_name, DARK_STYLE)