"""
config.py — 全局常量配置
职责：
  - 屏幕尺寸、FPS
  - 颜色常量
  - 字体定义
  - DEBUG_MODE 开关

外部依赖：
  - 无（所有模块导入此文件）

不包含：
  - 任何游戏数据（data.py）
  - 任何游戏逻辑
"""
import pygame
import sys

# === 显示配置 ===
SCREEN_W = 1200
SCREEN_H = 760
FPS = 60

# === 颜色常量 ===
C_RED    = (239, 68, 68)
C_GREEN  = (74, 222, 128)
C_BLUE   = (59, 130, 246)
C_GOLD   = (232, 200, 122)
C_PURPLE = (168, 85, 247)
C_TEXT   = (200, 190, 220)
C_REALM  = (176, 144, 224)

# === 字体 ===
FONT     = pygame.font.SysFont("microsoftyaheiui", 18)
FONT_B   = pygame.font.SysFont("microsoftyaheiui", 22, bold=True)
FONT_L   = pygame.font.SysFont("microsoftyaheiui", 14)
FONT_SK  = pygame.font.SysFont("Segoe UI Emoji", 22)

# === 全局状态 ===
DEBUG_MODE = False
version = "v19"

# === 初始化（延迟到 main.py 中 pygame.init() 之后） ===
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
