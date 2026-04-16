"""
input.py — 输入处理模块
职责：
  - 键盘事件处理（handle_menu_keys / handle_play_keys）
  - 鼠标事件处理（handle_mouse / handle_shop_mouse）
  - 药品快捷栏点击（_try_potion_at）

外部依赖：
  - game 主对象（通过参数传入）
  - data.py（ITEMS, SKILLS, WORLD）
  - equipment.py（EquipmentManager）
  - combat.py（CombatManager）

不包含：
  - 任何渲染代码（render.py 负责）
"""
import math
import pygame
from config import *
from audio import get_audio
try:
    audio = get_audio()
except Exception:
    audio = None


class InputHandler:
    """输入处理（替代原全局 handle_* 函数）"""

    @staticmethod
    def handle_menu_keys(k, game):
        """菜单界面按键"""
        if k.type == pygame.KEYDOWN:
            if k.key in (pygame.K_UP, pygame.K_w):
                game.midx = (game.midx - 1) % 3
            elif k.key in (pygame.K_DOWN, pygame.K_s):
                game.midx = (game.midx + 1) % 3
            elif k.key in (pygame.K_RETURN, pygame.K_SPACE):
                from data import CLASS_D
                cls = list(CLASS_D.keys())[game.midx]
                game.new_game(cls)

    @staticmethod
    def handle_menu_mouse(pos, game):
        """菜单界面鼠标点击 - 职业按钮"""
        from data import CLASS_D
        mx, my = pos
        cl = list(CLASS_D.keys())
        cx = 640 - 3 * 170 // 2  # SCREEN_W // 2 - 3 * 170 // 2 = 640
        cy = 240
        bw, bh = 155, 170
        for i in range(len(cl)):
            bx = cx + i * 170
            by = cy
            if bx <= mx <= bx + bw and by <= my <= by + bh:
                if game.midx != i:
                    game.midx = i
                else:
                    cls = cl[i]
                    game.new_game(cls)
                break

    @staticmethod
    def handle_play_keys(k, game):
        """游戏进行中按键"""
        p = game.p
        if k.type == pygame.KEYDOWN:
            # 技能释放
            if pygame.K_1 <= k.key <= pygame.K_9:
                idx = k.key - pygame.K_1
                if idx < len(p["qb"]):
                    skn = p["qb"][idx]
                    if skn not in p["sk"]:
                        return
                    from data import SKILLS
                    sk_shape = SKILLS.get(skn, {}).get("shape", "single")
                    # 只有单体（single）需要目标；其他形状可空放
                    needs_target = (sk_shape == "single")
                    alive = [e for e in game.enemies if not e.get("dead")]
                    if needs_target and not alive:
                        game._ft(p["x"], p["y"] - 30, "没有目标!", C_RED)
                        return
                    if game.cds.get(skn, 0) > 0:
                        game._ft(p["x"], p["y"] - 30, "冷却中!", C_RED)
                        return
                    # 优先使用当前锁定的敌人
                    tgt = getattr(game, '_target_enemy', None)
                    if needs_target and alive:
                        if tgt and not tgt.get("dead") and tgt in alive:
                            # 有锁定目标 → 更新面向方向指向目标
                            dx = tgt["x"] - p["x"]; dy = tgt["y"] - p["y"]
                            rd = math.hypot(dx, dy) or 1
                            game.facing_x = dx / rd; game.facing_y = dy / rd
                            target = tgt
                        else:
                            target = None
                    else:
                        target = None
                    # 普通攻击距离检测（单体必须范围内）
                    if sk_shape == "single" and target:
                        dist = math.hypot(target["x"] - p["x"], target["y"] - p["y"])
                        rng  = SKILLS.get(skn, {}).get("range", 60)
                        if dist > rng:
                            game._ft(p["x"], p["y"] - 30, "距离太远!", C_GOLD)
                            target = None
                    game.player_atk(target, skn)
            elif k.key == pygame.K_a:
                game.auto = not game.auto
                game._add_log(f"自动:{'开' if game.auto else '关'}", C_PURPLE)
            elif k.key == pygame.K_ESCAPE:
                if game.potion_sel is not None:
                    game.potion_sel = None
                else:
                    game.s = "save"
                    game._save_sel = 0

            # F5 快速存档
            elif k.key == pygame.K_F5:
                from save import SaveManager
                msg = SaveManager.save_game(game)
                game._add_log(msg)

            # F9 快速读档（读取最新存档）
            elif k.key == pygame.K_F9:
                from save import SaveManager
                data = SaveManager.load_save_file(0)
                if data:
                    msg = SaveManager.apply_save(game, data)
                    game._add_log(msg)
                else:
                    game._add_log("无存档可读！")

    @staticmethod
    def handle_mouse(pos, game):
        """游戏进行中鼠标点击"""
        mx, my = pos
        p = game.p

        # ── 一键挂机按钮 ─────────────────────────────────
        if game.s == "playing":
            af_btn = getattr(game, '_autofarm_btn', None)
            if af_btn and len(af_btn) == 4:
                bx, by, bw, bh = af_btn
                if bx <= mx <= bx+bw and by <= my <= by+bh:
                    game.auto_farm = not game.auto_farm
                    game._add_log(f"一键挂机：{'开' if game.auto_farm else '关'}")
                    return

        # ── 药品快捷栏（3格小槽，44×44，qy与技能栏对齐）─
        if game.s in ("playing", "shop"):
            qy = SCREEN_H - 290
            potion_ids = {"elixir_s", "elixir_mp", "elixir_b", "elixir_mp_b", "gold_elixir"}
            avail = [iv for iv in p.get("inv", []) if iv["id"] in potion_ids and iv["n"] > 0]
            # 检测自动买药切换按钮
            buy_rect = getattr(game, '_buy_btn_rect', None)
            if buy_rect and len(buy_rect) == 4:
                bx, by, bw, bh = buy_rect
                if bx <= mx <= bx + bw and by <= my <= by + bh:
                    game.potion_sel = None
                    if game.potion_buy_qty_sel:
                        # 弹窗已开 → 关闭弹窗
                        game.potion_buy_qty_sel = False
                        return
                    # 弹窗关闭 → 打开数量选择弹窗（不激活开关，等待选好数量再激活）
                    game.potion_buy_qty_sel = True
                    return
            # 买药数量弹窗已开：先处理弹窗点击
            if game.potion_buy_qty_sel:
                pop_rect = getattr(game, '_buy_qty_pop_rect', None)
                if pop_rect:
                    px, py2, pw, ph = pop_rect
                    if px <= mx <= px + pw and py2 <= my <= py2 + ph:
                        qty_choices = [10, 20, 30, 50, 99]
                        for idx, qty in enumerate(qty_choices):
                            iy2 = py2 + 32 + idx * 36
                            if px + 8 <= mx <= px + pw - 8 and iy2 <= my <= iy2 + 28:
                                game.potion_buy_qty = qty
                                game.potion_buy_qty_sel = False
                                game.potion_buy = True
                                from shop import ShopManager
                                ShopManager.auto_buy(p, game)
                                return
                        # 点在弹窗内但没点到选项 → 关闭弹窗
                        game.potion_buy_qty_sel = False
                        return
                    else:
                        # 点在弹窗外 → 关闭弹窗
                        game.potion_buy_qty_sel = False
                        return
            # 检测自动/手动切换按钮
            auto_rect = getattr(game, '_auto_btn_rect', None)
            if auto_rect and len(auto_rect) == 4:
                bx, by, bw, bh = auto_rect
                if bx <= mx <= bx + bw and by <= my <= by + bh:
                    game.potion_auto = not game.potion_auto
                    game.potion_sel = None
                    return
            # 如果弹出菜单已打开，先处理菜单点击
            if game.potion_sel is not None:
                slot_idx = game.potion_sel
                sx = 150 + slot_idx * 48
                sy_pop = qy + 50
                rows = len(avail) + 1
                pop_h = rows * 36 + 8
                pop_w = 200
                # 点在菜单内 → 根据实际点击坐标计算选哪行
                if sx <= mx <= sx + pop_w and sy_pop <= my <= sy_pop + pop_h:
                    clicked_row = (my - sy_pop - 22) // 36
                    if 0 <= clicked_row < len(avail):
                        from shop import ShopManager
                        ShopManager.assign_potion(p, slot_idx, avail[clicked_row]["id"])
                    game.potion_sel = None
                    return
                else:
                    # 点在菜单外，关闭
                    game.potion_sel = None
                    return
            # 未开菜单：检测左键点击槽位
            for i, slot in enumerate(p["potion_slots"]):
                px2 = 150 + i * 48
                if px2 <= mx <= px2 + 44 and qy <= my <= qy + 44:
                    if slot.get("id") and slot.get("n", 0) > 0:
                        # 有药：直接使用
                        from shop import ShopManager
                        ShopManager.use_potion(p, i, game.floats, game)
                    else:
                        # 空槽：打开选药菜单
                        game.potion_sel = i
                    return

        if game.s == "playing":
            # 底部标签切换
            if my >= SCREEN_H - 200:
                tabs = ["技能", "背包", "装备", "铸造", "宠物", "坐骑", "商店", "世界"]
                tab_start = SCREEN_W - 20 - 76
                for i, tab in enumerate(tabs):
                    tx = tab_start - i * 80 + 38  # 文字中心x
                    tx_half = 20  # 文字半径（点击敏感区域）
                    ty_top = SCREEN_H - 200; ty_bot = SCREEN_H - 164  # 文字行高度
                    if tx - tx_half <= mx <= tx + tx_half and ty_top <= my <= ty_bot:
                        game.tab = tab
                        if game.tab == "商店":
                            if not getattr(game, 'shop_cat', None):
                                game.shop_cat = "装备"
                            game.s = "shop"
                        return
                # 没有点到标签 → 尝试底部面板（装备/宠物/坐骑/铸造标签）
                if game.tab in ("装备", "宠物", "坐骑", "铸造"):
                    InputHandler._handle_bottom_panel(mx, my, game)
                # 世界标签的地图按钮在底部，不能提前返回
                if game.tab != "世界":
                    return

            # ── 左侧面板装备槽点击（点击已穿装备图标卸下）─────────────────────
            if game.panel_left and 8 <= mx <= 208 and 56 <= my <= SCREEN_H - 204:
                slot_x = 16; slot_y0 = 244; slot_s = 44; slot_gap = 4
                for i_off, sid in enumerate(("weapon", "armor", "acc")):
                    sy_slot = slot_y0 + i_off * (slot_s + slot_gap)
                    hit = (p["eq"][sid] and slot_x <= mx <= slot_x + slot_s and sy_slot <= my <= sy_slot + slot_s)
                    if hit:
                        from equipment import EquipmentManager
                        EquipmentManager.unequip_to_list(p, sid, game)
                        return

            # 菜单按钮
            if 900 <= mx <= 980 and 12 <= my <= 38:
                game.dlg = {"title": "菜单", "body": ""}
                game.dlg_btns = ["存档列表", "存档", "作弊"]
                game.dlg_i = 0
                game.s = "dialog"
                game.dlg_mode = None
                def cb(idx):
                    from save import SaveManager
                    if idx == 0:
                        # 存档列表（按职业分组）
                        grouped = SaveManager.list_saves()
                        # 同时保存扁平列表（带原始slot索引）供点击检测用
                        flat = []
                        for cls, entries in grouped.items():
                            for sv in entries:
                                flat.append(sv)
                        game.dlg = {"title": "存档列表", "body": ""}
                        game.dlg_btns = []
                        game.dlg_mode = "saves"
                        game.dlg_data = grouped
                        game.dlg_data_flat = flat
                        game.dlg_i = 0
                    elif idx == 1:
                        # 存档（立即存档，新文件不覆盖）
                        game._pending_save = True
                        game._add_log("已存档", C_GOLD)
                    else:
                        # 作弊面板
                        game.dlg = {"title": "作弊面板", "body": ""}
                        game.dlg_btns = []
                        game.dlg_mode = "cheat"
                        game.dlg_i = 0
                game.dlg_cb = cb
                return

            # 自动战斗按钮
            if 780 <= mx <= 870 and 12 <= my <= 38:
                game.auto = not game.auto
                game._add_log(f"自动:{'开' if game.auto else '关'}", C_PURPLE)
                return

            # 左侧面板折叠切换
            if 8 <= mx <= 38 and 12 <= my <= 38:
                game.panel_left = not game.panel_left
                return

            # 宠物标签
            if game.tab == "宠物":
                sy = SCREEN_H - 160
                LOG = "C:\\Users\\Administrator\\Desktop\\bug_log.txt"
                with open(LOG, "a") as f:
                    f.write(f"[DBG pet_tab] sy={sy} mx={mx} my={my} n={len(p['pets'])}\n")
                # 休息按钮（宠物休息）
                ux = 20; uy = sy + 8; uw = 96; uh = 22
                if p["pet"] and ux <= mx <= ux + uw and uy <= my <= uy + uh:
                    p["pet"] = None
                    game._recalc()
                    game._add_log("宠物休息中", C_TEXT)
                    return
                # 已有宠物列表
                for i, pt in enumerate(p["pets"]):
                    iy2 = sy + 8 + i * 40
                    bx = 256; by2 = iy2 + 6; bw = 52; bh = 26
                    own = p["pet"] and p["pet"]["id"] == pt["id"]
                    with open(LOG, "a") as f:
                        f.write(f"[DBG pet_btn] i={i} iy2={iy2} bx={bx} by2={by2} bh={bh} own={own} hit={bx <= mx <= bx+bw and by2 <= my <= by2+bh}\n")
                    if bx <= mx <= bx + bw and by2 <= my <= by2 + bh:
                        if own:
                            p["pet"] = None
                            game._recalc()
                            game._add_log("宠物休息中", C_TEXT)
                        else:
                            p["pet"] = dict(pt)
                            game._recalc()
                            qpct = {"凡兽":0.10,"珍兽":0.20,"灵兽":0.30,"仙兽":0.40,"神灵":0.50}
                            pct = qpct.get(pt["q"], 0)
                            game._add_log(f"{pt['name']}出战！+{int(pct*100)}%属性", C_GOLD)
                        return

            # 坐骑标签
            if game.tab == "坐骑":
                LOG = "C:\\Users\\Administrator\\Desktop\\bug_log.txt"
                with open(LOG, "a") as f:
                    f.write(f"[DBG mount_tab] sy={sy} mx={mx} my={my} n={len(p['mounts'])} mount_id={p['mount'].get('id') if p['mount'] else None}\n")
                sy = SCREEN_H - 160
                ux = 20; uy = sy + 8; uw = 96; uh = 22
                if p["mount"] and ux <= mx <= ux + uw and uy <= my <= uy + uh:
                    with open(LOG, "a") as f:
                        f.write(f"[DBG mount] 休息按钮命中 mount=None\n")
                    p["mount"] = None
                    game._recalc()
                    game._add_log("已卸下坐骑", C_TEXT)
                    return
                for i, mt in enumerate(p["mounts"]):
                    iy2 = sy + 8 + i * 40
                    bx = 256; by2 = iy2 + 6; bw2 = 52; bh = 26
                    own = p["mount"] and p["mount"]["id"] == mt["id"]
                    hit = (bx <= mx <= bx + bw2 and by2 <= my <= by2 + bh)
                    with open(LOG, "a") as f:
                        f.write(f"[DBG mount_btn] i={i} iy2={iy2} bx={bx} by2={by2} own={own} hit={hit} mx={mx} my={my}\n")
                    if hit:
                        if own:
                            with open(LOG, "a") as f:
                                f.write(f"[DBG mount] 乘骑按钮命中 卸下 own={own}\n")
                            p["mount"] = None
                            game._recalc()
                            game._add_log("已卸下坐骑", C_TEXT)
                        else:
                            with open(LOG, "a") as f:
                                f.write(f"[DBG mount] 乘骑按钮命中 装上 own={own}\n")
                            p["mount"] = dict(mt)
                            game._recalc()
                            game._add_log(f"骑上坐骑：{mt['name']}！速度 {p['spd']}", C_GOLD)
                        return

            # 背包标签
            if game.tab == "背包":
                sy = SCREEN_H - 160
                from data import ITEMS
                for i in range(30):
                    col_n = i % 8
                    row_n = i // 8
                    ix = 16 + col_n * 50
                    iy = sy + 45 + row_n * 50
                    if ix <= mx <= ix + 46 and iy <= my <= iy + 46:
                        if i < len(p["inv"]):
                            inv = p["inv"][i]
                            it = ITEMS.get(inv["id"], {})
                            if it.get("tp") == "cons":
                                from inventory import InventoryManager
                                InventoryManager.use_item(p, inv["id"], game)
                            elif it.get("tp") in ("weapon", "armor", "acc"):
                                from equipment import EquipmentManager
                                EquipmentManager.equip(p, inv["id"], game)
                        return

            # 装备标签（仅处理右侧物品网格 x >= 100，左侧装备槽由主 handler 处理）
            if game.tab == "装备" and mx >= 100:
                sy = SCREEN_H - 160
                cols = 6; item_w = 140; item_h = 50; gap = 6; iy = sy + 10
                from data import ITEMS
                for i, eq_item in enumerate(p["equips"]):
                    col_n = i % cols; row_n = i // cols
                    ix = 20 + col_n * (item_w + gap)
                    iy2 = iy + row_n * (item_h + gap)
                    bx2 = ix + 88; by2 = iy2 + 18; bw2 = 46; bh2 = 22
                    if bx2 <= mx <= bx2 + bw2 and by2 <= my <= by2 + bh2:
                        from equipment import EquipmentManager
                        EquipmentManager.equip_by_idx(p, i, game)
                        return

            # 铸造标签（仅处理右侧物品网格 x >= 100）
            if game.tab == "铸造" and mx >= 100:
                sy = SCREEN_H - 160
                cols = 6; item_w = 140; item_h = 50; gap = 6
                from data import ITEMS
                for i, eq_item in enumerate(p["equips"]):
                    col_n = i % cols; row_n = i // cols
                    ix = 20 + col_n * (item_w + gap)
                    iy = sy + row_n * (item_h + gap)
                    bx2 = ix + 88; by2 = iy + 18; bw2 = 46; bh2 = 22
                    if bx2 <= mx <= bx2 + bw2 and by2 <= my <= by2 + bh2:
                        from equipment import EquipmentManager
                        EquipmentManager.equip_by_idx(p, i, game)
                        return
                # 已穿装备强化按钮
                sy2 = sy + 4
                for sid, snm, icn in [("weapon", "武 器", "⚔"), ("armor", "护 甲", "🛡"), ("acc", "饰 品", "💍")]:
                    e = p["eq"][sid]
                    if not e:
                        continue
                    bx3 = 218; by3 = sy2 + 6; bw3 = 82; bh3 = 24
                    if bx3 <= mx <= bx3 + bw3 and by3 <= my <= by3 + bh3:
                        game.dlg = {"title": "强化", "body": f"强化 {e['name']}\n\n1.普通 2.保级(需固魂石)"}
                        game.dlg_btns = ["普通强化", "保级强化"]
                        game.dlg_i = 0
                        game.s = "dialog"
                        def mk_cb(sid):
                            def cb(idx):
                                from equipment import EquipmentManager
                                EquipmentManager.enhance(p, sid, idx == 1, game)
                                game.s = "playing"
                            return cb
                        game.dlg_cb = mk_cb(sid)
                        return
                    sy2 += 40

            # 技能标签
            if game.tab == "技能" and my >= SCREEN_H - 160:
                from data import SKILLS
                all_sk = [nm for nm in SKILLS if SKILLS[nm].get("cls") in ("all", p["cls"])]
                cols = 9
                for i, nm in enumerate(all_sk):
                    col_n = i % cols
                    row_n = i // cols
                    sx2 = 16 + col_n * 58
                    sy2 = SCREEN_H - 160 + row_n * 58
                    if sx2 <= mx <= sx2 + 54 and sy2 <= my <= sy2 + 54:
                        if nm not in p["sk"]:
                            return
                        if game.cds.get(nm, 0) > 0:
                            game._ft(p["x"], p["y"] - 30, "冷却中!", C_RED)
                            return
                        sk_t = SKILLS.get(nm, {}).get("t", "atk")
                        needs_enemy = sk_t in ("atk", "debuf")
                        alive = [e for e in game.enemies if not e.get("dead")]
                        if needs_enemy and not alive:
                            game._ft(p["x"], p["y"] - 30, "没有目标!", C_RED)
                            return
                        # heal/buff/shield 类型不需要敌人
                        target = alive[0] if (needs_enemy and alive) else None
                        game.player_atk(target, nm)
                        return

            # ── 世界标签：地图进入按钮 ──
            if game.tab == "世界":
                rects = getattr(game, '_world_btn_rects', [])
                for mid, rx, ry, rw, rh, bx, by2, bw, bh in rects:
                    if bx <= mx <= bx + bw and by2 <= my <= by2 + bh:
                        if mid != getattr(game, 'map_id', None):
                            game.load_map(mid)
                            game._add_log(f"切换到：{mid}", C_GOLD)
                        return

            # 点击敌人
            for e in game.enemies:
                if e.get("dead"):
                    continue
                if abs(mx - e["x"]) < 30 and abs(my - e["y"]) < 30:
                    if e["lv"] > p["lv"] + 5:
                        game._ft(e["x"], e["y"] - 30, "等级差距太大!", C_RED)
                        return
                    # 设为目标、开始走向怪物边缘（inCombat等走到距离auto-attack时再触发）
                    game._target_enemy = e
                    game._patk_cd = 0
                    # 计算移动目标：怪物边缘20px处（不重叠）
                    dx2 = p["x"] - e["x"]; dy2 = p["y"] - e["y"]
                    d2 = math.hypot(dx2, dy2)
                    if d2 > 20:
                        p["move_to"] = (e["x"] + dx2 / d2 * 20, e["y"] + dy2 / d2 * 20)
                    else:
                        p["move_to"] = None
                    return

            # 点击移动
            if mx > 216 and mx < SCREEN_W - 228 and my > 56 and my < SCREEN_H - 208:
                p["move_to"] = (mx, my)

    @staticmethod
    def handle_shop_mouse(pos, game):
        """商店界面鼠标点击"""
        mx, my = pos
        p = game.p
        pw, ph = 780, 520
        px = (SCREEN_W - pw) // 2
        py = (SCREEN_H - ph) // 2

        # ── 世界标签：关商店切到世界，让 handle_mouse 处理地图按钮 ──
        sy_tab = SCREEN_H - 160
        if sy_tab <= my <= SCREEN_H:
            tabs = ["技能", "背包", "装备", "铸造", "宠物", "坐骑", "商店", "世界"]
            tab_w = 76
            for i, tab in enumerate(tabs):
                tx = 20 + i * (tab_w + 4)
                if tx <= mx <= tx + tab_w:
                    if tab == "世界":
                        # 关闭商店，进入世界标签（地图按钮将由 handle_mouse 处理）
                        game.s = "playing"
                        game.tab = "世界"
                        return
                    else:
                        game.tab = tab
                        return

        # 关闭按钮
        close_x = px + pw - 45
        if close_x <= mx <= close_x + 35 and py + 12 <= my <= py + 38:
            game.shop_qty_item = None
            game.shop_qty_input = ""
            game.s = "playing"
            return

        # 分类标签
        cat_y = py + 52
        cats = list(getattr(game, 'shop_items', {}).keys())
        cat_start_x = px + 20
        cat_w = 90
        for i, cat in enumerate(cats):
            cx = cat_start_x + i * (cat_w + 8)
            if cx <= mx <= cx + cat_w and cat_y <= my <= cat_y + 32:
                game.shop_cat = cat
                return

        # 商品列表（坐标与 render.py 同步）
        if my >= py + 90 and my <= py + ph - 60:
            cat = getattr(game, 'shop_cat', '装备')
            from data import SHOP_ITEMS
            items = SHOP_ITEMS.get(cat, [])
            if cat == "技能书":
                items = [it for it in items if it.get("cls") == p.get("cls")]
            cols = 4
            item_w = 170
            item_h = 80
            gap_x = 8
            gap_y = 8
            grid_x = px + 16
            grid_y = py + 108

            for i, item in enumerate(items):
                col_n = i % cols
                row_n = i // cols
                ix = grid_x + col_n * (item_w + gap_x)
                iy = grid_y + row_n * (item_h + gap_y)

                if ix + item_w > px + pw:
                    break
                if ix <= mx <= ix + item_w and iy <= my <= iy + item_h:
                    from data import ITEMS
                    iid = item.get("id", "")
                    potion_ids = {"elixir_s", "elixir_mp", "elixir_b", "elixir_mp_b", "gold_elixir"}
                    # 消耗品：进入数量输入模式
                    if iid in potion_ids:
                        if game.shop_qty_item is None:
                            game.shop_qty_item = item
                            game.shop_qty_input = ""
                        else:
                            # 已有数量输入在进行，取消并重新开始
                            game.shop_qty_item = item
                            game.shop_qty_input = ""
                        return
                    # 非消耗品：直接购买
                    from shop import ShopManager
                    ShopManager.buy_item(p, item, game, audio, game)
                    return

        # 底部面板（宠物/坐骑标签在商店界面下仍然可交互）
        if game.tab in ("宠物", "坐骑", "装备", "铸造") and my >= SCREEN_H - 200:
            InputHandler._handle_bottom_panel(mx, my, game)

    @staticmethod
    def handle_save_keys(e, game):
        """存档界面键盘处理"""
        if e.type == pygame.KEYDOWN:
            k = e.key
            if k == pygame.K_ESCAPE or k == pygame.K_X:
                game.s = "playing"
            elif k in (pygame.K_UP, pygame.K_w):
                game._save_sel = max(0, getattr(game, "_save_sel", 0) - 1)
            elif k in (pygame.K_DOWN, pygame.K_s):
                from save import SaveManager
                saves = SaveManager.list_saves()
                game._save_sel = min(len(saves)-1, getattr(game, "_save_sel", 0) + 1)
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                from save import SaveManager
                msg = SaveManager.save_game(game, getattr(game, "_save_sel", 0))
                game._add_log(msg)

    @staticmethod
    def handle_save_mouse(pos, game):
        """存档界面鼠标处理"""
        mx, my = pos
        from save import SaveManager
        # 关闭X
        cb = getattr(game, "_close_btn", None)
        if cb and len(cb) == 4:
            if cb[0] <= mx <= cb[0]+cb[2] and cb[1] <= my <= cb[1]+cb[3]:
                game.s = "playing"
                return
        # 存档列表选择
        lr = getattr(game, "_save_list_range", None)
        if lr and len(lr) == 4:
            lx, ly, lw, lh = lr
            if lx <= mx <= lx+lw and ly <= my <= ly+lh:
                row = (my - ly) // 56
                saves = SaveManager.list_saves()
                if row < len(saves):
                    game._save_sel = row
                    return
        # 存档按钮
        sb = getattr(game, "_save_btn", None)
        if sb and len(sb) == 4:
            if sb[0] <= mx <= sb[0]+sb[2] and sb[1] <= my <= sb[1]+sb[3]:
                msg = SaveManager.save_game(game, getattr(game, "_save_sel", 0))
                game._add_log(msg)
                return
        # 读档按钮
        lb = getattr(game, "_load_btn", None)
        if lb and len(lb) == 4:
            if lb[0] <= mx <= lb[0]+lb[2] and lb[1] <= my <= lb[1]+lb[3]:
                data = SaveManager.load_save_file(getattr(game, "_save_sel", 0))
                if data:
                    msg = SaveManager.apply_save(game, data)
                    game._add_log(msg)
                else:
                    game._add_log("无存档可读！")
                return
        # 继续按钮
        rb = getattr(game, "_resume_btn", None)
        if rb and len(rb) == 4:
            if rb[0] <= mx <= rb[0]+rb[2] and rb[1] <= my <= rb[1]+rb[3]:
                game.s = "playing"
                return

    @staticmethod
    def _handle_bottom_panel(mx, my, game):
        """处理底部面板的宠物/坐骑/装备标签点击"""
        sy = SCREEN_H - 160
        p = game.p

        if game.tab == "宠物":
            ux = 20; uy = sy + 8; uw = 96; uh = 22
            if p["pet"] and ux <= mx <= ux + uw and uy <= my <= uy + uh:
                p["pet"] = None
                game._recalc()
                game._add_log("宠物休息中", C_TEXT)
                return
            for i, pt in enumerate(p["pets"]):
                iy2 = sy + 8 + i * 40
                bx = 256; by2 = iy2 + 6; bw = 52; bh = 26
                if bx <= mx <= bx + bw and by2 <= my <= by2 + bh:
                    if p["pet"] and p["pet"]["id"] == pt["id"]:
                        p["pet"] = None
                        game._recalc()
                        game._add_log("宠物休息中", C_TEXT)
                    else:
                        p["pet"] = dict(pt)
                        game._recalc()
                        qpct = {"凡兽":0.10,"珍兽":0.20,"灵兽":0.30,"仙兽":0.40,"神灵":0.50}
                        pct = qpct.get(pt["q"], 0)
                        game._add_log(f"{pt['name']}出战！+{int(pct*100)}%属性", C_GOLD)
                    return

        elif game.tab == "坐骑":
            LOG = "C:\\Users\\Administrator\\Desktop\\bug_log.txt"
            with open(LOG, "a") as f:
                f.write(f"[DBG _handle mount] mx={mx} my={my} n={len(p['mounts'])} mount_id={p['mount'].get('id') if p['mount'] else None}\n")
            # 休息按钮（卸下坐骑）
            ux = 20; uy = sy + 8; uw = 96; uh = 22
            if p["mount"] and ux <= mx <= ux + uw and uy <= my <= uy + uh:
                with open(LOG, "a") as f:
                    f.write(f"[DBG _handle mount] 休息按钮命中\n")
                p["mount"] = None
                game._recalc()
                game._add_log("已卸下坐骑", C_TEXT)
                return
            # 已有坐骑列表
            for i, mt in enumerate(p["mounts"]):
                iy2 = sy + 8 + i * 40
                bx = 256; by2 = iy2 + 6; bw2 = 52; bh = 26
                own = p["mount"] and p["mount"]["id"] == mt["id"]
                hit = (bx <= mx <= bx + bw2 and by2 <= my <= by2 + bh)
                with open(LOG, "a") as f:
                    f.write(f"[DBG _handle mount_btn] i={i} bx={bx} by2={by2} own={own} hit={hit}\n")
                if hit:
                    if own:
                        with open(LOG, "a") as f:
                            f.write(f"[DBG _handle mount] 乘骑按钮命中 卸下 own={own}\n")
                        p["mount"] = None
                        game._recalc()
                        game._add_log("已卸下坐骑", C_TEXT)
                    else:
                        with open(LOG, "a") as f:
                            f.write(f"[DBG _handle mount] 乘骑按钮命中 装上 own={own}\n")
                        p["mount"] = dict(mt)
                        game._recalc()
                        game._add_log(f"骑上坐骑：{mt['name']}！速度 {p['spd']}", C_GOLD)
                    return

        elif game.tab == "装备":
            sy = SCREEN_H - 160
            cols = 6; item_w = 140; item_h = 50; gap = 6; iy0 = sy + 10
            from data import ITEMS
            with open("C:\\Users\\Administrator\\Desktop\\bug_log.txt", "a") as f:
                f.write(f"[DBG bottom_panel] 装备 tab mx={mx} my={my} sy={sy} equips={len(p['equips'])}\n")
            for i, eq_item in enumerate(p["equips"]):
                col_n = i % cols; row_n = i // cols
                ix = 20 + col_n * (item_w + gap)
                iy2 = iy0 + row_n * (item_h + gap)
                bx2 = ix + 88; by2 = iy2 + 18; bw2 = 46; bh2 = 22
                if bx2 <= mx <= bx2 + bw2 and by2 <= my <= by2 + bh2:
                    with open("C:\\Users\\Administrator\\Desktop\\bug_log.txt", "a") as f:
                        f.write(f"[DBG bottom_panel] 穿上 CLICK! ix={ix} iy2={iy2} bx2={bx2} by2={by2}\n")
                    from equipment import EquipmentManager
                    EquipmentManager.equip_by_idx(p, i, game)
                    return
