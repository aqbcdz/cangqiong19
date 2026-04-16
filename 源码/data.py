"""
data.py — 游戏配置数据
职责：
  - ITEMS/SKILLS/PETS/MOUNTS/SHOP_ITEMS 物品数据
  - CLASS_D 职业定义
  - REALMS 境界数据
  - WORLD 地图数据
  - EN_MAX 强化等级上限
  - QC 品质颜色

外部依赖：
  - 无（纯数据，无依赖）

不包含：
  - 任何逻辑（逻辑在 combat.py / equipment.py 等）
  - 任何渲染（render.py 负责）
"""

# === 职业定义 ===
CLASS_D = {
    "pojun":    {"name":"破军",  "hp":150,"mp":40,"atk":15,"def":10,"crit":5,"dodge":3,"spd":3,"col":(239,83,80)},
    "tianshang": {"name":"天殇",  "hp":80,  "mp":80,"atk":22,"def":4,"crit":10,"dodge":2,"spd":5,"col":(171,71,188)},
    "lingxing":  {"name":"铃星",  "hp":100,"mp":70,"atk":12,"def":6,"crit":8,"dodge":6,"spd":4,"col":(66,165,245)},
}

# === 境界数据 ===
REALMS = [
    {"name":"练气期", "min":1,  "b":{"hp":0,  "atk":0,  "def":0,  "spd":0}},
    {"name":"筑基期", "min":10, "b":{"hp":20, "atk":3,  "def":2,  "spd":0.1}},
    {"name":"金丹期", "min":20, "b":{"hp":50, "atk":8,  "def":5,  "spd":0.2}},
    {"name":"元婴期", "min":35, "b":{"hp":100,"atk":15, "def":10, "spd":0.4}},
    {"name":"化神期", "min":50, "b":{"hp":180,"atk":25, "def":18, "spd":0.6}},
    {"name":"大乘期", "min":70, "b":{"hp":300,"atk":40, "def":30, "spd":0.9}},
    {"name":"渡劫期", "min":85, "b":{"hp":500,"atk":60, "def":45, "spd":1.2}},
    {"name":"飞升仙界","min":99, "b":{"hp":800,"atk":100,"def":80, "spd":1.8}},
]

