"""
inventory.py — 背包与物品管理系统
职责：
  - 物品增加（give_item：堆叠或新增）
  - 物品减少（take_item：堆叠不足时删除）
  - 物品使用（use_item：消耗品效果）
  - 背包格子数量检查

外部依赖：
  - data.py（ITEMS 物品定义）

不包含：
  - 装备穿戴/卸下（equipment.py 负责）
  - 商店购买/出售（shop.py 负责）
"""
from config import C_GREEN, C_BLUE


class InventoryManager:
    """背包物品管理（替代原 G 类的物品操作部分）"""

    @staticmethod
    def give_item(p, iid, n=1):
        """增加物品到背包，尝试堆叠"""
        for iv in p["inv"]:
            if iv["id"] == iid:
                iv["n"] += n
                return
        # 无法堆叠则新增条目
        p["inv"].append({"id": iid, "n": n})

    @staticmethod
    def take_item(p, iid, n=1):
        """从背包减少物品，返回是否成功"""
        for i, iv in enumerate(p["inv"]):
            if iv["id"] == iid:
                iv["n"] -= n
                if iv["n"] <= 0:
                    p["inv"].pop(i)
                return True
        return False

    @staticmethod
    def use_item(p, iid, game_ref):
        """使用消耗品，应用效果并从背包扣除"""
        if iid == "elixir_s":
            heal = int(p["maxhp"] * 0.15)
            p["hp"] = min(p["maxhp"], p["hp"] + heal)
            game_ref._add_log(f"+{heal}HP", C_GREEN)
        elif iid == "elixir_mp":
            heal = int(p["maxmp"] * 0.20)
            p["mp"] = min(p["maxmp"], p["mp"] + heal)
            game_ref._add_log(f"+{heal}MP", C_BLUE)
        elif iid == "elixir_b":
            heal = int(p["maxhp"] * 0.30)
            p["hp"] = min(p["maxhp"], p["hp"] + heal)
            game_ref._add_log(f"+{heal}HP", C_GREEN)
        elif iid == "elixir_mp_b":
            heal = int(p["maxmp"] * 0.40)
            p["mp"] = min(p["maxmp"], p["mp"] + heal)
            game_ref._add_log(f"+{heal}MP", C_BLUE)
        elif iid == "gold_elixir":
            p["hp"] = p["maxhp"]
            p["mp"] = p["maxmp"]
            game_ref._add_log("完全恢复！", C_GREEN)
        else:
            return False
        InventoryManager.take_item(p, iid, 1)
        return True

    @staticmethod
    def get_item_count(p, iid):
        """查询背包中某物品数量"""
        for iv in p["inv"]:
            if iv["id"] == iid:
                return iv["n"]
        return 0

    @staticmethod
    def has_space(p, max_slots=30):
        """检查背包是否有空位"""
        return len(p["inv"]) < max_slots
