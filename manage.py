#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import logging
logging.basicConfig(level=logging.INFO,  format="%(levelname)s %(message)s")



def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stablecoin.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    logging.critical("Handle fee for withdrawal from the protocol")
    logging.critical("You need to start redis-server")
    logging.critical("connect celery with command'celery -A stablecoin worker -l INFO'")
    
    
    main()
