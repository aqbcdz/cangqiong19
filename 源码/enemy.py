"""
enemy.py — 敌人与刷怪系统
职责：
  - 刷怪（spawn：根据地图生成普通/精英/Boss三类怪物）
  - 属性计算（_make_stats：根据等级+类型计算HP/ATK/DEF/SPD）
  - 品质生成（quality_for_level）

外部依赖：
  - data.py（ENEMY_TEMPLATES, ENEMY_SKILLS, WORLD）
  - random

不包含：
  - 战斗逻辑（combat.py 负责）
  - 渲染（render.py 负责）
"""
import random
from data import ENEMY_TEMPLATES, ENEMY_SKILLS


class EnemyManager:

    # ── 属性公式 ─────────────────────────────────
    # normal : HP=lv×15  ATK=lv×2   DEF=lv×0.5  SPD=lv×0.3
    # elite  : HP=lv×30  ATK=lv×4   DEF=lv×1.0  SPD=lv×0.3
    # boss   : HP=lv×90  ATK=lv×7   DEF=lv×2.5  SPD=lv×0.3
    STATS = {
        "normal": {"hp_mult": 15, "atk_mult": 2,   "def_mult": 0.5},
        "elite":  {"hp_mult": 30, "atk_mult": 4,   "def_mult": 1.0},
        "boss":   {"hp_mult": 90, "atk_mult": 7,   "def_mult": 2.5},
    }

    @staticmethod
    def _make_stats(lv, etype):
        s = EnemyManager.STATS[etype]
        return {
            "hp":   round(lv * s["hp_mult"]),
            "atk":  round(lv * s["atk_mult"], 1),
            "def":  round(lv * s["def_mult"], 1),
            "spd":  round(lv * 0.3, 1),
        }

    @staticmethod
    def quality_for_level(lv):
        r = random.random()
        if lv < 5:   return "white"
        if lv < 12:  return "green"  if r < 0.4  else "white"
        if lv < 22:  return "blue"   if r < 0.35 else "green"
        if lv < 38:  return "purple" if r < 0.3  else "blue"
        if lv < 55:  return "orange" if r < 0.25 else "purple"
        return "gold" if r < 0.15 else "orange"

    # ── 单只生成 ─────────────────────────────────
    @staticmethod
    def _spawn_one(mid, etype, x=None, y=None):
        tpl = ENEMY_TEMPLATES.get(mid)
        if not tpl:
            return None
        group = tpl.get(etype, tpl.get("normal", []))
        if etype == "boss":
            t = group
        elif etype == "elite":
            t = random.choice(group)
        else:
            t = random.choice(group)

        lv = tpl["lv"]
        st = EnemyManager._make_stats(lv, etype)

        name = t["name"]
        ic   = t["ic"]
        q    = EnemyManager.quality_for_level(lv)

        # 技能
        skills = []
        skill_cd = {}
        if etype == "elite":
            sid = t.get("skill")
            if sid and sid in ENEMY_SKILLS:
                skills = [sid]
                skill_cd = {sid: 0}
        elif etype == "boss":
            for sid in t.get("skills", []):
                if sid in ENEMY_SKILLS:
                    skills.append(sid)
            for sid in skills:
                skill_cd[sid] = 0

        enemy = {
            "x":        x if x is not None else random.randint(80, 750),
            "y":        y if y is not None else random.randint(80, 520),
            "name":     name,
            "ic":       ic,
            "lv":       lv,
            "q":        q,
            "etype":    etype,          # normal / elite / boss
            "hp":       st["hp"],
            "maxhp":    st["hp"],
            "atk":      st["atk"],
            "def":      st["def"],
            "spd":      st["spd"],
            "exp":      st["hp"] // 3,
            "gold":     st["hp"] // 5,
            "dead":     False,
            "stun":     0,
            "inCombat": False,
            "atkc":     0,
            "skills":   skills,         # [skill_id, ...]
            "skill_cd": skill_cd,       # {skill_id: remaining_cd}
            "skill_idx": 0,             # boss: 当前技能索引
            "shield":   0,
            "buffs":    [],             # [{n, t, v}, ...]
            "debuffs":  [],             # [{n, t, v, dur}, ...]
        }
        return enemy

    # ── 地图批量刷怪 ─────────────────────────────
    # 普通30只 / 精英15只 / Boss 1只
    @staticmethod
    def spawn(mid, player_level=None):
        enemies = []
        tpl = ENEMY_TEMPLATES.get(mid)
        if not tpl:
            return []

        # 普通怪 30只（3选1循环）
        normals = tpl["normal"]
        for i in range(30):
            e = EnemyManager._spawn_one(mid, "normal",
                                        x=80 + (i % 10) * 65,
                                        y=80 + (i // 10) * 90)
            if e:
                enemies.append(e)

        # 精英怪 15只（2选1循环）
        elites = tpl["elite"]
        for i in range(15):
            e = EnemyManager._spawn_one(mid, "elite",
                                        x=80 + (i % 8) * 80,
                                        y=120 + (i // 8) * 90)
            if e:
                enemies.append(e)

        # Boss 1只
        b = EnemyManager._spawn_one(mid, "boss", x=400, y=200)
        if b:
            enemies.append(b)

        return enemies
