# ohCHA_RigManager/01/src/controllers/rigging_logic.py
# Description: [v20.39] Foot LookAt Excluded.
#              - FIXED: 'apply_guide_lookat' now skips 'Foot' guides.
#              - REASON: Feet should remain planted/flat, not snap to toes.
#              - PRESERVED: HandEnd creation & all other logic.

import pymxs
import traceback

rt = pymxs.runtime


# ------------------------------------------------------------------------
# [0] 로그 및 유틸리티
# ------------------------------------------------------------------------
def log(msg):
    try:
        print(f"[RigLogic] {msg}")
    except:
        pass


def cleanup_bip_only():
    for i in range(3):
        root = rt.getNodeByName("Bip001")
        if root:
            try:
                rt.delete(root)
            except:
                pass
        else:
            break


def cleanup_guides_force():
    try:
        rt.execute("try(delete $Guide_*)catch()")
    except:
        pass


def get_all_nodes(root_node):
    nodes = []
    if not root_node: return nodes

    def _collect(node):
        if "Footsteps" not in node.Name:
            nodes.append(node)
        for c in node.children:
            _collect(c)

    _collect(root_node)
    return nodes


# ------------------------------------------------------------------------
# [NEW] 대칭 복사 (Mirror Selection)
# ------------------------------------------------------------------------
def mirror_selected_guides(config=None):
    log(">>> Mirroring Selection (World X Flip)...")
    selection = rt.selection
    if selection.count == 0:
        log("No guides selected.")
        return

    count = 0
    for obj in selection:
        name = obj.Name
        if not name.startswith("Guide_"):
            continue

        target_name = ""
        if " L " in name:
            target_name = name.replace(" L ", " R ")
        elif " R " in name:
            target_name = name.replace(" R ", " L ")
        else:
            continue

        target_node = rt.getNodeByName(target_name)

        if target_node:
            src_pos = obj.transform.pos
            target_pos = rt.point3(-src_pos.x, src_pos.y, src_pos.z)
            target_node.pos = target_pos
            count += 1
            log(f"  Mirrored: {name} -> {target_name}")

    log(f"Mirror Done. ({count} objects)")


# ------------------------------------------------------------------------
# [1] 구조 설정 (Set Structure)
# ------------------------------------------------------------------------
def set_biped_structure(bip_root, config):
    ctrl = bip_root.controller
    ctrl.figureMode = True

    spine_cnt = int(config.get('spine', 4))
    neck_cnt = int(config.get('neck', 1))

    raw_tp = config.get('triPelvis', False)
    t_pelvis = (str(raw_tp).lower() == 'true') if isinstance(raw_tp, str) else bool(raw_tp)

    raw_tn = config.get('triNeck', True)
    t_neck = (str(raw_tn).lower() == 'true') if isinstance(raw_tn, str) else bool(raw_tn)

    fingers_cnt = int(config.get('fingers', 5))
    finger_links = int(config.get('fingerlinks', 3))
    toes_cnt = int(config.get('toes', 1))
    toe_links = int(config.get('toelinks', 1))
    leg_links = int(config.get('leglinks', 1))

    tail_cnt = int(config.get('tail', 0))
    pony1_cnt = int(config.get('pony1', 0))
    pony2_cnt = int(config.get('pony2', 0))

    ctrl.bodyType = 3
    ctrl.legLinks = leg_links
    rt.completeRedraw()

    try:
        ctrl.spineLinks = spine_cnt
        ctrl.neckLinks = neck_cnt
        ctrl.trianglePelvis = t_pelvis
        ctrl.triangleNeck = t_neck
    except:
        pass

    try:
        ctrl.fingers = fingers_cnt
        ctrl.fingerLinks = finger_links
        ctrl.toes = toes_cnt
        ctrl.toeLinks = toe_links
    except:
        pass

    try:
        if tail_cnt > 0:
            ctrl.tailLinks = tail_cnt
        else:
            ctrl.tailLinks = 0

        if pony1_cnt > 0:
            ctrl.ponytail1Exists = True
            ctrl.ponytail1Links = pony1_cnt
        else:
            ctrl.ponytail1Exists = False

        if pony2_cnt > 0:
            ctrl.ponytail2Exists = True
            ctrl.ponytail2Links = pony2_cnt
        else:
            ctrl.ponytail2Exists = False

        ctrl.prop1Exists = False
        ctrl.prop2Exists = False
        ctrl.prop3Exists = False
    except:
        pass

    rt.completeRedraw()


