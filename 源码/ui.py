"""
ui.py — 用户界面绘制
职责：
  - 主HUD绘制（draw_ui：顶栏/左右面板/底部标签栏）
  - 底部标签面板绘制（draw_bot_tab）
  - 底部标签内容绘制（draw_bot_tab_content：技能/背包/装备/宠物/坐骑）
  - 菜单绘制（draw_menu）
  - 对话框绘制（draw_dlg）
  - 通用文字/血条绘制（txt / bar）

外部依赖：
  - config.py（SCREEN_W/SCREEN_H/FONT/颜色常量）
  - data.py（ITEMS/SKILLS/PETS/MOUNTS/QC）
  - player.py（PlayerManager.recalc）

不包含：
  - 主循环（main.py 负责调用）
  - 事件处理（input.py 负责）
"""
import pygame
import math
from config import *
from data import ITEMS, SKILLS, PETS, MOUNTS, QC, WORLD


# ═══════════ 通用绘制工具 ════════════════════════════════════════
def txt(s, t, pos, fn=None, c=C_TEXT, cent=False, max_w=0):
    """在屏幕上绘制文字，max_w>0时超过宽度截断"""
    f = fn or FONT
    if max_w > 0:
        # 截断过长的文字
        while t and f.size(t)[0] > max_w and len(t) > 1:
            t = t[:-2]
        if not t:
            t = ".."
    img = f.render(t, True, c)
    r = img.get_rect(center=pos) if cent else img.get_rect(topleft=pos)
    s.blit(img, r)


def bar(s, x, y, w, h, v, mv, fg=C_RED):
    """绘制血条/经验条"""
    pygame.draw.rect(s, (40, 30, 50), (x, y, w, h), border_radius=3)
    if v > 0:
        fw = max(2, int(w * min(1.0, v / mv)))
        pygame.draw.rect(s, fg, (x, y, fw, h), border_radius=3)


