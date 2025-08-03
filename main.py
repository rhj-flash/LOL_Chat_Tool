# main.py

import sys
import time
import keyboard
from PyQt6.QtGui import QIcon, QTextCursor, QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QComboBox, \
    QCheckBox, QHBoxLayout, QInputDialog, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from window_manager import WindowManager
from input_simulator import InputSimulator
from config_manager import ConfigManager
from custom_title_bar import CustomTitleBar  # 新增：导入自定义标题栏类
import threading
import ctypes
import logging
import webbrowser
import atexit

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MainWindow(QMainWindow):
    """
    应用程序主窗口类，包含 GUI 界面、热键处理和消息发送逻辑。
    """
    # 定义一个 pyqtSignal，用于在后台线程中安全地更新GUI
    log_signal = pyqtSignal(str)

    # 构造函数：初始化 GUI 和核心组件
    def __init__(self):

        """
        初始化主窗口，设置窗口标题、大小，并初始化配置管理器、窗口管理器和输入模拟器。
        同时加载消息列表，初始化UI，设置热键，并检查管理员权限。
        """
        super().__init__()

        # 移除默认标题栏
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("LOL友好交流器")
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
        self.sending_lock = threading.Lock()

        # 初始化UI，包括自定义标题栏
        self.init_ui()

        # 调用核心逻辑，但不再产生日志
        self.check_admin()
        self.setup_hotkey()

        # 使用 atexit 注册清理函数，确保程序退出时清理热键
        atexit.register(self.cleanup_hotkeys)

        # 初始时，如果消息列表不为空，默认选中并显示第一条
        if self.messages:
            self.message_selector.setCurrentIndex(0)
            self.display_selected_message(0)

        # 将启动时的所有日志信息一次性写入并设置滚动条位置
        startup_log_html = self.get_startup_log_html()
        self.log_display.insertHtml(startup_log_html)
        self.log_display.verticalScrollBar().setValue(0)

    # --------------------------- 新增/修改部分开始 -----------------------------

    def init_ui(self):
        """
        初始化 GUI 界面，使用自定义标题栏。
        """
        # 创建一个主容器Widget，作为中央窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 创建一个主布局，用于放置标题栏和内容区域
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 添加自定义标题栏
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # 创建一个内容区域的Widget，用于放置所有旧有的UI元素
        content_widget = QWidget()
        main_layout.addWidget(content_widget)

        # 创建一个垂直布局来容纳所有的UI元素（除了标题栏）
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # 创建一个新的水平布局来容纳 GitHub 按钮和消息选择下拉框
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setContentsMargins(0, 0, 0, 0)
        top_controls_layout.setSpacing(5)

        # 消息选择下拉框
        self.message_selector = QComboBox()
        self.message_selector.setMinimumHeight(30)
        top_controls_layout.addWidget(self.message_selector, 1)

        content_layout.addLayout(top_controls_layout)

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

        content_layout.addLayout(note_checkbox_layout)

        # 预览区域和按钮区域
        preview_and_button_layout = QHBoxLayout()
        preview_and_button_layout.setSpacing(5)
        preview_and_button_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧消息预览区
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("预览/编辑选中消息...")
        self.message_input.setMinimumHeight(40)
        self.message_input.setMaximumWidth(250)
        self.message_input.setReadOnly(True)
        preview_and_button_layout.addWidget(self.message_input, 1)

        # 右侧按钮布局
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)

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
        content_layout.addLayout(preview_and_button_layout)

        # 状态标签和日志按钮布局
        bottom_controls_layout = QHBoxLayout()
        bottom_controls_layout.setContentsMargins(0, 0, 0, 0)
        bottom_controls_layout.setSpacing(5)
        # 消息发送状态标签
        self.line_status_label = QLabel("当前选中：无消息")
        self.line_status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.line_status_label.setSizePolicy(label_policy)
        bottom_controls_layout.addWidget(self.line_status_label)

        # 增加一个弹性空间，将日志按钮推到右边
        bottom_controls_layout.addStretch(1)

        # 原始的日志切换按钮，现在只用于打开日志
        self.log_toggle_button = QPushButton("使用指南/日志▼")
        self.log_toggle_button.setStyleSheet("""
            QPushButton {
                border: 0px;
                border-radius: 5px;
                background-color: transparent;
                text-align: right;
                padding: 0;
            }
            QPushButton:hover {
                color: #0078d4;
            }
        """)
        self.log_toggle_button.clicked.connect(self.toggle_log_display)
        bottom_controls_layout.addWidget(self.log_toggle_button)

        content_layout.addLayout(bottom_controls_layout)

        # ==================== 日志叠加层部分修改 ====================
        # 创建一个日志显示区作为叠加层
        self.log_overlay_widget = QWidget(self)
        self.log_overlay_widget.setStyleSheet(
            "background-color: white; border-top: 1px solid #c4c4c4; border-radius: 5px;")
        log_overlay_layout = QVBoxLayout(self.log_overlay_widget)
        log_overlay_layout.setContentsMargins(5, 5, 5, 5)

        # 新增：用于关闭日志的按钮，位于叠加层内部
        self.close_log_button = QPushButton("日志▲")
        self.close_log_button.setStyleSheet("""
            QPushButton {
                border: 0px;
                border-radius: 5px;
                background-color: transparent;
                text-align: right;
                padding: 0;
            }
            QPushButton:hover {
                color: #0078d4;
            }
        """)
        self.close_log_button.clicked.connect(self.toggle_log_display)

        log_overlay_header_layout = QHBoxLayout()
        log_overlay_header_layout.addStretch()
        log_overlay_header_layout.addWidget(self.close_log_button)

        log_overlay_layout.addLayout(log_overlay_header_layout)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFontPointSize(8)
        self.log_display.setStyleSheet("background-color: #f0f0f0; border: none; border-radius: 5px;")
        log_overlay_layout.addWidget(self.log_display)
        self.log_overlay_widget.hide()  # 初始时隐藏叠加层
        # ==================== 日志叠加层部分修改结束 ====================

        # 设置主布局的伸缩因子，确保内容区域占据剩余所有空间
        main_layout.setStretch(1, 1)

        self.update_message_selector()

        self.message_selector.currentIndexChanged.connect(self.display_selected_message)
        self.message_selector.currentIndexChanged.connect(self.reset_message_line_index)
        self.message_selector.currentIndexChanged.connect(self.update_button_states)

        self.update_button_states()

    # --------------------------- 新增/修改部分结束 -----------------------------

    def cleanup_hotkeys(self):
        """
        程序退出时清理所有热键。
        """
        keyboard.unhook_all()
        logging.info("程序退出，已清除所有热键。")
        self.log_signal.emit("程序退出，已清除所有热键。")

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


    # main.py

    def toggle_log_display(self):
        """
        切换日志显示区叠加层的可见性。
        """
        if self.log_overlay_widget.isHidden():
            # 显示叠加层
            self.log_overlay_widget.setGeometry(
                0, self.height() - 150,
                self.width(), 150
            )
            self.log_overlay_widget.show()
            # 确保日志叠加层始终在所有控件的最上层
            self.log_overlay_widget.raise_()
        else:
            # 隐藏叠加层
            self.log_overlay_widget.hide()

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
        检查程序是否以管理员权限运行。
        """
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
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
        # 尝试获取锁，如果无法获取，说明上一次发送还在进行，则直接退出
        if not self.sending_lock.acquire(blocking=False):
            self.log_signal.emit("正在发送中，忽略本次热键请求。")
            return

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
            self.sending_lock.release()
            self.log_signal.emit("消息发送过程结束。")

    def start_send_thread(self):
        """
        创建一个新线程来执行 send_message 方法，避免阻塞GUI。
        """
        thread = threading.Thread(target=self.send_message)
        thread.daemon = True
        thread.start()

    def toggle_all_chat_checkbox(self):
        """
        切换全体消息勾选框的选中状态，并通过F12触发。
        """
        self.all_chat_checkbox.setChecked(not self.all_chat_checkbox.isChecked())

    def setup_hotkey(self):
        """
        设置全局热键F2和F12，按下时调用相应方法。
        """
        keyboard.add_hotkey('f2', self.start_send_thread)
        keyboard.add_hotkey('f12', self.toggle_all_chat_checkbox)
        logging.info("热键F2和F12已设置。")

    def log_message(self, message):
        """
        在GUI日志框中显示消息并记录到日志文件。
        """
        current_time = time.strftime('%M:%S', time.localtime())
        if "已以管理员身份运行" in message:
            html_message = f"<b>{current_time}</b> - <span style='color:green;'>{message}</span><br>"
        elif "警告：未以管理员身份运行" in message:
            html_message = f"<b>{current_time}</b> - <span style='color:red;'>{message}</span><br>"
        elif "热键F2和F12已设置" in message:
            html_message = f"<b>{current_time}</b> - <span style='color:blue;'>{message}</span><br>"
        elif message.startswith("<b>") or message.startswith("<span"):
            html_message = f"<b>{current_time}</b> - {message}"
        else:
            html_message = f"<b>{current_time}</b> - <span>{message}</span><br>"

        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_display.setTextCursor(cursor)
        self.log_display.insertHtml(html_message)

        if self.log_display.maximumHeight() > 0:
            self.log_display.verticalScrollBar().setValue(self.log_display.verticalScrollBar().maximum())

        logging.info(message)

    def closeEvent(self, event):
        """
        程序退出时清理所有热键。
        """
        self.cleanup_hotkeys()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())