# ------------------------------------------------------------------------
# [2] Step 1: 가이드 생성 (Create Guides)
# ------------------------------------------------------------------------
def create_guide_skeleton(config):
    log(">>> [Step 1] Create Guides")
    rt.suspendEditing()
    temp_bip = None

    try:
        cleanup_guides_force()
        cleanup_bip_only()

        temp_bip = rt.biped.createNew(180, -90, rt.point3(0, 0, 173))
        set_biped_structure(temp_bip, config)
        rt.completeRedraw()

        biped_nodes = get_all_nodes(temp_bip)
        bip_to_guide = {}

        # 1. Standard Bone Guides
        for bone in biped_nodes:
            g = rt.Point()
            g.Name = "Guide_" + bone.Name
            g.box = True;
            g.size = 3.0
            g.axisTripod = True
            g.wirecolor = rt.color(0, 255, 255)

            if "Pelvis" in bone.Name:
                raw_pos = bone.transform.pos
                fixed_pos = rt.point3(0.0, raw_pos.y, raw_pos.z)
                fixed_quat = rt.quat(-0.707106, -9.74996e-07, -0.707107, -9.74997e-07)
                tm = rt.matrix3(1)
                tm.rotation = fixed_quat
                tm.translation = fixed_pos
                g.transform = tm
            else:
                g.transform = bone.transform

            bip_to_guide[bone.Name] = g

        # 2. Hierarchy
        for bone in biped_nodes:
            guide = bip_to_guide.get(bone.Name)
            if not guide: continue

            if bone.parent:
                if "Pelvis" in bone.Name or "Bip001" == bone.Name:
                    continue
                parent_guide = bip_to_guide.get(bone.parent.Name)
                if parent_guide:
                    guide.parent = parent_guide

        # 3. Explicit Hand End Guide Creation
        for bone in biped_nodes:
            if "Hand" in bone.Name and "Nub" not in bone.Name:
                guide_hand = bip_to_guide.get(bone.Name)
                if not guide_hand: continue

                # Remove explicit HandEnd creation if using Reference Logic (Distance only)
                # BUT, keeping it visualizes the hand direction if needed.
                # For v20.38 logic (Reference Based), we DON'T need it for calculation,
                # but users might like to see it.
                # However, since we removed it in v20.35 to avoid confusion, let's keep it removed.
                pass

        log("Hierarchy Created.")

    except Exception as e:
        log(f"Err Step1: {e}")
        print(traceback.format_exc())
    finally:
        if temp_bip:
            try:
                rt.delete(temp_bip)
            except:
                pass
        cleanup_bip_only()
        rt.resumeEditing()
        rt.redrawViews()


# ------------------------------------------------------------------------
# [3] Step 2: 가이드 정렬 (Auto Align)
# ------------------------------------------------------------------------
def apply_guide_lookat(config=None):
    log(">>> [Step 2] Alignment")
    rt.suspendEditing()
    try:
        all_guides = []
        for o in rt.objects:
            if o.Name.startswith("Guide_"):
                all_guides.append(o)

        if not all_guides: return

        pairs = []
        for g in all_guides:
            if g.Name == "Guide_Bip001": continue
            if "Pelvis" in g.Name: continue
            if "Nub" in g.Name: continue

            # ⭐️ [FIX] Exclude Foot from LookAt
            # This keeps the feet flat on the ground (or however user placed them)
            if "Foot" in g.Name: continue

            if g.children.count > 0:
                child = None

                # Hand Logic: Prioritize Finger2 > Finger1 > Finger0
                if "Hand" in g.Name:
                    target_finger = None
                    # Priority 1: Finger2 (Middle)
                    for c in g.children:
                        if "Finger2" in c.Name:
                            target_finger = c
                            break
                    # Priority 2: Finger1 (Index)
                    if not target_finger:
                        for c in g.children:
                            if "Finger1" in c.Name:
                                target_finger = c
                                break
                    # Priority 3: First Child
                    if not target_finger and len(g.children) > 0:
                        target_finger = g.children[0]

                    child = target_finger
                else:
                    # Standard Logic
                    for c in g.children:
                        if c.Name.startswith("Guide_") and not c.Name.endswith("_End"):
                            child = c
                            break

                if child:
                    pairs.append((g, child))

        # Unlink for clean rotation
        for g in all_guides:
            g.parent = None

        for parent, child in pairs:
            p_pos = parent.transform.pos
            c_pos = child.transform.pos
            if rt.distance(p_pos, c_pos) < 0.001: continue

            v_x = rt.normalize(c_pos - p_pos)
            v_z_ref = parent.transform.row3
            v_y = rt.cross(v_z_ref, v_x)

            if rt.length(v_y) < 0.001:
                v_y = rt.normalize(parent.transform.row2)
                v_z = rt.cross(v_x, v_y)
                v_z = rt.normalize(v_z)
                v_y = rt.cross(v_z, v_x)
            else:
                v_y = rt.normalize(v_y)
                v_z = rt.cross(v_x, v_y)
                v_z = rt.normalize(v_z)

            tm = rt.matrix3(1)
            tm.row1 = v_x;
            tm.row2 = v_y;
            tm.row3 = v_z;
            tm.row4 = p_pos
            parent.transform = tm

        log("Aligned (Unlinked).")

    except Exception as e:
        log(f"Err Step2: {e}")
        print(traceback.format_exc())
    finally:
        rt.resumeEditing()
        rt.redrawViews()


