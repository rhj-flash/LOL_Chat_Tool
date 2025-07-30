# input_simulator.py
# 输入模拟模块：消息前后发送 Enter，统一大厅和对局窗口逻辑，逐字符输入，防止乱码

import ctypes
from ctypes import wintypes
import time
import win32gui
import win32con

# Windows API 结构定义
PUL = ctypes.POINTER(ctypes.c_ulong)


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", PUL)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", PUL)]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT)]

    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD),
                ("_input", _INPUT)]


# 常量定义
INPUT_KEYBOARD = 1
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LWIN = 0x5B


class InputSimulator:
    # 构造函数：初始化日志回调
    def __init__(self, log_callback):
        self.log_callback = log_callback
        self.user32 = ctypes.WinDLL('user32')
        self.user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)

    # 模拟单个按键
    def send_key(self, key_code, is_unicode=False, key_up=False):
        input_struct = INPUT()
        input_struct.type = INPUT_KEYBOARD
        input_struct.ki.wVk = key_code if not is_unicode else 0
        input_struct.ki.wScan = key_code if is_unicode else 0
        input_struct.ki.dwFlags = KEYEVENTF_UNICODE if is_unicode else (
            KEYEVENTF_KEYUP if key_up else KEYEVENTF_KEYDOWN)
        input_struct.ki.time = 0
        input_struct.ki.dwExtraInfo = None
        self.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(input_struct))
        self.log_callback(
            f"模拟按键: {hex(key_code)}, {'释放' if key_up else '按下'}, {'Unicode' if is_unicode else 'Virtual Key'}")
        time.sleep(0.3 if hasattr(self, 'is_game') and self.is_game else 0.05)

    # 清理输入队列
    def clear_input_queue(self):
        for key in [VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN]:
            self.send_key(key, key_up=True)
            self.log_callback(f"清理输入队列: 释放按键 {hex(key)}")
        time.sleep(0.15)

    # 发送消息，统一大厅和对局窗口逻辑
    def send_message(self, hwnd, message, is_game):
        try:
            start_time = time.time()
            self.is_game = is_game
            title = win32gui.GetWindowText(hwnd)

            # 确保窗口焦点
            if win32gui.GetForegroundWindow() != hwnd:
                win32gui.SetForegroundWindow(hwnd)
                self.log_callback(f"设置焦点: 句柄 {hwnd}, 标题 {title}")
                time.sleep(1.8)

            # 清理输入队列
            self.clear_input_queue()

            # 发送 Enter 打开聊天框
            self.log_callback(f"{'对局窗口' if is_game else '大厅窗口'}：发送 Enter 打开聊天框")
            self.send_key(VK_RETURN, key_up=False)
            self.send_key(VK_RETURN, key_up=True)
            time.sleep(0.5)
            # 验证聊天框
            test_char = ord('/')
            self.send_key(test_char, is_unicode=True, key_up=False)
            self.send_key(test_char, is_unicode=True, key_up=True)
            self.send_key(0x08, key_up=False)  # Backspace
            self.send_key(0x08, key_up=True)
            self.log_callback("聊天框验证通过")

            # 逐字符输入消息
            for char in message:
                unicode_val = ord(char)
                self.send_key(unicode_val, is_unicode=True, key_up=False)
                self.send_key(unicode_val, is_unicode=True, key_up=True)
                self.log_callback(f"输入字符: {char} (Unicode: {hex(unicode_val)})")

            # 发送 Enter 提交消息
            self.log_callback("发送 Enter 提交消息")
            self.send_key(VK_RETURN, key_up=False)
            self.send_key(VK_RETURN, key_up=True)

            # 清理输入队列
            self.clear_input_queue()

            end_time = time.time()
            self.log_message(f"消息发送: {message}, 耗时: {end_time - start_time:.3f}秒")
        except Exception as e:
            self.log_callback(f"发送失败: 句柄 {hwnd}, 错误: {str(e)}")

    # 日志记录
    def log_message(self, message):
        self.log_callback(message)