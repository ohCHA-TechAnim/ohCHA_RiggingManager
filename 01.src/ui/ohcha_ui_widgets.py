# ohCHA_RigManager/01/src/ui/ohcha_ui_widgets.py
# Description: [v21.49] WIDGETS FINAL.
#              - FORMAT: Fully expanded (no semicolons).
#              - INTEGRITY: 100% Full Code.
#              - TRANSLATION: OchaControllerInspector updated.

from pymxs import runtime as rt
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import functools
import collections

rt.print("✅ [Import Check] Loading ui.ohcha_ui_widgets...")

try:
    from utils.paths import get_icon_path
except ImportError:
    get_icon_path = lambda n: None

try:
    from utils.translator import translator
except ImportError:
    class T:
        get = lambda s, k: k


    translator = T()


# =================================================================
# 1. Basic Components
# =================================================================

class OchaFloatDial(QWidget):
    floatValueChanged = Signal(float)

    def __init__(self, title="Dial", min_val=0.0, max_val=100.0, default_val=1.0, precision=2, parent=None):
        super().__init__(parent)
        self.precision = precision
        self.multiplier = 10.0 ** precision

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dial = QDial()
        self.dial.setRange(int(min_val * self.multiplier), int(max_val * self.multiplier))
        self.dial.setNotchesVisible(True)
        self.dial.setWrapping(False)

        self.value_label = QLabel()
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        l = QVBoxLayout(self)
        l.setContentsMargins(0, 5, 0, 5)
        l.addWidget(self.title_label)
        l.addWidget(self.dial)
        l.addWidget(self.value_label)

        self.dial.valueChanged.connect(self._on_chg)
        self.setValue(default_val)

    def _on_chg(self, v):
        f = v / self.multiplier
        self.value_label.setText(f"{f:.{self.precision}f}")
        self.floatValueChanged.emit(f)

    def setValue(self, f):
        self.dial.setValue(int(f * self.multiplier))
        self.value_label.setText(f"{f:.{self.precision}f}")

    def getValue(self):
        return self.dial.value() / self.multiplier


class OchaAnimatedToggle(QWidget):
    toggled = Signal(bool)

    def __init__(self, width=40, height=20, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._is_on = False
        self._margin = 3.0
        self._diameter = float(height) - (2.0 * self._margin)
        self._radius = self._diameter / 2.0

        self._x_off = self._margin
        self._x_on = float(width) - self._margin - self._diameter

        self._c_off = QColor("#555555")
        self._c_on = QColor("#007ACC")
        self._c_handle = QColor("#DDDDDD")

        self._c_pos = self._x_off
        self._bg_col = self._c_off

        self.anim_pos = QPropertyAnimation(self, b"circle_position", self)
        self.anim_pos.setDuration(180)
        self.anim_pos.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.anim_col = QPropertyAnimation(self, b"background_color", self)
        self.anim_col.setDuration(180)

    @Property(float)
    def circle_position(self):
        return self._c_pos

    @circle_position.setter
    def circle_position(self, v):
        self._c_pos = v
        self.update()

    @Property(QColor)
    def background_color(self):
        return self._bg_col

    @background_color.setter
    def background_color(self, v):
        self._bg_col = v
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._bg_col))
        p.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)
        p.setBrush(QBrush(self._c_handle))
        p.drawEllipse(QRectF(self._c_pos, self._margin, self._diameter, self._diameter))
        p.end()

    def mousePressEvent(self, e):
        if self.isEnabled():
            self.setChecked(not self._is_on, animate=True)

    def isChecked(self):
        return self._is_on

    def setChecked(self, on, animate=False):
        if self._is_on == on: return
        self._is_on = on
        end_p = self._x_on if on else self._x_off
        end_c = self._c_on if on else self._c_off

        if animate:
            self.anim_pos.setEndValue(end_p)
            self.anim_col.setEndValue(end_c)
            self.anim_pos.start()
            self.anim_col.start()
        else:
            self.circle_position = end_p
            self.background_color = end_c
        self.toggled.emit(self._is_on)


