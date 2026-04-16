"""
player.py — 玩家数据与状态管理
职责：
  - 玩家状态字典 p 的初始化（new_game）
  - 属性重算 _recalc（境界/等级/装备/宠物/坐骑加成）
  - 升级 _lvlup（经验检查/突破境界/技能解锁）
  - 浮动文字 _ft / 日志 _add_log
  - 升级突破境界判定

外部依赖：
  - config.py（颜色常量）
  - data.py（CLASS_D, REALMS, SK_UNLCK）

不包含：
  - 物品操作（inventory.py 负责）
  - 装备操作（equipment.py 负责）
  - 战斗逻辑（combat.py 负责）
"""
from config import C_GOLD, C_GREEN, C_BLUE, C_TEXT, C_RED


class PlayerManager:
    """玩家状态管理（替代原 G 类的玩家部分）"""

    @staticmethod
    def new_game(p, cls):
        """初始化新游戏玩家状态"""
        from data import CLASS_D, REALMS, ITEMS
        d = CLASS_D[cls]
        r = REALMS[0]
        p.update({
            "name": d["name"] + "弟子",
            "cls": cls,
            "lv": 1,
            "exp": 0,
            "expn": 100,
            "realm": r,
            "hp": d["hp"],
            "maxhp": d["hp"],
            "mp": d["mp"],
            "maxmp": d["mp"],
            "atk": d["atk"],
            "def": d["def"],
            "crit": d["crit"],
            "dodge": d["dodge"],
            "gold": 100000,
            "x": 400,
            "y": 320,
            "sk": ["普通攻击"],
            "qb": ["普通攻击"],
            "inv": [{"id": "elixir_s", "n": 3}, {"id": "elixir_mp", "n": 2}],
            "equips": [],          # 拥有的装备列表（待穿上）
            "potion_slots": [{"id": "", "n": 0}, {"id": "", "n": 0}, {"id": "", "n": 0}],
            "eq": {"weapon": None, "armor": None, "acc": None},
            "buffs": [],
            "shield": 0,
            "pet": None,
            "mount": None,
            "mounts": [],
            "pets": [],
            "spd": 4,
            "qs": [
                {"id": "q1", "name": "初入仙途", "desc": "在水云山杀8只野猪",
                 "tp": "kill", "tgt": "野猪", "cnt": 0, "need": 8, "done": False, "rew": "100金币", "map": "shuiyun_mountain"},
                {"id": "q2", "name": "与长老对话", "desc": "与村长老对话",
                 "tp": "talk", "done": False, "rew": "50金币", "map": "shuiyun"},
            ]
        })

    @staticmethod
    def recalc(p):
        """重算玩家属性（境界/等级/装备/宠物/坐骑加成）"""
        from data import CLASS_D, REALMS
        d = CLASS_D[p["cls"]]
        r = p["realm"]

        # 基础属性 = 职业基础 + 等级成长 + 境界加成
        hp  = d["hp"]  + (p["lv"] - 1) * 12 + r["b"]["hp"]
        mp  = d["mp"]  + (p["lv"] - 1) * 6
        atk = d["atk"] + (p["lv"] - 1) * 3  + r["b"]["atk"]
        df  = d["def"] + (p["lv"] - 1) * 2  + r["b"]["def"]
        crit = d["crit"] + (p["lv"] - 1) * 0.5
        dodge = d["dodge"]

        # 装备加成（受品质倍率影响）
        quality_mult = {"white": 1, "green": 1.2, "blue": 1.5, "purple": 1.8, "orange": 2.2, "gold": 2.8}
        for sl in ["weapon", "armor", "acc"]:
            e = p["eq"][sl]
            if not e:
                continue
            mul = quality_mult.get(e.get("q", "white"), 1)
            if e.get("atk"):  atk  += int(e["atk"] * mul)
            if e.get("def"):  df   += int(e["def"] * mul)
            if e.get("hp"):   hp   += int(e["hp"] * mul)
            if e.get("crit"): crit += e["crit"]
            if e.get("dodge"): dodge += e.get("dodge", 0)

        # 宠物加成
        if p["pet"]:
            q = p["pet"]["q"]
            pct = {"凡兽":0.10,"珍兽":0.20,"灵兽":0.30,"仙兽":0.40,"神灵":0.50}.get(q, 0)
            hp  += int(p["pet"]["hp"] * pct)
            atk += int(p["pet"]["atk"] * pct)
            crit += p["pet"]["crit"] * pct

        # 速度 = 基础速度 * 坐骑速度倍率
        base_spd = d["spd"] + (p["lv"] - 1) * 0.3 + r["b"]["spd"]
        mount_spd = p["mount"]["spd"] if p["mount"] else 1.0

        # 坐骑加成（hp/atk/def/spd）
        if p["mount"]:
            mnt = p["mount"]
            if mnt.get("hp"):  hp  += mnt["hp"]
            if mnt.get("atk"): atk += mnt["atk"]
            if mnt.get("def"): df  += mnt["def"]

        # 应用
        p["maxhp"] = hp
        p["maxmp"] = mp
        p["atk"]   = atk
        p["def"]   = df
        p["spd"]   = round(base_spd * mount_spd, 2)
        p["crit"]  = crit
        p["dodge"] = dodge

        # 防止溢出
        p["hp"] = min(p["hp"], p["maxhp"])
        p["mp"] = min(p["mp"], p["maxmp"])

    @staticmethod
    def level_up(p, game_ref):
        """检查升级/突破境界/解锁技能"""
        from data import REALMS, SK_UNLCK, CLASS_D
        while p["exp"] >= p["expn"]:
            p["exp"] -= p["expn"]
            p["lv"] += 1
            p["expn"] = int(100 * (1.15 ** (p["lv"] - 1)))

            d = CLASS_D[p["cls"]]
            oh = p["maxhp"]
            p["maxhp"] = d["hp"] + (p["lv"] - 1) * 12 + p["realm"]["b"]["hp"]
            p["maxmp"] = d["mp"] + (p["lv"] - 1) * 6
            p["hp"] = p["hp"] - oh + p["maxhp"]
            p["mp"] = p["maxmp"]

            game_ref._add_log(f"升级至 Lv.{p['lv']}！", C_GOLD)
            game_ref._ft(p["x"], p["y"] - 40, f"升级! Lv.{p['lv']}", C_GOLD, 24)

            # 境界突破检测
            for i in range(len(REALMS) - 1, -1, -1):
                if p["lv"] >= REALMS[i]["min"] and i > REALMS.index(p["realm"]):
                    p["realm"] = REALMS[i]
                    p["maxhp"] += REALMS[i]["b"]["hp"]
                    p["maxmp"] += max(0, p["def"] * (i + 1) // 2)
                    p["atk"]   += REALMS[i]["b"]["atk"]
                    p["def"]   += REALMS[i]["b"]["def"]
                    p["hp"] = p["maxhp"]
                    p["mp"] = p["maxmp"]
                    game_ref._add_log(f"突破：{REALMS[i]['name']}！", C_GOLD)

            # 技能解锁提示
            for lk, names in SK_UNLCK.items():
                if p["lv"] == lk:
                    for nm in names:
                        if nm not in p["sk"]:
                            game_ref._add_log(f"可购买技能：{nm}", C_BLUE)

            PlayerManager.recalc(p)
