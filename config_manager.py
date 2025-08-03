# config_manager.py

import json
import os
import logging
from typing import List, Dict, Any


class ConfigManager:
    """
    配置管理器类，负责加载、保存和管理消息配置文件 (messages.json)。
    该类实现了对消息数据的增、删、改、查操作。
    """
    # 消息文件的文件名
    _MESSAGES_FILE = 'messages.json'
    # 默认的消息文件内容
    _DEFAULT_MESSAGES = [
        {
            "note": "友好大中指",
            "lines": [
                "兄弟，别骂了，我知道你很急，但你先别急"
            ]
        },
        {
            "note": "谢谢你",
            "lines": [
                "谢谢你，泰罗"
            ]
        }
    ]

    def __init__(self):
        """
        构造函数：初始化配置管理器。
        尝试加载消息文件，如果不存在或加载失败，则创建一个新的默认消息文件。
        """
        self.messages: List[Dict[str, Any]] = []
        self._load_messages()

    def _load_messages(self):
        """
        从文件中加载消息列表。
        如果文件不存在，则创建默认文件。
        如果文件存在但格式不正确，则记录错误并创建默认文件。
        """
        if not os.path.exists(self._MESSAGES_FILE):
            logging.info(f"消息文件 '{self._MESSAGES_FILE}' 不存在，正在创建默认文件。")
            self.messages = self._DEFAULT_MESSAGES
            self._save_messages()
            return

        try:
            with open(self._MESSAGES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    # 检查是否是新版格式（列表套字典）
                    if data and all(isinstance(item, dict) and 'note' in item and 'lines' in item for item in data):
                        self.messages = data
                        logging.info("成功加载新版格式的消息。")
                    else:
                        # 可能是旧版格式或其他格式，尝试转换
                        if data and isinstance(data[0], list):
                            logging.warning("检测到旧版消息文件格式，正在尝试转换为新版格式。")
                            self.messages = [{"note": f"消息组 {i + 1}", "lines": group} for i, group in enumerate(data)]
                            self._save_messages()  # 转换后立即保存
                        else:
                            raise ValueError("消息文件格式不正确，既不是新版也不是可识别的旧版。")
                else:
                    raise ValueError("消息文件不是列表格式。")
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            logging.error(f"加载消息文件失败: {e}。正在创建默认文件。")
            self.messages = self._DEFAULT_MESSAGES
            self._save_messages()

    def _save_messages(self):
        """
        将当前消息列表保存到文件中。
        """
        try:
            with open(self._MESSAGES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=4)
            logging.info(f"消息已成功保存到 '{self._MESSAGES_FILE}'。")
        except IOError as e:
            logging.error(f"保存消息文件失败: {e}")

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        获取当前加载的消息列表。
        """
        return self.messages

    def add_message(self, note: str, message_str: str) -> bool:
        """
        添加一条新消息到列表中。
        """
        if not note or not message_str:
            return False

        lines = [line.strip() for line in message_str.split('\n')]
        new_message = {
            "note": note,
            "lines": lines
        }
        self.messages.append(new_message)
        self._save_messages()
        return True

    def delete_message(self, index: int) -> bool:
        """
        删除指定索引的消息。
        """
        if 0 <= index < len(self.messages):
            del self.messages[index]
            self._save_messages()
            return True
        return False

    def update_message(self, index: int, new_note: str, new_message_str: str) -> bool:
        """
        更新指定索引的消息的备注和内容。
        :param index: 要更新的消息的索引。
        :param new_note: 新的消息备注。
        :param new_message_str: 新的消息内容（多行字符串）。
        :return: 如果更新成功返回 True，否则返回 False。
        """
        if not new_note or not new_message_str:
            logging.warning("更新消息失败：备注或消息内容为空。")
            return False

        if 0 <= index < len(self.messages):
            lines = [line.strip() for line in new_message_str.split('\n') if line.strip()]
            self.messages[index]['note'] = new_note
            self.messages[index]['lines'] = lines
            self._save_messages()
            logging.info(f"成功更新消息组 {index + 1} 的备注和内容。")
            return True
        else:
            logging.warning(f"更新消息失败：索引 {index} 超出范围。")
            return False