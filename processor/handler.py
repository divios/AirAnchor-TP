
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


LOGGER = logging.getLogger(__name__)


FAMILY_NAME = 'AirAnchor'
FAMILY_VERSION = "1.0"

LOCATION_KEY_ADDRESS_PREFIX = hashlib.sha512(
    FAMILY_NAME.encode('utf-8')).hexdigest()[0:6]

def make_location_key_address(key, hash):
    return LOCATION_KEY_ADDRESS_PREFIX + key[:6] + hash[-58:]


def get_ca_pub(pub_key):    
    with open(pub_key, "r") as f:
        key_hex = f.read()

    return Secp256k1PublicKey.from_hex(key_hex)
    

class AirAnchorTransactionHandler(TransactionHandler):
    
    def __init__(self, ca_pub):
        self._ca_pub = get_ca_pub(ca_pub)
    
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
        
        _set_state_data(address, updated_state, context)
        
        
    def _unpack_transaction(self, transaction):
        key, hash, data, csr, csr_firm = _decode_transaction(transaction)
        
        # _validate_key(key)      # Should be already validated
        _validate_firm(self._ca_pub, csr, csr_firm)
        _validate_data(data)
            
        return key, hash, data
    
    
def _decode_transaction(transaction):
    key = transaction.header.signer_public_key
    hash = transaction.header.payload_sha512
    
    try:
        content = cbor.loads(transaction.payload)
    except Exception as e:
        raise InvalidTransaction('Invalid payload serialization') from e
    
    try:
        csr = content['csr']
    except AttributeError:
        raise InvalidTransaction('csr is required') from AttributeError
    
    try:
        csr_firm = content['csr_firm']
    except AttributeError:
        raise InvalidTransaction('crs_firm is required') from AttributeError
    
    try:
        content['nonce']
    except AttributeError:
        raise InvalidTransaction('nonce is required') from AttributeError

    try:
        data = content['data']
    except AttributeError:
        raise InvalidTransaction('data is required') from AttributeError
    
    return key, hash, data, csr, csr_firm


def _validate_key(key):
    try:
        Secp256k1PublicKey.from_hex(key)
        
    except Exception as e:
        raise InvalidTransaction('Invalid public key received in transaction') from e
        

def _validate_firm(pub, csr, csr_firm):              
    context = create_context('secp256k1')
    
    if not context.verify(csr_firm, cbor.dumps(csr), pub):
        raise InvalidTransaction('csr firm is not valid')
    
    
def _validate_data(data):
    if not isinstance(data, str):
        raise InvalidTransaction('firm must be an string')

        
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
    
    res = requests.get("http://192.168.1.169:8086")
    LOGGER.debug(res.content)
    
    updated = dict(state.items())
    updated[hash] = data

    return updated


def _set_state_data(address, state, context):
    encoded = cbor.dumps(state)

    addresses = context.set_state({address: encoded})

    if not addresses:
        raise InternalError('State error')