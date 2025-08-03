# main.py

import sys
import time
import keyboard
from PyQt6.QtGui import QIcon, QTextCursor, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QComboBox, \
    QCheckBox, QHBoxLayout, QInputDialog, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from window_manager import WindowManager
from input_simulator import InputSimulator
from config_manager import ConfigManager
import threading
import ctypes
import logging
import webbrowser

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MainWindow(QMainWindow):
    # 定义一个 pyqtSignal，用于在后台线程中安全地更新GUI
    log_signal = pyqtSignal(str)

    # 构造函数：初始化 GUI 和核心组件
    def __init__(self):
        """
        初始化主窗口，设置窗口标题、大小，并初始化配置管理器、窗口管理器和输入模拟器。
        同时加载消息列表，初始化UI，设置热键，并检查管理员权限。
        """
        super().__init__()
        self.setWindowTitle("LOL友好交流器")
        # 修改：移除固定窗口大小，改为设置初始大小
        # 将窗口大小设置为固定
        self.setFixedSize(300, 270)

        # 将信号连接到槽函数
        self.log_signal.connect(self.log_message)

        # 设置窗口图标，确保 icon.ico 文件在项目根目录
        self.setWindowIcon(QIcon("icon.ico"))

        # 应用新的样式表，实现圆角、按钮美化等
        self.setStyleSheet("""
            /* 统一设置控件的圆角 */
            QTextEdit, QPushButton, QComboBox {
                border-radius: 5px;
            }

            /* 按钮的样式 */
            QPushButton {
                border: 1px solid #c4c4c4;
                padding: 5px;
            }

            QPushButton:hover {
                background-color: #e6e6e6; /* 悬停时背景稍亮 */
            }

            QPushButton:pressed {
                background-color: #dcdcdc; /* 按下时背景稍暗 */
                padding-top: 6px;
                padding-bottom: 4px;
            }

            /* 文本编辑框的样式 */
            QTextEdit {
                border: 1px solid #c4c4c4;
            }

            /* 下拉框的样式 */
            QComboBox {
                border: 1px solid #c4c4c4;
                padding-left: 5px;
            }

            /* 垂直滚动条的样式，实现圆角和美化，移除边框 */
            QScrollBar:vertical {
                border: none; /* 移除滚动条的边框 */
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background: #c4c4c4;
                border: none; /* 移除滑块的边框 */
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background: #a8a8a8;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
            }

            QScrollBar::groove:vertical {
                background: #e1e1e1;
                border-radius: 5px;
            }
        """)

        self.config_manager = ConfigManager()
        self.window_manager = WindowManager(self.log_signal.emit)
        self.input_simulator = InputSimulator(self.log_signal.emit)
        self.messages = self.config_manager.get_messages()
        self.message_group_index = 0
        self.message_line_index = 0
        self.line_status_label = None

        self.init_ui()

        # 调用核心逻辑，但不再产生日志
        self.check_admin()
        self.setup_hotkey()

        # 初始时，如果消息列表不为空，默认选中并显示第一条
        if self.messages:
            self.message_selector.setCurrentIndex(0)
            self.display_selected_message(0)

        # 将启动时的所有日志信息一次性写入并设置滚动条位置
        startup_log_html = self.get_startup_log_html()
        self.log_display.insertHtml(startup_log_html)
        self.log_display.verticalScrollBar().setValue(0)

    def get_startup_log_html(self):
        """
        生成启动时的所有日志信息的HTML字符串。
        """
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        admin_log = "已以管理员身份运行。" if is_admin else "警告：未以管理员身份运行，热键可能无法在游戏内工作。"

        startup_guide_html = (
            "<span style='color:red;'>软件用管理员身份打开</span><br>"
            "<b><span style='color:red;'>第一次使用请阅读：</span></b><br>"
            "<b><span style='color:blue;'>== 软件使用指南 ==</span></b><br>"
            "<b>F2</b>: 发送选中消息组（对局中无需打开聊天框直接按F2）。<br>"
            "<b>F12</b>: 切换全局聊天模式。<br>"
            "若热键无效，请以管理员身份运行。<br>"
        )

        selected_message_note = "无消息"
        if self.messages:
            selected_message_note = self.messages[0].get('note', f"消息组 1")

        log_html = (
            f"<span style='color:green;'>{admin_log}</span><br>"
            f"<span style='color:blue;'>热键F2和F12已设置。</span><br>"
            f"<span>已选择消息组: 1 ({selected_message_note})</span><br>"
            f"{startup_guide_html}"
        )
        return log_html

    def show_startup_guide(self):
        """
        此函数已被修改，不再写入日志，因为启动日志已在__init__中硬编码。
        """
        pass

    # 初始化 GUI 界面
    def init_ui(self):
        """
        初始化 GUI 界面，优化布局。
        - 增加下拉框的高度。
        - 减小预览区的高度和宽度。
        - 按钮高度增加并增加上下间距。
        - 调整“当前选中”标签和“日志”按钮的布局，使“当前选中”位于左下，日志按钮位于右下。
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建一个新的水平布局来容纳 GitHub 按钮和消息选择下拉框
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setContentsMargins(0, 0, 0, 0)
        top_controls_layout.setSpacing(5)

        # 消息选择下拉框
        self.message_selector = QComboBox()
        self.message_selector.setMinimumHeight(30)
        top_controls_layout.addWidget(self.message_selector, 1)

        # GitHub 按钮
        self.github_button = QPushButton()
        self.github_button.setFixedSize(QSize(25, 25))
        self.github_button.setIcon(QIcon("github_icon.ico"))
        self.github_button.setToolTip("访问我的GitHub")
        self.github_button.clicked.connect(self.open_github_link)
        self.github_button.setStyleSheet("""
            QPushButton {
                border: 0px;
                border-radius: 5px;
                background-color: transparent;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton:pressed {
                background-color: #dcdcdc;
            }
        """)
        top_controls_layout.addWidget(self.github_button)

        main_layout.addLayout(top_controls_layout)

        # 备注和勾选框布局
        note_checkbox_layout = QHBoxLayout()
        note_checkbox_layout.setContentsMargins(0, 0, 0, 0)
        # 备注标签
        self.note_label = QLabel("备注：")
        self.note_label.setStyleSheet("font-weight: bold;")
        note_checkbox_layout.addWidget(self.note_label)

        note_checkbox_layout.addStretch(1)  # 添加弹性空间，使布局更均匀

        # 勾选框
        self.all_chat_checkbox = QCheckBox(" /all  F12全局聊天")
        note_checkbox_layout.addWidget(self.all_chat_checkbox)

        # 连接勾选框的stateChanged信号
        self.all_chat_checkbox.stateChanged.connect(lambda: self.log_signal.emit(
            "全体消息 " + ("已勾选" if self.all_chat_checkbox.isChecked() else "已取消勾选")
        ))

        main_layout.addLayout(note_checkbox_layout)

        # 预览区域和按钮区域
        preview_and_button_layout = QHBoxLayout()
        preview_and_button_layout.setSpacing(5)
        preview_and_button_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧消息预览区
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("预览/编辑选中消息...")
        self.message_input.setMinimumHeight(40)  # 减小预览区的最小高度
        self.message_input.setMaximumWidth(250)  # 减小预览区的最大宽度
        self.message_input.setReadOnly(True)
        preview_and_button_layout.addWidget(self.message_input, 1)

        # 右侧按钮布局
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)  # 增加按钮之间的垂直间距

        # 使用 sizePolicy 来增加按钮高度
        size_policy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        # 为按钮添加圆角和阴影效果，提升视觉美感
        button_style = """
            QPushButton {
                border: 1px solid #c4c4c4;
                border-radius: 5px;
                padding: 5px;
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                 stop: 0 #f6f7fa, stop: 1 #dadbde);
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:hover {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                 stop: 0 #e6e7ea, stop: 1 #c4c5c8);
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                 stop: 0 #dadbde, stop: 1 #e6e7ea);
                padding-top: 6px;
                padding-bottom: 4px;
            }
        """

        self.add_message_button = QPushButton("添加新消息")
        self.add_message_button.clicked.connect(self.add_new_message)
        self.add_message_button.setSizePolicy(size_policy)
        self.add_message_button.setStyleSheet(button_style)
        button_layout.addWidget(self.add_message_button)

        self.edit_message_button = QPushButton("编辑选中消息")
        self.edit_message_button.clicked.connect(self.edit_selected_message)
        self.edit_message_button.setSizePolicy(size_policy)
        self.edit_message_button.setStyleSheet(button_style)
        button_layout.addWidget(self.edit_message_button)

        self.delete_button = QPushButton("删除选中消息")
        self.delete_button.clicked.connect(self.delete_selected_message)
        self.delete_button.setSizePolicy(size_policy)
        self.delete_button.setStyleSheet(button_style)
        button_layout.addWidget(self.delete_button)

        preview_and_button_layout.addLayout(button_layout)

        main_layout.addLayout(preview_and_button_layout)

        # 新增：用于日志显示区域的垂直布局
        log_section_layout = QVBoxLayout()
        log_section_layout.setContentsMargins(0, 0, 0, 0)
        log_section_layout.setSpacing(5)

        # 创建一个新的水平布局来容纳日志按钮和状态标签，但现在将它们分开
        bottom_controls_layout = QHBoxLayout()

        # 消息发送状态标签
        self.line_status_label = QLabel("当前选中：无消息")
        # 将标签对齐到左侧，并与预览区底部对齐
        self.line_status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # 使用 QSizePolicy 来控制其在布局中的行为，让它占据左侧空间
        label_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.line_status_label.setSizePolicy(label_policy)
        bottom_controls_layout.addWidget(self.line_status_label)

        # 增加一个弹性空间，将日志按钮推到右边
        bottom_controls_layout.addStretch(1)

        # 日志切换按钮
        self.log_toggle_button = QPushButton("日志▼")
        self.log_toggle_button.setStyleSheet("""
            QPushButton {
                border: 0px;
                border-radius: 5px;
                background-color: transparent;
                text-align: right; /* 将按钮文本对齐到右侧 */
                padding: 0;
            }
            QPushButton:hover {
                color: #0078d4; /* 悬停时颜色变化 */
            }
        """)
        self.log_toggle_button.clicked.connect(self.toggle_log_display)
        bottom_controls_layout.addWidget(self.log_toggle_button)

        # 将这个新的水平布局添加到主布局
        main_layout.addLayout(bottom_controls_layout)

        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        # 初始时设置日志区高度为0，使其默认隐藏
        self.log_display.setMaximumHeight(0)
        main_layout.addWidget(self.log_display)

        # 将日志光标设置到最开始，避免打开软件时在中间
        self.log_display.moveCursor(QTextCursor.MoveOperation.Start)

        # UI元素创建完成后再更新选择器，确保所有控件都已存在
        self.update_message_selector()

        self.message_selector.currentIndexChanged.connect(self.display_selected_message)
        self.message_selector.currentIndexChanged.connect(self.reset_message_line_index)
        self.message_selector.currentIndexChanged.connect(self.update_button_states)

        self.update_button_states()

    # 修改：用于切换日志显示区可见性的方法
    def toggle_log_display(self):
        """
        切换日志显示区的可见性，并更新按钮文本。
        """
        if self.log_display.maximumHeight() > 0:
            # 当前已展开，将其收起
            self.log_display.setMaximumHeight(0)
            self.log_toggle_button.setText("日志▼")
        else:
            # 当前已收起，将其展开
            self.log_display.setMaximumHeight(150)  # 设置展开后的高度
            self.log_toggle_button.setText("日志▲")

    def open_github_link(self):
        """
        槽函数：打开指定的GitHub链接。
        """
        github_url = "https://github.com/rhj-flash/LOL_Chat_Tool"
        try:
            webbrowser.open(github_url)
            self.log_signal.emit(f"已打开GitHub链接: {github_url}")
        except Exception as e:
            self.log_signal.emit(f"无法打开GitHub链接: {str(e)}")

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
        检查程序是否以管理员权限运行。此函数现在只执行检查逻辑，不再产生日志。
        """
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            # 这里可以保留日志记录到文件，但不再写入GUI
            logging.info("已以管理员身份运行。" if is_admin else "警告：未以管理员身份运行，热键可能无法在游戏内工作。")
        except Exception as e:
            logging.exception(f"检查管理员权限失败: {e}")

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
            self.log_signal.emit(f"已选择消息组: {index + 1} ({note})")
            self.update_line_status_label()
        else:
            self.message_input.clear()
            self.note_label.setText("备注：")
            self.log_signal.emit("消息列表为空，已清空预览区。")
            self.update_line_status_label()

    def add_new_message(self):
        """
        弹出一个独立的输入对话框，用于添加新消息。
        """
        # 1. 输入备注
        note, ok_note = QInputDialog.getText(self, "添加新消息", "请输入消息备注：")
        if not ok_note or not note.strip():
            self.log_signal.emit("备注为空，添加操作已取消。")
            return

        # 2. 输入消息内容
        message_str, ok_message = QInputDialog.getMultiLineText(self, "添加新消息", "请输入新消息内容，多行请换行：", "")
        if not ok_message or not message_str.strip():
            self.log_signal.emit("消息内容为空，添加操作已取消。")
            return

        # 3. 添加消息
        if self.config_manager.add_message(note, message_str):
            self.update_message_selector()
            self.message_selector.setCurrentIndex(len(self.messages) - 1)
            self.log_signal.emit(f"已成功添加新消息:\n备注: {note}\n内容: {message_str}")
        else:
            self.log_signal.emit("消息为空或已存在，添加失败。")

    def edit_selected_message(self):
        """
        弹出一个独立的输入对话框，预填充当前消息内容，用于编辑。
        """
        current_index = self.message_selector.currentIndex()
        if current_index < 0:
            self.log_signal.emit("未选择消息，无法编辑。")
            return

        current_message_data = self.messages[current_index]
        current_note = current_message_data['note']
        current_message_list = current_message_data['lines']
        current_message_str = "\n".join(current_message_list)

        # 1. 编辑备注
        new_note, ok_note = QInputDialog.getText(self, "编辑选中消息", f"编辑消息组 {current_index + 1} 的备注：",
                                                 text=current_note)
        if not ok_note or not new_note.strip():
            self.log_signal.emit("备注为空，编辑操作已取消。")
            return

        # 2. 编辑消息内容
        new_message_str, ok_message = QInputDialog.getMultiLineText(self, "编辑选中消息",
                                                                    f"编辑消息组 {current_index + 1} 的内容：",
                                                                    current_message_str)
        if not ok_message or not new_message_str.strip():
            self.log_signal.emit("消息内容为空，编辑操作已取消。")
            return

        # 3. 更新消息
        if self.config_manager.update_message(current_index, new_note, new_message_str):
            self.update_message_selector()
            self.message_selector.setCurrentIndex(current_index)
            self.log_signal.emit(f"已更新消息组 {current_index + 1}:\n新备注: {new_note}\n新内容: {new_message_str}")
        else:
            self.log_signal.emit("更新消息失败。")

    def delete_selected_message(self):
        """
        删除选中的消息。
        """
        current_index = self.message_selector.currentIndex()
        if current_index >= 0:
            if self.config_manager.delete_message(current_index):
                self.update_message_selector()
                self.log_signal.emit("已删除选中消息。")
                if self.messages:
                    self.message_selector.setCurrentIndex(0)
                else:
                    self.display_selected_message(-1)  # 清空显示
        else:
            self.log_signal.emit("未选择消息，无法删除。")

    def send_message(self):
        """
        发送消息核心逻辑，所有异常都在此捕获，以保证程序不退出。
        修改为每次调用只发送当前行的内容，然后移动到下一行。
        """
        try:
            self.log_signal.emit("开始发送消息...")
            hwnd, is_game = self.window_manager.find_lol_window()

            if not hwnd:
                self.log_signal.emit("未找到LOL窗口，无法发送消息。操作已终止。")
                return

            if not is_game:
                self.window_manager.activate_window(hwnd)
                self.log_signal.emit("已激活客户端窗口。")
            else:
                self.log_signal.emit("检测到对局窗口，将不激活窗口。")

            if not self.messages:
                self.log_signal.emit("消息列表为空，无法发送。")
                return

            current_message_data = self.messages[self.message_group_index]
            current_message_list = current_message_data['lines']
            current_note = current_message_data['note']
            total_lines = len(current_message_list)

            if total_lines == 0:
                self.log_signal.emit(f"消息组 {self.message_group_index + 1} ({current_note}) 为空，无法发送。")
                return

            if self.message_line_index >= total_lines:
                self.message_line_index = 0

            line_to_send = current_message_list[self.message_line_index]

            if not line_to_send.strip():
                self.log_signal.emit(
                    f"消息组 {self.message_group_index + 1} ({current_note}) 的第 {self.message_line_index + 1} 行为空行，跳过发送。")
            else:
                self.log_signal.emit(
                    f"准备发送消息组 {self.message_group_index + 1} ({current_note}) 的第 {self.message_line_index + 1} 行: {line_to_send}")

                prefix = "/all " if self.all_chat_checkbox.isChecked() else ""
                final_line = prefix + line_to_send

                self.input_simulator.send_message(hwnd, final_line, is_game)

            self.message_line_index = (self.message_line_index + 1) % total_lines
            self.update_line_status_label()

        except Exception as e:
            self.log_signal.emit(f"发送消息失败，发生异常: {str(e)}")
            logging.exception("发送消息时发生未处理的异常")
        finally:
            self.log_signal.emit("消息发送过程结束。")

    def start_send_thread(self):
        """
        创建一个新线程来执行 send_message 方法，避免阻塞GUI。
        """
        thread = threading.Thread(target=self.send_message)
        thread.daemon = True
        thread.start()

    def log_all_chat_state(self):
        """
        记录全体消息勾选框的状态。
        此函数不再直接调用，而是通过信号间接调用。
        """
        pass

    def toggle_all_chat_checkbox(self):
        """
        切换全体消息勾选框的选中状态，并通过F12触发。
        """
        self.all_chat_checkbox.setChecked(not self.all_chat_checkbox.isChecked())

    def setup_hotkey(self):
        """
        设置全局热键F2和F12，按下时调用相应方法。
        此函数现在只执行热键设置逻辑，不再产生日志。
        """
        keyboard.add_hotkey('f2', self.start_send_thread)
        keyboard.add_hotkey('f12', self.toggle_all_chat_checkbox)
        logging.info("热键F2和F12已设置。")

    def log_message(self, message):
        """
        在GUI日志框中显示消息并记录到日志文件。
        此函数现在是一个槽（slot），通过信号从其他线程安全地调用。
        :param message: 要显示的日志消息。
        """
        # 新增代码：获取当前时间并格式化为 分:秒
        current_time = time.strftime('%M:%S', time.localtime())

        # 构建HTML格式的日志消息
        if "已以管理员身份运行" in message:
            html_message = f"<b>{current_time}</b> - <span style='color:green;'>{message}</span><br>"
        elif "警告：未以管理员身份运行" in message:
            html_message = f"<b>{current_time}</b> - <span style='color:red;'>{message}</span><br>"
        elif "热键F2和F12已设置" in message:
            html_message = f"<b>{current_time}</b> - <span style='color:blue;'>{message}</span><br>"
        elif message.startswith("<b>") or message.startswith("<span"):
            # 对于包含HTML标签的特殊消息，保持其原有格式并添加时间戳
            html_message = f"<b>{current_time}</b> - {message}"
        else:
            html_message = f"<b>{current_time}</b> - <span>{message}</span><br>"

        # 确保滚动条在底部
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_display.setTextCursor(cursor)
        self.log_display.insertHtml(html_message)

        # 确保在日志区显示时，滚动条能自动滚动到底部
        if self.log_display.maximumHeight() > 0:
            self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())

        # 同时记录到日志文件，这里使用原始的logging配置，因为它通常需要完整的日期时间
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