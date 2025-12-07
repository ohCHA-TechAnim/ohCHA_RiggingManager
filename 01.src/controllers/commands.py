# ohCHA_RigManager/01/src/controllers/commands.py
# Description: [Refactored] Removed legacy 'Rigging Commands' (Biped/Weight).
#              Now focuses on Edit Mesh and Skinning commands only.

from pymxs import runtime as rt
import traceback

try:
    from controllers import edit_mesh_logic, skinning_logic
except ImportError as e:
    rt.print(f"❌ [Commands] 로직 임포트 실패: {e}")
    # IDE 경고 방지용 더미 클래스
    class edit_mesh_logic: pass
    class skinning_logic: pass

class BaseCommand:
    """커맨드 패턴 기본 클래스"""
    def __init__(self, node=None, name="Base Command"):
        self.node = node; self.name = name
        if node and not rt.isValidNode(node): rt.print(f"⚠️ [Command: {name}] Invalid Node.")

    def execute(self) -> bool:
        rt.print(f"--- Executing: {self.name} ---")
        try: return self._run()
        except Exception as e:
            rt.print(f"❌ [Error: {self.name}] {e}"); rt.print(traceback.format_exc()); return False

    def _run(self) -> bool: raise NotImplementedError

# --- Edit Mesh Commands ---
class FixScaleCommand(BaseCommand):
    def __init__(self, n): super().__init__(n, "Fix Scale")
    def _run(self): return edit_mesh_logic.apply_reset_xform(self.node)

class FixSkinCommand(BaseCommand):
    def __init__(self, n): super().__init__(n, "Fix Skin")
    def _run(self): return edit_mesh_logic.delete_skin_modifier(self.node)

class FixPivotCommand(BaseCommand):
    def __init__(self, n): super().__init__(n, "Fix Pivot")
    def _run(self): return edit_mesh_logic.move_pivot_to_origin(self.node)

class LockTransformCommand(BaseCommand):
    def __init__(self, n): super().__init__(n, "Lock Transforms")
    def _run(self): return edit_mesh_logic.lock_all_transforms(self.node)

class EnableInheritanceCommand(BaseCommand):
    def __init__(self, n): super().__init__(n, "Enable Inheritance")
    def _run(self): return edit_mesh_logic.enable_all_inheritance(self.node)

class AddSkinCommand(BaseCommand):
    def __init__(self, n, limit, dq):
        super().__init__(n, "Add Skin"); self.limit = limit; self.dq = dq
    def _run(self): return edit_mesh_logic.finalize_add_skin(self.node, self.limit, self.dq)

# --- Skinning Commands ---
class SkinHideCommand(BaseCommand):
    def __init__(self, type, uns): super().__init__(None, f"Hide {type}"); self.type = type; self.uns = uns
    def _run(self): skinning_logic.hide_selection(self.type, self.uns); return True

class SkinUnhideAllCommand(BaseCommand):
    def __init__(self): super().__init__(None, "Unhide All")
    def _run(self): skinning_logic.unhide_all(); return True