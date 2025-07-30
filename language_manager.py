import os


class LanguageManager:
    def __init__(self, file_path):
        """初始化语言管理器，加载语言库文件

        Args:
            file_path (str): 语言库TXT文件的路径
        """
        self.file_path = file_path
        self.messages = {}
        self.load_language_library()
        print(f"语言库初始化完成，加载了 {len(self.messages)} 条消息")

    def load_language_library(self):
        """从TXT文件中加载语言库"""
        # 检查文件是否存在
        if not os.path.exists(self.file_path):
            print(f"错误：文件 {self.file_path} 不存在，请确保文件已创建并位于正确路径")
            print(f"当前工作目录：{os.getcwd()}")
            return

        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    # 跳过注释行和空行
                    if line.startswith('#') or not line.strip():
                        continue
                    # 解析编号和消息内容
                    parts = line.strip().split('|')
                    if len(parts) == 2:
                        message_id, message_content = parts
                        self.messages[message_id] = message_content
                    else:
                        print(f"警告：无效的行格式 - {line.strip()}")
        except Exception as e:
            print(f"加载语言库时发生错误：{str(e)}")

    def get_message(self, message_id):
        """根据编号获取消息内容

        Args:
            message_id (str): 消息编号

        Returns:
            str: 对应的消息内容，如果不存在返回None
        """
        message = self.messages.get(message_id)
        if message is None:
            print(f"警告：消息编号 {message_id} 不存在")
        return message

    def get_all_messages(self):
        """获取所有消息内容

        Returns:
            dict: 包含所有消息的字典
        """
        return self.messages


if __name__ == "__main__":
    # 测试语言管理器
    manager = LanguageManager("language_library.txt")
    print("所有消息：", manager.get_all_messages())
    print("测试获取消息 1：", manager.get_message("1"))
    print("测试获取消息 3：", manager.get_message("3"))