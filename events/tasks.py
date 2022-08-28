from datetime import datetime
import secrets
from time import time
from celery import shared_task
from Blockchains.Stellar.operations import get_horizon_server
from modelApp.models import PeriodicTaskRun
from django.utils import timezone
from decouple import config as env_config
from Api.utils import isTransaction_Valid

# pull last 200 records, check which ones are not there during our last task'


# @shared_task(bind=True)
def transaction_list(staking_address=env_config("STAKING_ADDRESS"), withdrawal_address=env_config("STABLECOIN_ISSUER")):
    test = PeriodicTaskRun.objects.latest("created_at")

    last_updated_time = test.created_at.strftime("%Y-%m-%d %H:%M:%S")
    print()
    print("===================================")
    new_time = timezone.now()
    PeriodicTaskRun.objects.update(created_at=new_time)
    try:
        horizon_server = get_horizon_server()
        transactions_ = horizon_server.transactions().for_account(staking_address).limit(200).call()
        # transactions_ = horizon_server.transactions().for_account(account).limit(200).call()
    except Exception as err:
        #notify admin
        print(err)
    else:
        for transaction in transactions_["_embedded"]["records"]:
            try:
                hash_ = transaction["hash"]
                tx_time = transaction["created_at"]
                tx_memo = transaction["memo"]
            except KeyError:
                #transaction does not have a memo
                pass
            except Exception as error:
                #notify admin
                pass
            splitted_date_time = tx_time.replace("T", " ")
            transaction_time = datetime.strptime(splitted_date_time.split("Z")[0], "%Y-%m-%d %H:%M:%S")
            if  transaction_time >= datetime.strptime(last_updated_time, "%Y-%m-%d %H:%M:%S"):
                print("forward one to celery")
                isTransaction_Valid.delay(transaction_hash=hash_, memo=tx_memo)
    print("===================================")
    
        

    
    # print(adc.created_at)
    # print(adc.created_at.strftime("%Y-%m-%d %H:%M:%S"))

