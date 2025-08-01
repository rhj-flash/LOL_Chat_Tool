# input_simulator.py
# 输入模拟模块：使用 SendInput 模拟键盘输入，适配大厅和对局窗口

import ctypes
import time
from ctypes import wintypes
import win32gui
import win32con
from pip._internal.utils import logging
import pydirectinput
import win32gui
import ctypes
import time
import logging

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
VK_SPACE = 0x20  # 空格键的虚拟键码


class InputSimulator:
    def __init__(self, log_callback):
        self.log_callback = log_callback
        self.user32 = ctypes.WinDLL("user32")
        # 定义必要的 ctypes 结构体
        self.INPUT_KEYBOARD = 1
        self.KEYEVENTF_UNICODE = 0x0004
        self.KEYEVENTF_KEYUP = 0x0002

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [("wVk", ctypes.c_ushort),
                        ("wScan", ctypes.c_ushort),
                        ("dwFlags", ctypes.c_ulong),
                        ("time", ctypes.c_ulong),
                        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [("uMsg", ctypes.c_ulong),
                        ("wParamL", ctypes.c_short),
                        ("wParamH", ctypes.c_ushort)]

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", ctypes.c_long),
                        ("dy", ctypes.c_long),
                        ("mouseData", ctypes.c_ulong),
                        ("dwFlags", ctypes.c_ulong),
                        ("time", ctypes.c_ulong),
                        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

        class Union_Input(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT),
                        ("mi", MOUSEINPUT),
                        ("hi", HARDWAREINPUT)]

        class INPUT(ctypes.Structure):
            _fields_ = [("type", ctypes.c_ulong),
                        ("union_input", Union_Input)]

        # 将这些定义绑定到 self
        self.INPUT = INPUT
        self.KEYBDINPUT = KEYBDINPUT
        self.Union_Input = Union_Input

    def send_message(self, hwnd, message, is_game):
        """
        发送消息，区分大厅和对局窗口
        本次修改：将硬编码的过长延迟调整为更短、更合理的间隔，以提高发送速度和稳定性。
        :param hwnd: 目标窗口句柄
        :param message: 要发送的消息内容
        :param is_game: 是否为对局窗口
        """
        try:
            start_time = time.time()
            self.log_callback("尝试发送消息...")

            # 确保窗口焦点
            foreground_hwnd = win32gui.GetForegroundWindow()
            if foreground_hwnd != hwnd:
                self.log_callback("重新设置窗口焦点")
                win32gui.SetForegroundWindow(hwnd)
                # 增加短暂的等待时间，确保窗口焦点完全切换
                time.sleep(0.05)

            # 激活聊天窗口，统一使用回车键。使用 pydirectinput 模拟按键，对游戏兼容性更好
            self.log_callback("尝试激活聊天框...")
            pydirectinput.press('enter')
            # 增加短暂的等待时间，确保聊天框弹出
            time.sleep(0.05)
            self.log_callback("已激活聊天框")

            # 保留你原始的 SendInput 逻辑来发送完整消息
            self.log_callback("准备发送完整消息...")
            inputs = []
            for char in message:
                down_input = self.INPUT(type=self.INPUT_KEYBOARD, union_input=self.Union_Input(
                    ki=self.KEYBDINPUT(wScan=ord(char), dwFlags=self.KEYEVENTF_UNICODE)))
                inputs.append(down_input)

                up_input = self.INPUT(type=self.INPUT_KEYBOARD, union_input=self.Union_Input(
                    ki=self.KEYBDINPUT(wScan=ord(char), dwFlags=self.KEYEVENTF_UNICODE | self.KEYEVENTF_KEYUP)))
                inputs.append(up_input)

            if inputs:
                inputs_array = (self.INPUT * len(inputs))(*inputs)
                self.user32.SendInput(len(inputs), inputs_array, ctypes.sizeof(self.INPUT))
                self.log_callback(f"消息 '{message}' 已发送")
            else:
                self.log_callback("消息为空，未发送")

            self.log_callback("输入完成")
            # 增加短暂的等待时间，确保输入被完全处理
            time.sleep(0.05)

            # 再次使用 pydirectinput 模拟回车键以发送消息
            pydirectinput.press('enter')
            self.log_callback("已发送消息")

            end_time = time.time()
            self.log_callback(f"消息发送耗时: {end_time - start_time:.3f}秒")

        except Exception as e:
            self.log_callback(f"输入模拟失败: {str(e)}")
            logging.exception("在send_message方法中发生异常")