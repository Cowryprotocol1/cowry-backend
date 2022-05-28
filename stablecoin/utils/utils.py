from random import randint
import secrets
from stellar_sdk.keypair import Keypair



def uidGenerator(size=10):
    return ''.join(secrets.token_hex(size))

    
def createStellarAddress():
    keys = Keypair.random()
    return {"pubKey": keys.public_key, "privKey": keys.secret}

# to be used inside model before saving


def Id_generator():
    id = randint(1, 9999999999)
    return "200"+str(id)

