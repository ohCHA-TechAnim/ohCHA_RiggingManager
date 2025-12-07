# ohCHA_RigManager/01/src/ui/tabs/layer_tool.py
# Description: [v20.61] Simplified & Stable.
#              - REMOVED: Scene Object List (Right panel).
#              - UPDATED: 'Assign' now uses current Max Viewport Selection.
#              - LAYOUT: Clean vertical layout focused on Hierarchy.

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QInputDialog, QMessageBox, QAbstractItemView,
    QMenu, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator,
    QFileDialog, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from pymxs import runtime as rt

try:
    from utils.translator import translator
except ImportError:
    class T:
        get = lambda s, k: k


    translator = T()

try:
    from controllers.layer_controller import layer_controller_instance
except ImportError:
    layer_controller_instance = None


class LayerTree(QTreeWidget):
    itemDropped = Signal()

    def dropEvent(self, event):
        super().dropEvent(event)
        pos = event.position().toPoint()
        target_item = self.itemAt(pos)
        if target_item: target_item.setExpanded(True)
        self.itemDropped.emit()


class LayerToolWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = layer_controller_instance

        self._setup_ui()
        self._connect_signals()
        self.retranslate_ui()
        self._refresh_layers()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # 1. Preset Buttons
        preset_layout = QHBoxLayout()
        self.btn_save_preset = QPushButton("Save Preset")
        self.btn_load_preset = QPushButton("Load Preset")

        btn_style = "QPushButton { font-weight: bold; border-radius: 4px; padding: 6px; color: white; }"
        self.btn_save_preset.setStyleSheet(btn_style + "background-color: #27AE60;")
        self.btn_load_preset.setStyleSheet(btn_style + "background-color: #8E44AD;")

        preset_layout.addWidget(self.btn_save_preset)
        preset_layout.addWidget(self.btn_load_preset)
        main_layout.addLayout(preset_layout)

        # 2. Header (Label + Refresh)
        header_layout = QHBoxLayout()
        self.lbl_layers = QLabel("Layer Hierarchy")
        self.lbl_layers.setStyleSheet("font-weight: bold; color: #DDD; font-size: 12px;")

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setFixedSize(60, 24)
        self.btn_refresh.setStyleSheet(
            "QPushButton { background-color: #444; border: none; border-radius: 3px; color: #CCC; font-weight: bold; } QPushButton:hover { color: white; background-color: #555; }")

        header_layout.addWidget(self.lbl_layers)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_refresh)
        main_layout.addLayout(header_layout)

        # 3. Layer Tree
        self.tree_layers = LayerTree()
        self.tree_layers.setHeaderHidden(True)
        self.tree_layers.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tree_layers.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_layers.setStyleSheet("""
            QTreeWidget { background-color: #222; border: 1px solid #444; border-radius: 3px; } 
            QTreeWidget::item { padding: 5px; }
            QTreeWidget::item:selected { background-color: #007ACC; color: white; }
            QTreeWidget::item:hover { background-color: #333; }
        """)
        self.tree_layers.setDragEnabled(True)
        self.tree_layers.setAcceptDrops(True)
        self.tree_layers.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        main_layout.addWidget(self.tree_layers)

        # 4. Create Row
        create_row = QHBoxLayout()
        create_row.setSpacing(5)
        self.txt_new_layer = QLineEdit()
        self.txt_new_layer.setFixedHeight(30)
        self.txt_new_layer.setPlaceholderText("New Layer Name...")
        self.txt_new_layer.setStyleSheet(
            "background-color: #2b2b2b; border: 1px solid #555; border-radius: 4px; padding-left: 5px; color: #EEE;")

        self.btn_create = QPushButton("+")
        self.btn_create.setFixedSize(40, 30)
        self.btn_create.setStyleSheet(
            "QPushButton { background-color: #007ACC; color: white; font-weight: bold; border-radius: 4px; border: none; font-size: 16px; } QPushButton:hover { background-color: #008ae6; }")

        create_row.addWidget(self.txt_new_layer)
        create_row.addWidget(self.btn_create)
        main_layout.addLayout(create_row)

        # 5. Main Action Button (Assign Selection)
        self.btn_assign = QPushButton("Add Selected Objects to Layer")
        self.btn_assign.setFixedHeight(36)
        self.btn_assign.setStyleSheet("""
            QPushButton { background-color: #2980B9; color: white; font-weight: bold; border-radius: 4px; font-size: 13px; } 
            QPushButton:hover { background-color: #3498DB; }
            QPushButton:pressed { background-color: #1F618D; }
        """)
        main_layout.addWidget(self.btn_assign)

        # 6. Layer Management Buttons
        mgmt_row = QHBoxLayout()
        mgmt_row.setSpacing(5)

        self.btn_select_layer_obj = QPushButton("Select Layer Objects")
        self.btn_rename = QPushButton("Rename")
        self.btn_delete = QPushButton("Delete")

        btn_base = "QPushButton { border: none; border-radius: 4px; padding: 8px; font-weight: bold; font-size: 12px; }"
        self.btn_select_layer_obj.setStyleSheet(btn_base + "background-color: #555; color: #EEE;")
        self.btn_rename.setStyleSheet(btn_base + "background-color: #555; color: #EEE;")
        self.btn_delete.setStyleSheet(btn_base + "background-color: #C0392B; color: white;")

        mgmt_row.addWidget(self.btn_select_layer_obj)
        mgmt_row.addWidget(self.btn_rename)
        mgmt_row.addWidget(self.btn_delete)

        main_layout.addLayout(mgmt_row)

    def _connect_signals(self):
        self.btn_create.clicked.connect(self._on_create_layer)
        self.txt_new_layer.returnPressed.connect(self._on_create_layer)
        self.btn_delete.clicked.connect(self._on_delete_layer)
        self.btn_rename.clicked.connect(self._on_rename_layer)

        self.btn_refresh.clicked.connect(self._refresh_layers)

        # ⭐️ Main Assignment Logic
        self.btn_assign.clicked.connect(self._on_assign_selection)
        self.btn_select_layer_obj.clicked.connect(self._on_select_layer_objects)

        self.tree_layers.customContextMenuRequested.connect(self._on_layer_context_menu)
        self.btn_save_preset.clicked.connect(self._on_save_preset)
        self.btn_load_preset.clicked.connect(self._on_load_preset)
        self.tree_layers.itemDropped.connect(self._on_hierarchy_changed)

    def retranslate_ui(self):
        self.btn_save_preset.setText(translator.get("layer_btn_save"))
        self.btn_load_preset.setText(translator.get("layer_btn_load"))
        self.lbl_layers.setText(translator.get("layer_lbl_hierarchy"))
        self.btn_refresh.setText(translator.get("layer_btn_refresh"))
        self.txt_new_layer.setPlaceholderText(translator.get("layer_ph_new"))

        self.btn_assign.setText(translator.get("layer_tip_assign"))  # "Assign Objects"

        self.btn_select_layer_obj.setText(translator.get("layer_btn_sel_obj"))
        self.btn_rename.setText(translator.get("layer_btn_rename"))
        self.btn_delete.setText(translator.get("layer_btn_del"))

    def _refresh_layers(self):
        if not self.controller: return

        # Save expansion state
        expanded_layers = []
        it = QTreeWidgetItemIterator(self.tree_layers)
        while it.value():
            item = it.value()
            if item.isExpanded(): expanded_layers.append(item.text(0))
            it += 1

        self.tree_layers.blockSignals(True)
        self.tree_layers.clear()

        layer_data = self.controller.get_layer_hierarchy()

        items = {}
        # Create items
        for l in layer_data:
            item = QTreeWidgetItem([l['name']])
            if l['name'] == "0":
                item.setForeground(0, QColor("#AAA"))
                item.setToolTip(0, "Default Layer (Root)")
                item.setExpanded(True)
            items[l['name']] = item

        # Build Hierarchy
        for l in layer_data:
            name = l['name']
            p_name = l['parent']
            item = items[name]

            if p_name and p_name in items:
                items[p_name].addChild(item)
            else:
                self.tree_layers.addTopLevelItem(item)

        # Restore expansion
        it = QTreeWidgetItemIterator(self.tree_layers)
        while it.value():
            item = it.value()
            if item.text(0) in expanded_layers:
                item.setExpanded(True)
            it += 1

        self.tree_layers.blockSignals(False)

    def _get_selected_layer_name(self):
        items = self.tree_layers.selectedItems()
        return items[0].text(0) if items else None

    def _on_create_layer(self):
        name = self.txt_new_layer.text().strip()
        if not name: return

        parent_name = self._get_selected_layer_name() or "0"
        if self.controller.create_layer(name, parent_name):
            self.txt_new_layer.clear()
            self._refresh_layers()

            # Auto Select
            items = self.tree_layers.findItems(name, Qt.MatchFlag.MatchRecursive | Qt.MatchFlag.MatchExactly)
            if items:
                self.tree_layers.setCurrentItem(items[0])
        else:
            QMessageBox.warning(self, translator.get("layer_msg_err"), translator.get("layer_msg_fail"))

    def _on_delete_layer(self):
        name = self._get_selected_layer_name()
        if not name or name == "0": return
        res = QMessageBox.question(self, translator.get("layer_msg_del_title"),
                                   translator.get("layer_msg_del_confirm").format(name),
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            self.controller.delete_layer(name)
            self._refresh_layers()

    def _on_rename_layer(self):
        old_name = self._get_selected_layer_name()
        if not old_name or old_name == "0": return
        new_name, ok = QInputDialog.getText(self, translator.get("layer_msg_ren_title"),
                                            translator.get("layer_msg_ren_label"), text=old_name)
        if ok and new_name:
            self.controller.rename_layer(old_name, new_name)
            self._refresh_layers()

    # ⭐️ Assign Current Selection in Max to Selected Layer
    def _on_assign_selection(self):
        layer_name = self._get_selected_layer_name()
        if not layer_name:
            QMessageBox.warning(self, translator.get("title_info"), "Please select a target layer.")
            return

        # Get handles directly from Max Selection
        handles = [o.handle for o in rt.selection]
        if not handles:
            QMessageBox.warning(self, translator.get("title_info"), "No objects selected in the scene.")
            return

        if self.controller.add_objects_to_layer(layer_name, handles):
            # Visual feedback could be added here (e.g. status bar)
            pass

    def _on_select_layer_objects(self):
        name = self._get_selected_layer_name()
        if name: self.controller.select_layer_objects(name)

    def _on_save_preset(self):
        path, _ = QFileDialog.getSaveFileName(self, translator.get("layer_btn_save"), "", "JSON (*.json)")
        if path and self.controller.save_layer_preset(path):
            QMessageBox.information(self, translator.get("layer_msg_success"), translator.get("layer_msg_saved"))

    def _on_load_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, translator.get("layer_btn_load"), "", "JSON (*.json)")
        if path and self.controller.load_layer_preset(path):
            self._refresh_layers()
            QMessageBox.information(self, translator.get("layer_msg_success"), translator.get("layer_msg_loaded"))

    def _on_hierarchy_changed(self):
        self._sync_tree_to_max(self.tree_layers.invisibleRootItem())

    def _sync_tree_to_max(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            child_name = child.text(0)

            parent = child.parent()
            target_parent_name = parent.text(0) if parent else ""

            if child_name != "0":
                self.controller.set_layer_parent(child_name, target_parent_name)

            self._sync_tree_to_max(child)

    def _on_layer_context_menu(self, pos):
        item = self.tree_layers.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        menu.addAction(translator.get("layer_btn_sel_obj"), self._on_select_layer_objects)
        if item.text(0) != "0":
            menu.addAction(translator.get("layer_btn_rename"), self._on_rename_layer)
            menu.addAction(translator.get("layer_btn_del"), self._on_delete_layer)
        menu.exec(self.tree_layers.mapToGlobal(pos))