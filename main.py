# main.py
# 主程序：GUI 界面和核心逻辑，协调窗口管理和输入模拟，支持大厅和对局窗口，永不退出

import sys
import keyboard
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QLineEdit, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from window_manager import WindowManager
from input_simulator import InputSimulator
import threading
import ctypes
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QMainWindow):
    # 构造函数：初始化 GUI 和核心组件
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LOL自动脚本控制面板")
        self.setFixedSize(400, 300)
        self.init_ui()
        self.window_manager = WindowManager(self.log_message)
        self.input_simulator = InputSimulator(self.log_message)
        self.messages = ["大家好！", "一起加油！", "祝好运！"]  # 默认中文消息
        self.message_index = 0
        self.is_running = False
        self.setup_hotkey()
        self.check_admin()

    # 初始化 GUI 界面，添加消息输入框
    def init_ui(self):
        layout = QVBoxLayout()
        # 测试发送按钮
        self.test_button = QPushButton("测试消息发送")
        self.test_button.clicked.connect(self.test_send_message)
        layout.addWidget(self.test_button)
        # 消息输入框
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入新消息，按保存添加")
        layout.addWidget(self.message_input)
        # 保存消息按钮
        self.save_button = QPushButton("保存消息")
        self.save_button.clicked.connect(self.save_message)
        layout.addWidget(self.save_button)
        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # 检查是否以管理员权限运行
    def check_admin(self):
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                self.log_message("警告：请以管理员权限运行程序以确保功能正常")
        except Exception as e:
            self.log_message(f"检查管理员权限失败: {str(e)}")

    # 设置 F2 热键
    def setup_hotkey(self):
        threading.Thread(target=self.monitor_hotkey, daemon=True).start()

    # 监听 F2 键触发消息发送
    def monitor_hotkey(self):
        while True:
            try:
                keyboard.wait('f2')
                if not self.is_running:
                    self.is_running = True
                    self.log_message("F2 热键触发，启动消息发送")
                    self.send_message()
                    self.is_running = False
            except Exception as e:
                self.log_message(f"F2 热键处理失败: {str(e)}")
                time.sleep(1)  # 防止高频异常循环
                # 继续循环，不退出

    # 测试按钮触发消息发送
    def test_send_message(self):
        try:
            if not self.is_running:
                self.is_running = True
                self.log_message("测试按钮触发，启动消息发送")
                threading.Thread(target=self.send_message).start()
        except Exception as e:
            self.log_message(f"测试按钮处理失败: {str(e)}")
            self.is_running = False

    # 保存用户输入的消息
    def save_message(self):
        try:
            message = self.message_input.text().strip()
            if message:
                self.messages.append(message)
                self.log_message(f"已保存消息: {message}")
                self.message_input.clear()
            else:
                self.log_message("消息不能为空")
        except Exception as e:
            self.log_message(f"保存消息失败: {str(e)}")

    # 发送消息核心逻辑
    def send_message(self):
        try:
            hwnd, is_game = self.window_manager.find_lol_window()
            if not hwnd:
                self.log_message("未找到LOL窗口")
                self.is_running = False
                return
            self.window_manager.activate_window(hwnd)
            message = self.messages[self.message_index]
            self.input_simulator.send_message(hwnd, message, is_game)
            self.log_message(f"发送消息: {message} ({'对局窗口' if is_game else '大厅窗口'})")
            self.message_index = (self.message_index + 1) % len(self.messages)
        except Exception as e:
            self.log_message(f"发送消息失败: {str(e)}")
        finally:
            self.is_running = False

    # 日志显示并自动滚动
    def log_message(self, message):
        try:
            self.log_display.append(message)
            self.log_display.ensureCursorVisible()
            logging.info(message)
        except Exception as e:
            logging.error(f"日志记录失败: {str(e)}")

# 主函数：启动程序，捕获所有异常以确保永不退出
def main():
    while True:
        try:
            app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            window.log_message("程序启动")
            app.exec()
            window.log_message("用户手动关闭窗口，程序退出")
            break  # 用户手动关闭窗口后退出
        except BaseException as e:
            logging.error(f"程序异常: {str(e)}，重新启动")
            time.sleep(2)  # 等待 2 秒后重启，防止高频循环

if __name__ == "__main__":
    main()