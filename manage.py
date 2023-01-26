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
    logging.warning("add merchant signin and signout with wallet connect")
    logging.warning("when you clear out db, dont forget to, create a default value for periodicTask")
    
    logging.critical("Handle fee for withdrawal from the protocol")

    logging.critical("You need to start redis-server")
    logging.critical("add returning multiple IFP for deposit more then an amount an IFP can process")
    logging.critical("connect celery with command'celery -A stablecoin worker -l INFO'")
    logging.info("add merchant specific off boarding from the protocol, this will handle reconcile the fee they have accumulated on their acct")
    logging.critical("complete api test for other apis")
    logging.critical("complete api test to include testing adding removing, etx transactions and IFPs")
    logging.critical("what happen when an existing IFP with transaction hash try to top and then call the listen endpoint with the old hash")
    logging.critical("restrict IFP from making deposits and withdrawals directly from their own acct")


    
    
    main()
