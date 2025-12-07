# ohCHA_RigManager/01/src/utils/config.py
# Description: [v0.91_Beta] CONFIG UPDATE.
#              - DEFAULT TAB: Changed to 'info'.
#              - ADDED: Tutorial & LinkedIn URLs.

from pymxs import runtime as rt

rt.print("✅ [Import Check] Loading utils.config...")

# Tool Version
VERSION = "0.90_Beta"

# Contact Info
CONTACT_EMAIL = "ckekdnlt@naver.com"
LINKEDIN_URL = "https://www.linkedin.com/in/ohcha"
TUTORIAL_URL = "https://discreet-colt-bfc.notion.site/ohCHA_RigManager-Guide-2c0a37c8c303803f9ae5daf1d9fbce9f?source=copy_link"

# UI Constants
SIDEBAR_EXPANDED_WIDTH = 170
SIDEBAR_COLLAPSED_WIDTH = 60

# Edit Mesh Logic Configuration
EDIT_MESH_CHECKS = [
    {
        "id": "non_uniform_scale",
        "label_key": "chk_scale_lbl",
        "info_key": "chk_scale_inf",
        "fix_key": "chk_scale_fix"
    },
    {
        "id": "existing_skin",
        "label_key": "chk_skin_lbl",
        "info_key": "chk_skin_inf",
        "fix_key": "chk_skin_fix"
    },
    {
        "id": "pivot_not_at_origin",
        "label_key": "chk_pivot_lbl",
        "info_key": "chk_pivot_inf",
        "fix_key": "chk_pivot_fix"
    },
]

# Main Tab Configuration
TABS_CONFIG = [
    {
        "id": "edit_mesh",
        "cls_path": "ui.tabs.edit_mesh_tab.EditMeshTab",
        "icon": "Mesh_Icon.png",
        "trans_key": "tab_edit_mesh"
    },
    {
        "id": "rigging",
        "cls_path": "ui.tabs.rigging_tab.RiggingTab",
        "icon": "Rigging_Icon.png",
        "trans_key": "tab_rigging"
    },
    {
        "id": "skinning",
        "cls_path": "ui.tabs.skinning_tab.SkinningTab",
        "icon": "Skinning_Icon.png",
        "trans_key": "tab_skinning"
    },
    {
        "id": "info",
        "cls_path": "ui.tabs.info_tab.InfoTab",
        "icon": "info_Icon.png",
        "trans_key": "tab_info"
    }
]

# Default Tab to open on launch
# Changed from 'rigging' to 'info'
DEFAULT_TAB_ID = "info"

rt.print("✅ [Import Check] FINISHED loading utils.config.")