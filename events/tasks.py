from datetime import datetime
from Blockchains.Stellar.operations import get_horizon_server, STABLECOIN_CODE, STABLECOIN_ISSUER
from modelApp.models import PeriodicTaskRun
from django.utils import timezone
from decouple import config as env_config
from Api.utils import isTransaction_Valid

# pull last 200 records, check which ones are not there during our last task'


# @shared_task(bind=True)
def transaction_list(staking_address=env_config("STAKING_ADDRESS"), withdrawal_address=env_config("STABLECOIN_ISSUER")):
    # try:
    test = PeriodicTaskRun.objects.latest("created_at")
    # except PeriodicTaskRun.DoesNotExist:
    #     print("this query has not been created yet")
    #     print("this should be created")
    #     #set the default value and try again when it the right time
    #     PeriodicTaskRun.objects.create(task_id=1000, task_name="default_value")
    # else:
    last_updated_time = test.created_at.strftime("%Y-%m-%d %H:%M:%S")
    print()
    print("===================================")
    new_time = timezone.now()
    PeriodicTaskRun.objects.update(created_at=new_time)
    horizon_server = get_horizon_server()
    try:
        staking_transaction = horizon_server.transactions().for_account(staking_address).limit(200).call()
        # withdrawal_transaction = horizon_server.transactions().for_account(withdrawal_address).limit(200).call()
    except Exception as err:
        #notify admin
        print(err)
    else:
        
        #handles MA that just staked with the protocol to start processing transactions
        for transaction in staking_transaction["_embedded"]["records"]:
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
            stake_transaction_time = datetime.strptime(splitted_date_time.split("Z")[0], "%Y-%m-%d %H:%M:%S")
            if  stake_transaction_time >= datetime.strptime(last_updated_time, "%Y-%m-%d %H:%M:%S"):
                print("forward one to celery")
                isTransaction_Valid.delay(transaction_hash=hash_, memo=tx_memo, event_transaction_type="merchant_staking")
    try:
        withdrawal_transaction = horizon_server.transactions().for_account(withdrawal_address).limit(200).call()
    except Exception as err:
        #notify admin
        print(err)
    else:
        #Handles MA that want to leave the protocol
        for transaction in withdrawal_transaction["_embedded"]["records"]:
            try:
                staked_tx_hash_ = transaction["hash"]
                staked_tx_time = transaction["created_at"]
                staked_tx_memo = transaction["memo"]
            except KeyError:
                #transaction does not have a memo
                pass
            except Exception as error:
                #notify admin
                pass
            stake_splitted_date_time = staked_tx_time.replace("T", " ")
            staked_transaction_time = datetime.strptime(stake_splitted_date_time.split("Z")[0], "%Y-%m-%d %H:%M:%S")
            if  staked_transaction_time >= datetime.strptime(last_updated_time, "%Y-%m-%d %H:%M:%S"):
                print("forward one to staked_transaction_time")
                isTransaction_Valid.delay(
                        transaction_hash=staked_tx_hash_,
                        memo=staked_tx_memo,
                        _address=STABLECOIN_ISSUER,
                        _asset_code=STABLECOIN_CODE,
                        _asset_issuer=STABLECOIN_ISSUER,
                        event_transaction_type="user_withdrawals",
                    )
    print("===================================")
    
        

    
    # print(adc.created_at)
    # print(adc.created_at.strftime("%Y-%m-%d %H:%M:%S"))