# ═══════════ 主 HUD ════════════════════════════════════════════
def draw_ui(s, game):
    """绘制主界面HUD"""
    p = game.p
    if not p:
        return
    mx, my = pygame.mouse.get_pos()
    r = p["realm"]

    # 顶栏背景
    pygame.draw.rect(s, (10, 8, 20), (0, 0, SCREEN_W, 50))
    pygame.draw.rect(s, (42, 34, 64), (0, 50, SCREEN_W, 1))

    # 角色名 + 境界 + 等级
    txt(s, p["name"], (16, 15), FONT_B, C_GOLD)
    pygame.draw.rect(s, (42, 26, 64), (160, 12, 100, 26), border_radius=13)
    txt(s, r["name"], (210, 25), FONT, C_REALM, cent=True)
    txt(s, f"Lv.{p['lv']}", (275, 15), FONT_B, C_TEXT)
    bar(s, 275, 33, 100, 5, p["exp"], p["expn"], fg=(74, 42, 128))

    # 血条 + 蓝条
    bar(s, 380, 8,  80, 10, p["hp"], p["maxhp"], C_RED)
    txt(s, f"{p['hp']}/{p['maxhp']}", (382, 8), FONT_L, (255, 255, 255))
    bar(s, 380, 22, 80, 10, p["mp"], p["maxmp"], C_BLUE)
    txt(s, f"{p['mp']}/{p['maxmp']}", (382, 22), FONT_L, (255, 255, 255))

    # 金币 + 战斗力
    txt(s, f"💰 {p['gold']}", (620, 15), FONT, C_GOLD)
    txt(s, f"⚡ {game.cp()}", (700, 15), FONT_B, C_PURPLE)

    # 自动战斗标记
    if game.auto:
        pygame.draw.rect(s, (74, 48, 128), (780, 12, 90, 26), border_radius=4)
        txt(s, "自动战斗", (825, 25), FONT_L, (192, 160, 240), cent=True)

    # 菜单按钮
    pygame.draw.rect(s, (26, 18, 48), (900, 12, 80, 26), border_radius=4)
    txt(s, "菜单", (940, 25), FONT, (136, 136, 136), cent=True)

    # 左侧面板切换按钮
    if game.panel_left:
        pygame.draw.rect(s, (42, 26, 64), (8, 12, 30, 26), border_radius=4)
        txt(s, "<<", (23, 25), FONT, (136, 136, 136), cent=True)
    else:
        pygame.draw.rect(s, (42, 26, 64), (8, 12, 30, 26), border_radius=4)
        txt(s, ">>", (23, 25), FONT, (136, 136, 136), cent=True)

    # 左侧面板
    if game.panel_left:
        pl = pygame.Surface((200, SCREEN_H - 260), pygame.SRCALPHA)
        pl.fill((10, 8, 20, 230))
        s.blit(pl, (8, 56))
        pygame.draw.rect(s, (42, 34, 64), (8, 56, 200, SCREEN_H - 260), border_radius=8, width=1)
        yo = 68
        txt(s, "角色信息", (16, yo), FONT_L, (138, 122, 90))
        yo += 22
        for lb, val in [
            ("生命", f"{p['hp']}/{p['maxhp']}"),
            ("灵力", f"{p['mp']}/{p['maxmp']}"),
            ("攻击", p["atk"]),
            ("防御", p["def"]),
            ("暴击", f"{p['crit']}%"),
            ("闪避", f"{p['dodge']}%"),
            ("速度", p["spd"]),
        ]:
            txt(s, lb, (16, yo), FONT, (150, 150, 150))
            txt(s, str(val), (150, yo), FONT, (220, 220, 220))
            yo += 16

        yo += 6
        txt(s, "战斗力", (16, yo), FONT_L, (138, 122, 90))
        yo += 18
        fn28 = pygame.font.SysFont("microsoftyahei", 26, bold=True)
        txt(s, str(game.cp()), (100, yo), fn28, C_GOLD, cent=True)

        # 装备槽 + 属性显示（点击可卸下）
        # 槽位：x=16~60，yo起始=244，每格48px；三槽各自独立hover检测
        yo += 10
        # （无标题标签）
        yo += 16
        slot_size = 44; slot_gap = 4; slot_y0 = 244; attr_x = 66
        slot_index = {"weapon": 0, "armor": 1, "acc": 2}
        for sid, icn in [("weapon", "⚔"), ("armor", "🛡"), ("acc", "💍")]:
            e = p["eq"][sid]
            sy_s = slot_y0 + slot_index[sid] * (slot_size + slot_gap)
            # 每槽独立hover：只检测当前槽自己的矩形（不共享状态）
            in_this = (16 <= mx <= 16 + slot_size and sy_s <= my <= sy_s + slot_size)
            qc = QC.get(e.get("q", "white"), (100, 100, 100)) if e else (60, 60, 80)
            if e:
                bw = 2 if in_this else 1
                pygame.draw.rect(s, qc, (16, sy_s, slot_size, slot_size), border_radius=6, width=bw)
                if in_this:
                    pygame.draw.rect(s, (80, 70, 120), (16, sy_s, slot_size, slot_size), border_radius=6, width=1)
                img = FONT_SK.render(e.get("icon", "?"), True, (255, 255, 255))
                s.blit(img, img.get_rect(center=(16 + slot_size // 2, sy_s + slot_size // 2 - 2)))
                en = e.get("en", 0)
                if en > 0:
                    txt(s, f"+{en}", (16 + slot_size - 2, sy_s + 2), FONT_L, C_GOLD)
                qc2 = QC.get(e.get("q", "white"), (180, 180, 180))
                txt(s, e.get("name", "?"), (attr_x, sy_s + 2), FONT, qc2)
                attrs = []
                if e.get("atk"): attrs.append(f"攻+{e['atk']}")
                if e.get("def"): attrs.append(f"防+{e['def']}")
                if e.get("hp"): attrs.append(f"HP+{e['hp']}")
                if e.get("mp"): attrs.append(f"MP+{e['mp']}")
                if e.get("crit"): attrs.append(f"暴+{e['crit']}%")
                if e.get("dodge"): attrs.append(f"躲+{e['dodge']}%")
                if e.get("spd"): attrs.append(f"速+{e['spd']}")
                attr_txt = " ".join(attrs) if attrs else ""
                if attr_txt:
                    txt(s, attr_txt, (attr_x, sy_s + 18), FONT_L, (160, 200, 160))
                if in_this:
                    txt(s, "点击卸下", (attr_x + 60, sy_s + 8), FONT_L, (220, 180, 100))
            else:
                # 空槽：纯灰色凹槽，不显示任何emoji图标
                pygame.draw.rect(s, (18, 16, 32), (16, sy_s, slot_size, slot_size), border_radius=6)
                pygame.draw.rect(s, (50, 45, 65), (16, sy_s, slot_size, slot_size), border_radius=6, width=1)
                if in_this:
                    sn = {"weapon": "武器", "armor": "衣服", "acc": "饰品"}[sid]
                    txt(s, f"[{sn}]", (16, sy_s - 14), FONT, (255, 255, 100))
        # 三个槽结束后更新yo（用于后续宠物/坐骑布局）
        yo = slot_y0 + 3 * (slot_size + slot_gap)

        # ── 出战宠物 ──
        yo += 8
        attr_x = 66
        if p["pet"]:
            pet_slot = 44
            pygame.draw.rect(s, (18, 15, 35), (16, yo, pet_slot, pet_slot), border_radius=6)
            img_pet = FONT_SK.render(p["pet"].get("ic", "🦊"), True, (255, 255, 255))
            s.blit(img_pet, img_pet.get_rect(center=(16 + pet_slot // 2, yo + pet_slot // 2)))
            qc_pet = QC.get(p["pet"].get("q", "凡兽"), (150, 150, 150))
            txt(s, p["pet"]["name"], (attr_x, yo + 4), FONT, qc_pet)
            pattrs = []
            if p["pet"].get("hp"): pattrs.append(f"血+{p['pet']['hp']}")
            if p["pet"].get("atk"): pattrs.append(f"攻+{p['pet']['atk']}")
            if p["pet"].get("crit"): pattrs.append(f"暴+{p['pet']['crit']}%")
            if p["pet"].get("sk"): pattrs.append(f"技:{p['pet']['sk']}")
            txt(s, " ".join(pattrs), (attr_x, yo + 20), FONT_L, (150, 200, 150))
            yo += pet_slot + 6

        # ── 乘骑坐骑 ──
        attr_x = 66
        if p.get("mount"):
            mnt = p["mount"]
            mnt_slot = 44
            pygame.draw.rect(s, (18, 15, 50), (16, yo, mnt_slot, mnt_slot), border_radius=6)
            img_mnt = FONT_SK.render(mnt.get("icon", "🐎"), True, (255, 255, 255))
            s.blit(img_mnt, img_mnt.get_rect(center=(16 + mnt_slot // 2, yo + mnt_slot // 2)))
            qc_mnt = QC.get(mnt.get("q", "凡马"), (150, 150, 150))
            txt(s, f"{mnt['name']}", (attr_x, yo + 4), FONT, qc_mnt)
            mnattrs = []
            if mnt.get("spd"): mnattrs.append(f"速度x{mnt['spd']}")
            if mnt.get("hp"): mnattrs.append(f"血+{mnt['hp']}")
            if mnt.get("atk"): mnattrs.append(f"攻+{mnt['atk']}")
            if mnt.get("def"): mnattrs.append(f"防+{mnt['def']}")
            txt(s, " ".join(mnattrs), (attr_x, yo + 20), FONT_L, (160, 200, 255))
            yo += mnt_slot + 6

    # 右侧面板
    pr2 = pygame.Surface((220, SCREEN_H - 260), pygame.SRCALPHA)
    pr2.fill((10, 8, 20, 230))
    s.blit(pr2, (SCREEN_W - 228, 56))
    pygame.draw.rect(s, (42, 34, 64), (SCREEN_W - 228, 56, 220, SCREEN_H - 260), border_radius=8, width=1)

    rw, rh = 196, 120
    pygame.draw.rect(s, (10, 8, 21), (SCREEN_W - 220, 62, rw, rh), border_radius=4)
    if game.map:
        for npc in game.map["npcs"]:
            mx = int((SCREEN_W - 220) + npc["x"] * rw)
            my = int(62 + npc["y"] * rh)
            pygame.draw.circle(s, C_GOLD, (mx, my), 3)
        for e in game.enemies:
            if not e.get("dead"):
                mx = int((SCREEN_W - 220) + e["x"] / 800 * rw)
                my = int(62 + e["y"] / 560 * rh)
                col = (255, 80, 80) if e.get("inCombat") else C_RED
                pygame.draw.circle(s, col, (mx, my), 2)
        if p:
            mx = int((SCREEN_W - 220) + p["x"] / 800 * rw)
            my = int(62 + p["y"] / 560 * rh)
            pygame.draw.circle(s, C_GREEN, (mx, my), 4)

    txt(s, game.map["name"] if game.map else "", (SCREEN_W - 122, 180), FONT_L, (138, 122, 90), cent=True)

    # 任务
    yo = 196
    txt(s, "任务", (SCREEN_W - 220, yo), FONT_L, (138, 122, 90))
    yo += 18
    for q in p["qs"]:
        if q.get("done"):
            continue
        prog = f"({q['cnt']}/{q['need']})" if q["tp"] == "kill" else ""
        txt(s, f"• {q['name']} {prog}", (SCREEN_W - 220, yo), FONT_L, (200, 160, 224))
        yo += 16

    # 日志
    yo += 14
    txt(s, "日志", (SCREEN_W - 220, yo), FONT_L, (138, 122, 90))
    yo += 16
    for m, c in game.logs[:8]:
        txt(s, m[:30], (SCREEN_W - 220, yo), FONT_L, c)
        yo += 14

    # 底部面板
    pygame.draw.rect(s, (8, 6, 16), (0, SCREEN_H - 200, SCREEN_W, 200))
    pygame.draw.rect(s, (42, 34, 64), (0, SCREEN_H - 200, SCREEN_W, 1))

    # 底部标签页（hover = 选中态）
    tabs = ["技能", "背包", "装备", "铸造", "宠物", "坐骑", "商店", "世界"]
    tab_start = SCREEN_W - 20 - 76
    tab_w = 76
    for i, tab in enumerate(tabs):
        cx = tab_start - i * 80
        tx = cx + 38; tx_half = 20  # 文字区域（点击区域）
        in_text = (tx - tx_half <= mx <= tx + tx_half and
                   SCREEN_H - 200 <= my <= SCREEN_H - 164)
        hover = in_text; act = (tab == game.tab)
        if act:
            pygame.draw.rect(s, (20, 18, 35), (cx, SCREEN_H - 200, tab_w, 36), border_radius=4)
            pygame.draw.line(s, C_GOLD, (cx, SCREEN_H - 200), (cx + tab_w, SCREEN_H - 200), 3)
        elif hover:
            pygame.draw.rect(s, (60, 40, 100), (cx, SCREEN_H - 200, tab_w, 36), border_radius=4)
        txt(s, tab, (tx, SCREEN_H - 182), FONT, C_GOLD if act else ((220, 200, 255) if hover else (110, 110, 130)), cent=True)

    draw_bot_tab(s, game)

    # ── 药品快捷栏：3个44×44小槽在技能栏左边 ──
    qy = SCREEN_H - 290  # 与技能栏同一行

    # 自动买药按钮（hover = 选中态）
    buy_btn_x = 50
    buy_on = game.potion_buy
    in_buy = (buy_btn_x <= mx <= buy_btn_x + 44 and qy <= my <= qy + 44)
    buy_bg = (60, 40, 100) if (in_buy or buy_on) else ((20, 30, 40) if buy_on else (30, 20, 20))
    buy_border = (60, 40, 100) if in_buy else ((50, 120, 200) if buy_on else (120, 60, 60))
    buy_color = (220, 200, 255) if in_buy else ((80, 160, 255) if buy_on else (150, 80, 80))
    pygame.draw.rect(s, buy_bg, (buy_btn_x, qy, 44, 44), border_radius=6)
    pygame.draw.rect(s, buy_border, (buy_btn_x, qy, 44, 44), border_radius=6, width=1)
    buy_label = "买药"
    txt(s, buy_label, (buy_btn_x + 22, qy + 14), FONT, buy_color, cent=True)
    buy_icon = "✓" if buy_on else "✗"
    txt(s, buy_icon, (buy_btn_x + 22, qy + 30), FONT_L, buy_color, cent=True)
    game._buy_btn_rect = (buy_btn_x, qy, 44, 44)

    # 买药数量选择弹窗（点买药按钮时弹出在按钮下方）
    if game.potion_buy_qty_sel:
        qty_choices = [10, 20, 30, 50, 99]
        sx_pop = buy_btn_x
        sy_pop = qy + 50
        pop_w = 120
        pop_h = len(qty_choices) * 36 + 16
        pygame.draw.rect(s, (12, 10, 28), (sx_pop, sy_pop, pop_w, pop_h), border_radius=8)
        pygame.draw.rect(s, (50, 120, 200), (sx_pop, sy_pop, pop_w, pop_h), border_radius=8, width=1)
        txt(s, f"每次买药量", (sx_pop + pop_w // 2, sy_pop + 12), FONT, (180, 180, 220), cent=True)
        for idx, qty in enumerate(qty_choices):
            iy2 = sy_pop + 32 + idx * 36
            in_qty = (sx_pop + 8 <= mx <= sx_pop + pop_w - 8 and iy2 <= my <= iy2 + 28)
            is_sel = (qty == game.potion_buy_qty)
            if is_sel:
                bg = (60, 40, 100) if in_qty else (30, 60, 120)
                txt_color = (220, 200, 255) if in_qty else C_GOLD
            else:
                bg = (60, 40, 100) if in_qty else (20, 20, 40)
                txt_color = (220, 200, 255) if in_qty else (160, 160, 200)
            pygame.draw.rect(s, bg, (sx_pop + 8, iy2, pop_w - 16, 28), border_radius=5)
            label = f"{qty}瓶"
            txt(s, label, (sx_pop + pop_w // 2, iy2 + 14), FONT, txt_color, cent=True)
        # 保存弹窗热区供input.py点击检测
        game._buy_qty_pop_rect = (sx_pop, sy_pop, pop_w, pop_h)

    # 自动/手动切换按钮（hover = 选中态）
    auto_btn_x = 100
    auto_on = game.potion_auto
    in_auto = (auto_btn_x <= mx <= auto_btn_x + 44 and qy <= my <= qy + 44)
    auto_bg = (60, 40, 100) if (in_auto or auto_on) else ((20, 40, 20) if auto_on else (40, 15, 15))
    auto_border = (60, 40, 100) if in_auto else ((60, 180, 60) if auto_on else (180, 50, 50))
    pygame.draw.rect(s, auto_bg, (auto_btn_x, qy, 44, 44), border_radius=6)
    pygame.draw.rect(s, auto_border, (auto_btn_x, qy, 44, 44), border_radius=6, width=1)
    auto_label = "自动" if auto_on else "手动"
    auto_color = (80, 200, 80) if auto_on else (200, 100, 100)
    txt(s, auto_label, (auto_btn_x + 22, qy + 14), FONT, auto_color, cent=True)
    auto_icon = "✓" if auto_on else "✗"
    txt(s, auto_icon, (auto_btn_x + 22, qy + 30), FONT_L, auto_color, cent=True)
    # 保存按钮热区供input.py点击检测
    game._auto_btn_rect = (auto_btn_x, qy, 44, 44)

    potion_slots = p.get("potion_slots", [])
    for i, slot in enumerate(potion_slots):
        px2 = 150 + i * 48   # 3格44×44，间距4px，在两个按钮右边
        iid = slot.get("id", "")
        n = slot.get("n", 0)
        item = ITEMS.get(iid, {})
        icon = item.get("icon", "?") if iid else "?"
        active = (iid and n > 0)
        bg = (18, 15, 35) if active else (10, 8, 16)
        border = (80, 70, 120) if active else (40, 35, 55)
        # 高亮正在配置的格
        if game.potion_sel == i:
            border = C_GOLD
        pygame.draw.rect(s, bg, (px2, qy, 44, 44), border_radius=6)
        pygame.draw.rect(s, border, (px2, qy, 44, 44), border_radius=6, width=1)
        img = FONT_SK.render(icon, True, (220, 220, 255) if active else (60, 60, 80))
        s.blit(img, img.get_rect(center=(px2 + 22, qy + 22)))
        if n > 0:
            txt(s, f"×{n}", (px2 + 22, qy + 8), FONT_L, C_GOLD, cent=True)
        txt(s, str(i + 1), (px2 + 2, qy + 2), FONT_L, (60, 60, 80))

    # ── 药品选择弹出菜单 ──
    if game.potion_sel is not None:
        from inventory import InventoryManager
        potion_ids = {"elixir_s", "elixir_mp", "elixir_b", "elixir_mp_b", "gold_elixir"}
        # 收集背包里所有药品及数量
        avail = []
        for iv in p.get("inv", []):
            if iv["id"] in potion_ids and iv["n"] > 0:
                avail.append(iv)

        slot_idx = game.potion_sel
        sx = 100 + slot_idx * 48   # 弹出菜单位于对应格子下方
        sy_pop = qy + 50

        # 背景框
        rows = len(avail) + 1   # +1=关闭按钮
        pop_h = rows * 36 + 8
        pop_w = 200
        pygame.draw.rect(s, (12, 10, 28), (sx, sy_pop, pop_w, pop_h), border_radius=8)
        pygame.draw.rect(s, (80, 60, 100), (sx, sy_pop, pop_w, pop_h), border_radius=8, width=1)
        txt(s, "选择药品", (sx + pop_w // 2, sy_pop + 12), FONT, C_GOLD, cent=True)

        for r, iv in enumerate(avail):
            iy2 = sy_pop + 22 + r * 36
            item = ITEMS.get(iv["id"], {})
            hover = (sx <= mx <= sx + pop_w and iy2 <= my <= iy2 + 32)
            rb = (30, 28, 50) if hover else (18, 15, 35)
            pygame.draw.rect(s, rb, (sx + 4, iy2, pop_w - 8, 32), border_radius=4)
            if hover:
                pygame.draw.rect(s, C_GOLD, (sx + 4, iy2, pop_w - 8, 32), border_radius=4, width=1)
            img2 = FONT_SK.render(item.get("icon", "?"), True, (200, 200, 255))
            s.blit(img2, img2.get_rect(center=(sx + 20, iy2 + 16)))
            txt(s, item.get("name", ""), (sx + 38, iy2 + 8), FONT_L, (180, 170, 200))
            txt(s, f"×{iv['n']}", (sx + 38, iy2 + 22), FONT_L, C_GOLD)
            # 记录鼠标悬停在哪一行（用于input.py点击）
            game._potion_row = r

        # 关闭按钮
        cy = sy_pop + 22 + len(avail) * 36
        ch = (sx <= mx <= sx + pop_w and cy <= my <= cy + 32)
        rb2 = (50, 20, 20) if ch else (30, 15, 15)
        pygame.draw.rect(s, rb2, (sx + 4, cy, pop_w - 8, 32), border_radius=4)
        txt(s, "关闭", (sx + pop_w // 2, cy + 16), FONT, (200, 150, 150) if ch else (120, 100, 100), cent=True)
        game._potion_row = len(avail)  # 关闭按钮所在行
        game._potion_pop_rect = (sx, sy_pop, pop_w, pop_h)

    # 快捷技能栏
    qy = SCREEN_H - 290

    # ── 一键挂机按钮（普通攻击左侧）────────────────────
    bx = SCREEN_W // 2 - 4 * 48 - 48 - 4   # 普通攻击格子左边空一格
    bw, bh = 44, 44
    af = getattr(game, "auto_farm", False)
    # 背景
    abg = (20, 80, 40) if af else (30, 25, 45)
    pygame.draw.rect(s, abg, (bx, qy, bw, bh), border_radius=6)
    acol = (80, 220, 120) if af else (110, 100, 140)
    pygame.draw.rect(s, acol, (bx, qy, bw, bh), border_radius=6, width=1 if af else 1)
    # 文字
    img = FONT_SK.render("挂", True, acol)
    s.blit(img, img.get_rect(center=(bx + bw // 2, qy + bh // 2 - 4)))
    # 状态点
    if af:
        pygame.draw.circle(s, (80, 255, 120), (bx + bw - 10, qy + 10), 5)
    # 记录按钮区域（供 input.py 点击检测）
    game._autofarm_btn = (bx, qy, bw, bh)

    for i, skn in enumerate(p["qb"][:9]):
        qx = SCREEN_W // 2 - 4 * 48 + i * 48
        sk = SKILLS.get(skn, {})
        cd = game.cds.get(skn, 0)
        bg = (18, 15, 35) if cd == 0 else (30, 20, 50)
        pygame.draw.rect(s, bg, (qx, qy, 44, 44), border_radius=6)
        pygame.draw.rect(s, (60, 48, 80), (qx, qy, 44, 44), border_radius=6, width=1)
        img = FONT_SK.render(sk.get("icon", "?"), True, (200, 200, 200) if cd == 0 else (100, 100, 100))
        s.blit(img, img.get_rect(center=(qx + 22, qy + 18)))
        txt(s, str(i + 1), (qx + 3, qy + 3), FONT_L, (80, 80, 80))
        if cd > 0:
            ov2 = pygame.Surface((44, 44), pygame.SRCALPHA)
            ov2.fill((0, 0, 0, 150))
            s.blit(ov2, (qx, qy))
            txt(s, str(cd), (qx + 22, qy + 22), FONT, (255, 255, 255), cent=True)


# ═══════════ 底部标签栏 ════════════════════════════════════════
def draw_bot_tab(s, game):
    """绘制底部标签面板内容"""
    p = game.p
    sy = SCREEN_H - 160
    draw_bot_tab_content(s, sy, 0, 0, game)


def draw_bot_tab_content(s, sy, mx, my, game):
    """绘制底部标签内容（技能/背包/装备/铸造/宠物/坐骑）"""
    p = game.p
    tab = game.tab

    if tab == "技能":
        # 技能列表（6列）
        cols = 6; item_w = 140; item_h = 50; gap = 6
        iy = sy + 10
        for i, skn in enumerate(p["sk"]):
            col_n = i % cols; row_n = i // cols
            ix = 20 + col_n * (item_w + gap)
            iy2 = iy + row_n * (item_h + gap)
            sk = SKILLS.get(skn, {})
            cd = game.cds.get(skn, 0)
            sel = (ix <= mx <= ix + item_w and iy2 <= my <= iy2 + item_h)
            bg = (30, 28, 50) if sel else (18, 15, 35)
            pygame.draw.rect(s, bg, (ix, iy2, item_w, item_h), border_radius=6)
            if sel:
                pygame.draw.rect(s, C_GOLD, (ix, iy2, item_w, item_h), border_radius=6, width=1)
            img = FONT_SK.render(sk.get("icon", "?"), True, (200, 200, 200) if cd == 0 else (100, 100, 100))
            s.blit(img, (ix + 6, iy2 + 6))
            txt(s, skn, (ix + 34, iy2 + 10), FONT, C_TEXT)
            txt(s, sk["desc"] if "desc" in sk else "", (ix + 34, iy2 + 26), FONT_L, (100, 100, 100))
            if cd > 0:
                txt(s, f"CD:{cd}", (ix + item_w - 38, iy2 + 4), FONT_L, C_RED)

    elif tab == "背包":
        cols = 6; item_w = 140; item_h = 50; gap = 6; iy = sy + 10
        for i, iv in enumerate(p["inv"]):
            col_n = i % cols; row_n = i // cols
            ix = 20 + col_n * (item_w + gap)
            iy2 = iy + row_n * (item_h + gap)
            it = ITEMS.get(iv["id"], {})
            qc = QC.get(it.get("q", "white"), (100, 100, 100))
            sel = (ix <= mx <= ix + item_w and iy2 <= my <= iy2 + item_h)
            bg = (30, 28, 50) if sel else (18, 15, 35)
            pygame.draw.rect(s, bg, (ix, iy2, item_w, item_h), border_radius=6)
            pygame.draw.rect(s, qc, (ix, iy2, item_w, item_h), border_radius=6, width=1)
            img = FONT_SK.render(it.get("icon", "?"), True, (255, 255, 255))
            s.blit(img, (ix + 6, iy2 + 6))
            txt(s, f"{it.get('name', iv['id'])} x{iv['n']}", (ix + 34, iy2 + 10), FONT, C_TEXT)
            txt(s, it.get("desc", ""), (ix + 34, iy2 + 26), FONT_L, (100, 100, 100))

    elif tab == "装备":
        # 已购买待穿戴装备列表
        cols = 6; item_w = 140; item_h = 50; gap = 6; iy = sy + 10
        for i, eq_item in enumerate(p["equips"]):
            col_n = i % cols; row_n = i // cols
            ix = 20 + col_n * (item_w + gap)
            iy2 = iy + row_n * (item_h + gap)
            it = ITEMS.get(eq_item["id"], {})
            qc = QC.get(it.get("q", "white"), (100, 100, 100))
            sel = (ix <= mx <= ix + item_w and iy2 <= my <= iy2 + item_h)
            bg = (30, 28, 50) if sel else (18, 15, 35)
            pygame.draw.rect(s, bg, (ix, iy2, item_w, item_h), border_radius=6)
            pygame.draw.rect(s, qc, (ix, iy2, item_w, item_h), border_radius=6, width=1)
            img = FONT_SK.render(it.get("icon", "?"), True, (255, 255, 255))
            s.blit(img, (ix + 6, iy2 + 6))
            txt(s, it.get("name", "?"), (ix + 34, iy2 + 8), FONT, C_TEXT)
            txt(s, it.get("desc", ""), (ix + 34, iy2 + 24), FONT_L, (100, 100, 100))
            # 穿上按钮
            bx2 = ix + 88; by2 = iy2 + 18; bw2 = 46; bh2 = 22
            if bx2 <= mx <= bx2 + bw2 and by2 <= my <= by2 + bh2:
                pygame.draw.rect(s, (80, 60, 120), (bx2, by2, bw2, bh2), border_radius=4)
                txt(s, "穿上", (bx2 + bw2 // 2, by2 + bh2 // 2), FONT_L, C_GOLD, cent=True)
            else:
                pygame.draw.rect(s, (40, 30, 60), (bx2, by2, bw2, bh2), border_radius=4)
                txt(s, "穿上", (bx2 + bw2 // 2, by2 + bh2 // 2), FONT_L, (150, 150, 150), cent=True)

    elif tab == "铸造":
        # 装备强化
        iy = sy + 10
        txt(s, "强化装备：点击底部已穿上装备的槽位", (20, iy), FONT_L, (138, 122, 90))
        iy += 24
        for sid in ["weapon", "armor", "acc"]:
            e = p["eq"][sid]
            if not e:
                continue
            ix = 20
            iy2 = iy
            qc = QC.get(e.get("q", "white"), (100, 100, 100))
            pygame.draw.rect(s, (18, 15, 35), (ix, iy2, 400, 40), border_radius=6)
            pygame.draw.rect(s, qc, (ix, iy2, 400, 40), border_radius=6, width=1)
            txt(s, e.get("icon", "?"), (ix + 10, iy2 + 8), FONT_SK, C_TEXT)
            txt(s, f"{e.get('name', '')} +{e.get('en', 0)}", (ix + 40, iy2 + 8), FONT, C_TEXT)
            # 强化按钮（hover = 选中态）
            bx = ix + 280; bw_qh = 50; bh_qh = 30
            in_btn = (bx <= mx <= bx + bw_qh and iy2 + 4 <= my <= iy2 + 4 + bh_qh)
            qh_bg = (60, 40, 100) if in_btn else (40, 30, 60)
            qh_col = (220, 200, 255) if in_btn else (150, 150, 150)
            pygame.draw.rect(s, qh_bg, (bx, iy2 + 4, bw_qh, bh_qh), border_radius=4)
            txt(s, "强化", (bx + 25, iy2 + 19), FONT_L, qh_col, cent=True)
            iy += 46

    elif tab == "宠物":
        iy = sy + 8
        icon_sz = 28
        btn_w, btn_h = 52, 26
        for i, pet in enumerate(p["pets"]):
            iy2 = iy
            pygame.draw.rect(s, (18, 15, 35), (20, iy2, 290, 38), border_radius=4)
            # 宠物图标
            pygame.draw.rect(s, (28, 25, 48), (22, iy2 + 6, icon_sz, icon_sz), border_radius=3)
            img_p = FONT_SK.render(pet.get('ic', '🐾'), True, (255, 255, 255))
            s.blit(img_p, img_p.get_rect(center=(22 + icon_sz // 2, iy2 + 6 + icon_sz // 2)))
            # 名称+属性（单行压缩）
            txt(s, pet.get('name', '?'), (56, iy2 + 4), FONT, C_TEXT)
            pattr_str = f"血{pet['hp']} 攻{pet['atk']} 暴{pet['crit']}% {pet.get('sk','')}"
            txt(s, pattr_str, (56, iy2 + 20), FONT_L, (110, 110, 140))
            # 出战/休息按钮（hover = 选中态）
            bx = 256; by2 = iy2 + 6
            in_btn = (bx <= mx <= bx + btn_w and by2 <= my <= by2 + btn_h)
            is_active = p["pet"] and p["pet"].get("id") == pet.get("id")
            if is_active:
                bg = (60, 40, 100) if in_btn else (80, 55, 130)
                txt_col = (220, 200, 255) if in_btn else C_GOLD
                label = "🐾 休息"
            else:
                bg = (60, 40, 100) if in_btn else (50, 40, 80)
                txt_col = (220, 200, 255) if in_btn else (170, 170, 190)
                label = "出战"
            pygame.draw.rect(s, bg, (bx, by2, btn_w, btn_h), border_radius=4)
            txt(s, label, (bx + 26, by2 + 5), FONT_L, txt_col, cent=True)
            iy += 40
        if not p["pets"]:
            txt(s, "还没有宠物，去商店购买吧！", (20, iy), FONT_L, (100, 100, 100))

    elif tab == "坐骑":
        iy = sy + 8
        icon_sz = 28
        btn_w, btn_h = 52, 26
        for i, mnt in enumerate(p["mounts"]):
            iy2 = iy
            pygame.draw.rect(s, (18, 15, 35), (20, iy2, 290, 38), border_radius=4)
            # 坐骑图标
            pygame.draw.rect(s, (28, 25, 48), (22, iy2 + 6, icon_sz, icon_sz), border_radius=3)
            img_m = FONT_SK.render(mnt.get('icon', '🐎'), True, (255, 255, 255))
            s.blit(img_m, img_m.get_rect(center=(22 + icon_sz // 2, iy2 + 6 + icon_sz // 2)))
            # 名称+属性（单行压缩）
            txt(s, mnt.get('name', '?'), (56, iy2 + 4), FONT, C_TEXT)
            desc_str = f"血{mnt.get('hp',0)} 攻{mnt.get('atk',0)} 速{mnt.get('spd',0)}x"
            txt(s, desc_str, (56, iy2 + 20), FONT_L, (110, 110, 140))
            # 乘骑/离鞍按钮（hover = 选中态）
            bx = 256; by2 = iy2 + 6
            in_btn = (bx <= mx <= bx + btn_w and by2 <= my <= by2 + btn_h)
            is_active = p["mount"] and p["mount"].get("id") == mnt.get("id")
            if is_active:
                bg = (60, 40, 100) if in_btn else (80, 55, 130)
                txt_col = (220, 200, 255) if in_btn else C_GOLD
                label = "🐎 离鞍"
            else:
                bg = (60, 40, 100) if in_btn else (50, 40, 80)
                txt_col = (220, 200, 255) if in_btn else (170, 170, 190)
                label = "乘骑"
            pygame.draw.rect(s, bg, (bx, by2, btn_w, btn_h), border_radius=4)
            txt(s, label, (bx + 26, by2 + 5), FONT_L, txt_col, cent=True)
            iy += 40
        if not p["mounts"]:
            txt(s, "还没有坐骑，去商店购买吧！", (20, iy), FONT_L, (100, 100, 100))

    elif tab == "世界":
        n_maps = len(WORLD)
        # 3列布局，充分利用左中区域（右侧保留给信息面板）
        cols = 3
        card_w = (SCREEN_W - 228 - 20 - 16) // cols
        card_h = 40
        gap_x = 8; gap_y = 10
        start_x = 20; start_y = sy + 8

        # 保存按钮热区，供 input.py 点击检测
        game._world_btn_rects = []

        for i, m in enumerate(WORLD):
            col_n = i % cols; row_n = i // cols
            mx2 = start_x + col_n * (card_w + gap_x)
            my2 = start_y + row_n * (card_h + gap_y)

            # 边框颜色：当前地图高亮金色，其他用蓝色系
            is_current = (getattr(game, 'map_id', None) == m["id"])
            border_col = C_GOLD if is_current else (50, 45, 90)
            bg = (22, 20, 40) if is_current else (16, 14, 30)
            pygame.draw.rect(s, bg, (mx2, my2, card_w - gap_x, card_h), border_radius=10)
            pygame.draw.rect(s, border_col, (mx2, my2, card_w - gap_x, card_h), border_radius=10, width=2)

            # 地图名（左上方）
            txt(s, m["name"], (mx2 + 10, my2 + 10), FONT_B, C_GOLD if is_current else (200, 185, 230))
            # 推荐等级（左下方装饰）
            txt(s, f"推荐 Lv{m['lv']}", (mx2 + 10, my2 + card_h - 8), FONT_L, (80, 75, 110))

            # 进入按钮（卡片右方中间）
            btn_w = 52; btn_h = 26
            btn_x = mx2 + card_w - gap_x - btn_w - 4
            btn_y = my2 + (card_h - btn_h) // 2
            btn_bg = (60, 50, 120) if is_current else (40, 35, 80)
            btn_col = C_GOLD if is_current else (180, 165, 220)
            pygame.draw.rect(s, btn_bg, (btn_x, btn_y, btn_w, btn_h), border_radius=6)
            txt(s, "进入", (btn_x + btn_w // 2, btn_y + btn_h // 2), FONT_B, btn_col, cent=True)

            # 记录热区：(mid, card_x, card_y, card_w, card_h, btn_x, btn_y, btn_w, btn_h)
            game._world_btn_rects.append((m["id"], mx2, my2, card_w - gap_x, card_h, btn_x, btn_y, btn_w, btn_h))

        if n_maps == 0:
            txt(s, "暂无可用地图", (SCREEN_W // 2, sy + 80), FONT_L, (80, 80, 100), cent=True)


# ═══════════ 菜单 ════════════════════════════════════════════════
def draw_menu(s, game, audio):
    """绘制主菜单"""
    if not game._menu_bgm:
        game._menu_bgm = True
        audio.play_bgm()

    s.fill((8, 8, 16))
    for y in range(SCREEN_H):
        t = y / SCREEN_H
        r2 = int(26 * (1 - t) + 8 * t)
        g3 = int(10 * (1 - t) + 8 * t)
        b2 = int(46 * (1 - t) + 16 * t)
        pygame.draw.line(s, (r2, g3, b2), (0, y), (SCREEN_W, y))

    t = pygame.time.get_ticks()
    for i in range(80):
        px = (i * 137 + int(t / 50)) % SCREEN_W
        py = (i * 89 + int(t / 80)) % SCREEN_H
        br = 100 + int(math.sin(t / 500 + i) * 50)
        pygame.draw.circle(s, (br, br, br + 20), (px, py), 1)

    fn = pygame.font.SysFont("microsoftyahei", 64, bold=True)
    txt(s, "苍穹仙途", (SCREEN_W // 2, 100), fn, C_GOLD, cent=True)

    from data import CLASS_D
    cl = list(CLASS_D.keys())
    cx = SCREEN_W // 2 - 3 * 170 // 2
    cy = 240
    mx, my = pygame.mouse.get_pos()
    for i, cls in enumerate(cl):
        d = CLASS_D[cls]
        bx = cx + i * 170
        by = cy
        sel = (game.midx == i)
        bw, bh = 155, 170
        hover = (bx <= mx <= bx + bw and by <= my <= by + bh)
        if sel:
            pygame.draw.rect(s, (*d["col"], 30), (bx, by, bw, bh), border_radius=12, width=2)
            pygame.draw.rect(s, C_GOLD, (bx, by, bw, bh), border_radius=12, width=2)
        elif hover:
            pygame.draw.rect(s, (80, 50, 120), (bx, by, bw, bh), border_radius=12, width=2)
        else:
            pygame.draw.rect(s, (20, 15, 35), (bx, by, bw, bh), border_radius=12, width=1)
        name_col = (220, 200, 255) if (sel or hover) else d["col"]
        txt(s, d["name"], (bx + bw // 2, by + 25), FONT_B, name_col, cent=True)
        wn = "长枪" if cls == "pojun" else "法杖" if cls == "tianshang" else "魔琴"
        wn_col = (220, 200, 255) if (sel or hover) else (100, 100, 100)
        txt(s, f"武器：{wn}", (bx + bw // 2, by + 52), FONT_L, wn_col, cent=True)
        ds = {"pojun": ("血厚防高", "近战王者", "嘲讽减伤"),
              "tianshang": ("输出爆炸", "远程法师", "群攻惊人"),
              "lingxing": ("治疗辅助", "团队核心", "加血护盾")}
        for j, desc in enumerate(ds[cls]):
            desc_col = (220, 200, 255) if (sel or hover) else (120, 120, 120)
            txt(s, desc, (bx + bw // 2, by + 78 + j * 18), FONT_L, desc_col, cent=True)

    txt(s, "鼠标悬停/点击 选择职业", (SCREEN_W // 2, cy + 195), FONT_L, (100, 100, 100), cent=True)
    txt(s, "鼠标点击移动  ·  数字键释放技能  ·  点击按钮自动挂机", (SCREEN_W // 2, cy + 220), FONT_L, (80, 80, 80), cent=True)


# ═══════════ 对话框 ════════════════════════════════════════════
def draw_dlg(s, game):
    """绘制对话框"""
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 180))
    s.blit(ov, (0, 0))

    dw, dh = 500, 300
    dx = (SCREEN_W - dw) // 2
    dy = (SCREEN_H - dh) // 2
    pygame.draw.rect(s, (18, 16, 42), (dx, dy, dw, dh), border_radius=16)
    pygame.draw.rect(s, (60, 50, 100), (dx, dy, dw, dh), border_radius=16, width=2)
    txt(s, game.dlg.get("title", ""), (dx + 30, dy + 24), FONT_B, C_GOLD)

    # ── 存档列表（按职业分组）─────────────────────
    if game.dlg_mode == "saves":
        grouped = getattr(game, "dlg_data", {}) or {}
        # 操作说明
        txt(s, "左键=读档  右键=删除", (dx + 30, dy + 55), FONT, (130, 130, 130))
        ey = dy + 82
        for cls, entries in grouped.items():
            # 分组标题
            txt(s, f"═══ {cls} ═══", (dx + 30, ey), FONT_B, C_GOLD)
            ey += 26
            for sv in entries:
                bg = (30, 20, 50)
                pygame.draw.rect(s, bg, (dx + 20, ey, dw - 40, 30), border_radius=4)
                txt(s, f"Lv{sv.get('lv','?')}  {sv.get('date','?')}", (dx + 30, ey + 8), FONT, (180, 255, 200))
                txt(s, sv["file"], (dx + 230, ey + 8), FONT, (120, 120, 120), max_w=dw - 40 - 230)
                ey += 34
            ey += 8  # 组间距
        if not grouped:
            txt(s, "暂无存档", (dx + dw // 2, dy + 150), FONT, (100, 100, 100), cent=True)
        # 记录当前列表底部（供点击检测用）
        game._saves_ey = ey
    # ── 作弊面板 ──────────────────────────────────
    elif game.dlg_mode == "cheat":
        # 等级
        txt(s, "等级:", (dx + 30, dy + 60), FONT, C_TEXT)
        bx = dx + 90; by2 = dy + 52; bw = 120; bh = 30
        bg = (50, 40, 80) if game.cheat_focus == 0 else (25, 20, 45)
        pygame.draw.rect(s, bg, (bx, by2, bw, bh), border_radius=4)
        txt(s, game.cheat_lv_input or "_", (bx + bw // 2, by2 + 8), FONT, (220, 200, 255), cent=True)
        txt(s, "(回车确认)", (bx + bw + 10, dy + 60), FONT, (100, 100, 100))
        # 金币
        txt(s, "金币:", (dx + 30, dy + 100), FONT, C_TEXT)
        bx2 = dx + 90; by3 = dy + 92; bw2 = 160; bh2 = 30
        bg2 = (50, 40, 80) if game.cheat_focus == 1 else (25, 20, 45)
        pygame.draw.rect(s, bg2, (bx2, by3, bw2, bh2), border_radius=4)
        txt(s, game.cheat_gold_input or "_", (bx2 + bw2 // 2, by3 + 8), FONT, (220, 200, 255), cent=True)
        txt(s, "(回车确认)  Tab切换", (bx2 + bw2 + 10, dy + 100), FONT, (100, 100, 100))
        # 无敌按钮
        bx3 = dx + 30; by4 = dy + 145; bw3 = 120; bh3 = 34
        inv_on = game.invincible
        bg3 = (80, 50, 20) if inv_on else (25, 20, 45)
        txt3 = "无敌: 开" if inv_on else "无敌: 关"
        col3 = C_GOLD if inv_on else (140, 120, 160)
        pygame.draw.rect(s, bg3, (bx3, by4, bw3, bh3), border_radius=6)
        txt(s, txt3, (bx3 + bw3 // 2, by4 + 10), FONT, col3, cent=True)
    # ── 普通对话框（含读档确认） ───────────────────
    else:
        txt(s, game.dlg.get("body", "")[:80], (dx + 30, dy + 60), FONT, C_TEXT)
        mx, my = pygame.mouse.get_pos()
        for i, btn in enumerate(game.dlg_btns):
            bx = dx + 30 + i * 140
            by = dy + dh - 55
            hover = (bx <= mx <= bx + 120 and by <= my <= by + 36)
            bg = (80, 50, 120) if hover else ((60, 40, 100) if game.dlg_i == i else (30, 20, 40))
            pygame.draw.rect(s, bg, (bx, by, 120, 36), border_radius=6)
            col = (220, 200, 255) if (hover or game.dlg_i == i) else (140, 120, 160)
            txt(s, btn, (bx + 60, by + 18), FONT, col, cent=True)

    # 右上角 X 关闭按钮（所有模式）
    cx = dx + dw - 40; cy = dy + 10
    mx2, my2 = pygame.mouse.get_pos()
    hover = (cx <= mx2 <= cx + 30 and cy <= my2 <= cy + 26)
    bg_x = (80, 30, 30) if hover else (50, 20, 20)
    pygame.draw.rect(s, bg_x, (cx, cy, 30, 26), border_radius=4)
    txt(s, "✕", (cx + 15, cy + 6), FONT, (220, 180, 180) if hover else (150, 120, 120), cent=True)
