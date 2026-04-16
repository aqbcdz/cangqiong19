"""
main.py — 游戏主入口
职责：
  - pygame 初始化
  - Game 类（整合所有模块）
  - 主循环：事件处理 → 更新 → 渲染
  - 游戏状态切换（menu/playing/shop/dialog）
  - 全局 game 实例

模块依赖（最后整合，单向无循环）：
  config.py → data.py → audio.py → player.py / inventory.py / equipment.py / combat.py / shop.py / enemy.py / map.py
                                   ↓
  ui.py ← render.py ← input.py ← main.py（主循环）
"""
import pygame
import math
import random
import sys

# ═══════════ 初始化 ════════════════════════════════════════════
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
pygame.display.set_caption("苍穹仙途")
screen = pygame.display.set_mode((1200, 760))
clock = pygame.time.Clock()

# ═══════════ 导入所有模块 ════════════════════════════════════════
from config import *
from data import CLASS_D, REALMS, WORLD, SKILLS, ITEMS, SHOP_ITEMS, PETS, MOUNTS, EN_MAX
from audio import Audio
from effects import SE
from player import PlayerManager
from inventory import InventoryManager
from equipment import EquipmentManager
from combat import CombatManager
from shop import ShopManager
from enemy import EnemyManager
from map import MapManager
from ui import draw_ui, draw_menu, draw_dlg, draw_bot_tab_content, txt, bar
from render import draw_bg, draw_pl, draw_npc, draw_enemy, draw_shop_overlay, draw_save_overlay
from input import InputHandler

# ═══════════ 全局实例 ════════════════════════════════════════════════
audio = Audio()


