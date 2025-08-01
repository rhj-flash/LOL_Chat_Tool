# window_manager.py
# 窗口管理模块：查找和激活 LOL 窗口，区分大厅和对局窗口

import win32gui
import win32con
import time
import logging

class WindowManager:
    # 构造函数：初始化日志回调
    def __init__(self, log_callback):
        self.log_callback = log_callback

    # 查找 LOL 窗口，返回句柄和是否为对局窗口
    def find_lol_window(self):
        try:
            hwnd = None
            is_game = False
            titles = [
                ("League of Legends (TM) Client", True),  # 对局窗口优先
                ("League of Legends", False),  # 大厅窗口（英文）
                ("英雄联盟", False)  # 大厅窗口（中文）
            ]
            for title, game_flag in titles:
                hwnd = win32gui.FindWindow(None, title)
                if hwnd:
                    self.log_callback(f"找到LOL窗口: {title}, 句柄: {hwnd}, {'对局窗口' if game_flag else '大厅窗口'}")
                    return hwnd, game_flag
            self.log_callback("未找到LOL窗口")
            return None, False
        except Exception as e:
            self.log_callback(f"查找LOL窗口失败: {str(e)}")
            logging.exception("查找LOL窗口时发生异常")
            return None, False

    # 激活窗口并置顶
    def activate_window(self, hwnd):
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.SetActiveWindow(hwnd)
            # 额外尝试确保窗口激活
            win32gui.BringWindowToTop(hwnd)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            self.log_callback(f"激活窗口: 句柄 {hwnd}")
            time.sleep(0.1)  # 增加等待时间确保窗口激活
        except Exception as e:
            self.log_callback(f"激活窗口失败: {str(e)}")
            logging.exception("激活窗口时发生异常")