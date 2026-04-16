"""商店管理"""
from config import C_GOLD, C_RED, C_TEXT, C_GREEN
from inventory import InventoryManager
from data import MOUNTS, PETS, ITEMS, SKILLS, SHOP_ITEMS


class ShopManager:

    @staticmethod
    def show_shop(game_ref):
        gs = [
            ("elixir_s", "初级丹药", 20, "+30HP"),
            ("elixir_mp", "初级灵露", 15, "+20MP"),
            ("elixir_b", "中级丹药", 80, "+80HP"),
            ("gold_elixir", "金创丹", 300, "完全恢复"),
            ("enhance_stone", "强化石", 50, "材料"),
            ("soul_guard", "固魂石", 200, "保级"),
        ]
        lines = ["杂货商 - 欢迎！"]
        for i, (gid, gn, gc2, gd) in enumerate(gs):
            lines.append(f"{i + 1}. {gn} ({gc2}金币) {gd}")
        game_ref.dlg = {"title": "杂货商", "body": "\n".join(lines)}
        game_ref.dlg_btns = [str(i + 1) for i in range(len(gs))] + ["关闭"]
        game_ref.dlg_i = 0
        game_ref.s = "dialog"

        def cb(idx):
            if idx < len(gs):
                gid, gn, gc2, gd = gs[idx]
                p = game_ref.p
                if p["gold"] < gc2:
                    game_ref._add_log("金币不足！", C_RED)
                else:
                    p["gold"] -= gc2
                    potion_ids = {"elixir_s", "elixir_mp", "elixir_b", "elixir_mp_b", "gold_elixir"}
                    if gid in potion_ids:
                        for slot in p["potion_slots"]:
                            if slot["id"] == gid:
                                slot["n"] += 1
                                game_ref._add_log(f"购买 {gn}！", C_GOLD)
                                game_ref.s = "shop"
                                return
                    InventoryManager.give_item(p, gid, 1)
                    game_ref._add_log(f"购买 {gn}！", C_GOLD)
            game_ref.s = "shop"
        game_ref.dlg_cb = cb

    @staticmethod
    def auto_drink(p, game_ref=None):
        """自动喝药（血或灵力任一低于60%就补，不分优先级）"""
        from inventory import InventoryManager
        slots = p.get("potion_slots", [])
        if not slots:
            return
        # 血和蓝都已达60%以上，停止
        if p["hp"] >= p["maxhp"] * 0.6 and p["mp"] >= p["maxmp"] * 0.6:
            return
        # 血或蓝低于60%，从槽里找对应药喝
        for i, slot in enumerate(slots):
            iid = slot.get("id", "")
            if InventoryManager.get_item_count(p, iid) <= 0:
                continue
            # 蓝药：MP未满60%
            if iid in ("elixir_mp_b", "elixir_mp", "gold_elixir") and p["mp"] < p["maxmp"] * 0.6:
                ShopManager._consume_potion_slot(p, i, game_ref)
                return
            # 血药：HP未满60%
            if iid in ("elixir_b", "elixir_s", "gold_elixir") and p["hp"] < p["maxhp"] * 0.6:
                ShopManager._consume_potion_slot(p, i, game_ref)
                return

    @staticmethod
    def auto_buy(p, game_ref):
        """
        自动买药：检测每个药品槽，当绑定药品的背包数量 < 20 时自动购买50瓶补满。
        仅在自动买药开关开启时生效。
        """
        from inventory import InventoryManager
        from data import ITEMS
        slots = p.get("potion_slots", [])
        bought_any = False
        for slot in slots:
            iid = slot.get("id", "")
            if not iid:
                continue
            cnt = InventoryManager.get_item_count(p, iid)
            if cnt >= 20:
                continue
            # 从SHOP_ITEMS查价格（价格不在ITEMS里）
            price = 0
            item = None
            for cat_items in SHOP_ITEMS.values():
                for it in cat_items:
                    if it.get("id") == iid:
                        price = it.get("price", 0)
                        item = it
                        break
                if price:
                    break
            if price <= 0:
                continue
            buy_qty = getattr(game_ref, 'potion_buy_qty', 50)
            qty = min(buy_qty, p["gold"] // price, 99)
            if qty <= 0:
                continue
            total = price * qty
            p["gold"] -= total
            InventoryManager.give_item(p, iid, qty)
            # 同步更新槽的 n 值
            slot["n"] = InventoryManager.get_item_count(p, iid)
            bought_any = True
            if game_ref:
                game_ref._add_log(f"自动购买 {item.get('name', iid)} ×{qty}！", C_GOLD)
        if bought_any:
            from audio import get_audio
            get_audio().coin()

    @staticmethod
    def _consume_potion_slot(p, idx, game_ref):
        """消费快捷栏第idx格（从背包扣药，更新槽显示数量，设置2秒potion_cd）"""
        from inventory import InventoryManager
        slots = p.get("potion_slots", [])
        if idx < 0 or idx >= len(slots):
            return
        slot = slots[idx]
        iid = slot.get("id", "")
        if not iid:
            return
        cnt = InventoryManager.get_item_count(p, iid)
        if cnt <= 0:
            slot["id"] = ""
            slot["n"] = 0
            return
        # 从背包消耗1个，然后使用
        InventoryManager.take_item(p, iid, 1)
        InventoryManager.use_item(p, iid, game_ref)
        # 更新槽位显示为背包剩余数量
        remaining = InventoryManager.get_item_count(p, iid)
        if remaining <= 0:
            slot["id"] = ""
            slot["n"] = 0
        else:
            slot["n"] = remaining

    @staticmethod
    def use_potion(p, idx, floats_ref, game_ref):
        """手动使用快捷栏药品（F1/F2/F3 或点击槽位）"""
        slots = p.get("potion_slots", [])
        if idx < 0 or idx >= len(slots):
            return
        slot = slots[idx]
        iid = slot.get("id", "")
        if not iid:
            return
        from inventory import InventoryManager
        cnt = InventoryManager.get_item_count(p, iid)
        if cnt <= 0:
            # 背包已空，槽位自动清空
            slot["id"] = ""
            slot["n"] = 0
            return
        # 检查是否可喝（满属性限制）
        hp_full = (p["hp"] >= p["maxhp"])
        mp_full = (p["mp"] >= p["maxmp"])
        hp_potion = (iid in ("elixir_s", "elixir_b"))
        mp_potion = (iid in ("elixir_mp", "elixir_mp_b"))
        if iid == "gold_elixir":
            if hp_full and mp_full:
                return
        else:
            if hp_potion and hp_full:
                return
            if mp_potion and mp_full:
                return
        # 检查冷却中不允许喝
        if game_ref is not None and game_ref.potion_cd > 0:
            return
        # 手动喝药设置2秒冷却
        if game_ref is not None:
            game_ref.potion_cd = 2
        # 通过统一消费逻辑消耗（从背包扣1，更新槽显示）
        ShopManager._consume_potion_slot(p, idx, game_ref)

    @staticmethod
    def assign_potion(p, idx, iid):
        """绑定快捷栏第idx格到指定药品（不退背包，槽显示背包剩余量）"""
        from inventory import InventoryManager
        slots = p.get("potion_slots", [])
        if idx < 0 or idx >= len(slots):
            return
        cnt = InventoryManager.get_item_count(p, iid)
        if cnt <= 0:
            return
        # 检查同种药是否已在其他槽（不允许重复绑定）
        for si in range(len(slots)):
            if si != idx and slots[si].get("id") == iid:
                return
        slot = slots[idx]
        old_iid = slot.get("id", "")
        # 旧药品不需要还背包（因为从未真正从背包取出）
        slot["id"] = iid
        slot["n"] = cnt  # 显示背包当前剩余数量

    @staticmethod
    def remove_potion(p, idx):
        """右击卸下快捷栏绑定（不清背包，因为本来就没从背包拿走）"""
        slots = p.get("potion_slots", [])
        if idx < 0 or idx >= len(slots):
            return
        slot = slots[idx]
        slot["id"] = ""
        slot["n"] = 0

    @staticmethod
    def buy_item(p, item, tab_ref, audio_ref, logs_ref, qty=1):
        """购买商店物品（全部 try/except 保护），qty为消耗品购买数量"""
        LOG = "C:\\Users\\Administrator\\Desktop\\bug_log.txt"
        def dbg(msg):
            with open(LOG, "a") as f:
                f.write(f"[DBG buy_item] {msg}\n")
        dbg(f"START iid={item.get('id')} qty={qty} p_gold={p.get('gold','MISSING')}")
        try:
            price = item["price"]
            iid = item["id"]
            dbg(f"price={price} iid={iid}")

            # ── 装备：先检查是否已有，再扣金币（排除消耗品） ──
            potion_ids = {"elixir_s", "elixir_mp", "elixir_b", "elixir_mp_b", "gold_elixir"}
            if iid in ITEMS and iid not in potion_ids:
                dbg(f"装备分支 p[equips]={p.get('equips')}")
                if any(eq["id"] == iid for eq in p.get("equips", [])):
                    logs_ref._add_log("已有该装备！", C_RED); audio_ref.hit(); dbg("已有装备 return"); return
                if p["gold"] < price:
                    logs_ref._add_log("金币不足！", C_RED); audio_ref.hit(); dbg("金币不足 return"); return
                p["gold"] -= price
                p["equips"].append({"id": iid})
                logs_ref._add_log(f"获得 {item.get('name', iid)}！去装备标签穿上吧！", C_GOLD)
                tab_ref.tab = "装备"
                audio_ref.coin(); dbg("装备购买完成"); return

            # ── 坐骑 ──
            if iid.startswith("mnt_"):
                mid = iid[4:]
                for m in MOUNTS:
                    if m["id"] == mid:
                        if any(mo["id"] == mid for mo in p["mounts"]):
                            logs_ref._add_log("已有该坐骑！", C_RED); audio_ref.hit(); dbg("已有坐骑 return"); return
                        if p["gold"] < price:
                            logs_ref._add_log("金币不足！", C_RED); audio_ref.hit(); dbg("金币不足 return"); return
                        p["gold"] -= price
                        p["mounts"].append(dict(m))
                        logs_ref._add_log(f"获得坐骑：{m['name']}！", C_GOLD)
                        tab_ref.tab = "坐骑"
                        audio_ref.levelup(); dbg("坐骑购买完成"); return

            # ── 宠物 ──
            if iid.startswith("pet_"):
                pid = iid[4:]
                for pt in PETS:
                    if pt["id"] == pid:
                        if any(pk["id"] == pid for pk in p["pets"]):
                            logs_ref._add_log("已有该宠物！", C_RED); audio_ref.hit(); dbg("已有宠物 return"); return
                        if p["gold"] < price:
                            logs_ref._add_log("金币不足！", C_RED); audio_ref.hit(); dbg("金币不足 return"); return
                        p["gold"] -= price
                        p["pets"].append(dict(pt))
                        logs_ref._add_log(f"获得宠物：{pt['name']}！", C_GOLD)
                        tab_ref.tab = "宠物"
                        audio_ref.levelup(); dbg("宠物购买完成"); return

            # ── 消耗品：可重复购买，不检查已有 ──
            if iid in potion_ids:
                qty = max(1, min(qty, 99))
                total_price = price * qty
                if p["gold"] < total_price:
                    logs_ref._add_log("金币不足！", C_RED); audio_ref.hit(); dbg("金币不足 return"); return
                p["gold"] -= total_price
                # 绑定槽的n值直接用背包数量刷新（绑定模式下槽n=背包剩余量）
                for slot in p["potion_slots"]:
                    if slot["id"] == iid:
                        from inventory import InventoryManager
                        cnt = InventoryManager.get_item_count(p, iid)
                        slot["n"] = cnt + qty
                        InventoryManager.give_item(p, iid, qty)
                        logs_ref._add_log(f"购买 {item.get('name', iid)} ×{qty}！", C_GOLD)
                        audio_ref.coin(); return
                from inventory import InventoryManager
                InventoryManager.give_item(p, iid, qty)
                logs_ref._add_log(f"购买 {item.get('name', iid)} ×{qty}！", C_GOLD)
                audio_ref.coin(); return

            # ── 技能书 ──
            if iid.startswith("sk_"):
                skname = iid[3:]
                skdata = SKILLS.get(skname, {})
                if skdata.get("cls") not in ("all", p["cls"]):
                    logs_ref._add_log("职业不符！", C_RED); audio_ref.hit(); dbg("职业不符 return"); return
                if skname in p["sk"]:
                    logs_ref._add_log(f"已学会 {skname}！", C_RED); audio_ref.hit(); dbg("已学会 return"); return
                if p["gold"] < price:
                    logs_ref._add_log("金币不足！", C_RED); audio_ref.hit(); dbg("金币不足 return"); return
                p["gold"] -= price
                if skname in SKILLS:
                    p["sk"].append(skname); p["qb"].append(skname)
                    logs_ref._add_log(f"学会技能：{skname}！", C_GOLD)
                    audio_ref.levelup(); dbg("技能购买完成"); return
                logs_ref._add_log(f"技能不存在：{skname}", C_RED); dbg("技能不存在 return"); return

            # ── 其他物品 ──
            if p["gold"] < price:
                logs_ref._add_log("金币不足！", C_RED); audio_ref.hit(); dbg("金币不足 return"); return
            p["gold"] -= price
            InventoryManager.give_item(p, iid, 1)
            logs_ref._add_log(f"购买 {item.get('name', iid)}！", C_GOLD)
            audio_ref.coin()
            dbg("其他物品购买完成")

        except Exception as e:
            import traceback, io
            with open(LOG, "a") as fl:
                fl.write(f"[DBG buy_item] EXCEPTION: {e}\n")
                buf = io.StringIO()
                traceback.print_exc(file=buf)
                fl.write(buf.getvalue())
