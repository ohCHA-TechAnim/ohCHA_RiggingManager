# ohCHA_RigManager/01/src/controllers/naming_controller.py
import pymxs
from pymxs import runtime as rt


class NamingController:
    def __init__(self):
        self._current_objects = []  # List of dicts {handle, original_name, new_name}

    def load_selection(self):
        """Loads currently selected objects in Max."""
        self._current_objects = []
        for obj in rt.selection:
            if rt.isValidNode(obj):
                self._current_objects.append({
                    "handle": obj.handle,
                    "original_name": obj.name,
                    "new_name": obj.name
                })
        # Sort by name for UX
        self._current_objects.sort(key=lambda x: x["original_name"])
        return len(self._current_objects)

    def get_preview_data(self, params):
        """
        Calculates new names based on parameters.
        params: {
            prefix: str, suffix: str,
            base_name: str, use_base: bool,
            rem_first: int, rem_last: int,
            use_num: bool, start: int, step: int, padding: int
        }
        """
        if not self._current_objects: return []

        prefix = params.get("prefix", "")
        suffix = params.get("suffix", "")
        base_name = params.get("base_name", "")
        use_base = params.get("use_base", False)
        rem_first = params.get("rem_first", 0)
        rem_last = params.get("rem_last", 0)
        use_num = params.get("use_num", False)
        start_num = params.get("start", 1)
        step_num = params.get("step", 1)
        padding = params.get("padding", 3)

        result_list = []
        current_num = start_num

        for item in self._current_objects:
            orig = item["original_name"]

            # 1. Base Name Logic
            core_name = base_name if use_base and base_name else orig

            # 2. Remove Characters (only if not using base name)
            if not use_base:
                if rem_first > 0:
                    core_name = core_name[rem_first:]
                if rem_last > 0 and len(core_name) > rem_last:
                    core_name = core_name[:-rem_last]

            # 3. Numbering
            num_str = ""
            if use_num:
                # Python f-string padding: 0{padding}d
                fmt = f"{{:0{padding}d}}"
                num_str = fmt.format(current_num)
                current_num += step_num

            # 4. Combine
            final_name = f"{prefix}{core_name}{suffix}{num_str}"

            item["new_name"] = final_name
            result_list.append((orig, final_name))

        return result_list

    def apply_rename(self):
        """Calls MaxScript to apply changes."""
        if not self._current_objects: return False

        handles = []
        new_names = []

        for item in self._current_objects:
            handles.append(item["handle"])
            new_names.append(item["new_name"])

        # Call MS
        mxs_handles = rt.Array(*(int(h) for h in handles))
        mxs_names = rt.Array(*(str(n) for n in new_names))

        return rt.ohCHA_NamingLogic.renameObjects(mxs_handles, mxs_names)


naming_controller_instance = NamingController()