# === 技能数据（新版：含距离/范围形状）======================
# shape: single(单体) | circle(圆形) | cone(扇形) | rect(矩形) | self(自身范围)
# range: 最大施法距离(px)，从玩家当前位置算起
# radius: 圆形/扇形扩散半径(px)，center_shape=circle 时为落点半径
#         center_shape=cone 时为扇形半径
# width:  矩形宽度(px)
# length: 矩形长度(px)
# stun/dot/heal 等特效在 skill_effects 表（combat.py 用）
SKILLS = {
    # ── 通用 ───────────────────────────────────────
    "普通攻击":  {"t":"atk","cls":"all","mp":0,"cd":0,"pct":1.0,
                  "shape":"single","range":60,
                  "icon":"⚔","desc":"基础攻击"},

    # ══ 破军（近战 · 战士）══════════════════════════
    "突刺":      {"t":"atk","cls":"pojun","mp":5,"cd":1,"pct":1.5,
                  "shape":"single","range":80,
                  "icon":"⚔","desc":"单体穿刺150%，破甲"},
    "战吼":      {"t":"buff","cls":"pojun","mp":15,"cd":2,"dur":3,
                  "bt":"def","bv":0.5,
                  "shape":"self","range":0,"radius":70,
                  "icon":"👊","desc":"自身范围+防御50%"},
    "横扫千军":  {"t":"atk","cls":"pojun","mp":20,"cd":3,"pct":1.5,
                  "shape":"cone","range":55,"radius":90,"cone_deg":120,
                  "icon":"💥","desc":"扇形120°·90px·150%伤害"},
    "不动如山":  {"t":"buff","cls":"pojun","mp":25,"cd":5,"dur":3,
                  "bt":"def","bv":0.6,
                  "shape":"self","range":0,"radius":80,
                  "icon":"🛡","desc":"自身范围+减伤60%"},
    "苍穹灭世":  {"t":"atk","cls":"pojun","mp":60,"cd":7,"pct":5.0,"ls":0.3,
                  "shape":"circle","range":0,"radius":120,
                  "icon":"🐉","desc":"以自身为圆心r=120·500%·吸血30%"},

    # ══ 天殇（远程 · 法师）══════════════════════════
    "火球术":    {"t":"atk","cls":"tianshang","mp":10,"cd":1,"pct":1.3,"dot":True,
                  "shape":"circle","range":180,"radius":45,
                  "icon":"🔥","desc":"落点圆形r=45·130%+灼烧"},
    "冰封术":    {"t":"debuf","cls":"tianshang","mp":15,"cd":2,"pct":0.8,
                  "shape":"circle","range":160,"radius":50,
                  "stun":2,"icon":"❄","desc":"落点r=50·冻结2秒+伤害"},
    "天雷咒":    {"t":"atk","cls":"tianshang","mp":25,"cd":3,"pct":2.2,
                  "shape":"single","range":220,
                  "icon":"⚡","desc":"单体220%·可穿越障碍"},
    "群体炎爆":  {"t":"atk","cls":"tianshang","mp":30,"cd":5,"pct":1.5,
                  "shape":"circle","range":170,"radius":80,
                  "icon":"☄","desc":"落点r=80·全体150%"},
    "虚空湮灭":  {"t":"atk","cls":"tianshang","mp":60,"cd":7,"pct":5.0,
                  "shape":"rect","range":220,"width":80,"length":200,
                  "icon":"💫","desc":"前方矩形80×200·500%"},

    # ══ 灵行（远程 · 辅助）══════════════════════════
    "灵箭术":    {"t":"atk","cls":"lingxing","mp":12,"cd":1,"pct":1.3,
                  "shape":"single","range":150,
                  "slow":3,"icon":"🏹","desc":"单体130%·减速3秒"},
    "灵力涌动":  {"t":"heal","cls":"lingxing","mp":20,"cd":2,"pct":0.5,
                  "shape":"circle","range":130,"radius":60,
                  "icon":"💚","desc":"落点r=60·治疗50%HP"},
    "璇玑破":    {"t":"atk","cls":"lingxing","mp":22,"cd":3,"pct":1.8,"dot":True,
                  "shape":"cone","range":115,"radius":100,"cone_deg":90,
                  "icon":"💠","desc":"扇形90°·100px·180%+中毒"},
    "仙音浩荡":  {"t":"buff","cls":"lingxing","mp":40,"cd":5,"dur":3,
                  "bt":"atk","bv":0.3,
                  "shape":"self","range":0,"radius":100,
                  "icon":"🎵","desc":"自身r=100·全体+30%攻击"},
    "天璇破":    {"t":"atk","cls":"lingxing","mp":35,"cd":7,"pct":1.8,
                  "shape":"circle","range":165,"radius":90,
                  "stun":1,"icon":"🌟","desc":"落点r=90·180%+眩晕1秒"},
}

# === 技能解锁等级 ===
SK_UNLCK = {
    5:["突刺","火球术","灵箭术"],
    10:["横扫千军","冰封术","灵力涌动"],
    15:["不动如山","天雷咒","仙音浩荡"],
    20:["战吼","群体炎爆","璇玑破"],
    25:["天璇破"],
    30:["苍穹灭世","虚空湮灭"],
}

