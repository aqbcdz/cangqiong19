"""
map.py — 地图与NPC交互系统
职责：
  - 地图加载（load_map）
  - NPC交互（handle_npc：商店/任务）
  - 任务系统（on_q_accept：接受任务奖励）
  - 地图切换（切换地图后重置玩家位置和刷怪）

外部依赖：
  - data.py（WORLD 地图数据）
  - audio.py（Audio 实例，用于切换地图后更换BGM）
  - enemy.py（EnemyManager.spawn）
  - player.py（PlayerManager.recalc）

不包含：
  - 战斗逻辑（combat.py 负责）
  - 渲染（render.py 负责）
"""
from data import WORLD


class MapManager:
    """地图管理（替代原 G 类的地图相关方法和 NPC 交互）"""

    @staticmethod
    def load_map(game_ref, mid, audio_ref):
        """
        加载地图并触发刷怪
        game_ref: 游戏主对象（用于访问 .map / .p / .enemies / .logs）
        mid: 地图ID字符串
        audio_ref: 音频实例
        """
        for m in WORLD:
            if m["id"] == mid:
                game_ref.map = m
                game_ref.map_id = mid
                break

        game_ref.p["x"] = 400
        game_ref.p["y"] = 320
        game_ref.move_to = None

        # 刷怪
        from enemy import EnemyManager
        game_ref.enemies = EnemyManager.spawn(mid)

        game_ref.logs.clear()

        audio_ref.play_bgm(mid)

        # 切换地图时自动存档
        from save import SaveManager
        SaveManager.save_game(game_ref)

    @staticmethod
    def handle_npc(npc, game_ref):
        """处理NPC交互"""
        if npc["tp"] == "shop":
            from shop import ShopManager
            ShopManager.show_shop(game_ref)
        elif npc["tp"] == "quest":
            game_ref._add_log(f"与 {npc['name']} 对话...", (200, 190, 220))

    @staticmethod
    def accept_quest(q, idx, game_ref):
        """接受任务奖励（对话后）"""
        pass  # 原实现为空，任务奖励在 _kill 中自动发放
