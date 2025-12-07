# ohCHA_RigManager/01/src/controllers/group_controller.py
# Description: [v1.2.4] Changed storage: Removed MaxFileName dependency.
#              Groups are now persistent per Mesh Name.

import os
import json
import re
from pymxs import runtime as rt
import collections

try:
    from utils.paths import get_project_root
except ImportError:
    get_project_root = lambda: ""

class GroupController:
    def __init__(self):
        self.node = None
        self.groups_data = {}

    def set_current_node(self, node):
        if node and rt.isValidNode(node):
            if self.node != node:
                self.node = node
                self.load_groups()
        else:
            self.node = None
            self.groups_data = {}

    def _get_group_file_path(self):
        if not self.node or not rt.isValidNode(self.node): return None
        project_root = get_project_root()
        if not project_root: return None
        
        cache_dir = os.path.join(project_root, "data", "skin_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # ⭐️ [Fix] Removed MaxFileName. Use Node Name only.
        node_name_safe = re.sub(r'[\\/*?:"<>|]', "_", self.node.name).replace(" ", "_")
        return os.path.join(cache_dir, f"{node_name_safe}.ohchaGroups")

    def load_groups(self):
        filepath = self._get_group_file_path()
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.groups_data = json.load(f)
                    return
            except Exception:
                pass
        self.groups_data = {"groups": {}}

    def save_groups(self):
        filepath = self._get_group_file_path()
        if not filepath: return False
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.groups_data, f, indent=4)
            return True
        except Exception:
            return False

    def add_group(self, name: str) -> bool:
        if name in self.groups_data.get("groups", {}):
            return False
        if "groups" not in self.groups_data:
            self.groups_data["groups"] = {}
        self.groups_data["groups"][name] = []
        return self.save_groups()

    def remove_group(self, name: str) -> bool:
        if name in self.groups_data.get("groups", {}):
            del self.groups_data["groups"][name]
            return self.save_groups()
        return False
        
    def rename_group(self, old_name: str, new_name: str) -> bool:
        groups = self.groups_data.get("groups", {})
        if old_name in groups and new_name not in groups and new_name:
            groups[new_name] = groups.pop(old_name)
            return self.save_groups()
        return False

    def assign_bones_to_group(self, group_name: str, bone_ids: list[int]):
        groups = self.groups_data.get("groups", {})
        if group_name not in groups:
            return False
            
        for name, ids in groups.items():
            if name != group_name:
                groups[name] = [bone_id for bone_id in ids if bone_id not in bone_ids]
        
        current_ids = set(groups[group_name])
        current_ids.update(bone_ids)
        groups[group_name] = sorted(list(current_ids))
        
        return self.save_groups()

    def get_groups_for_ui(self, all_bones: list[dict]) -> dict:
        groups_ui_data = {}
        bone_map = {b['id']: b for b in all_bones}
        assigned_bone_ids = set()

        for name in self.groups_data.get("groups", {}).keys():
            groups_ui_data[name] = []

        for name, ids in self.groups_data.get("groups", {}).items():
            for bone_id in ids:
                if bone_id in bone_map:
                    groups_ui_data[name].append(bone_map[bone_id])
                    assigned_bone_ids.add(bone_id)

        ungrouped_bones = [b for b in all_bones if b['id'] not in assigned_bone_ids]
        if ungrouped_bones:
            groups_ui_data["[Ungrouped]"] = ungrouped_bones
            
        return groups_ui_data


group_controller_instance = GroupController()