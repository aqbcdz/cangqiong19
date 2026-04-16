"""
render.py — 所有渲染函数
职责：
  - 游戏背景绘制（draw_bg + 地形装饰）
  - 玩家绘制（draw_pl）
  - NPC绘制（draw_npc）
  - 敌人绘制（draw_enemy）
  - 商店界面绘制（draw_shop_overlay）
  - 浮动文字/击中特效绘制

外部依赖：
  - config.py（SCREEN_W/SCREEN_H/颜色/FONT_SK）
  - data.py（CLASS_D, QC, SHOP_ITEMS）

不包含：
  - 主循环（main.py 负责）
  - UI层（ui.py 负责 draw_ui/draw_menu/draw_dlg）
"""
import pygame
import math
import random
from config import *
from data import QC


# ═══════════ 通用绘制工具 ════════════════════════════════════════
def txt(s, t, pos, fn=None, c=C_TEXT, cent=False):
    f = fn or FONT
    img = f.render(t, True, c)
    r = img.get_rect(center=pos) if cent else img.get_rect(topleft=pos)
    s.blit(img, r)


def bar(s, x, y, w, h, v, mv, fg=C_RED):
    pygame.draw.rect(s, (40, 30, 50), (x, y, w, h), border_radius=3)
    if v > 0:
        fw = max(2, int(w * min(1.0, v / mv)))
        pygame.draw.rect(s, fg, (x, y, fw, h), border_radius=3)


