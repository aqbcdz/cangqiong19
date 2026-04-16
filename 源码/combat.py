"""
combat.py — 战斗系统
职责：
  - 玩家攻击（player_atk：技能释放/伤害计算）
  - 敌人攻击（enemy_atk：敌人回合）
  - 伤害计算（_dmg）
  - 击杀处理（_kill：掉落/经验/任务）
  - 战斗状态开启（start_combat）
  - 战斗特效触发（调用 effects.SE）
  - 自动喝药（_auto_drink_potion）

外部依赖：
  - data.py（SKILLS, ITEMS）
  - audio.py（Audio 实例）
  - effects.py（SE 类）

不包含：
  - 渲染（render.py 负责）
  - 玩家状态修改（player.py 负责）
"""
import random
import math
from config import C_RED, C_BLUE, C_GOLD, C_GREEN, C_TEXT
from data import SKILLS, ITEMS, ENEMY_SKILLS


class CombatManager:
    """战斗管理（替代原 G 类的战斗方法）"""

    @staticmethod
    def start_combat(enemies, e, logs_ref):
        """开启与敌人的战斗状态"""
        e["inCombat"] = True
        e["atkc"] = 0
        logs_ref._add_log(f"与 {e['name']} 交战！", C_RED)

    @staticmethod

    @staticmethod
    def _skill_targets(p, enemies, sk, facing_x, facing_y):
        """
        根据技能形状 + 玩家面向方向，找出所有符合条件的敌人。
        p: 玩家字典（含 x, y）
        enemies: 活着的敌人列表
        sk: 技能配置字典
        facing_x, facing_y: 面向方向的单位向量 (dx/r, dy/r)
        返回: [(enemy, hit_x, hit_y), ...] 命中敌人及命中位置
        """
        import math
        px, py = p["x"], p["y"]
        shape = sk.get("shape", "single")
        rng   = sk.get("range", 60)
        radius= sk.get("radius", 0)
        alive = [e for e in enemies if not e.get("dead")]

        hits = []

        if shape == "single":
            candidates = []
            for e in alive:
                ex, ey = e["x"], e["y"]
                dist = math.hypot(ex - px, ey - py)
                if dist <= rng:
                    dx, dy = ex - px, ey - py
                    r = math.hypot(dx, dy) or 1
                    dot = (dx / r) * facing_x + (dy / r) * facing_y
                    candidates.append((dot, dist, e, ex, ey))
            if candidates:
                # 优先正面方向 > 其次最近距离
                candidates.sort(reverse=True)
                _, _, best_e, hx, hy = min(candidates, key=lambda x: x[1])
                hits.append((best_e, hx, hy))

        elif shape == "circle":
            # 落点在面向方向最远处
            if enemies:
                candidates = []
                for e in alive:
                    dx, dy = e["x"] - px, e["y"] - py
                    r = math.hypot(dx, dy) or 1
                    dot = (dx/r)*facing_x + (dy/r)*facing_y
                    if dot > 0:
                        candidates.append((dot, math.hypot(dx, dy), e))
                if candidates:
                    candidates.sort(reverse=True)
                    _, _, best_e = candidates[0]
                    cx, cy = best_e["x"], best_e["y"]
                else:
                    cx = px + facing_x * rng
                    cy = py + facing_y * rng
            else:
                cx = px + facing_x * rng
                cy = py + facing_y * rng
            for e in alive:
                if math.hypot(e["x"] - cx, e["y"] - cy) <= radius:
                    hits.append((e, cx, cy))

        elif shape == "cone":
            deg = math.radians(sk.get("cone_deg", 90) / 2)
            cr  = radius or rng
            for e in alive:
                dx, dy = e["x"] - px, e["y"] - py
                dist = math.hypot(dx, dy)
                if dist < 1 or dist > cr:
                    continue
                dot = (dx/dist)*facing_x + (dy/dist)*facing_y
                angle = math.acos(max(-1, min(1, dot)))
                if angle <= deg:
                    hits.append((e, e["x"], e["y"]))

        elif shape == "rect":
            w  = sk.get("width", 80)
            ln = sk.get("length", rng)
            px_, py_ = -facing_y, facing_x
            for e in alive:
                dx, dy = e["x"] - px, e["y"] - py
                dist = math.hypot(dx, dy)
                if dist < 1:
                    continue
                along  = dx * facing_x + dy * facing_y
                across = abs(dx * px_ + dy * py_)
                if 0 <= along <= ln and across <= w / 2:
                    hits.append((e, e["x"], e["y"]))

        elif shape == "self":
            r = radius or 80
            for e in alive:
                if math.hypot(e["x"] - px, e["y"] - py) <= r:
                    hits.append((e, px, py))

        return hits

    @staticmethod
    def player_attack(p, enemies, skname, cds, auto, effects_list, floats_list,
                      logs_ref, audio_ref, shield_ref=None, facing_x=1, facing_y=0):
        """
        玩家施放技能（范围感知，无锁定）。
        facing_x/facing_y: 玩家面向方向单位向量（默认向右）
        """
        import math
        sk = SKILLS.get(skname, SKILLS["普通攻击"])

        if p["mp"] < sk["mp"]:
            logs_ref._ft(p["x"], p["y"] - 30, "灵力不足!", C_RED)
            return
        if cds.get(skname, 0) > 0:
            logs_ref._ft(p["x"], p["y"] - 30, "冷却中!", C_RED)
            return

        p["mp"] -= sk["mp"]
        if sk["cd"] > 0:
            cds[skname] = sk["cd"]

        audio_ref.skill_snd(skname)

        # 找出范围内敌人
        hits = CombatManager._skill_targets(p, enemies, sk, facing_x, facing_y)

        # 特效落点
        shape = sk.get("shape", "single")
        if shape == "self":
            ef_x, ef_y = p["x"], p["y"] - 30
        elif hits:
            ef_x = sum(e["x"] for e, _, _ in hits) / len(hits)
            ef_y = sum(e["y"] for e, _, _ in hits) / len(hits) - 20
        else:
            rng = sk.get("range", 60)
            ef_x = p["x"] + facing_x * rng
            ef_y = p["y"] + facing_y * rng - 20

        from effects import SE
        effects_list.append(SE(skname, ef_x, ef_y, p["x"], p["y"],
                              sk.get("mg", False), False, None))

        t = sk["t"]

        if t == "atk":
            CombatManager._do_skill_atk(p, enemies, hits, sk, effects_list,
                                        floats_list, logs_ref, audio_ref)

        elif t == "debuf":
            CombatManager._do_skill_debuf(p, enemies, hits, sk, effects_list,
                                          floats_list, logs_ref, audio_ref)

        elif t == "heal":
            amount = int(p["maxhp"] * sk["pct"])
            p["hp"] = min(p["maxhp"], p["hp"] + amount)
            CombatManager._add_float(floats_list, p["x"], p["y"] - 30, f"+{amount}", C_GREEN)
            logs_ref._add_log(f"{skname}恢复{amount}HP！", C_GREEN)

        elif t == "buff":
            dur = sk.get("dur", 3)
            bv  = sk.get("bv", 0)
            bt  = sk.get("bt", "atk")
            p["buffs"].append({"n": skname, "t": dur, "bt": bt, "bv": bv})
            logs_ref._add_log(f"{skname}！{bt}+{int(bv*100)}%", C_BLUE)
            if skname == "不动如山":
                sh_val = int(p["maxhp"] * 0.3)
                p["shield"] = p.get("shield", 0) + sh_val
                if shield_ref:
                    shield_ref["l"] = 600; shield_ref["ml"] = 600
                    shield_ref["col"] = (232, 200, 122)
                logs_ref._add_log(f"护盾+{sh_val}", C_BLUE)
            elif skname == "冰封术":
                sh_val = int(p["maxhp"] * 0.2)
                p["shield"] = p.get("shield", 0) + sh_val
                logs_ref._add_log(f"寒冰护体！护盾+{sh_val}", C_BLUE)
            p["mp"] = min(p["maxmp"], p["mp"] + int(sk["mp"] * 0.5))

        # BUFF 递减
        p["buffs"] = [b for b in p["buffs"] if b.get("t", 1) > 0]
        for b in p["buffs"]:
            b["t"] -= 1

        if auto:
            import pygame
            pygame.time.set_timer(pygame.USEREVENT + 1, 1000)

    @staticmethod
    def _do_skill_atk(p, enemies, hits, sk, effects_list, floats_list, logs_ref, audio_ref):
        """处理技能攻击伤害"""
        if not hits:
            logs_ref._ft(p["x"], p["y"] - 30, "空放!", C_TEXT)
            return
        killed = []
        for e, _, _ in hits:
            d = CombatManager._calc_damage(p, e, sk)
            e["hp"] = max(0, e["hp"] - d)
            CombatManager._add_float(floats_list, e["x"], e["y"] - 20, f"-{d}", C_RED)
            audio_ref.hit()
            if sk.get("stun") and e["hp"] > 0:
                e["stun"] = max(e.get("stun", 0), sk["stun"])
                logs_ref._add_log(f"{e['name']}被冻结！", C_BLUE)
            if e["hp"] <= 0:
                killed.append(e)
        for e in killed:
            CombatManager._kill(p, e, enemies, logs_ref, audio_ref, floats_list, effects_list)
        # 吸血
        total = sum(max(0, CombatManager._calc_damage(p, e, sk))
                    for e, _, _ in hits if e.get("hp", 0) > 0)
        if sk.get("ls"):
            ls_amt = int(total * sk["ls"])
            p["hp"] = min(p["maxhp"], p["hp"] + ls_amt)
            if ls_amt > 0:
                CombatManager._add_float(floats_list, p["x"], p["y"] - 30, f"+{ls_amt}", C_GREEN)

    @staticmethod
    def _do_skill_debuf(p, enemies, hits, sk, effects_list, floats_list, logs_ref, audio_ref):
        """处理 debuf 类技能（伤害+控制）"""
        if not hits:
            logs_ref._ft(p["x"], p["y"] - 30, "空放!", C_TEXT)
            return
        dot_dmg = int(p["atk"] * sk.get("pct", 0.8))
        killed = []
        for e, _, _ in hits:
            d = CombatManager._calc_damage(p, e, sk)
            e["hp"] = max(0, e["hp"] - d)
            CombatManager._add_float(floats_list, e["x"], e["y"] - 20, f"-{d}", C_BLUE)
            stun_dur = sk.get("stun", 0)
            if stun_dur > 0:
                e["stun"] = max(e.get("stun", 0), stun_dur)
            if sk.get("dot"):
                e.setdefault("debuffs", []).append({"n": sk["name"], "dur": sk.get("dur", 3),
                                                      "v": max(1, dot_dmg // 3)})
            if e["hp"] <= 0:
                killed.append(e)
        for e in killed:
            CombatManager._kill(p, e, enemies, logs_ref, audio_ref, floats_list, effects_list)
        total_dmg = sum(max(0, CombatManager._calc_damage(p, e, sk))
                        for e, _, _ in hits if e.get("hp", 0) > 0)
        if sk.get("ls"):
            heal = int(total_dmg * sk["ls"])
            p["hp"] = min(p["maxhp"], p["hp"] + heal)
            CombatManager._add_float(floats_list, p["x"], p["y"] - 30, f"+{heal}", C_GREEN)

    @staticmethod
    def _calc_damage(atk, defn, sk):
        """伤害计算"""
        a = atk["atk"]
        for b in atk.get("buffs", []):
            if b["bt"] == "atk":
                a = int(a * (1 + b["bv"]))
        df = defn.get("def", 5)
        if sk.get("mg"):
            a = int(a * 1.3)
            df = int(df * 0.7)
        for b in atk.get("buffs", []):
            if b["n"] == "不动如山":
                df = int(df * 1.5)

        crit_dmg = 1.8
        dmg = max(1, int(a * sk.get("pct", 1.0)))
        dmg = int(dmg * random.uniform(0.9, 1.1))
        df2 = int(df * (0.5 if sk.get("mg") else 1.0))
        dmg = max(1, dmg - df2)
        if random.random() < atk["crit"] / 100:
            dmg = int(dmg * crit_dmg)
        return max(1, dmg)

    @staticmethod
    def enemy_attack(p, e, effects_list, floats_list, logs_ref, audio_ref):
        """敌人攻击玩家（精英/Boss使用技能，普通怪纯普攻）"""
        etype = e.get("etype", "normal")

        # 眩晕检查
        if e.get("stun", 0) > 0:
            e["stun"] -= 1
            logs_ref._add_log(f"{e['name']}被冻结，跳过！", C_BLUE)
            return

        # Buff/Debuff 持续时间递减
        for b in (e.get("buffs") or [])[:]:
            b["t"] -= 1
            if b["t"] <= 0:
                e["buffs"].remove(b)
        for d in (e.get("debuffs") or [])[:]:
            d["dur"] = d.get("dur", 1) - 1
            if d.get("dur", 1) <= 0:
                e["debuffs"].remove(d)

        # ── 精英/Boss：优先放技能 ────────────────
        used_skill = None
        if etype in ("elite", "boss") and e.get("skills"):
            # 找当前可用的技能（cd == 0）
            cds = e.get("skill_cd", {})
            if etype == "boss":
                # Boss：轮转技能列表
                idx = e.get("skill_idx", 0)
                for _ in range(len(e["skills"])):
                    sid = e["skills"][idx]
                    cd = cds.get(sid, 0)
                    if cd <= 0 and sid in ENEMY_SKILLS:
                        used_skill = sid
                        e["skill_idx"] = (idx + 1) % len(e["skills"])
                        break
                    idx = (idx + 1) % len(e["skills"])
            else:
                # 精英：随机选一个 cd=0 的技能
                for sid in e["skills"]:
                    if cds.get(sid, 0) <= 0 and sid in ENEMY_SKILLS:
                        used_skill = sid
                        break

        # 执行技能或普攻
        if used_skill:
            CombatManager._do_enemy_skill(p, e, used_skill, effects_list, floats_list, logs_ref, audio_ref)
            # 设置技能冷却
            sk_data = ENEMY_SKILLS.get(used_skill, {})
            cd_val = sk_data.get("cd", 3)
            e.setdefault("skill_cd", {})[used_skill] = cd_val
        else:
            # 普通攻击
            CombatManager._enemy_basic_atk(p, e, floats_list, logs_ref, audio_ref)

        # 技能冷却全局递减
        for sid in list(e.get("skill_cd", {}).keys()):
            if e["skill_cd"][sid] > 0:
                e["skill_cd"][sid] -= 1

        # ── 玩家死亡检测 ──────────────────────────
        if p["hp"] <= 0:
            p["hp"] = 0
            audio_ref.death()
            logs_ref._add_log("你被击败了...", C_RED)
            logs_ref._ft(p["x"], p["y"] - 40, "你被击败了...", C_RED, 28)
            p["hp"] = int(p["maxhp"] * 0.3)
            for x in p.get("enemies", []):
                x["inCombat"] = False

    @staticmethod
    def _enemy_basic_atk(p, e, floats_list, logs_ref, audio_ref):
        """敌人普通攻击"""
        if p.get("invincible", False):
            CombatManager._add_float(floats_list, p["x"], p["y"] - 20, "无敌!", (255, 200, 50))
            return
        dmg = max(1, int(e["atk"] - p["def"] * 0.8))
        sh = p.get("shield", 0)
        if sh > 0:
            ab = min(sh, dmg); sh -= ab; dmg -= ab; p["shield"] = sh
        p["hp"] = max(0, p["hp"] - dmg)
        CombatManager._add_float(floats_list, p["x"], p["y"] - 20, f"-{dmg}", C_RED)
        audio_ref.hit()
        logs_ref._add_log(f"{e['name']}普攻造成{dmg}伤害！", C_RED)

    @staticmethod
    def _do_enemy_skill(p, e, sid, effects_list, floats_list, logs_ref, audio_ref):
        """执行敌人技能（精英/Boss）"""
        if p.get("invincible", False):
            CombatManager._add_float(floats_list, p["x"], p["y"] - 20, "无敌!", (255, 200, 50))
            return
        sk = ENEMY_SKILLS.get(sid, {})
        skname = sk.get("name", sid)
        logs_ref._add_log(f"{e['name']}施展「{skname}」！", C_BLUE)

        t = sk.get("t", "dmg")
        mult = sk.get("dmg", 0)
        atk = e["atk"]
        is_aoe = sk.get("aoe", False)
        hits = sk.get("hits", 1)

        # 播放技能特效
        from effects import SE
        effects_list.append(SE(sid, p["x"], p["y"] - 30, e["x"], e["y"], sk.get("mg", False), is_aoe, None))

        if t == "dmg":
            # 伤害技能
            for _ in range(hits):
                dmg = max(1, int(atk * mult - p["def"] * 0.5))
                sh = p.get("shield", 0)
                if sh > 0:
                    ab = min(sh, dmg); sh -= ab; dmg -= ab; p["shield"] = sh
                p["hp"] = max(0, p["hp"] - dmg)
                CombatManager._add_float(floats_list, p["x"], p["y"] - 20, f"-{dmg}", C_RED)
            audio_ref.hit()
            logs_ref._add_log(f"{e['name']}「{skname}」造成{dmg}伤害！", C_RED)

        elif t == "dot":
            # 持续伤害（跳字）
            dot_dmg = max(1, int(atk * mult))
            p["hp"] = max(0, p["hp"] - dot_dmg)
            CombatManager._add_float(floats_list, p["x"], p["y"] - 20, f"-{dot_dmg}/s", (255, 100, 0))
            e.setdefault("debuffs", []).append({"n": skname, "dur": sk.get("dur", 3), "v": dot_dmg})
            logs_ref._add_log(f"{e['name']}「{skname}」附加持续伤害！", C_BLUE)

        elif t == "heal":
            heal = int(e["maxhp"] * sk.get("heal_val", 0.3))
            e["hp"] = min(e["maxhp"], e["hp"] + heal)
            CombatManager._add_float(floats_list, e["x"], e["y"] - 20, f"+{heal}", C_GREEN)
            logs_ref._add_log(f"{e['name']}「{skname}」恢复{heal}HP！", C_GREEN)

        elif t == "shield":
            val = int(e["maxhp"] * sk.get("shield_val", 0.5))
            e["shield"] = e.get("shield", 0) + val
            CombatManager._add_float(floats_list, e["x"], e["y"] - 30, f"护盾+{val}", C_BLUE)
            logs_ref._add_log(f"{e['name']}「{skname}」获得护盾！", C_BLUE)

        elif t == "buff":
            b = {"n": skname, "t": sk.get("dur", 3)}
            if sk.get("batk"):   b["batk"] = sk["batk"]
            if sk.get("dodge"):  b["dodge"] = sk["dodge"]
            e.setdefault("buffs", []).append(b)
            CombatManager._add_float(floats_list, e["x"], e["y"] - 30, skname, C_GOLD)
            logs_ref._add_log(f"{e['name']}「{skname}」自身强化！", C_GOLD)

        elif t == "debuf":
            d = {"n": skname, "dur": sk.get("dur", 3)}
            if sk.get("bdef"):  d["bdef"] = sk["bdef"]
            if sk.get("slow"):  d["slow"] = sk["slow"]
            p.setdefault("debuffs", []).append(d)
            CombatManager._add_float(floats_list, p["x"], p["y"] - 30, skname, (200, 100, 255))
            logs_ref._add_log(f"{p['name']}被「{skname}」弱化了！", C_BLUE)

        elif t == "stun":
            p["stun"] = sk.get("dur", 2)
            CombatManager._add_float(floats_list, p["x"], p["y"] - 30, "冻结!", C_BLUE, 20)
            logs_ref._add_log(f"{p['name']}被「{skname}」冻结了！", C_BLUE)

    @staticmethod
    def _kill(p, e, enemies, logs_ref, audio_ref, floats_list, effects_list):
        """处理敌人死亡"""
        e["dead"] = True
        e["inCombat"] = False
        logs_ref._add_log(f"击杀 {e['name']}！", C_GOLD)
        CombatManager._add_float(floats_list, e["x"], e["y"] - 30, "击杀!", C_GOLD, 22)
        # 清除死亡目标引用，防止空放
        if getattr(logs_ref, '_target_enemy', None) is e:
            logs_ref._target_enemy = None
        # 即时补充一只新怪物
        if logs_ref.map:
            from enemy import EnemyManager
            mid = logs_ref.map.get("id") if logs_ref.map else None
            new_enemy = EnemyManager._spawn_one(mid, "normal") if mid else None
            if new_enemy:
                enemies.append(new_enemy)
        audio_ref.coin()

        # 经验和金币
        p["gold"] += e.get("gold", 5)
        p["exp"] += e.get("exp", 10)

        # 升级检测
        logs_ref._lvlup()

        # 任务进度
        for q in p.get("qs", []):
            if not q.get("done") and q.get("tp") == "kill" and q.get("tgt") == e["name"]:
                q["cnt"] = min(q["cnt"] + 1, q["need"])
                if q["cnt"] >= q["need"]:
                    q["done"] = True
                    logs_ref._add_log(f"任务完成：{q['name']}！", C_GOLD)
                    CombatManager._give_reward(p, q.get("rew", ""), logs_ref, floats_list)

        # 随机掉落
        if random.random() < 0.55:
            r = random.random()
            cum = 0
            for did, ch in [
                ("elixir_s", 0.25), ("elixir_mp", 0.15), ("elixir_b", 0.08),
                ("gold_elixir", 0.05), ("soul_stone", 0.12), ("enhance_stone", 0.10)
            ]:
                cum += ch
                if r < cum:
                    from inventory import InventoryManager
                    InventoryManager.give_item(p, did, 1)
                    CombatManager._add_float(floats_list, e["x"], e["y"] - 50,
                                            f"+{ITEMS[did]['name']}", C_GOLD)
                    break

    @staticmethod
    def _give_reward(p, s, logs_ref, floats_list):
        """发放任务奖励"""
        if not s:
            return
        import re
        if "金币" in s:
            amt = int(re.search(r"\d+", s).group())
            p["gold"] += amt
            logs_ref._add_log(f"获得{amt}金币", C_GOLD)

    @staticmethod
    def _add_float(floats_list, x, y, t, c, sz=20):
        """添加浮动文字"""
        floats_list.append({"x": x, "y": y, "t": t, "c": c, "sz": sz, "l": 55, "ml": 55})

    @staticmethod
    def auto_drink_potion(p, potion_slots, floats_list):
        """自动喝药（血量<30%时）"""
        if p["hp"] > p["maxhp"] * 0.3:
            return
        for slot in potion_slots:
            from inventory import InventoryManager
            iid = slot.get("id")
            if not iid:
                continue
            # 找到对应的消耗品
            if iid in ("elixir_s", "elixir_mp", "elixir_b", "elixir_mp_b", "gold_elixir"):
                if InventoryManager.use_item(p, iid, None):
                    CombatManager._add_float(floats_list, p["x"], p["y"] - 40, f"自动喝药", C_GREEN)
                    break
