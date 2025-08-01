# main.py
# 主程序：GUI 界面和核心逻辑，协调窗口管理和输入模拟，支持大厅和对局窗口

import sys
import time

import keyboard
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QComboBox, \
    QCheckBox, QHBoxLayout
from PyQt6.QtCore import Qt
from window_manager import WindowManager
from input_simulator import InputSimulator
from config_manager import ConfigManager
import threading
import ctypes
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MainWindow(QMainWindow):
    # 构造函数：初始化 GUI 和核心组件
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LOL自动脚本控制面板")
        self.setFixedSize(350, 350)  # 将窗口大小固定为 350x350，使其不可更改

        # 移除所有自定义样式，让GUI恢复默认外观
        self.setStyleSheet("")

        self.config_manager = ConfigManager()  # 初始化配置管理
        self.window_manager = WindowManager(self.log_message)
        self.input_simulator = InputSimulator(self.log_message)
        self.messages = self.config_manager.get_messages()  # 从配置文件加载消息
        self.message_index = 0
        self.init_ui()
        self.setup_hotkey()
        self.check_admin()

        # 在程序启动时，如果消息列表不为空，则自动显示第一条消息
        if self.messages:
            self.display_selected_message(0)

    # 初始化 GUI 界面
    def init_ui(self):
        """
        初始化 GUI 界面，并优化布局，使其更加紧凑。
        本次修改将消息选择下拉框移动到最上方，并将三个按钮放在同一行。
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 调整布局间距，使其更紧凑
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # 消息选择 (移动到最上方)
        self.message_selector = QComboBox()
        self.update_message_selector()
        layout.addWidget(self.message_selector)

        self.message_selector.currentIndexChanged.connect(self.display_selected_message)

        # 消息输入和编辑
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("在此输入新消息，支持多行...")
        self.message_input.setMinimumHeight(80)
        layout.addWidget(self.message_input)

        # 按钮布局，使用 QHBoxLayout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        # 编辑消息按钮
        self.edit_button = QPushButton("编辑选中消息")
        self.edit_button.clicked.connect(self.edit_selected_message)
        button_layout.addWidget(self.edit_button)

        # 添加新消息按钮
        self.add_button = QPushButton("添加新消息")
        self.add_button.clicked.connect(self.add_new_message)
        button_layout.addWidget(self.add_button)

        # 删除消息
        self.delete_button = QPushButton("删除选中消息")
        self.delete_button.clicked.connect(self.delete_selected_message)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

        # 全体消息勾选框
        self.all_chat_checkbox = QCheckBox("按F12自动勾选/取消，勾选后每次发送自动添加 '/all '")
        layout.addWidget(self.all_chat_checkbox)

        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(70)  # 将日志区域高度限制在三行左右
        layout.addWidget(self.log_display)

    # 检查程序是否以管理员权限运行
    def check_admin(self):
        """
        检查程序是否以管理员权限运行，并在日志中显示结果。
        """
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if is_admin:
                self.log_message("已以管理员身份运行。")
            else:
                self.log_message("警告：未以管理员身份运行，热键可能无法在游戏内工作。")
        except Exception as e:
            self.log_message(f"检查管理员权限失败: {e}")

    # 更新消息选择器
    def update_message_selector(self):
        """
        更新消息选择器下拉框的内容，显示每条多行消息的第一行作为代表。
        """
        self.messages = self.config_manager.get_messages()
        self.message_selector.clear()
        if self.messages:
            # 遍历消息列表，每条消息本身是一个列表
            for msg_list in self.messages:
                # 检查消息列表是否为空，并取第一个元素作为显示文本
                if msg_list and msg_list[0]:
                    self.message_selector.addItem(msg_list[0])
                else:
                    # 如果消息列表为空或第一行为空，则添加一个默认占位符
                    self.message_selector.addItem("[空消息]")
            self.message_selector.setCurrentIndex(self.message_index)

    # 显示选中消息的内容到输入框
    def display_selected_message(self, index):
        """
        槽函数，当消息选择器的选择改变时，将选中消息的内容填充到输入框中。
        本次修改：当手动选择消息时，将内部发送索引 (self.message_index) 更新为当前选中索引。
        """
        # 将下拉框的当前索引赋值给内部消息索引
        self.message_index = index

        # 确保索引在有效范围内
        if 0 <= index < len(self.messages):
            # 获取选中的消息列表
            selected_message_list = self.messages[index]
            # 将消息列表中的每一行用换行符连接成一个字符串
            message_str = "\n".join(selected_message_list)
            # 将字符串设置到 QTextEdit
            self.message_input.setPlainText(message_str)
            self.log_message(f"已选择消息组: {selected_message_list}")
        else:
            # 如果索引无效（比如消息列表为空），清空输入框
            self.message_input.clear()
            self.log_message("消息列表为空或索引无效，已清空输入框。")

    # 添加新消息
    def add_new_message(self):
        """
        添加新消息。从 QTextEdit 获取多行文本。
        修改：添加后无论成功与否都清空输入框。
              同时，优化日志输出，当添加多行消息时，显示摘要而非完整内容，
              以避免日志显示被截断。
        """
        # 使用 toPlainText() 获取 QTextEdit 的内容
        new_message_str = self.message_input.toPlainText().strip()

        # 尝试添加消息
        success, message_lines = self.config_manager.add_message(new_message_str)

        if success:
            line_count = len(message_lines)
            first_line = message_lines[0] if message_lines else "[空消息]"
            self.update_message_selector()
            self.log_message(f"已成功添加新消息 (共 {line_count} 行): '{first_line}...'")
        else:
            self.log_message("消息为空或已存在，添加失败。")

        # 无论成功与否，清空输入框，以便用户输入下一条消息
        self.message_input.clear()

    # 编辑选中消息
    def edit_selected_message(self):
        """
        将文本框中的内容保存到当前选中的消息中。
        """
        current_index = self.message_selector.currentIndex()
        if current_index >= 0:
            new_message_str = self.message_input.toPlainText().strip()
            # 调用ConfigManager中的新方法来更新消息
            if self.config_manager.update_message(current_index, new_message_str):
                self.update_message_selector()
                self.message_selector.setCurrentIndex(current_index)
                self.log_message("已更新选中消息。")
            else:
                self.log_message("更新消息失败。")
        else:
            self.log_message("未选择消息，无法编辑。")

    # 删除选中消息
    def delete_selected_message(self):
        """
        删除选中的消息。
        """
        current_index = self.message_selector.currentIndex()
        if current_index >= 0:
            selected_message = self.messages[current_index]
            self.config_manager.delete_message(selected_message)
            self.update_message_selector()
            self.log_message(f"已删除消息: {selected_message}")
        else:
            self.log_message("未选择消息")

    # 发送消息核心逻辑
    def send_message(self):
            """
            发送消息核心逻辑，所有异常都在此捕获，以保证程序不退出。
            支持多行消息分次发送。
            本次修改：在发送的每一行消息前添加一个空格，以确保格式正确。
            """
            try:
                self.log_message("开始发送消息...")
                hwnd, is_game = self.window_manager.find_lol_window()
                if not hwnd:
                    self.log_message("未找到LOL窗口，无法发送消息。")
                    return

                # 根据窗口类型决定是否强制激活窗口
                if not is_game:
                    self.window_manager.activate_window(hwnd)
                    self.log_message("已激活客户端窗口。")
                else:
                    self.log_message("检测到对局窗口，为避免全屏模式被弹出，将不激活窗口。")

                if not self.messages:
                    self.log_message("消息列表为空，无法发送。")
                    return

                message_to_send_list = self.messages[self.message_index]
                self.log_message(f"准备发送多行消息组: '{message_to_send_list}'")

                prefix = "/all " if self.all_chat_checkbox.isChecked() else ""

                for line in message_to_send_list:
                    if not line.strip():
                        continue

                    # 在每行消息前添加一个空格
                    final_line = prefix + " " + line
                    self.log_message(f"准备发送消息行: '{final_line}'")
                    self.input_simulator.send_message(hwnd, final_line, is_game)
                    time.sleep(0.1)

                self.log_message("多行消息组已发送。")

                self.message_index = (self.message_index + 1) % len(self.messages) if self.messages else 0
                self.message_selector.setCurrentIndex(self.message_index)

            except Exception as e:
                self.log_message(f"发送消息失败，发生异常: {str(e)}")
                logging.exception("发送消息时发生未处理的异常")
            finally:
                self.log_message("消息发送过程结束。")

    # 启动消息发送线程
    def start_send_thread(self):
        """
        创建一个新线程来执行 send_message 方法，避免阻塞GUI。
        """
        thread = threading.Thread(target=self.send_message)
        thread.daemon = True
        thread.start()

    # 切换全体消息勾选框的状态
    def toggle_all_chat_checkbox(self):
        """
        切换全体消息勾选框的选中状态。
        """
        self.all_chat_checkbox.setChecked(not self.all_chat_checkbox.isChecked())
        state = "已勾选" if self.all_chat_checkbox.isChecked() else "已取消勾选"
        self.log_message(f"通过F12热键切换状态：全体消息 {state}")

    # 设置热键
    def setup_hotkey(self):
        """
        设置全局热键F2和F12，按下时调用相应方法。
        """
        keyboard.add_hotkey('f2', self.start_send_thread)
        keyboard.add_hotkey('f12', self.toggle_all_chat_checkbox)
        self.log_message("热键F2和F12已设置，随时待命。")

    # 日志显示并自动滚动
    def log_message(self, message):
        """
        在GUI日志框中显示消息并记录到日志文件。
        """
        self.log_display.append(message)
        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_display.setTextCursor(cursor)
        logging.info(message)

    # 退出程序时清理热键
    def closeEvent(self, event):
        """
        程序退出时清理所有热键。
        """
        keyboard.unhook_all()
        logging.info("程序退出，已清除所有热键。")
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())