# === 物品数据 ===
ITEMS = {
    # ── 武器行（3品质） ──
    "wp_iron":       {"name":"铁剑",       "tp":"weapon","q":"white",  "atk":8,  "icon":"🗡"},
    "wp_steel":      {"name":"精钢剑",     "tp":"weapon","q":"green",  "atk":18, "crit":3,"icon":"⚔"},
    "wp_spirit":     {"name":"灵剑",       "tp":"weapon","q":"blue",   "atk":32, "crit":6,"icon":"🔮"},
    "wp_demon":      {"name":"魔渊剑",     "tp":"weapon","q":"purple","atk":52, "crit":10,"atk_pct":8,"icon":"🗡"},

    # ── 护甲行（3品质） ──
    "ar_cloth":      {"name":"布甲",       "tp":"armor", "q":"white",  "def":4,  "hp":20,"icon":"👘"},
    "ar_leather":    {"name":"皮甲",       "tp":"armor", "q":"green",  "def":9,  "hp":40,"icon":"🧥"},
    "ar_chain":      {"name":"锁子甲",     "tp":"armor", "q":"blue",   "def":16, "hp":65,"icon":"⛓"},
    "ar_dragon":     {"name":"龙鳞甲",     "tp":"armor", "q":"purple","def":26, "hp":110,"crit":3,"icon":"🐉"},

    # ── 饰品行（3品质） ──
    "ac_rope":       {"name":"粗麻绳",     "tp":"acc",   "q":"white",  "hp":15, "icon":"🎒"},
    "ac_silver":     {"name":"银戒指",     "tp":"acc",   "q":"green",  "hp":30, "crit":2,"dodge":2,"icon":"💍"},
    "ac_jade":       {"name":"蓝玉坠",     "tp":"acc",   "q":"blue",   "hp":50, "crit":5,"dodge":3,"mp":15,"icon":"🔷"},
    "ac_soul":       {"name":"冥魂珠",     "tp":"acc",   "q":"purple","hp":80, "crit":8,"dodge":5,"icon":"💀"},
    "elixir_s":      {"name":"初级丹药",     "tp":"cons",  "icon":"💊",  "desc":"恢复15%HP"},
    "elixir_mp":     {"name":"初级灵露",     "tp":"cons",  "icon":"💧",  "desc":"恢复20%MP"},
    "elixir_b":      {"name":"中级丹药",     "tp":"cons",  "icon":"💊",  "desc":"恢复30%HP"},
    "elixir_mp_b":   {"name":"中级灵露",     "tp":"cons",  "icon":"💦",  "desc":"恢复40%MP"},
    "gold_elixir":   {"name":"金创丹",       "tp":"cons",  "icon":"✨",  "desc":"完全恢复HP和MP"},
    "soul_stone":    {"name":"魂石",         "tp":"mat",   "icon":"💎"},
    "enhance_stone": {"name":"强化石",       "tp":"mat",   "icon":"⬆"},
    "soul_guard":    {"name":"固魂石",       "tp":"mat",   "icon":"🛡"},
}

# === 品质颜色 ===
QC = {
    "white":(170,170,170), "green":(74,222,128), "blue":(96,165,250),
    "purple":(168,85,247), "orange":(249,115,22), "gold":(232,200,122)
}

# === 强化等级上限 ===
EN_MAX = {"white":3, "green":5, "blue":7, "purple":9, "orange":10, "gold":12}

