# ohCHA_RigManager/01/src/ui/tabs/naming_tool.py
# Description: [v20.68] Init Crash Fix.
#              - FIXED: Moved '_toggle_num(False)' to end of '_setup_ui'.
#              - REASON: Prevent accessing 'self.table' before it is created.
#              - SAFETY: Added attribute check in '_update_preview'.

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QGroupBox, QSpinBox, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QGridLayout, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

try:
    from utils.translator import translator
except ImportError:
    class T:
        get = lambda s, k: k


    translator = T()

try:
    from controllers.naming_controller import naming_controller_instance
except ImportError:
    naming_controller_instance = None


class NamingToolWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = naming_controller_instance
        self._setup_ui()
        self._connect_signals()
        self.retranslate_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Common Styles ---
        group_style = """
            QGroupBox { 
                border: 1px solid #555; 
                border-radius: 5px; 
                margin-top: 10px; 
                font-weight: bold; 
                color: #DDD; 
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
        """
        input_style = "background-color: #2b2b2b; border: 1px solid #555; border-radius: 3px; padding: 4px; color: #EEE;"
        spin_style = "QSpinBox { " + input_style + " } QSpinBox::up-button, QSpinBox::down-button { width: 0px; }"

        checkbox_style = """
            QCheckBox { spacing: 8px; color: #DDD; font-weight: bold; }
            QCheckBox::indicator { 
                width: 18px; height: 18px; 
                background: #2b2b2b; 
                border: 1px solid #666; 
                border-radius: 4px; 
            }
            QCheckBox::indicator:hover { border: 1px solid #888; }
            QCheckBox::indicator:checked { 
                background-color: #007ACC; 
                border: 1px solid #007ACC; 
            }
        """

        # 1. Top Area: Load Selection
        top_layout = QHBoxLayout()
        self.btn_load = QPushButton("Load Selected")
        self.btn_load.setFixedHeight(30)
        self.btn_load.setStyleSheet(
            "QPushButton { background-color: #2980B9; color: white; font-weight: bold; border-radius: 4px; } QPushButton:hover { background-color: #3498DB; }")

        self.lbl_count = QLabel("Count: 0")
        self.lbl_count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_count.setStyleSheet("color: #AAA; font-weight: bold;")

        top_layout.addWidget(self.btn_load)
        top_layout.addWidget(self.lbl_count)
        main_layout.addLayout(top_layout)

        # 2. Naming Rules Group
        self.grp_rules = QGroupBox("Naming Rules")
        self.grp_rules.setStyleSheet(group_style)
        rules_grid = QGridLayout(self.grp_rules)
        rules_grid.setContentsMargins(10, 15, 10, 10)
        rules_grid.setSpacing(8)

        # Row 0: Base Name
        self.chk_base = QCheckBox("Use Base Name")
        self.chk_base.setStyleSheet(checkbox_style)

        self.txt_base = QLineEdit()
        self.txt_base.setStyleSheet(input_style)
        self.txt_base.setEnabled(False)
        rules_grid.addWidget(self.chk_base, 0, 0)
        rules_grid.addWidget(self.txt_base, 0, 1, 1, 3)

        # Row 1: Prefix / Suffix
        self.lbl_pre = QLabel("Prefix:")
        self.txt_pre = QLineEdit()
        self.txt_pre.setStyleSheet(input_style)

        self.lbl_suf = QLabel("Suffix:")
        self.txt_suf = QLineEdit()
        self.txt_suf.setStyleSheet(input_style)

        rules_grid.addWidget(self.lbl_pre, 1, 0)
        rules_grid.addWidget(self.txt_pre, 1, 1)
        rules_grid.addWidget(self.lbl_suf, 1, 2)
        rules_grid.addWidget(self.txt_suf, 1, 3)

        # Row 2: Remove Digits
        self.lbl_rem_f = QLabel("Rem First:")
        self.spin_rem_f = QSpinBox()
        self.spin_rem_f.setStyleSheet(spin_style)
        self.spin_rem_f.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_rem_f.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_rem_l = QLabel("Rem Last:")
        self.spin_rem_l = QSpinBox()
        self.spin_rem_l.setStyleSheet(spin_style)
        self.spin_rem_l.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_rem_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        rules_grid.addWidget(self.lbl_rem_f, 2, 0)
        rules_grid.addWidget(self.spin_rem_f, 2, 1)
        rules_grid.addWidget(self.lbl_rem_l, 2, 2)
        rules_grid.addWidget(self.spin_rem_l, 2, 3)

        main_layout.addWidget(self.grp_rules)

        # 3. Numbering Group
        self.grp_num = QGroupBox("Numbering")
        self.grp_num.setStyleSheet(group_style)
        num_layout = QHBoxLayout(self.grp_num)
        num_layout.setContentsMargins(10, 15, 10, 10)

        self.chk_num = QCheckBox("Enable")
        self.chk_num.setStyleSheet(checkbox_style)

        self.lbl_start = QLabel("Start:")
        self.spin_start = QSpinBox()
        self.spin_start.setRange(0, 9999)
        self.spin_start.setValue(1)
        self.spin_start.setStyleSheet(spin_style)

        self.lbl_step = QLabel("Step:")
        self.spin_step = QSpinBox()
        self.spin_step.setValue(1)
        self.spin_step.setStyleSheet(spin_style)

        self.lbl_pad = QLabel("Pad:")
        self.spin_pad = QSpinBox()
        self.spin_pad.setValue(3)
        self.spin_pad.setStyleSheet(spin_style)

        num_layout.addWidget(self.chk_num)
        num_layout.addStretch()
        num_layout.addWidget(self.lbl_start)
        num_layout.addWidget(self.spin_start)
        num_layout.addSpacing(10)
        num_layout.addWidget(self.lbl_step)
        num_layout.addWidget(self.spin_step)
        num_layout.addSpacing(10)
        num_layout.addWidget(self.lbl_pad)
        num_layout.addWidget(self.spin_pad)

        # ❌ Moved _toggle_num call to END of function
        main_layout.addWidget(self.grp_num)

        # 4. Preview Table
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Current Name", "New Name"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #222; border: 1px solid #444; border-radius: 4px; } 
            QTableWidget::item { padding: 4px; color: #DDD; }
            QHeaderView::section { background-color: #333; color: #DDD; border: none; padding: 4px; }
        """)
        main_layout.addWidget(self.table)

        # 5. Apply Button
        self.btn_apply = QPushButton("Rename Objects")
        self.btn_apply.setFixedHeight(45)
        self.btn_apply.setStyleSheet("""
            QPushButton { background-color: #27AE60; color: white; font-weight: bold; font-size: 14px; border-radius: 5px; }
            QPushButton:hover { background-color: #2ECC71; }
            QPushButton:pressed { background-color: #1E8449; }
        """)
        main_layout.addWidget(self.btn_apply)

        # ⭐️ Call initialization Logic AFTER widgets are created
        self._toggle_num(False)

    def _connect_signals(self):
        self.btn_load.clicked.connect(self._on_load)
        self.chk_base.toggled.connect(self._toggle_base)
        self.chk_num.toggled.connect(self._toggle_num)
        self.btn_apply.clicked.connect(self._on_apply)

        # Auto-Update Preview
        widgets = [self.txt_base, self.txt_pre, self.txt_suf,
                   self.spin_rem_f, self.spin_rem_l,
                   self.spin_start, self.spin_step, self.spin_pad]

        for w in widgets:
            if isinstance(w, QLineEdit): w.textChanged.connect(self._update_preview)
            if isinstance(w, QSpinBox): w.valueChanged.connect(self._update_preview)

        self.chk_base.toggled.connect(self._update_preview)
        self.chk_num.toggled.connect(self._update_preview)

    def _toggle_base(self, checked):
        self.txt_base.setEnabled(checked)
        self.spin_rem_f.setEnabled(not checked)
        self.spin_rem_l.setEnabled(not checked)
        self._update_preview()

    def _toggle_num(self, checked):
        self.spin_start.setEnabled(checked)
        self.spin_step.setEnabled(checked)
        self.spin_pad.setEnabled(checked)
        self._update_preview()

    def _on_load(self):
        count = self.controller.load_selection()
        self.lbl_count.setText(translator.get("name_lbl_count").format(count))
        self._update_preview()

    def _get_params(self):
        return {
            "base_name": self.txt_base.text(),
            "use_base": self.chk_base.isChecked(),
            "prefix": self.txt_pre.text(),
            "suffix": self.txt_suf.text(),
            "rem_first": self.spin_rem_f.value(),
            "rem_last": self.spin_rem_l.value(),
            "use_num": self.chk_num.isChecked(),
            "start": self.spin_start.value(),
            "step": self.spin_step.value(),
            "padding": self.spin_pad.value()
        }

    def _update_preview(self):
        # ⭐️ Safety Check
        if not hasattr(self, "table") or not self.controller: return

        data = self.controller.get_preview_data(self._get_params())

        self.table.setRowCount(len(data))
        for i, (orig, new) in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(orig))

            item_new = QTableWidgetItem(new)
            item_new.setForeground(QColor("#00FFCC"))  # Highlight new name
            self.table.setItem(i, 1, item_new)

    def _on_apply(self):
        if self.controller.apply_rename():
            QMessageBox.information(self, translator.get("title_complete"),
                                    translator.get("name_msg_success").format(self.table.rowCount()))
            self._on_load()
        else:
            QMessageBox.warning(self, translator.get("title_error"), translator.get("name_msg_no_sel"))

    def retranslate_ui(self):
        self.btn_load.setText(translator.get("name_btn_load"))

        self.grp_rules.setTitle(translator.get("name_grp_mod"))
        self.grp_num.setTitle(translator.get("name_grp_num"))

        self.chk_base.setText(translator.get("name_chk_base"))
        self.lbl_pre.setText(translator.get("name_lbl_pre"))
        self.lbl_suf.setText(translator.get("name_lbl_suf"))

        self.lbl_rem_f.setText(translator.get("name_lbl_rem_f"))
        self.lbl_rem_l.setText(translator.get("name_lbl_rem_l"))

        self.chk_num.setText(translator.get("name_chk_num"))
        self.lbl_start.setText(translator.get("name_lbl_start"))
        self.lbl_step.setText(translator.get("name_lbl_step"))
        self.lbl_pad.setText(translator.get("name_lbl_pad"))
        self.btn_apply.setText(translator.get("name_btn_apply"))

        self.table.setHorizontalHeaderLabels([
            translator.get("name_col_curr"),
            translator.get("name_col_new")
        ])