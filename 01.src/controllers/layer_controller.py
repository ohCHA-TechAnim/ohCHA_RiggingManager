# ohCHA_RigManager/01/src/controllers/layer_controller.py
# Description: [v20.52] Layer Controller Update.
#              - UPDATED: get_scene_objects retrieves Layer Name and Type.

import pymxs
import json
from pymxs import runtime as rt


class LayerController:
    def __init__(self):
        pass

    def _ensure_logic(self):
        return hasattr(rt, "ohCHA_LayerLogic")

    def get_layer_hierarchy(self):
        if not self._ensure_logic(): return []
        try:
            raw_data = rt.ohCHA_LayerLogic.getLayerHierarchyData()
            layers = []
            for entry in raw_data:
                name = str(entry[0])
                parent = str(entry[1]) if entry[1] else None
                layers.append({"name": name, "parent": parent})
            return layers
        except Exception as e:
            print(f"Layer Data Error: {e}")
            return []

    def create_layer(self, name, parent_name=None):
        if not name: return False
        p_name = parent_name if parent_name else ""
        return rt.ohCHA_LayerLogic.createLayer(name, p_name)

    def rename_layer(self, old_name, new_name):
        if not new_name or old_name == "0": return False
        return rt.ohCHA_LayerLogic.renameLayer(old_name, new_name)

    def delete_layer(self, name):
        if name == "0": return False
        return rt.ohCHA_LayerLogic.deleteLayer(name)

    def set_layer_parent(self, child_name, parent_name):
        if not child_name or child_name == "0": return False
        p_name = parent_name if parent_name else ""
        return rt.ohCHA_LayerLogic.setLayerParent(child_name, p_name)

    # ⭐️ Updated to include Layer Name and Type
    def get_scene_objects(self):
        objs = []
        for o in rt.objects:
            if rt.isValidNode(o) and not o.isHidden:
                # Identify Type
                o_type = "Object"
                if rt.isKindOf(o, rt.Biped_Object):
                    o_type = "Biped"
                elif rt.isKindOf(o, rt.BoneGeometry):
                    o_type = "Bone"
                elif rt.isKindOf(o, rt.Helper):
                    o_type = "Helper"
                elif rt.isKindOf(o, rt.GeometryClass):
                    o_type = "Geometry"
                elif rt.isKindOf(o, rt.Shape):
                    o_type = "Shape"
                elif rt.isKindOf(o, rt.Light):
                    o_type = "Light"
                elif rt.isKindOf(o, rt.Camera):
                    o_type = "Camera"

                # Get Layer
                layer_name = o.layer.name

                objs.append({
                    "name": o.name,
                    "handle": o.handle,
                    "layer": layer_name,
                    "type": o_type
                })

        objs.sort(key=lambda x: x["name"])
        return objs

    def add_objects_to_layer(self, layer_name, obj_handles):
        if not layer_name or not obj_handles: return False
        mxs_handles = rt.Array(*(int(h) for h in obj_handles))
        return rt.ohCHA_LayerLogic.addNodesToLayer(layer_name, mxs_handles)

    def select_layer_objects(self, layer_name):
        return rt.ohCHA_LayerLogic.selectLayerObjects(layer_name)

    def save_layer_preset(self, file_path):
        if not file_path: return False
        try:
            data = self.get_layer_hierarchy()
            save_data = [l for l in data if l['name'] != "0"]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=4)
            return True
        except Exception:
            return False

    def load_layer_preset(self, file_path):
        if not file_path: return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                layers = json.load(f)
            for l in layers: self.create_layer(l['name'])
            for l in layers:
                if l.get('parent') and l['parent'] != "0":
                    self.set_layer_parent(l['name'], l['parent'])
            return True
        except Exception:
            return False


layer_controller_instance = LayerController()