# ══════════════════════════════════════════════════════
# 敌人技能库（ENEMY_SKILLS）
# 格式："skill_id": {"name", "t"(type), "dmg", "cd", "dur", "desc"}
# type: dmg=伤害  dot=持续伤害  buff=增益  debuf=减益  heal=治疗  shield=护盾  stun=控制
# dmg/dot/heal 的数值为倍率（× enemy.atk 或 enemy.xxx）
# ══════════════════════════════════════════════════════
ENEMY_SKILLS = {
    # ── 精英通用技能 ──────────────────────────────
    "sk 利爪":      {"name":"利爪",    "t":"dmg",  "dmg":1.5,  "cd":3,  "dur":0, "desc":"利爪撕裂"},
    "sk 毒液":       {"name":"毒液",    "t":"dot",  "dmg":0.3,  "cd":4,  "dur":3, "desc":"每秒伤害"},
    "sk 冲锋":       {"name":"冲锋",    "t":"dmg",  "dmg":1.3,  "cd":5,  "dur":0, "stun":2,  "desc":"冲撞+眩晕"},
    "sk 寒爪":       {"name":"寒爪",    "t":"dmg",  "dmg":1.4,  "cd":4,  "dur":3, "slow":0.3, "desc":"攻击+减速"},
    "sk 冰封":       {"name":"冰封",    "t":"stun", "dmg":0,    "cd":6,  "dur":2, "desc":"冻结2秒"},
    "sk 火球":       {"name":"火球",    "t":"dmg",  "dmg":1.6,  "cd":4,  "dur":0, "mg":True,  "desc":"火焰攻击"},
    "sk 雷击":       {"name":"雷击",    "t":"dmg",  "dmg":1.8,  "cd":5,  "dur":0, "mg":True,  "desc":"雷属性攻击"},
    "sk 吸血":       {"name":"吸血",    "t":"dmg",  "dmg":1.2,  "cd":4,  "dur":0, "lifesteal":0.5, "desc":"伤害50%转HP"},
    "sk 护盾":       {"name":"护盾",    "t":"shield","dmg":0,   "cd":6,  "dur":3, "shield_val":0.5, "desc":"减免50%伤害"},
    "sk 狂暴":       {"name":"狂暴",    "t":"buff", "dmg":0,    "cd":8,  "dur":4, "batk":0.4,    "desc":"攻击+40%"},
    "sk 隐匿":       {"name":"隐匿",    "t":"buff", "dmg":0,    "cd":8,  "dur":3, "dodge":0.5,  "desc":"闪避+50%"},
    "sk 治疗":       {"name":"治疗",    "t":"heal", "dmg":0,    "cd":8,  "dur":0, "heal_val":0.3, "desc":"恢复30%HP"},
    "sk 嘲讽":       {"name":"嘲讽",    "t":"debuf", "dmg":0,   "cd":8,  "dur":2, "taunt":True, "desc":"强制攻击2秒"},
    "sk 破甲":       {"name":"破甲",    "t":"debuf", "dmg":0,   "cd":5,  "dur":3, "bdef":0.3,  "desc":"目标防御-30%"},
    "sk 灵魂锁链":    {"name":"灵魂锁链","t":"dmg",  "dmg":1.0,  "cd":6,  "dur":0, "lifesteal":0.3, "desc":"伤害+吸HP"},

    # ── Boss 专属技能 ─────────────────────────────
    "sk 重击":       {"name":"重击",    "t":"dmg",  "dmg":2.0,  "cd":4,  "dur":0, "desc":"强力单体"},
    "sk 怒吼":       {"name":"怒吼",    "t":"debuf", "dmg":0,   "cd":5,  "dur":3, "bdef":0.3,  "desc":"减防30%"},
    "sk 践踏":       {"name":"践踏",    "t":"dmg",  "dmg":0.8,  "cd":3,  "dur":0, "aoe":True,   "desc":"AOE×3次"},
    "sk 裂地斩":     {"name":"裂地斩",  "t":"dmg",  "dmg":2.5,  "cd":6,  "dur":0, "desc":"高伤单体"},
    "sk 横扫":       {"name":"横扫",    "t":"dmg",  "dmg":1.5,  "cd":3,  "dur":0, "aoe":True,   "desc":"范围150%×2"},
    "sk 飞斧":       {"name":"飞斧",    "t":"dmg",  "dmg":1.8,  "cd":4,  "dur":0, "desc":"单体高伤"},
    "sk 妖火":       {"name":"妖火",    "t":"dmg",  "dmg":1.8,  "cd":3,  "dur":0, "mg":True,    "desc":"火系单体"},
    "sk 幻术":       {"name":"幻术",    "t":"stun", "dmg":0,    "cd":6,  "dur":2, "desc":"混乱2秒"},
    "sk 九尾连击":    {"name":"九尾连击","t":"dmg",  "dmg":0.8,  "cd":3,  "dur":0, "hits":5,   "desc":"连击5次"},
    "sk 灵压":       {"name":"灵压",    "t":"dmg",  "dmg":2.0,  "cd":5,  "dur":0, "aoe":True,   "desc":"范围200%"},
    "sk 邪弹":       {"name":"邪弹",    "t":"dmg",  "dmg":1.5,  "cd":3,  "dur":0, "aoe":True,   "desc":"三连邪弹"},
    "sk 血祭":       {"name":"血祭",    "t":"dmg",  "dmg":1.5,  "cd":5,  "dur":0, "lifesteal":1.0, "desc":"吸血100%"},
    "sk 海啸":       {"name":"海啸",    "t":"dmg",  "dmg":1.7,  "cd":4,  "dur":0, "aoe":True,   "desc":"五连海啸"},
    "sk 潮汐护盾":    {"name":"潮汐护盾","t":"shield","dmg":0,   "cd":7,  "dur":4, "shield_val":0.6, "heal_val":0.1, "desc":"护盾+回血"},
    "sk 冰刺":       {"name":"冰刺",    "t":"dmg",  "dmg":1.5,  "cd":3,  "dur":0, "aoe":True,   "desc":"四连冰刺"},
    "sk 霜冻领域":    {"name":"霜冻领域","t":"dot",  "dmg":0.2,  "cd":5,  "dur":4, "aoe":True,   "desc":"范围持续伤害"},
    "sk 寒冰吐息":    {"name":"寒冰吐息","t":"dmg",  "dmg":2.5,  "cd":6,  "dur":0, "desc":"龙息单体"},
    "sk 虚空穿刺":    {"name":"虚空穿刺","t":"dmg",  "dmg":2.0,  "cd":3,  "dur":0, "aoe":True,   "desc":"五连虚空"},
    "sk 灵魂虹吸":    {"name":"灵魂虹吸","t":"dmg",  "dmg":2.5,  "cd":5,  "dur":0, "lifesteal":0.8, "desc":"吸HP+高伤"},
    "sk 湮灭光环":    {"name":"湮灭光环","t":"dmg",  "dmg":3.0,  "cd":6,  "dur":0, "aoe":True,   "desc":"全屏300%"},
    "sk 末日降临":    {"name":"末日降临","t":"dmg",  "dmg":8.0,  "cd":12, "dur":0, "desc":"终极技能"},
}

