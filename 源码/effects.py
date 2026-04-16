"""
effects.py — 技能粒子特效系统
职责：
  - 20+种技能特效的粒子生成（火球/雷电/治愈/护盾等）
  - 特效更新（update）和绘制（draw）
  - 特效生命周期管理

外部依赖：
  - 无（独立模块，纯数学计算 + pygame.Surface）

不包含：
  - 任何游戏逻辑（调用方负责触发条件）
  - 音效（audio.py 负责）
"""
import pygame
import math
import random

class SE:
    def __init__(self, name, tx, ty, sx, sy, mg=False, aoe=False, game=None):
        self.name = name
        self.tx, self.ty = tx, ty   # 目标坐标
        self.sx, self.sy = sx, sy   # 源坐标
        self.mg = mg                # 是否魔法属性
        self.aoe = aoe              # 是否AOE
        self.game = game
        self.particles = []
        self.done = False
        self._build()

    # ─── 粒子生成器 ─────────────────────────────────
    def _p(self, x, y, vx, vy, c, sz, l, ml, g=False):
        """普通粒子：位置/速度/颜色/大小/寿命"""
        self.particles.append([x, y, vx, vy, c, sz, l, ml, g, 0, 0])

    def _r(self, x, y, r, mr, c, l, ml, w=None):
        """环粒子：从圆形扩散"""
        for i in range(mr):
            ang = 2 * math.pi * i / mr
            vx = r * math.cos(ang)
            vy = r * math.sin(ang)
            self.particles.append([x, y, vx, vy, c, 4, l, ml, False, 0, 0])
        for i in range(mr // 2):
            ang = 2 * math.pi * i / (mr // 2) + 0.3
            vx = r * 1.5 * math.cos(ang)
            vy = r * 1.5 * math.sin(ang)
            self.particles.append([x, y, vx, vy, c, 2, l, ml, False, 0, 0])

    def _b(self, x, y, a, ln, mln, c, l, ml, w, tp="beam"):
        """光束/爆炸"""
        if tp == "beam":
            for i in range(ln):
                t = i / ln
                px = x + (self.tx - x) * t + random.uniform(-w, w)
                py = y + (self.ty - y) * t + random.uniform(-w, w)
                self.particles.append([px, py, 0, 0, c, 6 - t * 3, l * (1 - t * 0.5), ml, False, 0, 0])
        else:  # explosion
            for _ in range(ln):
                ang = random.uniform(0, 2 * math.pi)
                spd = random.uniform(1, mln)
                vx = math.cos(ang) * spd
                vy = math.sin(ang) * spd
                self.particles.append([x, y, vx, vy, c, random.uniform(2, 6), l, ml, False, 0, 0])

    def _l(self, tp, x, y, l, ml, sz):
        """治疗/护盾 光环特效"""
        if tp == "heal":
            for i in range(20):
                ang = random.uniform(0, 2 * math.pi)
                r = random.uniform(0, 30)
                px = x + r * math.cos(ang)
                py = y + r * math.sin(ang) - i * 2
                vy = -random.uniform(0.5, 1.5)
                self.particles.append([px, py, 0, vy, (80, 255, 160), sz, l + i * 0.05, ml, False, 0, 0])
        elif tp == "shield":
            for i in range(16):
                ang = 2 * math.pi * i / 16
                px = x + 35 * math.cos(ang)
                py = y + 35 * math.sin(ang)
                vx = math.cos(ang) * 0.3
                vy = math.sin(ang) * 0.3
                self.particles.append([px, py, vx, vy, (100, 180, 255), 5, l, ml, False, 0, 0])
        elif tp == "buff":
            for i in range(12):
                ang = 2 * math.pi * i / 12
                for j in range(3):
                    r = 20 + j * 12
                    px = x + r * math.cos(ang)
                    py = y + r * math.sin(ang)
                    self.particles.append([px, py, 0, -0.8, (255, 200, 50), 4, l + j * 0.1, ml, False, 0, 0])

    # ─── 特效构建 ───────────────────────────────────
    def _build(self):
        n = self.name
        tx, ty = self.tx, self.ty
        sx, sy = self.sx, self.sy
        dx = tx - sx; dy = ty - sy
        dist = math.hypot(dx, dy)
        dnx = dx / dist if dist > 0 else 0
        dny = dy / dist if dist > 0 else 1
        perp_x = -dny; perp_y = dnx

        if n == "普通攻击":
            self._b(sx, sy, None, 12, 0, (255, 220, 150), 0.25, 20, 6)
            if self.mg:
                self._p(sx, sy, dnx * 4, dny * 4, (200, 200, 255), 5, 0.3, 20)
            else:
                self._p(sx, sy, dnx * 5, dny * 5, (255, 180, 100), 4, 0.2, 15)

        elif n in ("突刺", "横扫千军"):
            self._b(sx, sy, None, 18, 0, (255, 120, 60), 0.3, 25, 8)
            if n == "横扫千军":
                for off in [-25, 0, 25]:
                    ox = sx + perp_x * off
                    oy = sy + perp_y * off
                    self._b(ox, oy, None, 10, 0, (255, 150, 50), 0.25, 20, 6)
        elif n == "苍穹灭世":
            self._r(tx, ty, 10, 30, (255, 100, 50), 0.5, 30)
            self._b(sx, sy, None, 30, 0, (255, 60, 30), 0.6, 40, 15)
            self._b(sx, sy, None, 20, 0, (255, 200, 100), 0.4, 30, 8)
        elif n == "火球术":
            self._b(sx, sy, None, 15, 0, (255, 100, 20), 0.4, 25, 7)
            for _ in range(8):
                self._p(tx + random.uniform(-15, 15), ty + random.uniform(-15, 15),
                        0, random.uniform(-1.5, -0.5), (255, 60, 0), 8, 0.5, 15, True)
        elif n == "天雷咒":
            self._p(tx, ty - 60, 0, 2, (180, 180, 255), 10, 0.8, 20)
            for i in range(5):
                bx = tx + random.uniform(-20, 20)
                by = ty - 60 + i * 15
                self._p(bx, by, random.uniform(-1, 1), 0, (220, 220, 120), 5, 0.2, 12)
        elif n == "群体炎爆":
            for _ in range(3):
                self._r(tx + random.uniform(-30, 30), ty + random.uniform(-30, 30),
                        5, 20, (255, 80, 20), 0.4, 20)
            self._b(sx, sy, None, 20, 0, (255, 130, 30), 0.5, 30, 10)
        elif n == "虚空湮灭":
            self._r(tx, ty, 5, 40, (150, 50, 255), 0.7, 35)
            self._b(sx, sy, None, 40, 0, (180, 80, 255), 0.8, 45, 18)
            for _ in range(15):
                self._p(tx + random.uniform(-20, 20), ty + random.uniform(-20, 20),
                        0, random.uniform(-2, -0.5), (200, 100, 255), 7, 0.6, 20, True)
        elif n == "冰封术":
            self._r(tx, ty, 5, 20, (150, 210, 255), 0.5, 25)
            for i in range(8):
                ang = 2 * math.pi * i / 8
                self._p(tx + 30 * math.cos(ang), ty + 30 * math.sin(ang),
                        0, -0.5, (200, 230, 255), 5, 0.4, 18)
            # 自身护盾光效
            for i in range(12):
                ang = 2 * math.pi * i / 12
                px2 = sx + 30 * math.cos(ang)
                py2 = sy + 30 * math.sin(ang)
                self._p(px2, py2, math.cos(ang) * 0.3, math.sin(ang) * 0.3,
                        (150, 210, 255), 4, 0.5, 20)
        elif n == "灵箭术":
            self._b(sx, sy, None, 15, 0, (200, 200, 255), 0.4, 25, 7)
            for i in range(6):
                ang = 2 * math.pi * i / 6
                self._p(tx + 12 * math.cos(ang), ty + 12 * math.sin(ang),
                        math.cos(ang) * 1.5, math.sin(ang) * 1.5,
                        (220, 220, 255), 4, 0.4, 18)
        elif n == "璇玑破":
            self._r(tx, ty, 5, 24, (180, 120, 255), 0.5, 28)
            self._b(sx, sy, None, 22, 0, (200, 160, 255), 0.5, 30, 10)
            for i in range(8):
                ang = 2 * math.pi * i / 8
                self._p(tx + 15 * math.cos(ang), ty + 15 * math.sin(ang),
                        math.cos(ang) * 2, math.sin(ang) * 2,
                        (180, 120, 255), 5, 0.4, 20)
        elif n == "天璇破":
            self._r(tx, ty, 5, 28, (255, 220, 80), 0.6, 30)
            self._b(sx, sy, None, 25, 0, (200, 180, 255), 0.5, 35, 12)
            for i in range(12):
                ang = 2 * math.pi * i / 12
                self._p(tx + 20 * math.cos(ang), ty + 20 * math.sin(ang),
                        math.cos(ang) * 2, math.sin(ang) * 2,
                        (255, 220, 80), 5, 0.5, 22)
        elif n == "灵力涌动":
            self._l("heal", tx, ty, 0.3, 20, 5)
        elif n in ("护盾术", "不动如山"):
            self._l("shield", tx, ty, 0.4, 22, 5)
        elif n in ("战吼", "仙音浩荡"):
            self._l("buff", tx, ty, 0.4, 20, 5)
        elif n == "普通治疗":
            self._l("heal", tx, ty, 0.3, 20, 5)
        elif n == "护盾":
            self._l("shield", tx, ty, 0.4, 22, 5)
        elif n == "不动如山":
            self._l("shield", tx, ty, 0.4, 22, 5)
        elif n == "战吼":
            self._l("buff", tx, ty, 0.4, 20, 5)
        elif n == "仙音浩荡":
            self._l("buff", tx, ty, 0.4, 20, 5)
        else:
            self._p(sx, sy, dnx * 3, dny * 3, (255, 200, 100), 4, 0.3, 18)

    # ─── 更新 ───────────────────────────────────────
    def update(self):
        alive = []
        for p in self.particles:
            x, y, vx, vy, c, sz, l, ml, g, bx, by = p
            x += vx; y += vy
            if g:
                vy += 0.05
            l -= 0.02
            sz *= 0.97
            if l > 0 and sz > 0.5:
                alive.append([x, y, vx, vy, c, sz, l, ml, g, bx, by])
        self.particles = alive
        if not self.particles:
            self.done = True

    # ─── 绘制 ───────────────────────────────────────
    def draw(self, surf):
        for p in self.particles:
            x, y, vx, vy, c, sz, l, ml, g, bx, by = p
            alpha = min(255, int(l * 400))
            try:
                temp = pygame.Surface((int(sz * 2 + 2), int(sz * 2 + 2)), pygame.SRCALPHA)
                pygame.draw.circle(temp, (*c, alpha), (int(sz + 1), int(sz + 1)), max(1, int(sz)))
                surf.blit(temp, (int(x - sz - 1), int(y - sz - 1)))
            except Exception:
                pass
