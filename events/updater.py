from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from .tasks import transaction_list



def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(transaction_list, 'interval', minutes=5)
    scheduler.start()