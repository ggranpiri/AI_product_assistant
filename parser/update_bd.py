from apscheduler.schedulers.blocking import BlockingScheduler
from config import UPDATE_BD_TIME
from parser.parse_bd import parse_product_from_vv


def auto_update_bd():
    scheduler = BlockingScheduler()

    # Планируем задачу
    scheduler.add_job(parse_product_from_vv, 'cron', hour=UPDATE_BD_TIME[0], minute=UPDATE_BD_TIME[1])
    scheduler.start()
