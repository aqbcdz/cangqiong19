"""
audio.py — 音效与背景音乐系统
职责：
  - BGM 生成（程序化合成旋律）
  - 音效播放（attack/hit/skill/death/coin/heal/levelup）
  - 音量控制

外部依赖：
  - 无（独立模块，通过 pygame.mixer 工作）

不包含：
  - 任何游戏逻辑
  - 任何渲染代码
"""
import pygame
import math
import random

class Audio:
    def __init__(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.bgm_channel = pygame.mixer.Channel(0)
        except Exception as e:
            print(f"[Audio] mixer init error: {e}")
            self.bgm_channel = None
        self.bgm_volume = 0.4
        self.se_volume = 0.7
        self.bgm_buffer = None
        self.bgm_playing = False

    # ─── 基础声音合成 ───────────────────────────────
    def tone(self, freq, dur, rate=22050):
        n = int(rate * dur)
        arr = numpyBuilder or self._build_tone_array(freq, n, rate)
        return pygame.mixer.Sound(array=arr)

    def _build_tone_array(self, freq, n, rate):
        # 备用：生成正弦波
        import array
        gain = 0.3
        arr = array.array('h')
        for i in range(n):
            t = i / rate
            v = int(gain * 32767 * math.sin(2 * math.pi * freq * t))
            arr.append(max(-32768, min(32767, v)))
        return arr

    def noise(self, dur, rate=22050):
        import array, random as r
        n = int(rate * dur)
        arr = array.array('h', (int((r.random()*2-1)*8000) for _ in range(n)))
        return pygame.mixer.Sound(array=arr)

    def make_snd(self, samples):
        import numpy as np
        # 先收集成1D数组，再转成2D（每行一个声道）
        mono = np.array([max(-32768, min(32767, int(v))) for v in samples], dtype=np.int16)
        stereo = np.stack([mono, mono], axis=1)  # shape (n, 2)
        return pygame.mixer.Sound(array=stereo)

    # ─── 音效播放 ───────────────────────────────────
    def play_ch(self, snd):
        if snd:
            snd.set_volume(self.se_volume)
            snd.play()

    def attack(self):
        try:
            s = self.noise(0.06)
            s.set_volume(0.5)
            s.play()
        except Exception as e:
            print(f"[Audio] attack error: {e}")

    def hit(self):
        try:
            s = self.noise(0.08)
            s.set_volume(0.35)
            s.play()
        except Exception as e:
            print(f"[Audio] hit error: {e}")

    def skill_snd(self, name):
        if not name or name == "普通攻击":
            return
        freq = 440 + hash(name) % 300
        dur = 0.15
        n = int(22050 * dur)
        arr = self._build_sin_fade(freq, freq * 1.5, n, 22050, 0.4)
        s = self.make_snd(arr)
        s.set_volume(0.5)
        s.play()

    def _build_sin_fade(self, f1, f2, n, rate, vol):
        import math
        return (int(vol * 32767 * math.sin(2*math.pi*(f1*(1-i/n)+f2*(i/n))*i/rate))
                for i in range(n))

    def levelup(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            import array, math
            rate = 22050
            n = int(rate * 0.3)
            freqs = [523, 659, 784, 1047]
            arr = array.array('h')
            for i in range(n):
                t = i / rate
                v = 0
                for j, f in enumerate(freqs):
                    amp = 0.3 / (j + 1)
                    v += amp * math.sin(2 * math.pi * f * t)
                v = int(max(-32768, min(32767, v * 8000)))
                arr.append(v)
            s = pygame.mixer.Sound(array=arr)
            s.set_volume(self.se_volume)
            s.play()
        except Exception as e:
            print(f"[Audio] levelup error: {e}")

    def coin(self):
        try:
            if not pygame.mixer.get_init():
                return
            import array, math
            rate = 22050
            n = int(rate * 0.08)
            arr = array.array('h')
            for i in range(n):
                v = int(6000 * math.sin(2 * math.pi * 1800 * i / rate) * math.exp(-3 * i / n))
                arr.append(max(-32768, min(32767, v)))
            s = pygame.mixer.Sound(array=arr)
            s.set_volume(0.4)
            s.play()
        except Exception as e:
            print(f"[Audio] coin error: {e}")

    def heal(self):
        try:
            if not pygame.mixer.get_init():
                return
            import array, math
            rate = 22050
            n = int(rate * 0.3)
            arr = array.array('h')
            for i in range(n):
                t = i / rate
                v = int(4000 * math.sin(2 * math.pi * (400 + 200 * t) * t) * math.exp(-2 * i / n))
                arr.append(max(-32768, min(32767, v)))
            s = pygame.mixer.Sound(array=arr)
            s.set_volume(0.5)
            s.play()
        except Exception as e:
            print(f"[Audio] heal error: {e}")

    def death(self):
        try:
            if not pygame.mixer.get_init():
                return
            import array, math
            rate = 22050
            n = int(rate * 0.4)
            arr = array.array('h')
            for i in range(n):
                v = int(5000 * math.sin(2 * math.pi * 150 * i / rate) * math.exp(-4 * i / n))
                arr.append(max(-32768, min(32767, v)))
            s = pygame.mixer.Sound(array=arr)
            s.set_volume(0.6)
            s.play()
        except Exception as e:
            print(f"[Audio] death error: {e}")

    # ─── BGM 系统 ───────────────────────────────────
    def bgm_gen(self, mid=""):
        """生成程序化 BGM，返回 pygame.Sound"""
        import array, math, random
        rate = 22050
        beats = int(rate * 4.0)
        buf = array.array('h')
        base = 220
        # 和弦进行
        chord_seq = [(1.0,1.25,1.5),(1.0,1.25,1.5),(0.75,0.875,1.0),(0.75,1.0,1.125)]
        cur = chord_seq[hash(mid) % len(chord_seq)]

        for i in range(beats):
            t = i / rate
            v = 0
            for j, mult in enumerate(cur):
                h = (j + 1)
                amp = 0.08 / h
                v += amp * (
                    math.sin(2*math.pi*base*mult*h*t) * 0.6 +
                    math.sin(2*math.pi*base*mult*h*1.005*t) * 0.3 +
                    math.sin(2*math.pi*base*mult*h*0.995*t) * 0.3
                )
                # 低音鼓
                if int(t * 2) % 4 == 0:
                    v += 0.1 * math.exp(-8 * (t % 0.5))
            # 副旋律
            if random.random() < 0.001:
                base2 = base * 2
                for k in range(3):
                    v += 0.04 * math.sin(2*math.pi*base2*(1+k*0.01)*t)
            s = int(max(-32768, min(32767, v * 32767)))
            buf.append(s)
        return pygame.mixer.Sound(array=buf)

    def play_bgm(self, mid=""):
        if self.bgm_playing:
            return
        try:
            self.bgm_buffer = self.bgm_gen(mid)
            self.bgm_buffer.set_volume(self.bgm_volume)
            self.bgm_channel.play(self.bgm_buffer, loops=-1)
            self.bgm_playing = True
        except Exception:
            pass

    def stop_bgm(self):
        self.bgm_channel.stop()
        self.bgm_playing = False


# ─── 单例（避免 circular import）────────────────────────────
_audio_instance = None
def get_audio():
    """全局唯一 Audio 实例，供其他模块导入使用"""
    global _audio_instance
    if _audio_instance is None:
        _audio_instance = Audio()
    return _audio_instance