# ═══════════ 背景 ════════════════════════════════════════════════
def draw_bg(s, bg):
    """绘制地图背景"""
    gc1 = {"village": (26, 42, 26), "forest": (10, 26, 10), "city": (26, 26, 42),
           "harbor": (10, 21, 32), "snow": (26, 32, 48), "cave": (8, 5, 12)}
    gc2 = {"village": (13, 26, 13), "forest": (5, 16, 5), "city": (13, 13, 26),
           "harbor": (5, 10, 16), "snow": (13, 21, 32), "cave": (5, 3, 8)}
    c1 = gc1.get(bg, (10, 10, 20)); c2 = gc2.get(bg, (5, 5, 10))
    for y in range(SCREEN_H):
        t = y / SCREEN_H
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g2 = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        pygame.draw.line(s, (r, g2, b), (0, y), (SCREEN_W, y))

    # 各地图地形装饰
    if bg == "village":
        pygame.draw.rect(s, (26, 46, 26), (0, 480, SCREEN_W, 200))
        for i in range(7):
            tx = 60 + i * 165; ty = 340 + int(math.sin(i) * 40)
            _tree(s, tx, ty, 0.6 + math.sin(i) * 0.3, False)
        _house(s, 150, 380, 0.8); _house(s, 700, 360, 0.9); _house(s, 950, 340, 0.7)
        pts = [(0, 600), (300, 380), (500, 400), (700, 360), (1200, 600)]
        for i in range(len(pts) - 1):
            pygame.draw.line(s, (50, 40, 20), pts[i], pts[i + 1], 20)
    elif bg == "forest":
        pygame.draw.rect(s, (10, 30, 10), (0, 480, SCREEN_W, 200))
        for i in range(10):
            tx = 30 + i * 120; ty = 280 + int(math.sin(i * 0.8) * 50)
            _tree(s, tx, ty, 0.5 + math.sin(i) * 0.3, False)
        for _ in range(8):
            pygame.draw.circle(s, (30, 60, 30),
                              (random.randint(0, SCREEN_W), random.randint(400, 560)),
                              random.randint(8, 18))
    elif bg == "city":
        pygame.draw.rect(s, (20, 20, 35), (0, 480, SCREEN_W, 200))
        for i in range(8):
            bx = 40 + i * 140; by = 360 - int(math.sin(i * 0.5) * 30)
            _building(s, bx, by, 0.6 + math.sin(i) * 0.4)
        for i in range(6):
            _lantern(s, 60 + i * 180, 340)
        pygame.draw.rect(s, (18, 16, 28), (0, 498, SCREEN_W, 30))
    elif bg == "harbor":
        pygame.draw.rect(s, (5, 10, 21), (0, 480, SCREEN_W, 200))
        for i in range(6):
            pygame.draw.rect(s, (10, 30, 60), (0, 488 + i * 16, SCREEN_W, 10), width=2)
        _boat(s, 300, 400); _boat(s, 650, 420)
        pygame.draw.rect(s, (42, 26, 16), (80, 470, 800, 18))
    elif bg == "snow":
        pygame.draw.rect(s, (20, 32, 48), (0, 480, SCREEN_W, 200))
        for i in range(8):
            tx = 40 + i * 148; ty = 320 + int(math.sin(i) * 35)
            _tree(s, tx, ty, 0.6 + math.sin(i) * 0.3, True)
        t = pygame.time.get_ticks()
        for i in range(50):
            sx = (t // 10 + i * 73) % SCREEN_W
            sy = (t // 15 + i * 47) % SCREEN_H
            pygame.draw.circle(s, (200, 220, 255), (sx, sy), 2)
    elif bg == "cave":
        pygame.draw.rect(s, (8, 5, 12), (0, 380, SCREEN_W, 300))
        for i in range(8):
            sx = 80 + i * (SCREEN_W - 160) // 7; h = 200 + int(math.sin(i) * 60)
            pts = [(sx - 12, 0), (sx, h), (sx + 12, 0)]
            pygame.draw.polygon(s, (20, 16, 30), pts)
        t = pygame.time.get_ticks()
        for i in range(6):
            cx = 80 + i * 180; cy = 460 + random.randint(10, 60)
            hue = (t // 20 + i * 60) % 360
            c3 = pygame.Color(0); c3.hsla = (hue, 80, 50, 30)
            pygame.draw.circle(s, c3, (cx, cy), 12 + int(math.sin(t / 200 + i) * 4))

    # 网格线
    for x in range(0, SCREEN_W, 40):
        pygame.draw.line(s, (22, 22, 40), (x, 0), (x, SCREEN_H))
    for y in range(0, SCREEN_H, 40):
        pygame.draw.line(s, (22, 22, 40), (0, y), (SCREEN_W, y))
    pygame.draw.rect(s, (40, 34, 64), (0, 0, SCREEN_W, SCREEN_H), 3)


# ═══════════ 地形装饰 ════════════════════════════════════════════
def _tree(s, x, y, sc, snow=False):
    h = 50 * sc
    pygame.draw.rect(s, (58, 32, 16), (int(x - 5), int(y), 10, int(h * 0.5)))
    col = (20, 50, 20) if not snow else (25, 35, 45)
    pygame.draw.circle(s, col, (int(x), int(y - h * 0.3)), int(h * 0.45))
    pygame.draw.circle(s, col, (int(x - h * 0.25), int(y + h * 0.05)), int(h * 0.35))
    pygame.draw.circle(s, col, (int(x + h * 0.25), int(y + h * 0.05)), int(h * 0.35))
    if snow:
        pygame.draw.circle(s, (180, 200, 230), (int(x), int(y - h * 0.4)), int(h * 0.25))


def _house(s, x, y, sc):
    w = 60 * sc; h = 40 * sc
    pygame.draw.rect(s, (42, 26, 16), (int(x - w // 2), int(y), int(w), int(h)))
    pts = [(int(x - w // 2 - 5), int(y)), (int(x), int(y - h * 0.8)), (int(x + w // 2 + 5), int(y))]
    pygame.draw.polygon(s, (25, 10, 5), pts)
    pygame.draw.rect(s, (232, 200, 122), (int(x - 5), int(y + h // 2), 10, 15))


def _building(s, x, y, sc):
    w = 50 * sc; h = 70 * sc
    pygame.draw.rect(s, (26, 21, 37), (int(x - w // 2), int(y), int(w), int(h)))
    pygame.draw.rect(s, (42, 32, 53), (int(x - w // 2), int(y - h * 0.4), int(w), int(h * 0.4)))
    for i in range(3):
        for j in range(3):
            lit = random.random() > 0.4
            c4 = (232, 200, 122, 100) if lit else (15, 15, 30)
            pygame.draw.rect(s, c4, (int(x - w // 2 + 8 + i * 14), int(y + h * 0.2 + j * 18), 10, 12))


def _lantern(s, x, y):
    pygame.draw.rect(s, (26, 26, 32), (int(x - 2), int(y), 4, 20))
    pygame.draw.circle(s, (232, 160, 50, 150), (int(x), int(y + 20)), 8)
    pygame.draw.circle(s, (232, 160, 50), (int(x), int(y + 20)), 4)


def _boat(s, x, y):
    pts = [(x - 25, y), (x, y + 12), (x + 25, y), (x + 20, y - 5), (x - 20, y - 5)]
    pygame.draw.polygon(s, (42, 26, 10), pts)
    pygame.draw.rect(s, (58, 37, 16), (int(x - 2), int(y - 28), 4, 28))
    pts2 = [(int(x + 2), int(y - 28)), (int(x + 2), int(y - 10)), (int(x + 18), int(y - 19))]
    pygame.draw.polygon(s, (200, 200, 220, 80), pts2)


# ═══════════ 角色绘制 ════════════════════════════════════════════
def draw_pl(s, x, y, cls, hpr, mpr, buffs=None, sh=0):
    from data import CLASS_D
    d = CLASS_D[cls]; c = d["col"]
    pygame.draw.ellipse(s, (0, 0, 0, 80), (int(x - 16), int(y + 18), 32, 10))
    gs = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.circle(gs, (*c, 30), (30, 30), 30); s.blit(gs, (int(x - 30), int(y - 30)))
    pygame.draw.rect(s, c, (int(x - 12), int(y - 18), 24, 30), border_radius=5)
    pygame.draw.circle(s, (245, 222, 179), (int(x), int(y - 24)), 9)
    pygame.draw.circle(s, (50, 50, 50), (int(x - 3), int(y - 25)), 1.5)
    pygame.draw.circle(s, (50, 50, 50), (int(x + 3), int(y - 25)), 1.5)
    if cls == "pojun":
        pygame.draw.rect(s, (180, 180, 180), (int(x + 10), int(y - 4), 20, 4))
    elif cls == "tianshang":
        pygame.draw.line(s, (192, 144, 240), (int(x + 12), int(y - 30)), (int(x + 12), int(y + 10)), 3)
        pygame.draw.circle(s, (144, 96, 192), (int(x + 12), int(y - 30)), 6)
    else:
        pygame.draw.rect(s, (80, 128, 192), (int(x + 8), int(y - 10), 16, 20), border_radius=4)
    if buffs:
        for b in buffs:
            if b["n"] == "不动如山":
                pygame.draw.circle(s, C_GOLD, (int(x), int(y)), 24, 2)
    if sh > 0:
        gs2 = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(gs2, (100, 150, 255, min(80, sh // 10)), (40, 40), 38)
        s.blit(gs2, (int(x - 40), int(y - 40)))
    bar(s, int(x - 18), int(y + 24), 36, 5, hpr, 1.0, C_RED)


def draw_npc(s, x, y, nm, tp):
    cm = {"quest": C_GOLD, "shop": C_GREEN, "guild": C_PURPLE, "boss": (255, 30, 30), "elite": (255, 100, 0)}
    c = cm.get(tp, (136, 136, 136))
    gs = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.circle(gs, (*c, 25), (25, 25), 25); s.blit(gs, (int(x - 25), int(y - 25)))
    pygame.draw.circle(s, c, (int(x), int(y)), 16)
    pygame.draw.circle(s, (20, 20, 40), (int(x), int(y)), 10)
    ic_map = {"quest": "❖", "shop": "☘", "guild": "⚜", "boss": "☠", "elite": "★"}
    fn = pygame.font.SysFont("Arial", 14, bold=True)
    img = fn.render(ic_map.get(tp, "?"), True, (255, 255, 255))
    s.blit(img, img.get_rect(center=(int(x), int(y))))
    txt(s, nm, (int(x), int(y + 32)), FONT_L, c, cent=True)


def draw_enemy(s, e):
    if e.get("dead"):
        return
    from data import QC, ENEMY_SKILLS
    qc = QC.get(e.get("q", "white"), (150, 150, 150))
    x, y = e["x"], e["y"]
    etype = e.get("etype", "normal")

    # ── 尺寸与颜色因类型而异 ────────────────────
    body_r = {"normal": 18, "elite": 22, "boss": 30}.get(etype, 18)
    badge_col = {"normal": None, "elite": (96, 165, 250), "boss": (249, 115, 22)}.get(etype)
    badge_txt = {"normal": "", "elite": "E", "boss": "B"}.get(etype, "")

    # 战斗中红色光环
    if e.get("inCombat"):
        t = pygame.time.get_ticks()
        pl = 0.5 + 0.5 * math.sin(t / 150)
        aura_sz = body_r * 2 + 14
        gs = pygame.Surface((aura_sz, aura_sz), pygame.SRCALPHA)
        pygame.draw.circle(gs, (255, 50, 50, int(40 * pl)), (aura_sz // 2, aura_sz // 2), aura_sz // 2)
        s.blit(gs, (int(x - aura_sz // 2), int(y - aura_sz // 2)))

    # 阴影
    shadow_w = body_r * 1.6
    pygame.draw.ellipse(s, (0, 0, 0, 60), (int(x - shadow_w / 2), int(y + body_r * 0.7), int(shadow_w), shadow_w * 0.3))

    # 身体光晕
    gs2 = pygame.Surface((body_r * 2 + 10, body_r * 2 + 10), pygame.SRCALPHA)
    pygame.draw.circle(gs2, (*qc, 25), (body_r + 5, body_r + 5), body_r + 5)
    s.blit(gs2, (int(x - body_r - 5), int(y - body_r - 5)))

    # 主体
    pygame.draw.circle(s, qc, (int(x), int(y)), body_r)

    # 头顶图标
    ic_sz = int(body_r * 0.9)
    img = FONT_SK.render(e.get("ic", "?"), True, (255, 255, 255))
    img = pygame.transform.scale(img, (ic_sz * 2, ic_sz * 2))
    s.blit(img, img.get_rect(center=(int(x), int(y))))

    # 类型徽章（左上角）
    if badge_col and badge_txt:
        badge_r = int(body_r * 0.5)
        pygame.draw.circle(s, badge_col, (int(x - body_r - 2), int(y - body_r - 2)), badge_r, 2)
        txt(s, badge_txt, (int(x - body_r - 2), int(y - body_r - 2 - badge_r * 0.5)),
            FONT_SK if etype != "boss" else FONT_L, badge_col, cent=True)

    # 血条
    bar_w = int(body_r * 2.2)
    bar(s, int(x - bar_w / 2), int(y + body_r + 5), bar_w, 5, e["hp"], e["maxhp"],
        C_RED if e["hp"] / e["maxhp"] > 0.3 else (255, 0, 0))

    # 血量数值
    txt(s, f"{e['hp']}/{e['maxhp']}", (int(x), int(y + body_r + 12)), FONT_SK, (180, 180, 180), cent=True)

    # 名字
    txt(s, e.get("name", ""), (int(x), int(y + body_r + 24)), FONT_SK, qc, cent=True)

    # Boss：显示5个技能图标
    if etype == "boss":
        skills = e.get("skills", [])
        total_w = len(skills) * 16 + (len(skills) - 1) * 4
        sx0 = int(x - total_w / 2)
        sy = int(y + body_r + 36)
        for i, sid in enumerate(skills[:5]):
            sk = ENEMY_SKILLS.get(sid, {})
            cd = e.get("skill_cd", {}).get(sid, 0)
            col = (60, 200, 60) if cd == 0 else (100, 100, 100)
            bx = sx0 + i * 20
            pygame.draw.rect(s, col, (bx, sy, 16, 16), border_radius=3)
            txt(s, sk.get("name", "?")[:1], (bx + 8, sy + 8), FONT_SK, (255, 255, 255), cent=True)

    # 冻结效果
    if e.get("stun", 0) > 0:
        ov = pygame.Surface((body_r * 2 + 10, body_r * 2 + 10), pygame.SRCALPHA)
        ov.fill((100, 180, 255, 150))
        s.blit(ov, (int(x - body_r - 5), int(y - body_r - 5)))
        txt(s, "❄", (int(x), int(y - body_r * 0.5)), FONT_SK, (200, 240, 255), cent=True)

    # 盾
    if e.get("shield", 0) > 0:
        sh_col = (100, 180, 255)
        pygame.draw.circle(s, sh_col, (int(x), int(y)), body_r + 4, 2)


# ═══════════ 商店 ════════════════════════════════════════════════
def draw_shop_overlay(s, game):
    """绘制商店悬浮界面"""
    p = game.p
    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 160))
    s.blit(ov, (0, 0))

    pw, ph = 780, 520
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2

    pygame.draw.rect(s, (12, 10, 28), (px, py, pw, ph), border_radius=16)
    pygame.draw.rect(s, (80, 60, 120), (px, py, pw, ph), border_radius=16, width=2)
    pygame.draw.rect(s, (20, 16, 40), (px, py, pw, 44), border_radius=16)
    pygame.draw.line(s, (60, 50, 100), (px + 16, py + 44), (px + pw - 16, py + 44))

    txt(s, "商店", (px + pw // 2, py + 22), FONT_B, C_GOLD, cent=True)
    txt(s, f"💰 {p['gold']}", (px + pw - 90, py + 22), FONT_B, C_GOLD)

    # 关闭按钮
    pygame.draw.rect(s, (40, 20, 30), (px + pw - 44, py + 8, 32, 28), border_radius=6)
    txt(s, "✕", (px + pw - 28, py + 22), FONT, (200, 160, 160), cent=True)

    # 分类标签
    from data import SHOP_ITEMS
    cats = list(SHOP_ITEMS.keys())
    cat_y = py + 60
    mx_r, my_r = pygame.mouse.get_pos()
    for i, cat in enumerate(cats):
        cx = px + 16 + i * 96
        sel = (game.shop_cat == cat)
        in_cat = (cx <= mx_r <= cx + 90 and cat_y <= my_r <= cat_y + 30)
        if sel:
            bg = (60, 40, 100) if in_cat else (50, 40, 90)
            txt_col = (220, 200, 255) if in_cat else C_GOLD
        else:
            bg = (60, 40, 100) if in_cat else (22, 18, 40)
            txt_col = (220, 200, 255) if in_cat else (110, 100, 130)
        pygame.draw.rect(s, bg, (cx, cat_y, 90, 30), border_radius=6)
        if sel and not in_cat:
            pygame.draw.rect(s, C_GOLD, (cx, cat_y, 90, 30), border_radius=6, width=1)
        txt(s, cat, (cx + 45, cat_y + 15), FONT, txt_col, cent=True)

    # 商品列表
    items = SHOP_ITEMS.get(game.shop_cat, [])
    if game.shop_cat == "技能书":
        items = [it for it in items if it.get("cls") == p["cls"]]

    cols = 4; item_w = 170; item_h = 80
    grid_x = px + 16; grid_y = cat_y + 48

    for i, item in enumerate(items):
        col_n = i % cols; row_n = i // cols
        ix = grid_x + col_n * (item_w + 8); iy = grid_y + row_n * (item_h + 8)
        if ix + item_w > px + pw:
            break
        qc = QC.get(item.get("q", "white"), (150, 150, 150))
        in_item = (ix <= mx_r <= ix + item_w and iy <= my_r <= iy + item_h)
        item_bg = (60, 40, 100) if in_item else (20, 18, 36)
        pygame.draw.rect(s, item_bg, (ix, iy, item_w, item_h), border_radius=8)
        pygame.draw.rect(s, qc, (ix, iy, item_w, item_h), border_radius=8, width=1)
        img = FONT_SK.render(item.get("icon", "?"), True, (255, 255, 255))
        s.blit(img, img.get_rect(center=(ix + 28, iy + 40)))
        name_col = (220, 200, 255) if in_item else (210, 200, 230)
        txt(s, item.get("name", ""), (ix + 56, iy + 18), FONT, name_col)
        txt(s, f"💰{item['price']}", (ix + 56, iy + 38), FONT_L, C_GOLD)
        txt(s, item.get("desc", ""), (ix + 56, iy + 58), FONT_L, (110, 110, 130))

    # ── 数量输入提示（消耗品点击后显示）─
    if game.shop_qty_item is not None:
        item = game.shop_qty_item
        i_name = item.get("name", item.get("id", ""))
        i_price = item.get("price", 0)
        qty_display = game.shop_qty_input if game.shop_qty_input else "_"
        # 半透明遮罩
        ov2 = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov2.fill((0, 0, 0, 120))
        s.blit(ov2, (0, 0))
        # 输入框
        bx = SCREEN_W // 2 - 200
        by = SCREEN_H // 2 - 40
        bw = 400; bh = 80
        pygame.draw.rect(s, (20, 18, 36), (bx, by, bw, bh), border_radius=12)
        pygame.draw.rect(s, C_GOLD, (bx, by, bw, bh), border_radius=12, width=2)
        # 上方物品名
        txt(s, f"购买：{i_name}  单价：{i_price}金币", (SCREEN_W // 2, by + 18), FONT, (200, 190, 230), cent=True)
        # 中间数量输入（高亮显示当前输入的数字）
        total = i_price * (int(game.shop_qty_input) if game.shop_qty_input else 1)
        txt(s, f"数量：{qty_display}  合计：{total}金币", (SCREEN_W // 2, by + 40), FONT_B, C_GOLD, cent=True)
        # 下方提示
        txt(s, "输入数字后按 Enter 购买 | ESC 取消", (SCREEN_W // 2, by + 62), FONT_L, (130, 120, 160), cent=True)

    txt(s, "左键购买 | ESC或点击✕关闭", (SCREEN_W // 2, py + ph - 18), FONT_L, (90, 80, 110), cent=True)


# ══════════════════════════════════════════════════════
# 存档界面
# ══════════════════════════════════════════════════════
def draw_save_overlay(s, game):
    """绘制存档/读档悬浮界面"""
    from save import SaveManager
    saves = SaveManager.list_saves()

    W, H = 600, 440
    px = (SCREEN_W - W) // 2
    py = (SCREEN_H - H) // 2

    ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 180))
    s.blit(ov, (0, 0))

    pygame.draw.rect(s, (10, 10, 25), (px, py, W, H), border_radius=16)
    pygame.draw.rect(s, (80, 70, 140), (px, py, W, H), border_radius=16, width=2)
    pygame.draw.rect(s, (20, 16, 40), (px, py, W, 48), border_radius=16)
    pygame.draw.line(s, (60, 50, 100), (px+16, py+48), (px+W-16, py+48))

    txt(s, "存档", (px + W//2, py+24), FONT_B, C_GOLD, cent=True)

    pygame.draw.rect(s, (40, 20, 30), (px+W-44, py+8, 32, 28), border_radius=6)
    txt(s, "X", (px+W-28, py+22), FONT, (200,160,160), cent=True)

    row_y = py + 65
    for i in range(min(5, len(saves))):
        sv = saves[i]
        ry = row_y + i * 56
        sel = (getattr(game, "_save_sel", 0) == i)
        bg = (30, 28, 60) if sel else (18, 16, 35)
        col = C_GOLD if sel else (110, 100, 140)
        pygame.draw.rect(s, bg, (px+16, ry, W-32, 50), border_radius=8)
        if sel:
            pygame.draw.rect(s, C_GOLD, (px+16, ry, W-32, 50), border_radius=8, width=1)
        cls_names = {"pojun":"破军", "tianshang":"天殇", "lingxing":"铃星"}
        cls_n = cls_names.get(sv.get("cls", "?"), sv.get("cls", "?"))
        info = f"{cls_n}  Lv{sv.get('lv', '?')}  |  {sv.get('date', '?')}"
        txt(s, info, (px+30, ry+14), FONT_L, col)
        txt(s, sv.get("file", ""), (px+30, ry+34), FONT_S, (80, 75, 110))

    if not saves:
        txt(s, "暂无存档", (px+W//2, py+H//2), FONT_L, (90,80,120), cent=True)

    btn_y = py + H - 50
    bx, bw, bh = px+30, 120, 36
    mx_r, my_r = pygame.mouse.get_pos()
    # 存档按钮
    in_b1 = (bx <= mx_r <= bx+bw and btn_y <= my_r <= btn_y+bh)
    bg1 = (60, 40, 100) if in_b1 else (20, 60, 30)
    col1 = (220, 200, 255) if in_b1 else (120, 220, 140)
    pygame.draw.rect(s, bg1, (bx, btn_y, bw, bh), border_radius=8)
    txt(s, "存档", (bx+bw//2, btn_y+bh//2), FONT_L, col1, cent=True)
    # 读档按钮
    bx2 = px + 180
    in_b2 = (bx2 <= mx_r <= bx2+bw and btn_y <= my_r <= btn_y+bh)
    bg2 = (60, 40, 100) if in_b2 else (20, 30, 60)
    col2 = (220, 200, 255) if in_b2 else (100, 160, 220)
    pygame.draw.rect(s, bg2, (bx2, btn_y, bw, bh), border_radius=8)
    txt(s, "读档", (bx2+bw//2, btn_y+bh//2), FONT_L, col2, cent=True)
    # 继续按钮
    bx3 = px + W - 150
    in_b3 = (bx3 <= mx_r <= bx3+120 and btn_y <= my_r <= btn_y+bh)
    bg3 = (60, 40, 100) if in_b3 else (30, 28, 45)
    col3 = (220, 200, 255) if in_b3 else (150, 140, 180)
    pygame.draw.rect(s, bg3, (bx3, btn_y, 120, bh), border_radius=8)
    txt(s, "继续", (bx3+60, btn_y+bh//2), FONT_L, col3, cent=True)

    txt(s, "选择存档后点存档/读档 | ESC关闭", (px+W//2, py+H-12), FONT_S, (80,75,110), cent=True)

    game._save_btn   = (bx, btn_y, bw, bh)
    game._load_btn   = (bx2, btn_y, bw, bh)
    game._resume_btn = (bx3, btn_y, 120, bh)
    game._close_btn  = (px+W-44, py+8, 32, 28)
    game._save_list_range = (px+16, row_y, W-32, min(5, len(saves)) * 56)