class OchaCircleToggle(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(16, 16)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText("")
        self.setStyleSheet("QPushButton { border: none; background-color: transparent; }")

    def sizeHint(self):
        return QSize(16, 16)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.isEnabled():
            color = QColor("#666666")
        elif self.isChecked():
            color = QColor("#2ECC71")
        else:
            color = QColor("#E74C3C")
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        center_x = self.width() / 2.0
        center_y = (self.height() / 2.0) - 7.0
        center = QPointF(center_x, center_y)
        painter.drawEllipse(center, 6.0, 6.0)


class OchaLanguageMenu(QWidget):
    languageChanged = Signal(str)
    LANG_MAP = {
        "en": ("icon_Flag_England.png", "English"),
        "kr": ("icon_Flag_Korea.png", "한국어"),
        "jp": ("icon_Flag_Japan.png", "日本語"),
        "cn": ("icon_Flag_China.png", "汉语")
    }

    def __init__(self, p=None):
        super().__init__(p)
        self._pop_open = False
        self._exp = True
        self.cur = "en"

        l = QVBoxLayout(self)
        l.setContentsMargins(0, 0, 0, 0)

        self.btn = QPushButton()
        self.btn.setCheckable(True)
        self._upd_btn()

        l.addWidget(self.btn)

        self.pop = self._mk_pop()
        self.btn.clicked.connect(self._tog)
        self.pop.closing.connect(self._foc_out)

    def _mk_btn(self, c):
        p, t = self.LANG_MAP.get(c, (None, "??"))
        b = QPushButton(t if self._exp else "")
        b.setObjectName("LangChoiceButton")
        b.setMinimumHeight(40)

        i = get_icon_path(p)
        if i:
            b.setIcon(QIcon(i))
            b.setIconSize(QSize(22, 22))

        b.clicked.connect(lambda checked=False, lang=c: self._sel(lang))
        return b

    def _mk_pop(self):
        if hasattr(self, "pop") and self.pop:
            self.pop.close()
            self.pop.deleteLater()

        p = LanguagePopup(self)
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(5)

        for c in ["en", "kr", "jp", "cn"]:
            l.addWidget(self._mk_btn(c))

        p.closing.connect(self._foc_out)
        return p

    def _tog(self):
        if self.pop.isVisible():
            self.pop.hide()
            self._pop_open = False
            self.btn.setChecked(False)
            return

        self._pop_open = True
        self.btn.setChecked(True)
        w = 150 if self._exp else 42
        self.pop.setMinimumWidth(w)

        pos = self.btn.mapToGlobal(QPoint(0, 0))
        x = pos.x() - (w / 2) + (self.btn.width() / 2)
        y = pos.y() - (40 * 4 + 15) - 5

        self.pop.move(int(x), int(y))
        self.pop.show()
        self.pop.activateWindow()

    def _sel(self, c):
        self.cur = c
        self._upd_btn()
        self.pop.hide()
        self._pop_open = False
        self.btn.setChecked(False)
        self.languageChanged.emit(c)

    def _foc_out(self):
        self.pop.hide()
        self._pop_open = False
        self.btn.setChecked(False)

    def _upd_btn(self):
        p, n = self.LANG_MAP[self.cur]
        i = get_icon_path(p)

        if self._exp:
            self.btn.setText(f" {n}")
            self.btn.setObjectName("MainLangButtonExpanded")
            self.btn.setFixedSize(150, 40)
        else:
            self.btn.setText("")
            self.btn.setObjectName("MainLangButton")
            self.btn.setFixedSize(32, 32)

        if i:
            self.btn.setIcon(QIcon(i))
            self.btn.setIconSize(QSize(22, 22))

        self.btn.style().unpolish(self.btn)
        self.btn.style().polish(self.btn)

    def set_expanded_mode(self, exp):
        self._exp = exp
        self._upd_btn()
        self.pop = self._mk_pop()


class LanguagePopup(QDialog):
    closing = Signal()

    def __init__(self, p=None):
        super().__init__(p)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("LanguagePopup")
        self.setStyleSheet("QDialog#LanguagePopup{background-color:transparent;}")

    def event(self, e):
        if e.type() == QEvent.Type.WindowDeactivate:
            self.closing.emit()
        return super().event(e)


class OchaCollapsibleGroup(QWidget):
    def __init__(self, title, expanded=True, parent=None):
        super().__init__(parent)
        self._exp = expanded

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn = QPushButton(title)
        self.btn.setObjectName("CollapsibleHeaderButton")
        self.btn.setCheckable(True)
        self.btn.setChecked(expanded)

        self.cont = QWidget()
        self.cont.setObjectName("CollapsibleContentArea")
        self.cont_layout = QVBoxLayout(self.cont)
        self.cont_layout.setContentsMargins(10, 10, 10, 10)

        self.anim = QPropertyAnimation(self.cont, b"maximumHeight")
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.anim.finished.connect(self._on_anim_finished)

        layout.addWidget(self.btn)
        layout.addWidget(self.cont)
        self.btn.clicked.connect(self._tog)
        self._upd_ico()

        if expanded:
            self.cont.setVisible(True)
            self.cont.setMaximumHeight(16777215)
        else:
            self.cont.setVisible(False)
            self.cont.setMaximumHeight(0)

    def _tog(self):
        self._exp = self.btn.isChecked()
        if self._exp:
            self.cont.setVisible(True)

        self.cont.adjustSize()
        h = self.cont.layout().sizeHint().height() if self.cont.layout() else self.cont.sizeHint().height()

        self.anim.setStartValue(0 if self._exp else h)
        self.anim.setEndValue(h if self._exp else 0)
        self.anim.start()
        self._upd_ico()

    def _on_anim_finished(self):
        if not self._exp:
            self.cont.setVisible(False)
        else:
            self.cont.setMaximumHeight(16777215)

    def _upd_ico(self):
        arr = "▼" if self._exp else "►"
        txt = self.btn.text().strip("►▼ ")
        self.btn.setText(f"{arr} {txt}")

    def setHeaderText(self, t):
        arr = "▼" if self._exp else "►"
        self.btn.setText(f"{arr} {t}")

    def setContentLayout(self, l: QLayout):
        if self.cont.layout():
            QWidget().setLayout(self.cont.layout())
        self.cont.setLayout(l)
        l.setContentsMargins(10, 10, 10, 10)


class OchaStyledButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedHeight(26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A;
                color: #AAAAAA;
                border: 1px solid #555;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #444;
                color: #DDDDDD;
                border: 1px solid #777;
            }
            QPushButton:checked {
                background-color: #007ACC;
                color: #FFFFFF;
                border: 1px solid #0099FF;
            }
            QPushButton:pressed {
                background-color: #005C99;
            }
        """)


# =================================================================
# 2. Skinning Components
# =================================================================

class BaseTreeItemWidget(QWidget):
    visibilityToggled = Signal(bool)

    def __init__(self, name="Item", enabled=True, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 2, 5, 2)
        self.layout.setSpacing(4)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.btn_vis = OchaCircleToggle()
        self.btn_vis.setChecked(enabled)
        self.btn_vis.toggled.connect(self.visibilityToggled.emit)

        self.label = QLabel(name)
        self.layout.addWidget(self.btn_vis)
        self.layout.addWidget(self.label)
        self.layout.addStretch(1)


class LayerTreeItemWidget(BaseTreeItemWidget):
    blendModeChanged = Signal(str)
    addMaskClicked = Signal()
    removeMaskClicked = Signal()

    def __init__(self, name="Layer", enabled=True, blend_mode="Overwrite", has_mask=False, parent=None):
        super().__init__(name, enabled, parent)
        self.combo_blend = QComboBox()
        self.combo_blend.addItems(["Overwrite", "Normal", "Add", "Subtract"])
        self.combo_blend.setCurrentText(blend_mode)

        self.btn_add_mask = QPushButton()
        self.btn_rem_mask = QPushButton()

        btn_style = "font-size: 10px; padding: 0px; font-weight: bold;"
        self.btn_add_mask.setStyleSheet(btn_style)
        self.btn_rem_mask.setStyleSheet(btn_style)
        self.btn_add_mask.setFixedSize(45, 20)
        self.btn_rem_mask.setFixedSize(45, 20)

        self.layout.addWidget(self.combo_blend)
        self.layout.addWidget(self.btn_add_mask)
        self.layout.addWidget(self.btn_rem_mask)

        self.combo_blend.currentTextChanged.connect(self.blendModeChanged.emit)
        self.btn_add_mask.clicked.connect(lambda c=False: self.addMaskClicked.emit())
        self.btn_rem_mask.clicked.connect(lambda c=False: self.removeMaskClicked.emit())

        self.retranslate_ui()
        self.set_mask_visibility(has_mask)

    def set_mask_visibility(self, has_mask):
        self.btn_add_mask.setVisible(not has_mask)
        self.btn_rem_mask.setVisible(has_mask)

    def retranslate_ui(self):
        self.btn_add_mask.setText(translator.get("layer_btn_mask_add"))
        self.btn_rem_mask.setText(translator.get("layer_btn_mask_rem"))
        self.btn_vis.setToolTip(translator.get("tip_toggle_layer"))


class MaskTreeItemWidget(BaseTreeItemWidget):
    addToMaskClicked = Signal()
    removeFromMaskClicked = Signal()
    selectMaskClicked = Signal()

    def __init__(self, name="└─ Mask", enabled=True, parent=None):
        super().__init__(name, enabled, parent)
        self.label.setStyleSheet("color: #BBB; font-style: italic;")
        self.btn_vis.setVisible(False)

        self.btn_add_mask = QPushButton()
        self.btn_rem_mask = QPushButton()
        self.btn_sel_mask = QPushButton()

        btn_style = "font-size: 10px; padding: 0px; font-weight: bold;"
        for b in [self.btn_add_mask, self.btn_rem_mask, self.btn_sel_mask]:
            b.setStyleSheet(btn_style)
            b.setFixedSize(35, 20)

        self.layout.addWidget(self.btn_add_mask)
        self.layout.addWidget(self.btn_rem_mask)
        self.layout.addWidget(self.btn_sel_mask)

        self.btn_add_mask.clicked.connect(lambda c=False: self.addToMaskClicked.emit())
        self.btn_rem_mask.clicked.connect(lambda c=False: self.removeFromMaskClicked.emit())
        self.btn_sel_mask.clicked.connect(lambda c=False: self.selectMaskClicked.emit())

        self.retranslate_ui()

    def retranslate_ui(self):
        self.btn_add_mask.setText(translator.get("mask_btn_add"))
        self.btn_rem_mask.setText(translator.get("mask_btn_sub"))
        self.btn_sel_mask.setText(translator.get("mask_btn_sel"))
        self.btn_vis.setToolTip(translator.get("tip_toggle_mask"))


class OchaWeightToolWidget(QWidget):
    selectionChanged = Signal(str)
    presetClicked = Signal(float)
    mathClicked = Signal(str, float)
    clipboardClicked = Signal(str)
    smoothClicked = Signal()
    healClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        style = """
            QPushButton { background-color: #444; color: #EEE; border-radius: 3px; font-size: 10px; font-weight: bold; min-height: 22px; padding: 0px; }
            QPushButton:hover { background-color: #555; }
            QPushButton:pressed { background-color: #333; }
            QDoubleSpinBox { border: 1px solid #555; border-radius: 3px; font-size: 10px; padding: 0px; }
        """
        self.setStyleSheet(style)

        row1 = QHBoxLayout()
        row1.setSpacing(1)
        self.btn_grow = QPushButton()
        self.btn_shrink = QPushButton()
        self.btn_loop = QPushButton()
        self.btn_ring = QPushButton()

        for b in [self.btn_grow, self.btn_shrink, self.btn_loop, self.btn_ring]:
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            row1.addWidget(b)
        main_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(1)
        self.btn_copy = QPushButton()
        self.btn_paste = QPushButton()
        self.btn_smooth = QPushButton()
        self.btn_heal = QPushButton()

        self.btn_copy.setStyleSheet("background-color: #2980B9;")
        self.btn_paste.setStyleSheet("background-color: #2980B9;")
        self.btn_smooth.setStyleSheet("background-color: #8E44AD;")
        self.btn_heal.setStyleSheet("background-color: #D35400;")

        for b in [self.btn_copy, self.btn_paste, self.btn_smooth, self.btn_heal]:
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            row2.addWidget(b)
        main_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(1)
        presets = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
        for v in presets:
            lbl = "0" if v == 0.0 else ("1" if v == 1.0 else str(v).replace("0.", "."))
            b = QPushButton(lbl)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.setMinimumWidth(18)
            b.clicked.connect(lambda c=False, val=v: self.presetClicked.emit(val))
            b.setToolTip(translator.get("tip_val_preset"))
            row3.addWidget(b)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        row3.addWidget(line)

        self.btn_sub = QPushButton("-")
        self.btn_add = QPushButton("+")
        self.btn_sub.setStyleSheet("background-color: #C0392B;")
        self.btn_add.setStyleSheet("background-color: #27AE60;")
        self.btn_sub.setFixedWidth(20)
        self.btn_add.setFixedWidth(20)

        self.spin_step = QDoubleSpinBox()
        self.spin_step.setRange(0.001, 1.0)
        self.spin_step.setSingleStep(0.01)
        self.spin_step.setDecimals(3)
        self.spin_step.setValue(0.01)
        self.spin_step.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_step.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_step.setFixedWidth(35)
        self.spin_step.setFixedHeight(22)

        row3.addWidget(self.btn_sub)
        row3.addWidget(self.spin_step)
        row3.addWidget(self.btn_add)
        main_layout.addLayout(row3)

        self.btn_grow.clicked.connect(lambda c=False: self.selectionChanged.emit("grow"))
        self.btn_shrink.clicked.connect(lambda c=False: self.selectionChanged.emit("shrink"))
        self.btn_loop.clicked.connect(lambda c=False: self.selectionChanged.emit("loop"))
        self.btn_ring.clicked.connect(lambda c=False: self.selectionChanged.emit("ring"))
        self.btn_copy.clicked.connect(lambda c=False: self.clipboardClicked.emit("copy"))
        self.btn_paste.clicked.connect(lambda c=False: self.clipboardClicked.emit("paste"))
        self.btn_smooth.clicked.connect(lambda c=False: self.smoothClicked.emit())
        self.btn_heal.clicked.connect(lambda c=False: self.healClicked.emit())
        self.btn_sub.clicked.connect(lambda c=False: self.mathClicked.emit("subtract", self.spin_step.value()))
        self.btn_add.clicked.connect(lambda c=False: self.mathClicked.emit("add", self.spin_step.value()))

        self.retranslate_ui()

    def retranslate_ui(self):
        self.btn_grow.setText(translator.get("btn_grow"))
        self.btn_grow.setToolTip(translator.get("tip_grow"))
        self.btn_shrink.setText(translator.get("btn_shrink"))
        self.btn_shrink.setToolTip(translator.get("tip_shrink"))
        self.btn_loop.setText(translator.get("btn_loop"))
        self.btn_loop.setToolTip(translator.get("tip_loop"))
        self.btn_ring.setText(translator.get("btn_ring"))
        self.btn_ring.setToolTip(translator.get("tip_ring"))
        self.btn_copy.setText(translator.get("btn_copy"))
        self.btn_copy.setToolTip(translator.get("tip_copy"))
        self.btn_paste.setText(translator.get("btn_paste"))
        self.btn_paste.setToolTip(translator.get("tip_paste"))
        self.btn_smooth.setText(translator.get("btn_smooth"))
        self.btn_smooth.setToolTip(translator.get("tip_smooth"))
        self.btn_heal.setText(translator.get("btn_heal"))
        self.btn_heal.setToolTip(translator.get("tip_heal"))
        self.btn_add.setToolTip(translator.get("tip_val_add"))
        self.btn_sub.setToolTip(translator.get("tip_val_sub"))
        self.spin_step.setToolTip(translator.get("tip_val_spinner"))


class OchaBoneListExplorer(QWidget):
    boneSelectionChanged = Signal(list)
    boneClicked = Signal(int)
    viewOptionsChanged = Signal()
    addGroupClicked = Signal()
    removeGroupClicked = Signal(str)
    renameGroupClicked = Signal(str)
    assignBonesClicked = Signal(str)
    removeInfluenceRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BoneExplorerPanel")

        l = QVBoxLayout(self)
        l.setContentsMargins(5, 5, 5, 5)
        l.setSpacing(5)

        top = QHBoxLayout()
        self.lbl_view = QLabel("View:")
        self.sort_combo = QComboBox()
        self.view_modes = ["view_default", "view_hierarchy", "view_scene_layer", "view_custom"]

        self.sort_order_button = QPushButton("↑↓")
        self.sort_order_button.setCheckable(True)
        self.sort_order_button.setObjectName("BoneSortOrderButton")

        top.addWidget(self.lbl_view)
        top.addWidget(self.sort_combo, 1)
        top.addWidget(self.sort_order_button)

        self.search_bar = QLineEdit()

        self.group_widget = QWidget()
        gl = QHBoxLayout(self.group_widget)
        gl.setContentsMargins(0, 5, 0, 0)
        self.btn_add_g = QPushButton()
        self.btn_rem_g = QPushButton()
        self.btn_ren_g = QPushButton()
        self.btn_asn_g = QPushButton()
        gl.addWidget(self.btn_add_g)
        gl.addWidget(self.btn_rem_g)
        gl.addWidget(self.btn_ren_g)
        gl.addStretch()
        gl.addWidget(self.btn_asn_g)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setMouseTracking(True)
        self.tree.installEventFilter(self)

        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)

        l.addLayout(top)
        l.addWidget(self.search_bar)
        l.addWidget(self.group_widget)
        l.addWidget(self.tree)
        self.group_widget.hide()

        self.search_bar.textChanged.connect(self._apply_filters)
        self.sort_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        self.sort_order_button.clicked.connect(self.viewOptionsChanged.emit)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemClicked.connect(self._on_item_clicked)

        self.btn_add_g.clicked.connect(lambda c=False: self.addGroupClicked.emit())
        self.btn_rem_g.clicked.connect(lambda c=False: self._on_remove_group_clicked())
        self.btn_ren_g.clicked.connect(lambda c=False: self._on_rename_group_clicked())
        self.btn_asn_g.clicked.connect(lambda c=False: self._on_assign_bones_clicked())

        self.retranslate_ui()

    def retranslate_ui(self):
        self.lbl_view.setText(translator.get("view_label"))
        self.search_bar.setPlaceholderText(translator.get("search_ph"))
        self.btn_add_g.setText(translator.get("btn_grp_add"))
        self.btn_rem_g.setText(translator.get("btn_grp_rem"))
        self.btn_ren_g.setText(translator.get("btn_grp_ren"))
        self.btn_asn_g.setText(translator.get("btn_assign"))

        curr = self.sort_combo.currentIndex()
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        for k in self.view_modes:
            self.sort_combo.addItem(translator.get(k))
        self.sort_combo.setCurrentIndex(curr if curr >= 0 else 0)
        self.sort_combo.blockSignals(False)

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item: return
        bid = item.data(0, Qt.ItemDataRole.UserRole)
        if bid is None: return
        menu = QMenu(self)
        act_remove = menu.addAction(translator.get("ctx_remove_infl"))
        act_remove.triggered.connect(lambda: self.removeInfluenceRequested.emit(bid))
        menu.exec(self.tree.mapToGlobal(pos))

    def _on_view_mode_changed(self, idx):
        key = self.view_modes[idx]
        self.group_widget.setVisible(key == "view_custom")
        self.viewOptionsChanged.emit()

    def _get_selected_group_name(self):
        item = self.tree.currentItem()
        if not item: return None
        while item.parent(): item = item.parent()
        if not (item.flags() & Qt.ItemIsSelectable): return item.text(0)
        return None

    def _on_remove_group_clicked(self):
        n = self._get_selected_group_name()
        if n: self.removeGroupClicked.emit(n)

    def _on_rename_group_clicked(self):
        n = self._get_selected_group_name()
        if n: self.renameGroupClicked.emit(n)

    def _on_assign_bones_clicked(self):
        n = self._get_selected_group_name()
        if n: self.assignBonesClicked.emit(n)

    def eventFilter(self, w, e):
        if w == self.tree and e.type() == QEvent.Type.ToolTip:
            item = self.tree.itemAt(e.pos())
            if item:
                QToolTip.showText(QCursor.pos(), item.toolTip(0), self.tree)
                return True
        return super().eventFilter(w, e)

    def silent_select_bone(self, bid):
        self.tree.blockSignals(True)
        it = QTreeWidgetItemIterator(self.tree)
        found = False
        self.tree.clearSelection()
        while it.value():
            if it.value().data(0, Qt.ItemDataRole.UserRole) == bid:
                it.value().setSelected(True)
                self.tree.scrollToItem(it.value())
                found = True
                break
            it += 1
        self.tree.blockSignals(False)
        return found

    def populate_bones(self, data):
        self.tree.blockSignals(True)
        self.tree.clear()
        idx = self.sort_combo.currentIndex()
        key = self.view_modes[idx if idx >= 0 else 0]
        desc = self.sort_order_button.isChecked()

        if not data:
            self.tree.blockSignals(False)
            return

        if key == "view_hierarchy":
            self._pop_tree(data)
        elif key == "view_scene_layer":
            self._pop_layer(data, desc)
        elif key == "view_custom":
            self._pop_custom(data, desc)
        else:
            self._pop_list(sorted(data, key=lambda x: x['name'], reverse=desc))

        self._apply_filters()
        self.tree.resizeColumnToContents(0)
        self.tree.blockSignals(False)

        self.tree.setSortingEnabled(key == "view_default")
        if key == "view_default":
            order = Qt.SortOrder.DescendingOrder if desc else Qt.SortOrder.AscendingOrder
            self.tree.sortItems(0, order)

    def _pop_list(self, data):
        for b in data:
            i = QTreeWidgetItem(self.tree)
            i.setText(0, b['name'])
            i.setData(0, Qt.ItemDataRole.UserRole, b['id'])
            i.setToolTip(0, b['name'])

    def _pop_tree(self, data):
        lookup = {}
        for b in data:
            if b.get('handle'):
                i = QTreeWidgetItem([b['name']])
                i.setData(0, Qt.ItemDataRole.UserRole, b['id'])
                i.setToolTip(0, b['name'])
                lookup[b['handle']] = i
        for b in data:
            if b['handle'] not in lookup: continue
            item = lookup[b['handle']]
            parent = lookup.get(b.get('parent_handle'))
            if parent:
                parent.addChild(item)
            else:
                self.tree.addTopLevelItem(item)
        self.tree.expandAll()

    def _pop_layer(self, data, desc):
        g = collections.defaultdict(list)
        for b in data: g[b.get('layer_name', '0')].append(b)
        for name in sorted(g.keys(), reverse=desc):
            p = QTreeWidgetItem(self.tree, [name])
            p.setFlags(p.flags() & ~Qt.ItemIsSelectable)
            p.setForeground(0, QColor("#f5b041"))
            f = p.font(0);
            f.setBold(True);
            p.setFont(0, f)
            for b in sorted(g[name], key=lambda x: x['name']):
                c = QTreeWidgetItem(p, [b['name']])
                c.setData(0, Qt.ItemDataRole.UserRole, b['id'])
                c.setToolTip(0, b['name'])
        self.tree.expandAll()

    def _pop_custom(self, data, desc):
        for name in sorted(data.keys(), reverse=desc):
            p = QTreeWidgetItem(self.tree, [name])
            p.setFlags(p.flags() & ~Qt.ItemIsSelectable)
            col = "#a9d0f5" if name != "[Ungrouped]" else "#777"
            p.setForeground(0, QColor(col))
            f = p.font(0);
            f.setBold(True);
            p.setFont(0, f)
            for b in sorted(data[name], key=lambda x: x['name']):
                c = QTreeWidgetItem(p, [b['name']])
                c.setData(0, Qt.ItemDataRole.UserRole, b['id'])
                c.setToolTip(0, b['name'])
        self.tree.expandAll()

    def _apply_filters(self, *args):
        txt = self.search_bar.text().lower()
        it = QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            name = item.text(0).lower()
            vis = txt in name
            is_grp = not (item.flags() & Qt.ItemIsSelectable)
            if vis:
                item.setHidden(False)
                p = item.parent()
                while p:
                    p.setHidden(False)
                    p = p.parent()
            else:
                hide = True
                if is_grp:
                    for i in range(item.childCount()):
                        if not item.child(i).isHidden():
                            hide = False
                            break
                if hide: item.setHidden(True)
            it += 1

    def filter_and_select_by_ids(self, valid_ids):
        self.tree.blockSignals(True)
        self.tree.clearSelection()
        self.search_bar.clear()
        valid_set = set(valid_ids)
        it = QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            bid = item.data(0, Qt.ItemDataRole.UserRole)
            is_grp = not (item.flags() & Qt.ItemIsSelectable)
            if not is_grp and bid is not None:
                if bid in valid_set:
                    item.setHidden(False)
                    item.setSelected(True)
                    p = item.parent()
                    while p:
                        p.setHidden(False)
                        p.setExpanded(True)
                        p = p.parent()
                else:
                    item.setHidden(True)
            elif is_grp:
                item.setHidden(True)
            it += 1
        self.tree.blockSignals(False)

    def _on_selection_changed(self):
        self.boneSelectionChanged.emit(self.get_selected_bone_ids())

    def _on_item_clicked(self, item, c):
        if len(self.tree.selectedItems()) <= 1:
            bid = item.data(0, Qt.ItemDataRole.UserRole)
            if bid is not None: self.boneClicked.emit(bid)

    def get_selected_bone_ids(self):
        return [i.data(0, Qt.ItemDataRole.UserRole) for i in self.tree.selectedItems()]

    def clear_list(self):
        self.tree.clear()
        self.search_bar.clear()
        self.sort_order_button.setChecked(False)


# =================================================================
# OchaControllerInspector (Updated with retranslate_ui)
# =================================================================
class OchaControllerInspector(QWidget):
    def __init__(self, controller_instance, parent=None):
        super().__init__(parent)
        self.controller = controller_instance
        self.current_node = None
        self.current_indices_path = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 1. Top: Info & Load
        self.grp_info = QGroupBox("Node Info")
        l_info = QVBoxLayout(self.grp_info)
        l_info.setSpacing(4)
        l_info.setContentsMargins(5, 8, 5, 5)

        row1 = QHBoxLayout()
        self.btn_load = QPushButton("Load Selected")
        self.btn_load.setFixedWidth(100)
        self.btn_load.setStyleSheet(
            "background-color: #2980B9; color: white; font-weight: bold; border-radius: 3px; padding: 4px;")

        self.lbl_node_name = QLabel("None")
        self.lbl_node_name.setStyleSheet("color: #00FFCC; font-weight: bold; font-size: 13px; margin-left: 5px;")
        self.lbl_node_name.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        row1.addWidget(self.btn_load)
        row1.addWidget(self.lbl_node_name, 1)

        self.tbl_info = QTableWidget(0, 2)
        self.tbl_info.horizontalHeader().setVisible(False)
        self.tbl_info.verticalHeader().setVisible(False)
        self.tbl_info.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_info.setStyleSheet("""
            QTableWidget { background-color: #2A2A2A; border: 1px solid #444; font-size: 11px; }
            QTableWidget::item { padding: 2px; border-bottom: 1px solid #333; }
        """)
        # ⭐️ HEIGHT INCREASED (1.5x)
        self.tbl_info.setMaximumHeight(150)

        l_info.addLayout(row1)
        l_info.addWidget(self.tbl_info)

        main_layout.addWidget(self.grp_info)

        # 2. Middle: Splitter (Tree | Editor)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(5)

        # Left Widget: Tree + Assign
        self.widget_left = QWidget()
        l_left = QVBoxLayout(self.widget_left)
        l_left.setContentsMargins(0, 0, 0, 0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Track Name", "Type"])
        # ⭐️ WIDTH INCREASED (~45%)
        self.tree.setColumnWidth(0, 240)
        self.tree.setAlternatingRowColors(False)
        self.tree.setMinimumHeight(350)
        self.tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.tree.setStyleSheet("""
            QTreeWidget { background-color: #252525; border: 1px solid #444; font-size: 12px; color: #DDD; }
            QTreeWidget::item { padding: 4px; height: 24px; border-bottom: 1px solid #333; }
            QTreeWidget::item:selected { background-color: #007ACC; color: white; }
            QTreeWidget::item:hover { background-color: #3A3A3A; }
            QHeaderView::section { background-color: #333; color: #DDD; padding: 4px; border: none; font-weight: bold; }
        """)

        row_assign = QHBoxLayout()
        self.combo_assign = QComboBox()
        self.btn_assign = QPushButton("Assign")
        self.btn_assign.setFixedWidth(60)
        self.btn_assign.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold;")
        row_assign.addWidget(self.combo_assign)
        row_assign.addWidget(self.btn_assign)

        l_left.addWidget(self.tree)
        l_left.addLayout(row_assign)

        # Right Widget: Stacked Editors
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        # Page 0: Empty
        self.page_empty = QLabel("Select a controller.")
        self.page_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_empty.setStyleSheet("color: #666; font-style: italic;")

        # Page 1: Script Editor (Simplified)
        self.page_script = QWidget()
        l_script = QVBoxLayout(self.page_script)
        l_script.setContentsMargins(5, 0, 0, 0)

        self.txt_editor = QTextEdit()
        self.txt_editor.setStyleSheet("font-family: Consolas; font-size: 12px; background: #1E1E1E; color: #DDD;")
        self.txt_editor.setMinimumHeight(100)

        self.btn_apply_script = QPushButton("Apply Code")
        self.btn_apply_script.setStyleSheet("background-color: #D35400; color: white; font-weight: bold;")

        self.lbl_script = QLabel("Script Code:")
        l_script.addWidget(self.lbl_script)
        l_script.addWidget(self.txt_editor)
        l_script.addWidget(self.btn_apply_script)

        # Page 2: Expression Editor (Simplified)
        self.page_expr = QWidget()
        l_expr = QVBoxLayout(self.page_expr)
        l_expr.setContentsMargins(5, 0, 0, 0)

        self.txt_expr_editor = QTextEdit()
        self.txt_expr_editor.setStyleSheet("font-family: Consolas; font-size: 12px; background: #1E1E1E; color: #AAA;")
        self.txt_expr_editor.setMinimumHeight(100)

        self.btn_apply_expr = QPushButton("Apply Expression")
        self.btn_apply_expr.setStyleSheet("background-color: #8E44AD; color: white;")

        self.lbl_expr = QLabel("Expression Code:")
        l_expr.addWidget(self.lbl_expr)
        l_expr.addWidget(self.txt_expr_editor)
        l_expr.addWidget(self.btn_apply_expr)

        # Page 3: Constraint Editor
        self.page_constraint = QWidget()
        l_cons = QVBoxLayout(self.page_constraint)
        l_cons.setContentsMargins(5, 0, 0, 0)

        self.tbl_targets = QTableWidget(0, 2)
        self.tbl_targets.setHorizontalHeaderLabels(["Target Node", "Weight"])
        self.tbl_targets.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_targets.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_targets.setStyleSheet("QTableWidget { background-color: #222; font-size: 11px; }")

        row_cons_btns = QHBoxLayout()
        self.btn_add_target = QPushButton("Add Selected")
        self.btn_rem_target = QPushButton("Remove")
        self.btn_add_target.setStyleSheet("background-color: #2980B9; color: white;")
        self.btn_rem_target.setStyleSheet("background-color: #C0392B; color: white;")
        row_cons_btns.addWidget(self.btn_add_target)
        row_cons_btns.addWidget(self.btn_rem_target)

        row_weight = QHBoxLayout()
        self.spin_weight = QDoubleSpinBox()
        self.spin_weight.setRange(0.0, 100.0)
        self.spin_weight.setValue(50.0)
        self.btn_set_weight = QPushButton("Set Weight")
        self.lbl_weight_label = QLabel("Weight:")
        row_weight.addWidget(self.lbl_weight_label)
        row_weight.addWidget(self.spin_weight)
        row_weight.addWidget(self.btn_set_weight)

        self.lbl_cons_targets = QLabel("Constraint Targets:")
        l_cons.addWidget(self.lbl_cons_targets)
        l_cons.addWidget(self.tbl_targets)
        l_cons.addLayout(row_cons_btns)
        l_cons.addLayout(row_weight)
        l_cons.addStretch()

        self.stack.addWidget(self.page_empty)
        self.stack.addWidget(self.page_script)
        self.stack.addWidget(self.page_expr)
        self.stack.addWidget(self.page_constraint)

        self.splitter.addWidget(self.widget_left)
        self.splitter.addWidget(self.stack)

        # ⭐️ Set Splitter Ratio (~45% : 55%)
        self.splitter.setStretchFactor(0, 10)
        self.splitter.setStretchFactor(1, 12)

        main_layout.addWidget(self.splitter)

        # Connections
        self.btn_load.clicked.connect(self._on_load)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.btn_assign.clicked.connect(self._on_assign)

        # Script
        self.btn_apply_script.clicked.connect(self._on_apply_script)

        # Expression
        self.btn_apply_expr.clicked.connect(self._on_apply_script)  # Reusing apply script logic

        # Constraint
        self.btn_add_target.clicked.connect(self._on_add_target)
        self.btn_rem_target.clicked.connect(self._on_rem_target)
        self.btn_set_weight.clicked.connect(self._on_set_weight)
        self.tbl_targets.itemClicked.connect(self._on_target_selected)

        # Full Controller List
        self.FLOAT_CONTROLLERS = [
            "Bezier_Float", "Float_List", "Float_Script", "Noise_Float", "Linear_Float", "Float_Expression",
            "Float_Motion_Capture", "Float_Reactor", "Slave_Float", "Waveform_Float"
        ]
        self.POSITION_CONTROLLERS = [
            "Position_XYZ", "Position_List", "Position_Constraint", "Path_Constraint", "Position_Script",
            "Noise_Position", "TCB_Position", "Bezier_Position", "Linear_Position", "Position_Motion_Capture",
            "Position_Reactor", "Slave_Position", "Attachment", "Surface_Constraint", "Position_Expression"
        ]
        self.ROTATION_CONTROLLERS = [
            "Euler_XYZ", "Rotation_List", "Orientation_Constraint", "LookAt_Constraint", "Rotation_Script",
            "Noise_Rotation", "TCB_Rotation", "Linear_Rotation", "Smooth_Rotation", "Rotation_Motion_Capture",
            "Rotation_Reactor", "Slave_Rotation", "Rotation_Expression"
        ]
        self.SCALE_CONTROLLERS = [
            "Bezier_Scale", "Scale_List", "Scale_Script", "Noise_Scale", "TCB_Scale", "Linear_Scale",
            "Scale_Motion_Capture", "Scale_Reactor", "Slave_Scale", "Scale_Expression"
        ]
        self.TRANSFORM_CONTROLLERS = ["PRS", "Transform_Script", "Link_Constraint"]

        self.retranslate_ui()

    def retranslate_ui(self):
        # ⭐️ TRANSLATION LOGIC ADDED HERE
        self.grp_info.setTitle(translator.get("insp_grp_info"))
        self.btn_load.setText(translator.get("insp_btn_load"))

        self.tree.headerItem().setText(0, translator.get("insp_lbl_track"))
        self.tree.headerItem().setText(1, translator.get("insp_lbl_type"))

        self.btn_assign.setText(translator.get("insp_btn_assign"))

        self.lbl_script.setText(translator.get("insp_lbl_script"))
        self.btn_apply_script.setText(translator.get("insp_btn_apply_script"))

        self.lbl_expr.setText(translator.get("insp_lbl_expr"))
        self.btn_apply_expr.setText(translator.get("insp_btn_apply_expr"))

        self.lbl_cons_targets.setText(translator.get("insp_lbl_targets"))
        self.tbl_targets.horizontalHeaderItem(0).setText(translator.get("insp_col_target"))
        self.tbl_targets.horizontalHeaderItem(1).setText(translator.get("insp_col_weight"))

        self.btn_add_target.setText(translator.get("insp_btn_add_tgt"))
        self.btn_rem_target.setText(translator.get("insp_btn_rem_tgt"))
        self.lbl_weight_label.setText(translator.get("insp_col_weight"))
        self.btn_set_weight.setText(translator.get("insp_btn_set_w"))

    def _on_load(self):
        sel = rt.selection
        if sel.count != 1: return
        self.current_node = sel[0]
        self.lbl_node_name.setText(self.current_node.name)

        # Populate Info Table
        info = self.controller.get_node_info(self.current_node)
        self.tbl_info.setRowCount(len(info))
        for i, (k, v) in enumerate(info.items()):
            self.tbl_info.setItem(i, 0, QTableWidgetItem(k))
            self.tbl_info.setItem(i, 1, QTableWidgetItem(str(v)))

        self._refresh_tree()

    def _refresh_tree(self):
        self.tree.clear()
        if not self.current_node: return
        data = self.controller.get_controller_hierarchy(self.current_node)
        item_map = {}
        root_data = [d for d in data if d['parent_index'] == 0]
        if not root_data: return
        for d in data:
            item = QTreeWidgetItem()
            item.setText(0, d['name'])
            item.setText(1, d['type'])
            item.setData(0, Qt.ItemDataRole.UserRole, d)
            item_map[d['index']] = item
        for d in data:
            if d['parent_index'] == 0:
                self.tree.addTopLevelItem(item_map[d['index']])
            elif d['parent_index'] in item_map:
                item_map[d['parent_index']].addChild(item_map[d['index']])
        self.tree.expandAll()

    def _on_item_clicked(self, item, col):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data: return
        path = []
        curr = item
        while curr:
            d = curr.data(0, Qt.ItemDataRole.UserRole)
            if d['sub_id'] > 0: path.insert(0, d['sub_id'])
            curr = curr.parent()
        self.current_indices_path = path
        self._update_assign_options(data['type'], data['name'])

        c_type = data['type'].lower()
        if "script" in c_type:
            self.stack.setCurrentWidget(self.page_script)
            self._load_script_data()
        elif "expression" in c_type:
            self.stack.setCurrentWidget(self.page_expr)
            self._load_expression_data()
        elif "constraint" in c_type:
            self.stack.setCurrentWidget(self.page_constraint)
            self._load_constraint_data()
        else:
            self.stack.setCurrentWidget(self.page_empty)

    def _update_assign_options(self, c_type, c_name):
        self.combo_assign.clear()
        t_lower = c_type.lower()
        n_lower = c_name.lower()
        items = []
        if "position" in t_lower or "pos" in t_lower:
            items = self.POSITION_CONTROLLERS
        elif "rotation" in t_lower or "rot" in t_lower or "euler" in t_lower or "quat" in t_lower:
            items = self.ROTATION_CONTROLLERS
        elif "scale" in t_lower:
            items = self.SCALE_CONTROLLERS
        elif "float" in t_lower:
            items = self.FLOAT_CONTROLLERS
        elif "transform" in t_lower or "prs" in t_lower:
            items = self.TRANSFORM_CONTROLLERS
        else:
            # Fallback based on name
            if "position" in n_lower:
                items = self.POSITION_CONTROLLERS
            elif "rotation" in n_lower:
                items = self.ROTATION_CONTROLLERS
            elif "scale" in n_lower:
                items = self.SCALE_CONTROLLERS
            else:
                items = self.FLOAT_CONTROLLERS

        final_items = []
        for i in items:
            # Link Constraint Filter
            if i == "Link_Constraint":
                if "transform" in t_lower or "prs" in t_lower: final_items.append(i)
            else:
                final_items.append(i)
        self.combo_assign.addItems(final_items)

    def _load_script_data(self):
        if not self.current_node: return
        info = self.controller.get_controller_details(self.current_node, self.current_indices_path)
        if not info: return
        self.txt_editor.setPlainText(info.get('code', ''))

    def _load_expression_data(self):
        if not self.current_node: return
        info = self.controller.get_controller_details(self.current_node, self.current_indices_path)
        if not info: return
        self.txt_expr_editor.setPlainText(info.get('code', ''))

    def _load_constraint_data(self):
        if not self.current_node: return
        info = self.controller.get_controller_details(self.current_node, self.current_indices_path)
        if not info: return
        targets = info.get('targets', [])
        self.tbl_targets.setRowCount(len(targets))
        for i, t in enumerate(targets):
            self.tbl_targets.setItem(i, 0, QTableWidgetItem(t['name']))
            self.tbl_targets.setItem(i, 1, QTableWidgetItem(str(t['weight'])))

    def _on_apply_script(self):
        if not self.current_node: return

        # Determine which editor is active
        if self.stack.currentWidget() == self.page_script:
            code = self.txt_editor.toPlainText()
        elif self.stack.currentWidget() == self.page_expr:
            code = self.txt_expr_editor.toPlainText()
        else:
            return

        if self.controller.apply_script_code(self.current_node, self.current_indices_path, code):
            rt.print("✅ Script Updated.")
        else:
            QMessageBox.warning(self, "Error", "Failed to apply script.")

    def _on_assign(self):
        if not self.current_node or not self.current_indices_path: return
        t_str = self.combo_assign.currentText()

        if self.controller.assign_controller(self.current_node, self.current_indices_path, t_str):
            self._refresh_tree()

            # Auto Re-Select
            it = QTreeWidgetItemIterator(self.tree)
            while it.value():
                item = it.value()
                if item.isSelected():
                    self._on_item_clicked(item, 0)
                    break
                it += 1

            rt.print(f"✅ Assigned {t_str}")
        else:
            QMessageBox.warning(self, "Error", "Failed to assign.")

    # Constraint Slots
    def _on_add_target(self):
        if not self.current_node: return
        if self.controller.add_constraint_target(self.current_node, self.current_indices_path):
            self._load_constraint_data()
        else:
            QMessageBox.warning(self, "Error", "Select a valid target node.")

    def _on_rem_target(self):
        r = self.tbl_targets.currentRow()
        if r < 0: return
        if self.controller.remove_constraint_target(self.current_node, self.current_indices_path, r + 1):
            self._load_constraint_data()

    def _on_target_selected(self, item):
        r = self.tbl_targets.currentRow()
        try:
            w = float(self.tbl_targets.item(r, 1).text())
            self.spin_weight.setValue(w)
        except:
            pass

    def _on_set_weight(self):
        r = self.tbl_targets.currentRow()
        if r < 0: return
        val = self.spin_weight.value()
        if self.controller.set_constraint_weight(self.current_node, self.current_indices_path, r + 1, val):
            self._load_constraint_data()


rt.print("✅ [Import Check] FINISHED loading ui.ohcha_ui_widgets.")