# ══════════════════════════════════════════════════════
# 怪物模板（ENEMY_TEMPLATES）
# 每张地图：普通30只（3选1随机）、精英15只（2选1随机）、Boss 1只
# ══════════════════════════════════════════════════════
ENEMY_TEMPLATES = {
    "shuiyun": {
        "lv": 1,
        "normal": [
            {"name":"草兔","ic":"🐰"},{"name":"山雀","ic":"🐦"},{"name":"笋龟","ic":"🐢"},
        ],
        "elite": [
            {"name":"灰毛狼","ic":"🐺","skill":"sk 利爪"},
            {"name":"竹叶青","ic":"🐍","skill":"sk 毒液"},
        ],
        "boss":  {"name":"山魈王","ic":"👹","skills":["sk 重击","sk 怒吼","sk 践踏","sk 裂地斩","sk 横扫"]},
    },
    "shuiyun_mountain": {
        "lv": 5,
        "normal": [
            {"name":"饿虎崽","ic":"🐯"},{"name":"毒蛙","ic":"🐸"},{"name":"褐蚁","ic":"🐜"},
        ],
        "elite": [
            {"name":"黑纹蛇","ic":"🐍","skill":"sk 冲锋"},
            {"name":"山贼刀客","ic":"⚔","skill":"sk 破甲"},
        ],
        "boss":  {"name":"黑风寨主","ic":"💀","skills":["sk 横扫","sk 飞斧","sk 狂暴","sk 护盾","sk 重击"]},
    },
    "lingfeng": {
        "lv": 12,
        "normal": [
            {"name":"僵尸","ic":"🧟"},{"name":"游魂","ic":"👻"},{"name":"妖狐","ic":"🦊"},
        ],
        "elite": [
            {"name":"尸卫","ic":"🧟","skill":"sk 寒爪"},
            {"name":"狐妖","ic":"🦊","skill":"sk 幻术"},
        ],
        "boss":  {"name":"九尾狐妖","ic":"🦊","skills":["sk 妖火","sk 幻术","sk 九尾连击","sk 灵压","sk 火球"]},
    },
    "yueyang": {
        "lv": 22,
        "normal": [
            {"name":"魔兽崽","ic":"👾"},{"name":"恶鬼","ic":"👹"},{"name":"邪修学徒","ic":"🧙"},
        ],
        "elite": [
            {"name":"魔兽统领","ic":"👾","skill":"sk 冲锋"},
            {"name":"邪修术士","ic":"🧙","skill":"sk 雷击"},
        ],
        "boss":  {"name":"天邪鬼王","ic":"👹","skills":["sk 邪弹","sk 血祭","sk 破甲","sk 灵魂锁链","sk 重击"]},
    },
    "lingbo": {
        "lv": 35,
        "normal": [
            {"name":"海妖幼体","ic":"🐙"},{"name":"溺魂","ic":"👻"},{"name":"蟹钳怪","ic":"🦀"},
        ],
        "elite": [
            {"name":"深海巨蟹","ic":"🦀","skill":"sk 践踏"},
            {"name":"溺魂首领","ic":"👻","skill":"sk 灵魂锁链"},
        ],
        "boss":  {"name":"海皇·利维坦","ic":"🐋","skills":["sk 海啸","sk 潮汐护盾","sk 冰封","sk 水系连击","sk 末日降临"]},
    },
    "xueyue": {
        "lv": 48,
        "normal": [
            {"name":"白狼崽","ic":"🐺"},{"name":"冰魔残影","ic":"🌀"},{"name":"雪猿","ic":"🦣"},
        ],
        "elite": [
            {"name":"极寒虎","ic":"🐅","skill":"sk 冰封"},
            {"name":"冰魔尊者","ic":"🌀","skill":"sk 寒爪"},
        ],
        "boss":  {"name":"极寒翼龙","ic":"🐉","skills":["sk 冰刺","sk 霜冻领域","sk 寒冰吐息","sk 护盾","sk 末日降临"]},
    },
    "qianyuan": {
        "lv": 60,
        "normal": [
            {"name":"古魔残魂","ic":"💀"},{"name":"凶兽崽","ic":"🦁"},{"name":"邪神碎片","ic":"👹"},
        ],
        "elite": [
            {"name":"远古魔将","ic":"💀","skill":"sk 狂暴"},
            {"name":"邪神圣殿骑士","ic":"⚔","skill":"sk 灵魂锁链"},
        ],
        "boss":  {"name":"苍穹古神","ic":"🌑","skills":["sk 虚空穿刺","sk 灵魂虹吸","sk 湮灭光环","sk 末日降临","sk 护盾"]},
    },
}

