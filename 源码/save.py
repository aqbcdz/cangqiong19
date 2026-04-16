"""
save.py — 存档系统
职责：
  - 构建存档数据（build_save）
  - 保存到文件（save_game）
  - 从文件加载（load_game）
  - 自动存档路径

外部依赖：
  - 游戏主对象（game）通过参数传入
  - json / os / time

不包含：
  - 存档UI（render.py / input.py 负责）
  - 存档列表（由调用方维护）
"""
import json
import os
import time

SAVE_VERSION = 1
SAVE_DIR = "saves"


class SaveManager:
    """存档管理器"""

    @staticmethod
    def _save_dir():
        base = os.path.dirname(os.path.abspath(__file__))
        d = os.path.join(base, SAVE_DIR)
        if not os.path.exists(d):
            os.makedirs(d)
        return d

    # ── 构建存档数据 ────────────────────────────────
    @staticmethod
    def build_save(game):
        p = game.p
        # 过滤掉循环引用和不可序列化对象
        qs = []
        for q in p.get("qs", []):
            qs.append({
                "id":    q.get("id", ""),
                "name":  q.get("name", ""),
                "desc":  q.get("desc", ""),
                "tp":    q.get("tp", ""),
                "tgt":  q.get("tgt", ""),
                "cnt":   q.get("cnt", 0),
                "need":  q.get("need", 1),
                "done":  q.get("done", False),
                "rew":   q.get("rew", ""),
                "map":   q.get("map", ""),
            })

        inv = []
        for it in p.get("inv", []):
            if it.get("id") and it.get("n", 0) > 0:
                inv.append({"id": it["id"], "n": it["n"]})

        equips = []
        for e in p.get("equips", []):
            if isinstance(e, dict) and e.get("id"):
                equips.append(e["id"])
            elif isinstance(e, str):
                equips.append(e)

        potion_slots = []
        for ps in p.get("potion_slots", []):
            if isinstance(ps, dict):
                potion_slots.append({"id": ps.get("id", ""), "n": ps.get("n", 0)})
            else:
                potion_slots.append({"id": "", "n": 0})

        return {
            "ver":    SAVE_VERSION,
            "date":   time.strftime("%Y-%m-%d %H:%M"),
            "cls":    p.get("cls", "pojun"),
            "player": {
                "name":         p.get("name", ""),
                "lv":           p.get("lv", 1),
                "exp":          p.get("exp", 0),
                "expn":         p.get("expn", 100),
                "realm":        p.get("realm", {}).get("name", "练气期") if isinstance(p.get("realm"), dict) else str(p.get("realm", "练气期")),
                "hp":           p.get("hp", 1),
                "maxhp":        p.get("maxhp", 1),
                "mp":           p.get("mp", 0),
                "maxmp":        p.get("maxmp", 1),
                "atk":          p.get("atk", 10),
                "def":          p.get("def", 5),
                "crit":         p.get("crit", 5),
                "dodge":        p.get("dodge", 3),
                "spd":          p.get("spd", 4),
                "gold":         p.get("gold", 0),
                "x":            p.get("x", 400),
                "y":            p.get("y", 320),
                "sk":           list(p.get("sk", [])),
                "qb":           list(p.get("qb", [])),
                "inv":          inv,
                "equips":       equips,
                "potion_slots": potion_slots,
                "eq": {
                    "weapon": p.get("eq", {}).get("weapon"),
                    "armor":  p.get("eq", {}).get("armor"),
                    "acc":    p.get("eq", {}).get("acc"),
                },
                "shield":       p.get("shield", 0),
                "pet":          p.get("pet"),
                "mount":        p.get("mount"),
                "mounts":       list(p.get("mounts", [])),
                "pets":         list(p.get("pets", [])),
                "qs":           qs,
            },
            "map_id":      getattr(game, "map_id", "shuiyun"),
            "settings": {
                "potion_auto": getattr(game, "potion_auto", False),
            },
        }

    # ── 保存游戏 ──────────────────────────────────
    @staticmethod
    def save_game(game, slot=0):
        data = SaveManager.build_save(game)
        cls   = data["cls"]
        lv    = data["player"]["lv"]
        # 微秒级时间戳，保证每次存档文件名唯一，绝不覆盖
        import time
        ts = f"{time.strftime('%Y%m%d-%H%M%S')}-{int(time.time() * 1e6) % 1000000:06d}"
        fname = f"save_{cls}_Lv{lv}_{ts}_s{slot}.json"
        fpath = os.path.join(SaveManager._save_dir(), fname)

        try:
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return f"存档成功：{fname}"
        except Exception as e:
            return f"存档失败：{e}"

    # ── 加载存档数据（返回 dict，不修改 game）───
    @staticmethod
    def load_save_file(slot=0):
        """从指定 slot 读取存档文件路径（slot 0=最新，其他=按时间排序第N个）"""
        d = SaveManager._save_dir()
        if not os.path.exists(d):
            return None
        files = sorted(
            [f for f in os.listdir(d) if f.endswith(".json")],
            key=lambda x: os.path.getmtime(os.path.join(d, x)),
            reverse=True
        )
        if slot >= len(files) or slot < 0:
            return None
        fpath = os.path.join(d, files[slot])
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # ── 获取存档列表（给 UI 显示用）──────────────
    @staticmethod
    @staticmethod
    def list_saves():
        d = SaveManager._save_dir()
        if not os.path.exists(d):
            return {}
        all_files = [f for f in os.listdir(d) if f.endswith(".json")]
        files = sorted(
            all_files,
            key=lambda x: os.path.getmtime(os.path.join(d, x)),
            reverse=True
        )
        # 按职业分组：{"战士": [entry, ...], "法师": [...]}
        grouped = {}
        for f in files:
            try:
                with open(os.path.join(d, f), "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    cls = data.get("cls", "?")
                    entry = {
                        "file": f,
                        "cls":  cls,
                        "lv":   data.get("player", {}).get("lv", "?"),
                        "date": data.get("date", "?"),
                        "ver":  data.get("ver", 0),
                    }
                    if cls not in grouped:
                        grouped[cls] = []
                    grouped[cls].append(entry)
            except Exception:
                pass
        return grouped
    def apply_save(game, data):
        """把加载的存档数据应用到 game 对象"""
        from data import CLASS_D, REALMS
        p = game.p
        pd = data.get("player", {})

        # 基础属性
        p["name"]  = pd.get("name", "弟子")
        p["cls"]   = pd.get("cls", "pojun")
        p["lv"]    = pd.get("lv", 1)
        p["exp"]   = pd.get("exp", 0)
        p["expn"]  = pd.get("expn", 100)
        p["hp"]    = pd.get("hp", 1)
        p["maxhp"] = pd.get("maxhp", 1)
        p["mp"]    = pd.get("mp", 0)
        p["maxmp"] = pd.get("maxmp", 1)
        p["atk"]   = pd.get("atk", 10)
        p["def"]   = pd.get("def", 5)
        p["crit"]  = pd.get("crit", 5)
        p["dodge"] = pd.get("dodge", 3)
        p["spd"]   = pd.get("spd", 4)
        p["gold"]  = pd.get("gold", 0)
        p["x"]     = pd.get("x", 400)
        p["y"]     = pd.get("y", 320)

        # 境界
        realm_name = pd.get("realm", "练气期")
        for r in REALMS:
            if r["name"] == realm_name:
                p["realm"] = r
                break
        else:
            p["realm"] = REALMS[0]

        # 技能
        p["sk"] = list(pd.get("sk", ["普通攻击"]))
        p["qb"] = list(pd.get("qb", ["普通攻击"]))

        # 背包
        p["inv"] = list(pd.get("inv", []))

        # 装备列表
        p["equips"] = list(pd.get("equips", []))

        # 药品槽
        p["potion_slots"] = list(pd.get("potion_slots", [
            {"id": "", "n": 0}, {"id": "", "n": 0}, {"id": "", "n": 0}
        ]))

        # 穿戴装备
        eq_data = pd.get("eq", {})
        p["eq"] = {
            "weapon": eq_data.get("weapon"),
            "armor":  eq_data.get("armor"),
            "acc":    eq_data.get("acc"),
        }

        p["shield"] = pd.get("shield", 0)
        p["buffs"]  = []
        p["pet"]    = pd.get("pet")
        p["mount"]  = pd.get("mount")
        p["mounts"] = list(pd.get("mounts", []))
        p["pets"]   = list(pd.get("pets", []))

        # 任务
        p["qs"] = list(pd.get("qs", []))

        # 地图
        mid = data.get("map_id", "shuiyun")
        game.map_id = mid

        # 设置
        game.potion_auto = data.get("settings", {}).get("potion_auto", False)

        # 重新计算属性（装备/境界加成）
        from player import PlayerManager
        PlayerManager.recalc(p)

        # 加载地图（触发刷怪）
        from map import MapManager
        MapManager.load_map(game, mid, __import__("audio", fromlist=["get_audio"]).get_audio())

        return f"读档成功：{pd.get('name', '')} Lv{pd.get('lv', 1)}"
