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
        if self.log_display.maximumHeight() > 0:  # 当前已展开，将其收起
            self.log_display.setMaximumHeight(0)
            self.log_toggle_button.setText("日志▼")
        else:  # 当前已收起，将其展开
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
        更新底部状态栏的文本，显示当前选中消息组和消息行。
        """
        current_index = self.message_selector.currentIndex()
        if self.messages and 0 <= current_index < len(self.messages):
            message_group = self.messages[current_index]
            note = message_group.get('note', f"消息组 {current_index + 1}")
            total_lines = len(message_group.get('lines', []))
            self.line_status_label.setText(f"当前选中: {note} ({self.message_line_index + 1}/{total_lines})")
        else:
            self.line_status_label.setText("当前选中：无消息")

    def log_message(self, message):
        """
        槽函数：在日志显示区域添加一条新消息。
        :param message: 要显示的日志消息。
        """
        self.log_display.append(f"<span style='color: #4a4a4a;'>{message}</span>")

    def update_message_selector(self):
        """
        更新消息选择下拉框的内容。
        """
        self.message_selector.clear()
        if self.messages:
            for i, msg in enumerate(self.messages):
                note = msg.get('note', f"消息组 {i + 1}")
                self.message_selector.addItem(note)
        else:
            self.message_selector.addItem("无消息")

    def display_selected_message(self, index):
        """
        根据下拉框选中的索引显示对应的消息内容到预览区。
        """
        if 0 <= index < len(self.messages):
            selected_message = self.messages[index]
            self.message_input.setPlainText("\n".join(selected_message.get('lines', [])))
            self.note_label.setText(f"备注：{selected_message.get('note', '')}")
            self.message_group_index = index
            self.update_line_status_label()
        else:
            self.message_input.clear()
            self.note_label.setText("备注：")
            self.line_status_label.setText("当前选中：无消息")

    def update_button_states(self):
        """
        根据消息列表是否为空来更新按钮的启用状态。
        """
        has_messages = bool(self.messages)
        self.edit_message_button.setEnabled(has_messages)
        self.delete_button.setEnabled(has_messages)
        self.message_selector.setEnabled(has_messages)

    def add_new_message(self):
        """
        处理“添加新消息”按钮的点击事件，弹窗让用户输入新消息。
        """
        new_note, ok = QInputDialog.getText(self, "添加新消息", "请输入消息组的备注:")
        if ok and new_note:
            new_message_str, ok = QInputDialog.getMultiLineText(self, "添加新消息", "请输入消息内容（可多行）:")
            if ok and new_message_str:
                self.config_manager.add_message(new_note, new_message_str)
                self.messages = self.config_manager.get_messages()  # 重新加载消息列表
                self.update_message_selector()
                # 自动选中新添加的消息
                self.message_selector.setCurrentIndex(len(self.messages) - 1)
                self.update_button_states()

    def edit_selected_message(self):
        """
        处理“编辑选中消息”按钮的点击事件，弹窗让用户编辑选中消息。
        """
        current_index = self.message_selector.currentIndex()
        if 0 <= current_index < len(self.messages):
            current_note = self.messages[current_index].get('note', '')
            current_lines = "\n".join(self.messages[current_index].get('lines', []))

            # 让用户编辑备注
            new_note, ok = QInputDialog.getText(self, "编辑消息备注", "请输入新备注:", text=current_note)
            if ok:
                # 让用户编辑消息内容
                new_message_str, ok_content = QInputDialog.getMultiLineText(self, "编辑消息内容", "请输入新消息内容:",
                                                                           text=current_lines)
                if ok_content:
                    self.config_manager.edit_message(current_index, new_note, new_message_str)
                    self.messages = self.config_manager.get_messages()
                    self.update_message_selector()
                    self.message_selector.setCurrentIndex(current_index)
                    self.display_selected_message(current_index)

    def delete_selected_message(self):
        """
        处理“删除选中消息”按钮的点击事件，删除选中的消息。
        """
        current_index = self.message_selector.currentIndex()
        if 0 <= current_index < len(self.messages):
            self.config_manager.delete_message(current_index)
            self.messages = self.config_manager.get_messages()
            self.update_message_selector()
            self.message_selector.setCurrentIndex(min(current_index, len(self.messages) - 1))
            self.update_button_states()

    def setup_hotkey(self):
        """
        设置全局热键，用于触发发送消息。
        """
        hotkey_start_send = self.config_manager.get_config("hotkey_start_send", "f2")
        hotkey_all_chat_toggle = self.config_manager.get_config("hotkey_all_chat_toggle", "f12")

        try:
            keyboard.add_hotkey(hotkey_start_send, self.send_selected_message_hotkey)
            keyboard.add_hotkey(hotkey_all_chat_toggle, self.toggle_all_chat_hotkey)
            self.log_signal.emit(f"热键 '{hotkey_start_send}' 和 '{hotkey_all_chat_toggle}' 已成功设置。")
        except Exception as e:
            self.log_signal.emit(f"设置热键失败: {e}。请尝试以管理员身份运行。")

    def toggle_all_chat_hotkey(self):
        """
        热键回调函数：切换 /all 聊天模式。
        """
        # 如果不是主线程，使用信号来更新GUI
        if self.thread() != QApplication.instance().thread():
            self.all_chat_checkbox.setCheckState(Qt.CheckState.Unchecked if self.all_chat_checkbox.isChecked() else Qt.CheckState.Checked)
        else:
            self.all_chat_checkbox.setChecked(not self.all_chat_checkbox.isChecked())

    def check_admin(self):
        """
        检查程序是否以管理员身份运行，并给出提示。
        """
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if not is_admin:
            self.log_signal.emit("警告：未以管理员身份运行，热键可能无法在游戏内工作。")

    # 这部分代码是关键修改，请仔细检查
    def send_selected_message_hotkey(self):
        """
        热键回调函数：发送下拉框中选中的整个消息组。
        此方法会在单独的线程中执行，以避免阻塞主GUI。
        """
        # 在新线程中执行，以确保UI不会因为等待输入而冻结
        thread = threading.Thread(target=self._send_all_messages_in_group_thread)
        thread.daemon = True
        thread.start()

    def _send_all_messages_in_group_thread(self):
        """
        后台线程函数：发送当前选中的整个消息组。
        """
        # 禁用热键，防止重复触发
        keyboard.unhook_all()
        try:
            current_index = self.message_selector.currentIndex()
            if not self.messages or not (0 <= current_index < len(self.messages)):
                self.log_signal.emit("没有可发送的消息组。")
                return

            message_group = self.messages[current_index]
            note = message_group.get('note', f"消息组 {current_index + 1}")
            lines = message_group.get('lines', [])

            self.log_signal.emit(f"准备发送消息组：'{note}'...")

            # 激活 LOL 窗口
            self.window_manager.activate_lol_window()

            # 检查是否需要发送 /all
            is_all_chat = self.all_chat_checkbox.isChecked()

            for i, line in enumerate(lines):
                # 确保在发送每条消息前都打开聊天框
                self.input_simulator.open_chat_and_send_message(line, is_all_chat)
                # 更新UI状态，通过信号回到主线程
                self.log_signal.emit(f"已发送消息({i + 1}/{len(lines)})：{line}")
                # 增加延时，防止输入过快
                time.sleep(0.5)

            self.log_signal.emit(f"消息组 '{note}' 发送完毕。")
            self.message_line_index = 0
            self.update_line_status_label()

        except Exception as e:
            self.log_signal.emit(f"发送消息时发生错误: {str(e)}")
            logging.exception("发送消息时发生异常")
        finally:
            # 重新设置热键
            self.setup_hotkey()

    def closeEvent(self, event):
        """
        重写 closeEvent，确保在程序关闭时解绑热键。
        """
        keyboard.unhook_all()
        logging.info("程序已关闭，热键已解绑。")
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())