# ══════════════════════════════════════════════════════
# 世界地图（WORLD）
# ══════════════════════════════════════════════════════
WORLD = [
    {"id":"shuiyun",           "name":"水云村·一层",  "lv":1,  "bg":"village",
     "npcs":[{"name":"村长老","x":0.65,"y":0.50,"tp":"quest"},{"name":"杂货商","x":0.28,"y":0.38,"tp":"shop"}],
     "title":"初入修仙界"},
    {"id":"shuiyun_mountain",   "name":"水云山·二层",  "lv":5,  "bg":"forest",
     "npcs":[{"name":"猎户","x":0.70,"y":0.30,"tp":"quest"},{"name":"药师","x":0.20,"y":0.60,"tp":"shop"}],
     "title":"妖兽横行"},
    {"id":"lingfeng",           "name":"凌凤城·三层",  "lv":12, "bg":"city",
     "npcs":[{"name":"城主","x":0.50,"y":0.50,"tp":"quest"},{"name":"丹药师","x":0.30,"y":0.30,"tp":"shop"}],
     "title":"亡魂遍地"},
    {"id":"yueyang",            "name":"云阳城·四层",  "lv":22, "bg":"city",
     "npcs":[{"name":"宗门使","x":0.50,"y":0.50,"tp":"guild"}],
     "title":"魔道猖獗"},
    {"id":"lingbo",             "name":"凌波港·五层",  "lv":35, "bg":"harbor",
     "npcs":[{"name":"船长","x":0.50,"y":0.50,"tp":"quest"}],
     "title":"深海凶兽"},
    {"id":"xueyue",             "name":"雪月山·六层",  "lv":48, "bg":"snow",
     "npcs":[{"name":"雪妖王","x":0.50,"y":0.40,"tp":"boss"}],
     "title":"极寒领域"},
    {"id":"qianyuan",           "name":"苍穹渊·七层",  "lv":60, "bg":"cave",
     "npcs":[{"name":"古神残魂","x":0.50,"y":0.50,"tp":"boss"}],
     "title":"神的遗迹"},
]
PETS = [
    {"id":"xiaohu",  "name":"小狐",  "q":"凡兽","hp":30,  "atk":3,  "crit":1,  "sk":"护盾","ic":"🦊"},
    {"id":"bingling","name":"冰灵",  "q":"灵兽","hp":60,  "atk":12, "crit":5,  "sk":"冰封","ic":"❄"},
    {"id":"huolong", "name":"火龙",  "q":"仙兽","hp":100, "atk":25, "crit":10, "sk":"炎爆","ic":"🐉"},
    {"id":"tianmo",  "name":"天魔",  "q":"神灵","hp":200, "atk":40, "crit":15, "sk":"天魔乱舞","ic":"👹"},
]

