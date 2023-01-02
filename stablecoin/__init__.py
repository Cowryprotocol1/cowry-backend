import pymysql
from .celery import app as celery_app
import os
from decouple import config
os.environ["REDIS_TLS_URL"] = config("REDIS_TLS_URL")

pymysql.install_as_MySQLdb()

__all__ = ('celery_app',)
