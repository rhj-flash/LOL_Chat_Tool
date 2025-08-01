# config_manager.py
# 配置管理模块：负责消息的永久保存和删除，使用 JSON 文件存储

import json
import os
import logging


class ConfigManager:
    """
    负责管理消息配置的类，包括加载、保存、添加、删除和编辑消息。
    消息以多行字符串列表的形式存储在 messages.json 文件中。
    """

    def __init__(self, config_file="messages.json"):
        """
        初始化 ConfigManager，设置配置文件路径并加载消息。
        :param config_file: 消息配置文件名。
        """
        self.config_file = config_file
        self.messages = self.load_messages()

    def load_messages(self):
        """
        从 JSON 文件加载消息列表。若文件不存在或加载失败，则返回空列表。
        :return: 消息列表，每个消息本身是字符串列表。
        """
        if not os.path.exists(self.config_file):
            logging.info("消息配置文件不存在，创建新的空配置文件。")
            self.save_messages([])
            return []
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_messages = json.load(f)
                # 检查加载的数据格式，确保是列表的列表
                if isinstance(loaded_messages, list) and all(isinstance(msg, list) for msg in loaded_messages):
                    logging.info("成功加载消息。")
                    return loaded_messages
                else:
                    logging.warning("配置文件格式不正确，将返回空列表。")
                    self.save_messages([])
                    return []
        except Exception as e:
            logging.error(f"加载消息失败: {str(e)}。将返回空列表。")
            self.save_messages([])
            return []

    def save_messages(self, messages):
        """
        将消息列表保存到 JSON 文件。
        :param messages: 要保存的消息列表。
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                # 使用 indent=4 确保 JSON 格式化输出，实现换行
                json.dump(messages, f, ensure_ascii=False, indent=4)
            logging.info("消息已成功保存到文件。")
        except Exception as e:
            logging.error(f"保存消息失败: {str(e)}")

    def add_message(self, new_message_str):
        """
        添加新消息到消息列表。
        本次修改：确保返回一个元组 (bool, list)。
        :param new_message_str: 用户输入的可能包含多行的消息字符串。
        :return: 如果添加成功，返回 (True, 消息行列表)；否则返回 (False, None)。
        """
        # 1. 检查输入是否为空或仅包含空格
        if not new_message_str or not new_message_str.strip():
            logging.warning("尝试添加空消息，操作取消。")
            return False, None

        # 2. 将多行字符串分割成一个列表，并去除每行首尾的空白
        new_message_lines = [line.strip() for line in new_message_str.split('\n')]
        # 3. 过滤掉分割后的空行，确保只添加有效内容
        new_message_lines = [line for line in new_message_lines if line]

        # 4. 再次检查分割后消息列表是否为空
        if not new_message_lines:
            logging.warning("分割后消息列表为空，操作取消。")
            return False, None

        # 5. 检查是否消息组已存在
        if new_message_lines in self.messages:
            logging.warning("消息已存在，添加失败。")
            return False, None

        self.messages.append(new_message_lines)
        self.save_messages(self.messages)
        logging.info(f"成功添加消息组: {new_message_lines}")
        return True, new_message_lines

    def update_message(self, index, new_message_str):
        """
        更新指定索引处的消息。
        :param index: 要更新的消息的索引。
        :param new_message_str: 新的消息字符串，可包含换行符。
        :return: 如果更新成功，返回 True；否则返回 False。
        """
        if not (0 <= index < len(self.messages)):
            logging.warning("索引超出消息列表范围，更新失败。")
            return False

        if not new_message_str or not new_message_str.strip():
            logging.warning("新消息为空，更新失败。")
            return False

        new_message_lines = [line.strip() for line in new_message_str.split('\n')]
        new_message_lines = [line for line in new_message_lines if line]

        if not new_message_lines:
            logging.warning("分割后新消息列表为空，更新失败。")
            return False

        self.messages[index] = new_message_lines
        self.save_messages(self.messages)
        logging.info(f"已更新索引 {index} 处的消息为: {new_message_lines}")
        return True

    def delete_message(self, message_list):
        """
        删除指定消息并保存。
        :param message_list: 要删除的消息（字符串列表）。
        :return: 如果删除成功则返回 True，否则返回 False。
        """
        if message_list in self.messages:
            self.messages.remove(message_list)
            self.save_messages(self.messages)
            logging.info(f"已删除消息: {message_list}")
            return True
        logging.warning("消息不存在，删除失败。")
        return False

    def get_messages(self):
        """
        返回当前消息列表。
        :return: 当前消息列表。
        """
        return self.messages