# === 坐骑数据 ===
MOUNTS = [
    {"id":"luotian",  "name":"落天驹",   "q":"凡马","hp":50,  "atk":5,  "def":3,  "spd":1.3, "icon":"🐎"},
    {"id":"bailie",   "name":"白鹿",     "q":"灵兽","hp":120, "atk":12, "def":8,  "spd":1.6, "icon":"🦌"},
    {"id":"xuetu",    "name":"雪羽鹤",   "q":"仙兽","hp":200, "atk":20, "def":15, "spd":2.0, "icon":"🦅"},
    {"id":"fenghuang","name":"凤凰",    "q":"神灵","hp":350, "atk":35, "def":25, "spd":2.5, "icon":"🔥"},
]

# === 商店商品 ===
SHOP_ITEMS = {
    "装备": [
        # ── 武器行（白→绿→蓝→紫） ──
        {"id":"wp_iron",   "name":"铁剑",    "q":"white",  "price":80,   "icon":"🗡",  "desc":"攻击+8"},
        {"id":"wp_steel",  "name":"精钢剑",  "q":"green",  "price":280,  "icon":"⚔",  "desc":"攻击+18 暴击+3%"},
        {"id":"wp_spirit","name":"灵剑",    "q":"blue",   "price":680,  "icon":"🔮",  "desc":"攻击+32 暴击+6%"},
        {"id":"wp_demon", "name":"魔渊剑",  "q":"purple", "price":1800, "icon":"🗡",  "desc":"攻击+52 暴击+10% 穿甲+8%"},
        # ── 护甲行（白→绿→蓝→紫） ──
        {"id":"ar_cloth",  "name":"布甲",    "q":"white",  "price":70,   "icon":"👘",  "desc":"防御+4 HP+20"},
        {"id":"ar_leather","name":"皮甲",    "q":"green",  "price":240,  "icon":"🧥",  "desc":"防御+9 HP+40"},
        {"id":"ar_chain", "name":"锁子甲",  "q":"blue",   "price":600,  "icon":"⛓",  "desc":"防御+16 HP+65"},
        {"id":"ar_dragon","name":"龙鳞甲",  "q":"purple", "price":1600, "icon":"🐉",  "desc":"防御+26 HP+110 暴击+3%"},
        # ── 饰品行（白→绿→蓝→紫） ──
        {"id":"ac_rope",  "name":"粗麻绳",  "q":"white",  "price":60,   "icon":"🎒",  "desc":"HP+15"},
        {"id":"ac_silver","name":"银戒指",  "q":"green",  "price":220,  "icon":"💍",  "desc":"HP+30 暴击+2% 闪避+2%"},
        {"id":"ac_jade",  "name":"蓝玉坠",  "q":"blue",   "price":560,  "icon":"🔷",  "desc":"HP+50 暴击+5% 闪避+3% MP+15"},
        {"id":"ac_soul",  "name":"冥魂珠",  "q":"purple", "price":1500, "icon":"💀",  "desc":"HP+80 暴击+8% 闪避+5%"},
    ],
    "技能书": [
        {"id":"sk_突刺",      "name":"突刺",      "cls":"pojun",    "price":120,  "icon":"📖",  "desc":"习得突刺·单体150%"},
        {"id":"sk_横扫千军",  "name":"横扫千军",  "cls":"pojun",    "price":350,  "icon":"📖",  "desc":"习得横扫千军·全体150%"},
        {"id":"sk_不动如山",  "name":"不动如山",  "cls":"pojun",    "price":400,  "icon":"📖",  "desc":"习得不动如山·防御+50%"},
        {"id":"sk_战吼",      "name":"战吼",      "cls":"pojun",    "price":450,  "icon":"📖",  "desc":"习得战吼·攻击+40%"},
        {"id":"sk_苍穹灭世",  "name":"苍穹灭世",  "cls":"pojun",    "price":900,  "icon":"📖",  "desc":"习得苍穹灭世·单体500%"},
        {"id":"sk_火球术",    "name":"火球术",    "cls":"tianshang","price":150,  "icon":"📖",  "desc":"习得火球术·单体130%"},
        {"id":"sk_冰封术",    "name":"冰封术",    "cls":"tianshang","price":450,  "icon":"📖",  "desc":"习得冰封术·冻结+伤害"},
        {"id":"sk_天雷咒",    "name":"天雷咒",    "cls":"tianshang","price":550,  "icon":"📖",  "desc":"习得天雷咒·单体220%"},
        {"id":"sk_群体炎爆",  "name":"群体炎爆",  "cls":"tianshang","price":650,  "icon":"📖",  "desc":"习得群体炎爆·全体150%"},
        {"id":"sk_虚空湮灭",  "name":"虚空湮灭",  "cls":"tianshang","price":900,  "icon":"📖",  "desc":"习得虚空湮灭·单体500%"},
        {"id":"sk_灵力涌动",  "name":"灵力涌动",  "cls":"lingxing", "price":480,  "icon":"📖",  "desc":"习得灵力涌动·治疗40%HP"},
        {"id":"sk_仙音浩荡",  "name":"仙音浩荡",  "cls":"lingxing", "price":700,  "icon":"📖",  "desc":"习得仙音浩荡·全体攻击+30%"},
        {"id":"sk_灵箭术",    "name":"灵箭术",    "cls":"lingxing", "price":220,  "icon":"📖",  "desc":"习得灵箭术·单体130%魔法伤害"},
        {"id":"sk_璇玑破",    "name":"璇玑破",    "cls":"lingxing", "price":580,  "icon":"📖",  "desc":"习得璇玑破·单体180%魔法伤害"},
        {"id":"sk_天璇破",    "name":"天璇破",    "cls":"lingxing", "price":680,  "icon":"📖",  "desc":"习得天璇破·全体150%魔法伤害"},
    ],
    "宠物": [
        {"id":"pet_xiaohu",   "name":"小狐",      "price":100,  "icon":"🦊",  "desc":"凡兽 血30 攻击3"},
        {"id":"pet_bingling", "name":"冰灵",      "price":600,  "icon":"❄",  "desc":"灵兽 血60 攻击12"},
        {"id":"pet_huolong",  "name":"火龙",      "price":1500, "icon":"🐉",  "desc":"仙兽 血100 攻击25"},
    ],
    "坐骑": [
        {"id":"mnt_luotian",  "name":"落天驹",   "price":300,  "icon":"🐎",  "q":"凡马","hp":50,  "atk":5,  "def":3,  "spd":1.3, "desc":"凡马 速度+30%"},
        {"id":"mnt_bailie",   "name":"白鹿",     "price":800,  "icon":"🦌",  "q":"灵兽","hp":120, "atk":12, "def":8,  "spd":1.6, "desc":"灵兽 速度+60%"},
        {"id":"mnt_xuetu",    "name":"雪羽鹤",   "price":2000, "icon":"🦅",  "q":"仙兽","hp":200, "atk":20, "def":15, "spd":2.0, "desc":"仙兽 速度+100%"},
    ],
    "消耗品": [
        {"id":"elixir_s",      "name":"初级丹药",  "price":20,   "icon":"💊",  "desc":"恢复15%HP"},
        {"id":"elixir_mp",     "name":"初级灵露",  "price":20,   "icon":"💧",  "desc":"恢复20%MP"},
        {"id":"elixir_b",      "name":"中级丹药",  "price":60,   "icon":"💊",  "desc":"恢复30%HP"},
        {"id":"elixir_mp_b",   "name":"中级灵露",  "price":60,   "icon":"💦",  "desc":"恢复40%MP"},
        {"id":"gold_elixir",   "name":"金创丹",    "price":150,  "icon":"✨",  "desc":"完全恢复HP和MP"},
        {"id":"enhance_stone", "name":"强化石",    "price":50,   "icon":"⬆",  "desc":"装备强化材料"},
        {"id":"soul_guard",    "name":"固魂石",    "price":200,  "icon":"🛡",  "desc":"强化保级材料"},
    ],
}
