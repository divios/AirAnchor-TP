
import logging
import hashlib

import cbor
import requests

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError

from sawtooth_signing.secp256k1 import Secp256k1PrivateKey, Secp256k1PublicKey
from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing import ParseError

from processor.protos import *
from processor.data import MongoRepo

LOGGER = logging.getLogger(__name__)


FAMILY_NAME = 'AirAnchor'
FAMILY_VERSION = "1.0"

LOCATION_KEY_ADDRESS_PREFIX = hashlib.sha512(
    FAMILY_NAME.encode('utf-8')).hexdigest()[0:6]

CONTEXT = create_context('secp256k1')

def _sha512(data):
    return hashlib.sha512(data).hexdigest()

def make_location_key_address(key, hash):
    return LOCATION_KEY_ADDRESS_PREFIX + key[:6] + hash[-58:]

def get_pub_key_wrapper(pub_key: str):
    try:
        Secp256k1PublicKey.from_hex(pub_key)
    except Exception:
        raise InvalidTransaction("Invalid public key")

def get_ca_pub(pub_key):    
    with open(pub_key, "r") as f:
        key_hex = f.read().strip()

    return Secp256k1PublicKey.from_hex(key_hex)
    

class AirAnchorTransactionHandler(TransactionHandler):
    
    def __init__(self, ca_pub, mongo_repo: MongoRepo):
        self._ca_pub = get_ca_pub(ca_pub)
        self._mongo_repo = mongo_repo
    
    # Disable invalid-overridden-method. The sawtooth-sdk expects these to be
    # properties.
    # pylint: disable=invalid-overridden-method
    @property
    def family_name(self):
        return FAMILY_NAME

    @property
    def family_versions(self):
        return [FAMILY_VERSION]

    @property
    def namespaces(self):
        return [LOCATION_KEY_ADDRESS_PREFIX]

    def apply(self, transaction, context):
        key, hash, data = self._unpack_transaction(transaction)
        
        address = make_location_key_address(key, hash)
                
        state = _get_state_data(address, context)
        
        updated_state = _do_logic(key, hash, data, state)
        
        context.add_event(
            FAMILY_NAME + "/create", [
                ['key', key],
                ['hash', hash]
        ])
               
        _set_state_data(address, updated_state, context)
        
        
    def _unpack_transaction(self, transaction):
        payload = _decode_transaction(transaction)
         
        _validate_certificate(payload, self._ca_pub)
            
        return payload.sender_public_key, payload.hash(), payload.data
    
    
def _decode_transaction(transaction) -> TransactionPayload:
    try:
        return TransactionPayload.deserialize(transaction.payload)
    except Exception as e:
        
        raise InvalidTransaction("Invalid payload")
    
def _validate_certificate(payload: TransactionPayload, ca_pub: Secp256k1PublicKey):    
    certificate_request = payload.certificate_request
        
    if not CONTEXT.verify(payload.certificate_authority_signature, certificate_request.serialize(), ca_pub):
        raise InvalidTransaction('Invalid certificate signature')
        
def _get_state_data(address, context):
    state_entries = context.get_state([address])

    try:
        return cbor.loads(state_entries[0].data)
    except IndexError:
        return {}
    except Exception as e:
        raise InternalError('Failed to load state data') from e
    
    
def _do_logic(key, hash, data, state):
    msg = 'Adding location for key {k} with hash {h} and data{d}'.format(k=key, h=hash, d=data)
    LOGGER.debug(msg)
        
    updated = dict(state.items())
    updated[hash] = data
    
    return updated


def _set_state_data(address, state, context):
    encoded = cbor.dumps(state)

    addresses = context.set_state({address: encoded})

    if not addresses:
        raise InternalError('State error')
