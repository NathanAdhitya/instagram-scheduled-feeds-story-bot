import schedule
import time
import os


def job():
    os.system("python ./cron.py")


schedule.every(5).minutes.do(job)

job()
while True:
    schedule.run_pending()
    time.sleep(1)