# ═══════════ Game 类（整合所有模块）═══════════════════════════════
class Game:
    def __init__(self):
        with open("C:\\debug_log.txt", "a") as f:
            f.write(f"[DBG] Game.__init__ called\n")
        self.s = "menu"
        self._menu_bgm = False
        self._target_enemy = None
        self._patk_cd = 0
        self.p = None
        self.map = None
        self.enemies = []
        self.effects = []
        self.floats = []
        self.logs = []
        self.tab = "技能"
        self.dlg = {}
        self.dlg_btns = []
        self.dlg_cb = None
        self.dlg_i = 0
        self.cds = {}
        self.auto = False
        self.midx = 0
        self.move_to = None
        self.panel_left = True
        self.potion_slots = [{"id": "", "n": 0}, {"id": "", "n": 0}, {"id": "", "n": 0}]
        self.potion_sel = None  # None=无, 0/1/2=正在配置第几格
        self.potion_auto = False  # True=自动喝药, False=手动（默认手动）
        self.auto_farm  = False  # True=一键挂机（自动找怪打）
        self.potion_buy = False    # True=自动买药（低于20瓶时自动从商店购买N瓶）
        self.potion_buy_qty = 50    # 自动买药每次购买数量
        self.potion_buy_qty_sel = False  # True=买药数量选择弹窗已打开
        self.potion_cd = 0         # 药品冷却计时（秒，USEREVENT+2每秒递减）
        self.shield_aura = None
        self.facing_x = 1.0        # 面向方向（单位向量，初始朝右）
        self.invincible = False     # 作弊：无敌模式
        self.dlg_mode = None        # 弹窗模式: None=普通, saves=存档列表, load_confirm=读档确认, cheat=作弊面板
        self.cheat_focus = 0        # 作弊面板焦点: 0=等级, 1=金币
        self.cheat_lv_input = ""   # 作弊等级输入
        self.cheat_gold_input = ""  # 作弊金币输入
        self._pending_save = False   # 存档延迟执行标记（避免卡顿）
        self.facing_y = 0.0
        self._last_click_time = 0
        self._last_click_pos = None
        self._eq_flash = None
        self._eq_flash_t = 0
        self._inv_flash = None
        self.version = "v19-refactor"
        self.shop_cat = "装备"
        self.shop_items = SHOP_ITEMS
        self.shop_qty_item = None   # 当前正在输入数量的物品（消耗品）
        self.shop_qty_input = ""    # 输入的数量字符串

    # ─── 状态切换 ──────────────────────────────────────
    def start(self):
        with open("C:\\Users\\Administrator\\debug_game_log.txt", "a") as f:
            f.write(f"[DBG] game.start() called\n")
        self.s = "menu"

    def new_game(self, cls):
        with open("C:\\Users\\Administrator\\debug_game_log.txt", "a") as f:
            f.write(f"[DBG] new_game called! cls={cls}\n")
        self.p = {}
        PlayerManager.new_game(self.p, cls)
        self.tab = "技能"
        self.cds = {}
        self.auto = False
        self.logs = []
        self.effects = []
        self.floats = []
        self.enemies = []
        self.move_to = None
        self.shop_cat = "装备"
        MapManager.load_map(self, "shuiyun", audio)
        self.s = "playing"
        self._menu_bgm = False
        audio.play_bgm()

    def load_map(self, mid):
        MapManager.load_map(self, mid, audio)

    # ─── 日志 / 浮动文字 ────────────────────────────────
    def _add_log(self, m, c=C_TEXT):
        try:
            self.logs.insert(0, (m, c))
            self.logs = self.logs[:12]
        except Exception as e:
            with open("C:\\Users\\Administrator\\debug_game_log.txt", "a") as f:
                f.write(f"[DBG _add_log] ERROR: {e} self.logs={getattr(self,'logs','MISSING')}\n")

    def start(self):
        import traceback
        with open("C:\\Users\\Administrator\\debug_game_log.txt", "a") as f:
            f.write(f"[DBG] game.start() called\n")
            buf = __import__("io").StringIO()
            traceback.print_stack(file=buf)
            f.write(buf.getvalue())
        self.s = "menu"

    def _ft(self, x, y, t, c, sz=20):
        self.floats.append({"x": x, "y": y, "t": t, "c": c, "sz": sz, "l": 55, "ml": 55})

    # ─── 属性重算 / 升级 ─────────────────────────────────
    def _recalc(self):
        PlayerManager.recalc(self.p)

    def _lvlup(self):
        PlayerManager.level_up(self.p, self)
        # 升级时自动存档
        from save import SaveManager
        SaveManager.save_game(self)

    # ─── 战斗力 ────────────────────────────────────────
    def cp(self):
        return EquipmentManager.calc_power(self.p)

    # ─── 战斗 ───────────────────────────────────────────
    def start_combat(self, e):
        CombatManager.start_combat(self.enemies, e, self)

    def player_atk(self, e, skname="普通攻击"):
        CombatManager.player_attack(
            self.p, self.enemies, skname,
            self.cds, self.auto, self.effects, self.floats,
            self, audio, self.shield_aura,
            self.facing_x, self.facing_y
        )

    def enemy_atk(self, e):
        CombatManager.enemy_attack(self.p, e, self.effects, self.floats, self, audio)

    # ─── 装备 ───────────────────────────────────────────
    def equip(self, iid):
        EquipmentManager.equip(self.p, iid, self)

    def unequip_to_list(self, sl):
        EquipmentManager.unequip_to_list(self.p, sl, self)

    def equip_by_idx(self, idx):
        EquipmentManager.equip_by_idx(self.p, idx, self)

    def enhance(self, sl, safe=False):
        EquipmentManager.enhance(self.p, sl, safe, self)

    # ─── 物品 ───────────────────────────────────────────
    def give_item(self, iid, n=1):
        InventoryManager.give_item(self.p, iid, n)

    def take_item(self, iid, n=1):
        return InventoryManager.take_item(self.p, iid, n)

    def use_item(self, iid):
        return InventoryManager.use_item(self.p, iid, self)


# ═══════════ 全局游戏实例 ════════════════════════════════════════
game = Game()
game.start()


# ═══════════ 主循环 ════════════════════════════════════════════════
pygame.time.set_timer(pygame.USEREVENT + 2, 1000)

