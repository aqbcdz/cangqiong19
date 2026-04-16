"""
equipment.py — 装备系统
职责：
  - 装备穿戴（equip: 从背包穿，equip_by_idx: 从已购列表穿）
  - 装备卸下（unequip: 回到背包，unequip_to_list: 回到已购列表）
  - 装备强化（enhance: 普通/保级）
  - 战斗力计算（cp）

外部依赖：
  - data.py（ITEMS, EN_MAX）
  - player.py（PlayerManager.recalc）
  - inventory.py（InventoryManager.give_item / take_item）

不包含：
  - 渲染（render.py 负责）
  - 商店购买（shop.py 负责）
"""
from config import C_GOLD, C_RED, C_TEXT
from data import ITEMS, EN_MAX
from inventory import InventoryManager
from player import PlayerManager


class EquipmentManager:
    """装备管理（替代原 G 类的装备相关方法）"""

    @staticmethod
    def equip(p, iid, game_ref):
        """从背包穿上装备"""
        it = ITEMS.get(iid)
        if not it:
            return
        slot_map = {"weapon": "weapon", "armor": "armor", "acc": "acc"}
        sl = slot_map.get(it["tp"])
        if not sl:
            return

        old = p["eq"][sl]
        # 旧装备放回背包
        if old:
            InventoryManager.give_item(p, old["id"])

        # 穿上新装备
        p["eq"][sl] = dict(it)
        p["eq"][sl]["id"] = iid
        p["eq"][sl]["en"] = 0
        InventoryManager.take_item(p, iid, 1)
        PlayerManager.recalc(p)
        game_ref._add_log(f"装备了 {it['name']}！", C_GOLD)

    @staticmethod
    def equip_by_idx(p, idx, game_ref):
        """从已拥有装备列表（p['equips']）穿上装备，idx为列表索引"""
        game_ref._add_log(f"[equip_by_idx] idx={idx} 进入了穿装备函数!", (255, 100, 255))
        print(f"[DEBUG equip_by_idx] START, idx={idx}, equips={len(p['equips'])}")

        if idx < 0 or idx >= len(p["equips"]):
            return

        item = p["equips"][idx]
        it = ITEMS.get(item["id"])
        if not it:
            return

        slot_map = {"weapon": "weapon", "armor": "armor", "acc": "acc"}
        sl = slot_map.get(it["tp"])
        if not sl:
            return

        # 槽位已有装备则卸下
        if p["eq"][sl]:
            EquipmentManager.unequip_to_list(p, sl, game_ref)

        # 穿上新装备
        p["eq"][sl] = dict(it)
        p["eq"][sl]["id"] = item["id"]
        p["eq"][sl]["en"] = 0
        p["equips"].pop(idx)

        PlayerManager.recalc(p)
        game_ref._add_log(f"穿上 {it['name']}！", C_GOLD)

    @staticmethod
    def unequip(p, sl, game_ref):
        """将装备从槽位卸下到背包"""
        if not p["eq"][sl] or len(p["inv"]) >= 30:
            return
        it = p["eq"][sl]
        InventoryManager.give_item(p, it["id"])
        p["eq"][sl] = None
        PlayerManager.recalc(p)

    @staticmethod
    def unequip_to_list(p, sl, game_ref):
        """将装备从槽位卸下到已拥有列表（p['equips']）"""
        it = p["eq"][sl]
        if not it:
            return
        p["equips"].append({"id": it["id"]})
        p["eq"][sl] = None
        PlayerManager.recalc(p)
        game_ref._add_log(f"卸下 {it['name']}！", C_TEXT)

    @staticmethod
    def enhance(p, sl, safe, game_ref):
        """装备强化"""
        it = p["eq"][sl]
        if not it:
            return

        lvl = it.get("en", 0)
        emax = EN_MAX.get(it.get("q", "white"), 12)

        if lvl >= emax:
            game_ref._ft(600, 300, f"已达强化上限 +{emax}！", C_RED)
            return

        if safe:
            if not InventoryManager.take_item(p, "soul_guard", 1):
                game_ref._ft(600, 300, "需要固魂石!", C_RED)
                return
            it["en"] = lvl + 1
            game_ref._ft(600, 300, f"强化成功! +{it['en']}", C_GOLD)
        else:
            rate = max(5, 100 - lvl * 8)
            if __import__("random").random() * 100 < rate:
                it["en"] = lvl + 1
                game_ref._ft(600, 300, f"强化成功! +{it['en']}", C_GOLD)
            else:
                pen = 0 if lvl < 6 else 1 if lvl < 11 else 2
                it["en"] = max(0, lvl - pen)
                msg = f"强化失败{(' -' + str(pen) + '级') if pen else ''}!"
                game_ref._ft(600, 300, msg, C_RED)

        PlayerManager.recalc(p)

    @staticmethod
    def calc_power(p):
        """计算战斗力"""
        return int(
            p["atk"] * 2 +
            p["def"] * 3 +
            p["maxhp"] * 0.5 +
            p["maxmp"] * 0.3 +
            (p["crit"] + p["dodge"]) * 5
        )
