import win32gui
def print_windows(hwnd, _):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if title:
            print(f"窗口标题：{title}")
win32gui.EnumWindows(print_windows, None)


def enum_child_windows(hwnd, _):
    class_name = win32gui.GetClassName(hwnd)
    title = win32gui.GetWindowText(hwnd)
    print(f"子控件：句柄={hwnd}, 类名={class_name}, 标题={title}")
hwnd = win32gui.FindWindow(None, "League of Legends (TM) Client")
if hwnd:
    win32gui.EnumChildWindows(hwnd, enum_child_windows, None)