running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    # ─── 事件处理 ───────────────────────────────────────
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        elif e.type == pygame.KEYDOWN:
            k = e.key
            if game.s == "menu":
                InputHandler.handle_menu_keys(e, game)
            elif game.s == "playing":
                InputHandler.handle_play_keys(e, game)
            elif game.s == "dialog":
                if game.dlg_mode == "cheat":
                    if k == pygame.K_ESCAPE:
                        game.s = "playing"
                        game.dlg_mode = None
                        game.dlg_btns = []
                        game.cheat_lv_input = ""
                        game.cheat_gold_input = ""
                    elif k == pygame.K_TAB:
                        game.cheat_focus = 1 - game.cheat_focus
                    elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if game.cheat_focus == 0 and game.cheat_lv_input:
                            lv = max(1, min(int(game.cheat_lv_input), 999))
                            from player import PlayerManager
                            p["lv"] = lv
                            p["exp"] = 0
                            p["expn"] = max(100, lv * 100)
                            PlayerManager.recalc(p)
                            game._add_log(f"等级设置为 {lv}", C_GOLD)
                            game.cheat_lv_input = ""
                        elif game.cheat_focus == 1 and game.cheat_gold_input:
                            gold = max(0, int(game.cheat_gold_input))
                            p["gold"] = gold
                            game._add_log(f"金币设置为 {gold}", C_GOLD)
                            game.cheat_gold_input = ""
                    elif k == pygame.K_BACKSPACE:
                        if game.cheat_focus == 0:
                            game.cheat_lv_input = game.cheat_lv_input[:-1]
                        else:
                            game.cheat_gold_input = game.cheat_gold_input[:-1]
                    elif pygame.K_0 <= k <= pygame.K_9 or pygame.K_KP0 <= k <= pygame.K_KP9:
                        digit = str(k - pygame.K_0)
                        if game.cheat_focus == 0:
                            if len(game.cheat_lv_input) < 3:
                                game.cheat_lv_input += digit
                        else:
                            if len(game.cheat_gold_input) < 9:
                                game.cheat_gold_input += digit
                elif k == pygame.K_ESCAPE:
                    game.s = "playing"
                    game.dlg_mode = None
                    game.dlg_btns = []
                elif k == pygame.K_LEFT:
                    game.dlg_i = max(0, game.dlg_i - 1)
                elif k == pygame.K_RIGHT:
                    game.dlg_i = min(len(game.dlg_btns) - 1, game.dlg_i + 1)
                elif k in (pygame.K_RETURN, pygame.K_SPACE):
                    if game.dlg_cb:
                        game.dlg_cb(game.dlg_i)
                    elif game.dlg_mode in ("load_confirm", "del_confirm"):
                        if game.dlg_i == 0:  # 确定
                            if game.dlg_mode == "load_confirm":
                                from save import SaveManager
                                flat = getattr(game, "dlg_data_flat", []) or []
                                if game.dlg_load_idx < len(flat):
                                    fp = os.path.join(SaveManager._save_dir(), flat[game.dlg_load_idx]["file"])
                                    import json as _json
                                    try:
                                        with open(fp, "r", encoding="utf-8") as f:
                                            data = _json.load(f)
                                        result = SaveManager.apply_save(game, data)
                                        game._add_log(result, C_GOLD)
                                    except Exception:
                                        game._add_log("读档失败", C_RED)
                            else:  # del_confirm
                                import os
                                from save import SaveManager
                                flat = getattr(game, "dlg_data_flat", []) or []
                                if game.dlg_del_idx < len(flat):
                                    fp = os.path.join(SaveManager._save_dir(), flat[game.dlg_del_idx]["file"])
                                    if os.path.exists(fp):
                                        os.remove(fp)
                                        game._add_log("已删除", C_TEXT)
                            game.s = "playing"
                            game.dlg_mode = None
                            game.dlg_btns = []
                        else:  # 取消
                            game.dlg_mode = "saves"
                            game.dlg = {"title": "存档列表", "body": ""}
                            game.dlg_btns = []
            elif game.s == "save":
                InputHandler.handle_save_keys(e, game)
            elif game.s == "shop":
                # 商店数量输入模式
                if game.shop_qty_item is not None:
                    if k == pygame.K_ESCAPE:
                        game.shop_qty_item = None
                        game.shop_qty_input = ""
                    elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        qty = int(game.shop_qty_input) if game.shop_qty_input else 1
                        qty = max(1, min(qty, 99))
                        ShopManager.buy_item(game.p, game.shop_qty_item, game, audio, game, qty=qty)
                        game.shop_qty_item = None
                        game.shop_qty_input = ""
                    elif k == pygame.K_BACKSPACE:
                        game.shop_qty_input = game.shop_qty_input[:-1]
                    elif pygame.K_0 <= k <= pygame.K_9:
                        if len(game.shop_qty_input) < 2:
                            game.shop_qty_input += pygame.key.name(k)
                elif k == pygame.K_ESCAPE:
                    game.shop_qty_item = None
                    game.shop_qty_input = ""
                    game.s = "playing"
                elif k == pygame.K_t:
                    n = len(game.p["equips"])
                    if n > 0:
                        game.equip_by_idx(0)
                elif k in (pygame.K_1, pygame.K_KP_1):
                    if len(game.p["equips"]) > 0:
                        game.equip_by_idx(0)
                elif k in (pygame.K_2, pygame.K_KP_2):
                    if len(game.p["equips"]) > 1:
                        game.equip_by_idx(1)
                elif k in (pygame.K_3, pygame.K_KP_3):
                    if len(game.p["equips"]) > 2:
                        game.equip_by_idx(2)
            elif game.s in ("playing", "shop"):
                if k == pygame.K_F1:
                    ShopManager.use_potion(game.p, 0, game.floats, audio, game)
                elif k == pygame.K_F2:
                    ShopManager.use_potion(game.p, 1, game.floats, audio, game)
                elif k == pygame.K_F3:
                    ShopManager.use_potion(game.p, 2, game.floats, audio, game)
                elif k == pygame.K_F4:
                    global DEBUG_MODE
                    DEBUG_MODE = not DEBUG_MODE
                    game._add_log("DEBUG_MODE: " + ("ON" if DEBUG_MODE else "OFF"), (200, 200, 100))

        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                pos = e.pos
                if game.s == "menu":
                    InputHandler.handle_menu_mouse(pos, game)
                elif game.s == "shop":
                    InputHandler.handle_shop_mouse(pos, game)
                elif game.s == "save":
                    InputHandler.handle_save_mouse(pos, game)
                elif game.s == "dialog":
                    dw, dh = 500, 300
                    dx = (SCREEN_W - dw) // 2; dy = (SCREEN_H - dh) // 2
                    # 右上角 X 关闭按钮（所有模式均有效）
                    if dx + dw - 40 <= e.pos[0] <= dx + dw - 10 and dy + 10 <= e.pos[1] <= dy + 36:
                        game.s = "playing"
                        game.s = "playing"
                        game.dlg_mode = None
                        game.dlg_btns = []
                        game.cheat_lv_input = ""
                        game.cheat_gold_input = ""
                    elif game.dlg_mode == "saves":
                        flat = getattr(game, "dlg_data_flat", []) or []
                        ey = dy + 82
                        for i, sv in enumerate(flat):
                            cls_key = sv["cls"]
                            ey += 26 if i == 0 or (flat[i-1]["cls"] != cls_key and i > 0) else 0
                            if dx + 20 <= e.pos[0] <= dx + dw - 20 and ey <= e.pos[1] <= ey + 30:
                                game.dlg = {"title": "是否读档？", "body": sv["file"]}
                                game.dlg_btns = ["确定", "取消"]
                                game.dlg_i = 1
                                game.dlg_mode = "load_confirm"
                                game.dlg_load_idx = i
                                game.dlg_cb = None
                                break
                            ey += 34
                    elif game.dlg_mode in ("load_confirm", "del_confirm"):
                        bx0 = dx + 30
                        for i, btn in enumerate(game.dlg_btns):
                            bx = bx0 + i * 140
                            if bx <= e.pos[0] <= bx + 120 and dy + dh - 55 <= e.pos[1] <= dy + dh - 19:
                                if i == 0:  # 确定
                                    if game.dlg_mode == "load_confirm":
                                        from save import SaveManager
                                        flat = getattr(game, "dlg_data_flat", []) or []
                                        if game.dlg_load_idx < len(flat):
                                            fp = os.path.join(SaveManager._save_dir(), flat[game.dlg_load_idx]["file"])
                                            import json as _json
                                            try:
                                                with open(fp, "r", encoding="utf-8") as f:
                                                    data = _json.load(f)
                                                result = SaveManager.apply_save(game, data)
                                                game._add_log(result, C_GOLD)
                                            except Exception:
                                                game._add_log("读档失败", C_RED)
                                    else:  # del_confirm
                                        import os
                                        from save import SaveManager
                                        flat = getattr(game, "dlg_data_flat", []) or []
                                        if game.dlg_del_idx < len(flat):
                                            fp = os.path.join(SaveManager._save_dir(), flat[game.dlg_del_idx]["file"])
                                            if os.path.exists(fp):
                                                os.remove(fp)
                                                game._add_log("已删除", C_TEXT)
                                    game.s = "playing"
                                    game.dlg_mode = None
                                    game.dlg_btns = []
                                else:  # 取消 → 返回存档列表
                                    game.dlg_mode = "saves"
                                    game.dlg = {"title": "存档列表", "body": ""}
                                    game.dlg_btns = []
                                break
                    elif game.dlg_mode == "cheat":
                        # 等级输入框 (dy+52~dy+82)
                        # 金币输入框 (dy+92~dy+122)
                        # 无敌按钮 (dy+145~dy+179)
                        bx2 = dx + 30
                        if bx2 <= e.pos[0] <= bx2 + 120 and dy + 145 <= e.pos[1] <= dy + 179:
                            game.invincible = not game.invincible
                            p["invincible"] = game.invincible
                            game._add_log(f"无敌:{'开' if game.invincible else '关'}", C_GOLD if game.invincible else C_TEXT)
                    else:
                        # 普通对话框（含读档确认）
                        bx0 = dx + 30
                        for i, btn in enumerate(game.dlg_btns):
                            bx = bx0 + i * 140
                            if bx <= e.pos[0] <= bx + 120 and dy + dh - 55 <= e.pos[1] <= dy + dh - 19:
                                if game.dlg_cb:
                                    game.dlg_cb(i)
                                elif i == 0 and game.dlg_mode == "load_confirm":
                                    from save import SaveManager
                                    flat = getattr(game, "dlg_data_flat", []) or []
                                    if game.dlg_load_idx < len(flat):
                                        fp = os.path.join(SaveManager._save_dir(), flat[game.dlg_load_idx]["file"])
                                        import json as _json
                                        try:
                                            with open(fp, "r", encoding="utf-8") as f:
                                                data = _json.load(f)
                                            result = SaveManager.apply_save(game, data)
                                            game._add_log(result, C_GOLD)
                                        except Exception:
                                            game._add_log("读档失败", C_RED)
                                    game.s = "playing"
                                    game.dlg_mode = None
                                    game.dlg_btns = []
                                break
                else:
                    InputHandler.handle_mouse(pos, game)
            elif e.button == 3:
                mx, my = e.pos
                if game.s == "dialog" and game.dlg_mode == "saves":
                    dw, dh = 500, 300
                    dx = (SCREEN_W - dw) // 2; dy = (SCREEN_H - dh) // 2
                    flat = getattr(game, "dlg_data_flat", []) or []
                    ey = dy + 82
                    for i, sv in enumerate(flat):
                        cls_key = sv["cls"]
                        ey += 26 if i == 0 or (flat[i-1]["cls"] != cls_key and i > 0) else 0
                        if dx + 20 <= mx <= dx + dw - 20 and ey <= my <= ey + 30:
                            game.dlg = {"title": "删除存档", "body": f"确定删除？\n{sv['file']}"}
                            game.dlg_btns = ["确定删除", "取消"]
                            game.dlg_i = 1
                            game.dlg_mode = "del_confirm"
                            game.dlg_del_idx = i
                            break
                        ey += 34
                elif game.s in ("playing", "shop"):
                    qy = SCREEN_H - 290
                    for i in range(3):
                        px2 = 150 + i * 48
                        if px2 <= mx <= px2 + 44 and qy <= my <= qy + 44:
                            from shop import ShopManager
                            ShopManager.remove_potion(game.p, i)
                            game.potion_sel = None
                            break

        elif e.type == pygame.USEREVENT + 1:
            if game.s == "playing" and game.auto:
                p = game.p
                ce = [x for x in game.enemies if not x.get("dead") and x.get("inCombat")]
                if not ce:
                    lv = [x for x in game.enemies if not x.get("dead")]
                    if lv:
                        ne = min(lv, key=lambda e2: math.hypot(e2["x"] - p["x"], e2["y"] - p["y"]))
                        p["move_to"] = (ne["x"], ne["y"])
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)

        elif e.type == pygame.USEREVENT + 2:
            if game.s in ("playing", "shop"):
                # 冷却递减
                for k in list(game.cds.keys()):
                    game.cds[k] -= 1
                    if game.cds[k] <= 0:
                        del game.cds[k]
                # 药品冷却递减
                if game.potion_cd > 0:
                    game.potion_cd -= 1
                # 自动喝药（仅在自动模式下，冷却中则等冷却结束再喝，补到60%以上才停）
                if game.potion_auto and game.potion_cd == 0:
                    ShopManager.auto_drink(game.p, game)
                # 自动买药（仅在开启时，每秒检测一次）
                if game.potion_buy and game.shop_cat:
                    ShopManager.auto_buy(game.p, game)

    # ─── 更新 ───────────────────────────────────────────
    # 延迟存档（避免存档时卡顿）
    if game._pending_save:
        game._pending_save = False
        from save import SaveManager
        msg = SaveManager.save_game(game)
        saves = SaveManager.list_saves()
        game.dlg = {"title": "存档列表", "body": f"{'共' + str(len(saves)) + '个存档' if saves else '暂无存档'}"}
        game.dlg_btns = []
        game.dlg_data = saves
        game.dlg_mode = "saves"
        game.dlg_i = 0
        game._add_log(msg, C_GOLD)

    if game.s == "playing" and game.p:
        p = game.p

        # 玩家移动
        if p.get("move_to"):
            tx, ty = p["move_to"]
            dx = tx - p["x"]; dy = ty - p["y"]
            d = math.hypot(dx, dy)
            if d < 5:
                p["move_to"] = None
            else:
                sp = p.get("spd", 4)
                step = sp if d >= sp else d
                ndx, ndy = dx / d, dy / d
                # 碰撞：若本步移动会穿越怪物（距怪物 < 20px），则吸附到边缘
                hit = False
                for e in game.enemies:
                    if e.get("dead"):
                        continue
                    ed = math.hypot(e["x"] - p["x"], e["y"] - p["y"])
                    # 预测移动后与怪物的距离
                    pred_x = p["x"] + ndx * step
                    pred_y = p["y"] + ndy * step
                    pred_ed = math.hypot(e["x"] - pred_x, e["y"] - pred_y)
                    if pred_ed < 20:
                        # 吸附到怪物边缘（半径20px处），停止
                        nx2 = (p["x"] - e["x"]) / ed if ed > 0 else 0
                        ny2 = (p["y"] - e["y"]) / ed if ed > 0 else 0
                        p["x"] = e["x"] + nx2 * 20
                        p["y"] = e["y"] + ny2 * 20
                        p["move_to"] = None
                        hit = True
                        break
                if not hit:
                    p["x"] += ndx * step
                    p["y"] += ndy * step
                    # 同步面向方向
                    game.facing_x = ndx
                    game.facing_y = ndy
                    if game._target_enemy:
                        ted = math.hypot(game._target_enemy["x"] - tx, game._target_enemy["y"] - ty)
                        if ted > 100:
                            game._target_enemy["inCombat"] = False
                            game._target_enemy = None
                            game._patk_cd = 0

        # 边界限制
        p["x"] = max(30, min(SCREEN_W - 238, p["x"]))
        p["y"] = max(30, min(SCREEN_H - 208, p["y"]))

        # 敌人攻击计时
        if game._patk_cd > 0:
            game._patk_cd -= 1
        for e in game.enemies:
            if e.get("dead") or not e.get("inCombat"):
                continue
            e["atkc"] = max(0, e.get("atkc", 0) - 1)
            if e["atkc"] <= 0:
                game.enemy_atk(e)
                e["atkc"] = max(30, 60 - e["lv"])

        # 玩家Debuff/DOT扣血（每秒约60帧，这里每帧扣一次，damage已均摊）
        debs = p.get("debuffs") or []
        for d in debs[:]:
            if d.get("v"):
                dmg = d["v"]
                p["hp"] = max(0, p["hp"] - dmg)
                CombatManager._add_float(game.floats, p["x"], p["y"] - 20, f"-{dmg}", (255, 80, 0))
            d["dur"] = d.get("dur", 1) - 1
            if d["dur"] <= 0:
                debs.remove(d)

        # 玩家Stun检测（冻结时跳过行动）
        if p.get("stun", 0) > 0:
            p["stun"] -= 1

        # 自动攻击（玩家走进80px范围时触发）
        if game._target_enemy:
            te = game._target_enemy
            if te.get("dead"):
                # 目标已死亡 → 清空并交给 auto_farm 找新目标
                game._target_enemy = None
            elif game._patk_cd <= 0 and te.get("inCombat"):
                dist = math.hypot(te["x"] - game.p["x"], te["y"] - game.p["y"])
                if dist < 80:
                    dx = te["x"] - game.p["x"]; dy = te["y"] - game.p["y"]
                    rd = math.hypot(dx, dy) or 1
                    game.facing_x = dx / rd; game.facing_y = dy / rd
                    audio.attack()
                    game.player_atk(te, "普通攻击")
                    game._patk_cd = 30
            elif not te.get("inCombat"):
                dist = math.hypot(te["x"] - game.p["x"], te["y"] - game.p["y"])
                if dist < 80:
                    game.start_combat(te)
                    te["inCombat"] = True

        # ── 一键挂机：自动找怪 + 技能循环 ─────────────────────
        if game.auto_farm and not p.get("stun", 0):
            # 优先锁定已有 inCombat 的怪物
            combat_enemies = [e for e in game.enemies
                              if not e.get("dead") and e.get("inCombat")]
            if combat_enemies:
                nearest = min(combat_enemies,
                              key=lambda e: math.hypot(e["x"]-p["x"], e["y"]-p["y"]))
            else:
                alive = [e for e in game.enemies if not e.get("dead")]
                nearest = min(alive, key=lambda e: math.hypot(e["x"]-p["x"], e["y"]-p["y"])) if alive else None

            if nearest:
                game._target_enemy = nearest
                dist = math.hypot(nearest["x"] - p["x"], nearest["y"] - p["y"])
                dx = nearest["x"] - p["x"]; dy = nearest["y"] - p["y"]
                rd = math.hypot(dx, dy) or 1
                game.facing_x = dx / rd; game.facing_y = dy / rd

                atk_range = 80

                # ── 每帧都设置 move_to，确保持续追击 ──────────────
                nx_ = dx / rd; ny_ = dy / rd
                p["move_to"] = (nearest["x"] - nx_ * 20, nearest["y"] - ny_ * 20)

                if dist < atk_range:
                    # ── 辅助/输出优先级判断 ──────────────────────────
                    used_skill = None
                    skill_target = nearest  # 默认对敌人释放

                    hp_ratio = p["hp"] / max(1, p["maxhp"])
                    mp_ratio = p["mp"] / max(1, p["maxmp"])

                    # 优先1：HP < 50% → 辅助技能（治愈/护盾/buff）
                    if hp_ratio < 0.5:
                        aux_skills = [skn for skn in p.get("qb", []) if skn != "普通攻击"
                                      and SKILLS.get(skn, {}).get("t") in ("heal", "shield", "buff")
                                      and game.cds.get(skn, 0) <= 0
                                      and p["mp"] >= SKILLS[skn]["mp"]]
                        if aux_skills:
                            used_skill = random.choice(aux_skills)
                            skill_target = None  # 辅助类对己方释放

                    # 优先2：HP >= 50% 但 MP < 20% → 回蓝
                    elif mp_ratio < 0.2:
                        mp_skills = [skn for skn in p.get("qb", []) if skn != "普通攻击"
                                     and SKILLS.get(skn, {}).get("t") == "heal"
                                     and game.cds.get(skn, 0) <= 0
                                     and p["mp"] >= SKILLS[skn]["mp"]]
                        if mp_skills:
                            used_skill = random.choice(mp_skills)
                            skill_target = None

                    # 优先3：HP >= 50% 且 MP >= 20% → 输出技能
                    else:
                        out_skills = []
                        for skn in p.get("qb", []):
                            if skn == "普通攻击":
                                continue
                            sk = SKILLS.get(skn, {})
                            if sk.get("t") not in ("atk", "debuf"):
                                continue
                            if game.cds.get(skn, 0) > 0 or p["mp"] < sk.get("mp", 0):
                                continue
                            shape = sk.get("shape", "single")
                            rng = sk.get("range", 60)
                            if shape == "single" and dist > rng:
                                continue
                            out_skills.append(skn)
                        if out_skills:
                            used_skill = random.choice(out_skills)

                    # 执行
                    if used_skill:
                        audio.skill_snd(used_skill)
                        game.player_atk(skill_target, used_skill)
                    elif game._patk_cd <= 0:
                        audio.attack()
                        game.player_atk(nearest, "普通攻击")
                        game._patk_cd = 30
            else:
                game._target_enemy = None
                p["move_to"] = None


    # ─── 特效更新 ───────────────────────────────────────
    for fx in game.effects[:]:
        fx.update()
        if fx.done:
            game.effects.remove(fx)

    # 浮动文字更新
    for fl in game.floats[:]:
        fl["l"] -= 1
        fl["y"] -= 0.4
        if fl["l"] <= 0:
            game.floats.remove(fl)

    # 护盾光环更新
    if game.shield_aura:
        game.shield_aura["l"] -= 10
        if game.shield_aura["l"] <= 0:
            game.shield_aura = None

    # ─── 渲染 ───────────────────────────────────────────
    if game.s == "menu":
        draw_menu(screen, game, audio)
    elif game.s == "save":
        # 存档界面时也要渲染底层游戏画面，再叠存档UI
        bg = game.map.get("bg") if game.map else "village"
        draw_bg(screen, bg)
        for e in game.enemies:
            draw_enemy(screen, e)
        if game.p:
            draw_pl(screen, game.p["x"], game.p["y"], game.p["cls"],
                    game.p["hp"]/game.p["maxhp"], game.p["mp"]/game.p["maxmp"],
                    game.p.get("buffs"), game.p.get("shield",0))
        draw_save_overlay(screen, game)
    else:
        # 游戏背景
        bg = game.map.get("bg") if game.map else "village"
        draw_bg(screen, bg)

        # 地图装饰NPC
        if game.map:
            for npc in game.map.get("npcs", []):
                nx = int(npc["x"] * (SCREEN_W - 228) + 216)
                ny = int(npc["y"] * (SCREEN_H - 260) + 56)
                draw_npc(screen, nx, ny, npc["name"], npc["tp"])

        # 敌人
        for e in game.enemies:
            draw_enemy(screen, e)

        # 玩家
        if game.p:
            sh = game.p.get("shield", 0)
            draw_pl(screen, game.p["x"], game.p["y"], game.p["cls"],
                    game.p["hp"] / game.p["maxhp"],
                    game.p["mp"] / game.p["maxmp"],
                    game.p.get("buffs"), sh)

        # 护盾光环
        if game.shield_aura and game.p:
            col = game.shield_aura.get("col", (100, 150, 255))
            ov = pygame.Surface((100, 100), pygame.SRCALPHA)
            ratio = game.shield_aura["l"] / game.shield_aura["ml"]
            pygame.draw.circle(ov, (*col, int(60 * ratio)), (50, 50), 45)
            screen.blit(ov, (int(game.p["x"] - 50), int(game.p["y"] - 50)))

        # 特效
        for fx in game.effects:
            fx.draw(screen)

        # 浮动文字
        for fl in game.floats:
            alpha = min(255, int(fl["l"] * 4.5))
            fn = pygame.font.SysFont("microsoftyahei", int(fl["sz"]), bold=True)
            img = fn.render(fl["t"], True, fl["c"])
            r = img.get_rect(center=(int(fl["x"]), int(fl["y"])))
            screen.blit(img, r)

        # UI层
        draw_ui(screen, game)

        # 商店界面
        if game.s == "shop":
            draw_shop_overlay(screen, game)

        # 对话框
        if game.s == "dialog":
            draw_dlg(screen, game)

    pygame.display.flip()

pygame.quit()
sys.exit()
