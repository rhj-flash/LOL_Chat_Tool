# custom_title_bar.py

import sys
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize, QPoint


class CustomTitleBar(QWidget):
    """
    自定义窗口标题栏，实现窗口拖动、最小化和关闭功能。
    移除最大化按钮以强制窗口固定大小。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # 不再需要 is_maximized 和 old_pos，因为窗口大小固定，没有最大化/还原功能
        self.old_pos = QPoint()

        # 设置标题栏的背景和高度
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #c4c4c4;")

        # 创建布局和控件
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        # 窗口图标
        self.window_icon_label = QLabel()
        self.window_icon_label.setFixedSize(18, 18)
        self.window_icon_label.setPixmap(QIcon("icon.ico").pixmap(18, 18))
        layout.addWidget(self.window_icon_label)

        # 窗口标题
        self.window_title_label = QLabel("LOL友好交流器 F2发送")
        self.window_title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.window_title_label)

        # 弹性空间，将按钮推向右侧
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # GitHub 按钮
        self.github_button = QPushButton()
        self.github_button.setFixedSize(QSize(25, 25))
        self.github_button.setIcon(QIcon("github_icon.ico"))
        self.github_button.setToolTip("访问我的GitHub")
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
        self.github_button.clicked.connect(self.open_github_link)
        layout.addWidget(self.github_button)

        # 最小化按钮
        self.minimize_button = QPushButton("-")
        self.minimize_button.setFixedSize(QSize(30, 25))
        self.minimize_button.setStyleSheet("""
            QPushButton {
                border: 0px;
                border-radius: 0;
                background-color: transparent;
                font-weight: bold;
                font-size: 16px;
                color: #555;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
        """)
        self.minimize_button.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.minimize_button)

        # 关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(QSize(30, 25))
        self.close_button.setStyleSheet("""
            QPushButton {
                border: 0px;
                border-radius: 0;
                background-color: transparent;
                font-weight: bold;
                font-size: 16px;
                color: #555;
            }
            QPushButton:hover {
                background-color: #FF6666;
            }
        """)
        self.close_button.clicked.connect(self.parent.close)
        layout.addWidget(self.close_button)

    def mousePressEvent(self, event):
        """
        处理鼠标按下事件，用于记录窗口拖动的起始位置。
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        处理鼠标移动事件，用于实现窗口拖动功能。
        """
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.parent.move(self.parent.x() + delta.x(), self.parent.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
            event.accept()

    def open_github_link(self):
        """
        槽函数：打开指定的GitHub链接。
        """
        import webbrowser
        github_url = "https://github.com/rhj-flash/LOL_Chat_Tool"
        try:
            webbrowser.open(github_url)
            self.parent.log_signal.emit(f"已打开GitHub链接: {github_url}")
        except Exception as e:
            self.parent.log_signal.emit(f"无法打开GitHub链接: {str(e)}")