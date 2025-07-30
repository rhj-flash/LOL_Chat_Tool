
# 获取鼠标点击坐标的工具脚本
import pyautogui
import mouse
import time
import logging


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    return logging.getLogger(__name__)


def get_mouse_position():
    """监听鼠标左键点击，获取并记录屏幕坐标"""
    logger = setup_logging()
    logger.info("请点击聊天框区域获取坐标，按 Ctrl+C 退出")

    try:
        while True:
            # 等待鼠标左键点击
            mouse.wait(button='left', target_types=('down'))
            x, y = pyautogui.position()
            logger.info(f"鼠标点击坐标：({x}, {y})")
            time.sleep(0.5)  # 防止重复记录
    except KeyboardInterrupt:
        logger.info("退出坐标获取")


if __name__ == "__main__":
    # 安装 mouse 库：pip install mouse
    get_mouse_position()
