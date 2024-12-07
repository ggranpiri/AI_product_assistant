from datetime import datetime


def get_date() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
