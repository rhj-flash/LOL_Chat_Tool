# window_manager.py
# 窗口管理模块：查找和激活 LOL 窗口，优先选择对局窗口，支持全屏模式和多窗口场景

import win32gui
import win32con
import win32api
import time

class WindowManager:
    # 构造函数：初始化日志回调
    def __init__(self, log_callback):
        self.log_callback = log_callback

    # 查找 LOL 窗口，优先返回对局窗口，返回句柄和是否为对局窗口
    def find_lol_window(self):
        titles = [
            ("League of Legends (TM) Client", True),  # 对局窗口（国际服）
            ("英雄联盟游戏", True),                   # 对局窗口（国服）
            ("League of Legends", False),           # 大厅窗口（国际服）
            ("英雄联盟", False),                    # 大厅窗口（国服）
            ("Riot Client", False),                # Riot 客户端（可能包含大厅）
        ]
        found_windows = []

        # 枚举所有窗口，收集匹配的 LOL 窗口
        def enum_windows(hwnd, results):
            title = win32gui.GetWindowText(hwnd).lower()
            for t, is_game in titles:
                if t.lower() in title:
                    results.append((hwnd, is_game, title))
        win32gui.EnumWindows(enum_windows, found_windows)

        if not found_windows:
            self.log_callback("未找到任何LOL窗口")
            return None, False

        # 日志记录所有找到的窗口
        self.log_callback(f"找到 {len(found_windows)} 个LOL窗口:")
        for hwnd, is_game, title in found_windows:
            self.log_callback(f"  - 标题: {title}, 句柄: {hwnd}, {'对局窗口' if is_game else '大厅窗口'}")

        # 优先选择对局窗口
        for hwnd, is_game, title in found_windows:
            if is_game:
                self.log_callback(f"选择对局窗口: {title}, 句柄: {hwnd}")
                return hwnd, True

        # 如果没有对局窗口，选择第一个大厅窗口
        hwnd, is_game, title = found_windows[0]
        self.log_callback(f"未找到对局窗口，选择大厅窗口: {title}, 句柄: {hwnd}")
        return hwnd, False

    # 激活窗口并置顶，处理最小化和全屏情况
    def activate_window(self, hwnd):
        try:
            # 检查窗口状态
            window_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            is_visible = window_style & win32con.WS_VISIBLE
            is_minimized = win32gui.IsIconic(hwnd)
            window_rect = win32gui.GetWindowRect(hwnd)
            window_title = win32gui.GetWindowText(hwnd)
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            is_fullscreen = (window_rect[2] - window_rect[0] >= screen_width and
                             window_rect[3] - window_rect[1] >= screen_height)
            self.log_callback(f"窗口状态: 句柄 {hwnd}, 标题 {window_title}, {'可见' if is_visible else '不可见'}, "
                             f"{'最小化' if is_minimized else '非最小化'}, {'全屏' if is_fullscreen else '非全屏'}, "
                             f"位置: {window_rect}")

            # 如果窗口不可见或最小化，执行还原
            if not is_visible or is_minimized:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
                self.log_callback(f"窗口不可见或最小化，执行还原: 句柄 {hwnd}")

            # 检查是否已置顶
            current_foreground = win32gui.GetForegroundWindow()
            if current_foreground == hwnd:
                self.log_callback(f"窗口已置顶: 句柄 {hwnd}")
                return

            # 置顶并激活（最多尝试 7 次）
            for attempt in range(7):
                if is_fullscreen:
                    # 全屏模式使用 Alt+Tab 切换
                    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt 按下
                    time.sleep(0.1)
                    win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)   # Tab 按下
                    time.sleep(0.1)
                    win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)
                    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                    self.log_callback(f"全屏模式：模拟 Alt+Tab 切换: 句柄 {hwnd}, 尝试 {attempt + 1}")
                else:
                    # 非全屏模式使用标准 API
                    win32gui.BringWindowToTop(hwnd)
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.SetActiveWindow(hwnd)
                    win32gui.SwitchToThisWindow(hwnd, True)
                    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                    self.log_callback(f"执行窗口置顶: 句柄 {hwnd}, 尝试 {attempt + 1}")
                time.sleep(0.8)  # 延长等待，确保窗口激活
                if win32gui.GetForegroundWindow() == hwnd:
                    self.log_callback(f"窗口置顶成功: 句柄 {hwnd}, 尝试 {attempt + 1}")
                    return
                self.log_callback(f"置顶失败，尝试 {attempt + 1}: 句柄 {hwnd}")
            self.log_callback(f"窗口置顶失败: 句柄 {hwnd}")
        except Exception as e:
            self.log_callback(f"激活窗口失败: {str(e)}")