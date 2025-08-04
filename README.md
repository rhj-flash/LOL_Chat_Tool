# LOL友好交流器
## EXE文件：[https://github.com/rhj-flash/LOL_Chat_Tool/blob/master/LOL%E5%8F%8B%E5%A5%BD%E4%BA%A4%E6%B5%81%E5%99%A8.exe]

一个基于Python和PyQt6的桌面工具，旨在帮助玩家在《英雄联盟》对局中快速发送预设的友好（或“骚话”）聊天信息。该工具通过模拟键盘输入，支持在游戏内外（大厅和对局中）一键发送消息，减少打字时间，提升游戏体验。

## 特性

- **一键发送：** 通过快捷键（默认为`F2`）快速发送预设消息，F12切换全局聊天。
- **自定义消息：** 支持用户通过配置文件 `messages.json` 自定义、添加、编辑或删除消息。
- **窗口识别：** 自动识别《英雄联盟》客户端，并在对局和大厅两种状态下都能正常工作。
- **跨平台兼容：** 主要为 Windows 系统设计，利用 `win32gui` 和 `ctypes` 等库实现底层输入模拟。
- **用户友好的界面：** 基于 `PyQt6` 构建的图形界面，直观易用，支持自定义标题栏和窗口拖动。

## 演示

### 主界面截图1

![主界面截图](https://github.com/rhj-flash/LOL_Chat_Tool/blob/master/example_photo/3.gif)


### 主界面截图2

![主界面截图](https://github.com/rhj-flash/LOL_Chat_Tool/blob/master/example_photo/2.jpg)

### 游戏内使用演示

![游戏内使用演示](https://github.com/rhj-flash/LOL_Chat_Tool/blob/master/example_photo/1.jpg)






