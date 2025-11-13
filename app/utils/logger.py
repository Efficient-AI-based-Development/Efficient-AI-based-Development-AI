# app/utils/logger.py

import os
import logging
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")


def setup_logger() -> None:
    """로깅 설정 초기화 (앱 전체에서 1회만 실행)"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # 기본 포맷
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 루트 로거 가져오기
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return  # 이미 설정된 경우 중복 방지

    root_logger.setLevel(logging.INFO)

    # 콘솔 출력
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    root_logger.addHandler(console_handler)

    # 파일 출력
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """모듈 이름 기준으로 로거 반환"""
    return logging.getLogger(name)


# 앱 시작 시 자동 설정
setup_logger()
