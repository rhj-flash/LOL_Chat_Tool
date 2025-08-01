import sys
import time
import keyboard
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QComboBox, \
    QCheckBox, QHBoxLayout, QInputDialog, QLabel
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
        """
        初始化主窗口，设置窗口标题、大小，并初始化配置管理器、窗口管理器和输入模拟器。
        同时加载消息列表，初始化UI，设置热键，并检查管理员权限。
        """
        super().__init__()
        self.setWindowTitle("LOL自动脚本控制面板")
        self.setFixedSize(350, 450)  # 调整窗口高度以容纳新的 UI 元素

        self.setStyleSheet("")

        self.config_manager = ConfigManager()
        self.window_manager = WindowManager(self.log_message)
        self.input_simulator = InputSimulator(self.log_message)
        self.messages = self.config_manager.get_messages()
        self.message_group_index = 0  # 追踪当前选中的消息组
        self.message_line_index = 0  # 新增：追踪当前消息组内发送到哪一行了
        self.line_status_label = None  # 在init_ui中创建，这里先初始化为None

        self.init_ui()
        self.setup_hotkey()
        self.check_admin()

        # 初始时，如果消息列表不为空，默认选中并显示第一条
        if self.messages:
            self.message_selector.setCurrentIndex(0)
            self.display_selected_message(0)

    # 初始化 GUI 界面
    def init_ui(self):
        """
        初始化 GUI 界面，恢复三个独立按钮，并优化布局。
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # 消息选择下拉框
        self.message_selector = QComboBox()
        layout.addWidget(self.message_selector)

        # 消息备注标签
        self.note_label = QLabel("备注：")
        self.note_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.note_label)

        # 消息输入和预览
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("预览/编辑选中消息...")
        self.message_input.setMinimumHeight(120)
        self.message_input.setReadOnly(True)
        layout.addWidget(self.message_input)

        # 消息发送状态标签
        self.line_status_label = QLabel("当前选中：无消息")
        self.line_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.line_status_label)

        # UI元素创建完成后再更新选择器，确保所有控件都已存在
        self.update_message_selector()

        self.message_selector.currentIndexChanged.connect(self.display_selected_message)
        self.message_selector.currentIndexChanged.connect(self.reset_message_line_index)
        self.message_selector.currentIndexChanged.connect(self.update_button_states)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        self.add_message_button = QPushButton("添加新消息")
        self.add_message_button.clicked.connect(self.add_new_message)
        button_layout.addWidget(self.add_message_button)

        self.edit_message_button = QPushButton("编辑选中消息")
        self.edit_message_button.clicked.connect(self.edit_selected_message)
        button_layout.addWidget(self.edit_message_button)

        self.delete_button = QPushButton("删除选中消息")
        self.delete_button.clicked.connect(self.delete_selected_message)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

        self.all_chat_checkbox = QCheckBox("按F12自动勾选/取消，勾选后每次发送自动添加 '/all '")
        layout.addWidget(self.all_chat_checkbox)

        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(80)
        layout.addWidget(self.log_display)

        self.update_button_states()

    def reset_message_line_index(self):
        """
        重置当前消息组的行索引。
        """
        self.message_line_index = 0
        self.update_line_status_label()

    def update_line_status_label(self):
        """
        更新消息发送状态标签。
        """
        current_index = self.message_selector.currentIndex()
        if self.messages and 0 <= current_index < len(self.messages):
            message_list = self.messages[current_index]['lines']
            total_lines = len(message_list)
            current_line = min(self.message_line_index + 1, total_lines)
            self.line_status_label.setText(f"当前选中：消息组 {current_index + 1} ({current_line}/{total_lines} 行)")
        else:
            self.line_status_label.setText("当前选中：无消息")

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

    def update_message_selector(self):
        """
        更新消息选择器下拉框的内容，显示消息组的序号和备注。
        """
        self.messages = self.config_manager.get_messages()
        self.message_selector.clear()
        if self.messages:
            for i, msg_data in enumerate(self.messages):
                note = msg_data.get('note', f"消息组 {i + 1}")
                self.message_selector.addItem(f"消息组 {i + 1} - {note}")
            if self.message_group_index >= len(self.messages):
                self.message_group_index = max(0, len(self.messages) - 1)
            self.message_selector.setCurrentIndex(self.message_group_index)
        self.reset_message_line_index()

    def update_button_states(self):
        """
        根据当前UI状态更新三个按钮的启用/禁用状态。
        """
        has_messages = bool(self.messages)
        self.add_message_button.setEnabled(True)
        self.edit_message_button.setEnabled(has_messages)
        self.delete_button.setEnabled(has_messages)

    def display_selected_message(self, index):
        """
        槽函数，当消息选择器的选择改变时，将选中消息的内容填充到输入框中。
        """
        self.message_group_index = index
        if 0 <= index < len(self.messages):
            selected_message_data = self.messages[index]
            selected_message_list = selected_message_data['lines']
            note = selected_message_data['note']
            message_str = "\n".join(selected_message_list)
            self.message_input.setPlainText(message_str)
            self.note_label.setText(f"备注：{note}")
            self.log_message(f"已选择消息组: {index + 1} ({note})")
            self.update_line_status_label()
        else:
            self.message_input.clear()
            self.note_label.setText("备注：")
            self.log_message("消息列表为空，已清空预览区。")
            self.update_line_status_label()

    def add_new_message(self):
        """
        弹出一个独立的输入对话框，用于添加新消息。
        """
        # 1. 输入备注
        note, ok_note = QInputDialog.getText(self, "添加新消息", "请输入消息备注：")
        if not ok_note or not note.strip():
            self.log_message("备注为空，添加操作已取消。")
            return

        # 2. 输入消息内容
        message_str, ok_message = QInputDialog.getMultiLineText(self, "添加新消息", "请输入新消息内容，多行请换行：", "")
        if not ok_message or not message_str.strip():
            self.log_message("消息内容为空，添加操作已取消。")
            return

        # 3. 添加消息
        if self.config_manager.add_message(note, message_str):
            self.update_message_selector()
            self.message_selector.setCurrentIndex(len(self.messages) - 1)
            self.log_message(f"已成功添加新消息:\n备注: {note}\n内容: {message_str}")
        else:
            self.log_message("消息为空或已存在，添加失败。")

    def edit_selected_message(self):
        """
        弹出一个独立的输入对话框，预填充当前消息内容，用于编辑。
        """
        current_index = self.message_selector.currentIndex()
        if current_index < 0:
            self.log_message("未选择消息，无法编辑。")
            return

        current_message_data = self.messages[current_index]
        current_note = current_message_data['note']
        current_message_list = current_message_data['lines']
        current_message_str = "\n".join(current_message_list)

        # 1. 编辑备注
        new_note, ok_note = QInputDialog.getText(self, "编辑选中消息", f"编辑消息组 {current_index + 1} 的备注：",
                                                 text=current_note)
        if not ok_note or not new_note.strip():
            self.log_message("备注为空，编辑操作已取消。")
            return

        # 2. 编辑消息内容
        new_message_str, ok_message = QInputDialog.getMultiLineText(self, "编辑选中消息",
                                                                    f"编辑消息组 {current_index + 1} 的内容：",
                                                                    current_message_str)
        if not ok_message or not new_message_str.strip():
            self.log_message("消息内容为空，编辑操作已取消。")
            return

        # 3. 更新消息
        if self.config_manager.update_message(current_index, new_note, new_message_str):
            self.update_message_selector()
            self.message_selector.setCurrentIndex(current_index)
            self.log_message(f"已更新消息组 {current_index + 1}:\n新备注: {new_note}\n新内容: {new_message_str}")
        else:
            self.log_message("更新消息失败。")

    def delete_selected_message(self):
        """
        删除选中的消息。
        """
        current_index = self.message_selector.currentIndex()
        if current_index >= 0:
            if self.config_manager.delete_message(current_index):
                self.update_message_selector()
                self.log_message("已删除选中消息。")
                if self.messages:
                    self.message_selector.setCurrentIndex(0)
                else:
                    self.display_selected_message(-1)  # 清空显示
        else:
            self.log_message("未选择消息，无法删除。")

    def send_message(self):
        """
        发送消息核心逻辑，所有异常都在此捕获，以保证程序不退出。
        修改为每次调用只发送当前行的内容，然后移动到下一行。
        """
        try:
            self.log_message("开始发送消息...")
            hwnd, is_game = self.window_manager.find_lol_window()
            if not hwnd:
                self.log_message("未找到LOL窗口，无法发送消息。")
                return

            if not is_game:
                self.window_manager.activate_window(hwnd)
                self.log_message("已激活客户端窗口。")
            else:
                self.log_message("检测到对局窗口，将不激活窗口。")

            if not self.messages:
                self.log_message("消息列表为空，无法发送。")
                return

            current_message_data = self.messages[self.message_group_index]
            current_message_list = current_message_data['lines']
            current_note = current_message_data['note']
            total_lines = len(current_message_list)

            if total_lines == 0:
                self.log_message(f"消息组 {self.message_group_index + 1} ({current_note}) 为空，无法发送。")
                return

            if self.message_line_index >= total_lines:
                self.message_line_index = 0

            line_to_send = current_message_list[self.message_line_index]

            if not line_to_send.strip():
                self.log_message(
                    f"消息组 {self.message_group_index + 1} ({current_note}) 的第 {self.message_line_index + 1} 行为空行，跳过发送。")
            else:
                self.log_message(
                    f"准备发送消息组 {self.message_group_index + 1} ({current_note}) 的第 {self.message_line_index + 1} 行: {line_to_send}")

                prefix = "/all " if self.all_chat_checkbox.isChecked() else ""
                final_line = prefix + line_to_send

                self.input_simulator.send_message(hwnd, final_line, is_game)

            self.message_line_index = (self.message_line_index + 1) % total_lines
            self.update_line_status_label()

        except Exception as e:
            self.log_message(f"发送消息失败，发生异常: {str(e)}")
            logging.exception("发送消息时发生未处理的异常")
        finally:
            self.log_message("消息发送过程结束。")

    def start_send_thread(self):
        """
        创建一个新线程来执行 send_message 方法，避免阻塞GUI。
        """
        thread = threading.Thread(target=self.send_message)
        thread.daemon = True
        thread.start()

    def toggle_all_chat_checkbox(self):
        """
        切换全体消息勾选框的选中状态。
        """
        self.all_chat_checkbox.setChecked(not self.all_chat_checkbox.isChecked())
        state = "已勾选" if self.all_chat_checkbox.isChecked() else "已取消勾选"
        self.log_message(f"通过F12热键切换状态：全体消息 {state}")

    def setup_hotkey(self):
        """
        设置全局热键F2和F12，按下时调用相应方法。
        """
        keyboard.add_hotkey('f2', self.start_send_thread)
        keyboard.add_hotkey('f12', self.toggle_all_chat_checkbox)
        self.log_message("热键F2和F12已设置，随时待命。")

    def log_message(self, message):
        """
        在GUI日志框中显示消息并记录到日志文件。
        """
        self.log_display.append(message)
        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_display.setTextCursor(cursor)
        logging.info(message)

    def closeEvent(self, event):
        """
        程序退出时清理所有热键。
        """
        keyboard.unhook_all()
        logging.info("程序退出，已清除所有热键。")
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())