# This has to be run from a seperate terminal


from stellar_sdk import AiohttpClient, ServerAsync
import asyncio
import requests
from decouple import config
import logging
logging.basicConfig(level=logging.INFO,  format="%(levelname)s %(message)s")



staking_address = config(
    "STABLECOIN_ISSUER")
HORIZON_URL = config("HORIZON_URL")
# base_url = config("BASE_URL")
event_url = config("listener")


"""
Event listner listen for transactions on the staking address,
and when a payment transaction is received, it will send a POST request to the event_url
"""


async def payments():
    async with ServerAsync(HORIZON_URL, AiohttpClient()) as server:
        async for transactions in server.transactions().for_account(staking_address).stream():
            try:
                logging.info(transactions['hash'])
                logging.info(transactions['memo'])
                data = (
                    {"hash": transactions["hash"], "memo": transactions["memo"], "event_type": "user_withdrawals"})
                requests.post(event_url, data=data)
            except Exception as e:
                # Add a way to send notification for error to admin group
                logging.critical(e)
                continue


async def listen():
    await asyncio.gather(payments())


if __name__ == "__main__":
    logging.info("Event Listener Started.....")
    logging.info("listening for withdrawals.....")
    asyncio.run(listen())