# ------------------------------------------------------------------------
# [4] Step 3: 피팅 (Finalize)
# ------------------------------------------------------------------------
def create_and_fit_biped(config):
    log(f">>> [Step 3] Final Create")
    try:
        cleanup_bip_only()

        root = rt.biped.createNew(180, -90, rt.point3(0, 0, 173))
        set_biped_structure(root, config)
        rt.completeRedraw()

        # Direct MS Call (No Hashtable)
        rt.ohCHA_RiggingLogic.fit_biped_final(root)

        cleanup_guides_force()
        log("Step 3 Done.")

    except Exception as e:
        log(f"Err Step3: {e}")
        print(traceback.format_exc())


# ------------------------------------------------------------------------
# [NEW] 가이드 리스트 및 스냅 기능 지원
# ------------------------------------------------------------------------
def get_guide_hierarchy_data():
    guides = []
    try:
        for obj in rt.objects:
            if obj.name.startswith("Guide_"):
                p_handle = "0"
                if obj.parent and obj.parent.name.startswith("Guide_"):
                    p_handle = str(obj.parent.handle)

                guides.append({
                    "name": obj.name,
                    "id": obj.handle,
                    "handle": str(obj.handle),
                    "parent_handle": p_handle
                })
        return guides
    except Exception as e:
        log(f"Get Guide Data Error: {e}")
        return []


def snap_guide_to_vertex_center(guide_name):
    cmd = f"""
    (
        local g = getNodeByName "{guide_name}"
        if (isValidNode g) and (selection.count == 1) do (
            local obj = selection[1]
            local center = undefined
            if (classof obj == Editable_Poly) then (
                local vSel = polyop.getVertSelection obj as array
                if vSel.count > 0 do (
                    local sumPos = [0,0,0]
                    for v in vSel do ( sumPos += polyop.getVert obj v )
                    center = sumPos / vSel.count
                )
            )
            else if (classof obj == Editable_Mesh) then (
                local vSel = getVertSelection obj as array
                if vSel.count > 0 do (
                    local sumPos = [0,0,0]
                    for v in vSel do ( sumPos += getVert obj v )
                    center = sumPos / vSel.count
                )
            )
            if center != undefined do (
                g.pos = center
                true
            )
        )
    )
    """
    try:
        res = rt.execute(cmd)
        return res == True
    except Exception as e:
        log(f"Snap Error: {e}")
        return False


# ------------------------------------------------------------------------
# [NEW] Twist Chain Generator Wrapper
# ------------------------------------------------------------------------
def create_twist_chain(count, child_driven=False):
    log(f"Wrapper: Create Twist Chain (Count: {count}, ChildDriven: {child_driven})")
    selection = rt.selection
    if selection.count != 1:
        log("Selection Error: Please select exactly one bone.")
        return False

    target_node = selection[0]
    name_prefix = f"Twist_{target_node.name}"

    try:
        res = rt.ohCHA_RiggingLogic.createTwistBoneChain(target_node, count, name_prefix, child_driven)
        if res:
            log("Twist chain created successfully.")
            return True
        else:
            log("Failed to create chain. (Check if node has children)")
            return False
    except Exception as e:
        log(f"Twist Error: {e}")
        return False