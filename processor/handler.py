
import logging
import hashlib

import cbor


from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError


LOGGER = logging.getLogger(__name__)


FAMILY_NAME = 'locationKey'

LOCATION_KEY_ADDRESS_PREFIX = hashlib.sha512(
    FAMILY_NAME.encode('utf-8')).hexdigest()[0:6]


def make_location_key_address(name):
    return LOCATION_KEY_ADDRESS_PREFIX + hashlib.sha512(
        name.encode('utf-8')).hexdigest()[-64:]


class LocationKeyTransactionHandler(TransactionHandler):
    # Disable invalid-overridden-method. The sawtooth-sdk expects these to be
    # properties.
    # pylint: disable=invalid-overridden-method
    @property
    def family_name(self):
        return FAMILY_NAME

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def namespaces(self):
        return [LOCATION_KEY_ADDRESS_PREFIX]

    def apply(self, transaction, context):
        key, hash, data = _unpack_transaction(transaction)
                
        state = _get_state_data(key, context)
        
        updated_state = _do_logic(key, hash, data, state)
        
        _set_state_data(key, updated_state, context)
        
        
def _unpack_transaction(transaction):
    key, hash, data = _decode_transaction(transaction)
    
    _validate_key(key)
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
        data = content['data']
    except AttributeError:
        raise InvalidTransaction('data is required') from AttributeError

    return key, data


def _validate_key(key):
    if not isinstance(key, str):
        raise InvalidTransaction('key must be an string')


def _validate_firm(firm):               # Firm is already validated by the validator
    if not isinstance(firm, str):
        raise InvalidTransaction('firm must be an string')
    
    
def _validate_data(data):
    if not isinstance(data, str):
        raise InvalidTransaction('firm must be an string')

        
def _get_state_data(name, context):
    address = make_location_key_address(name)

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


def _set_state_data(name, state, context):
    address = make_location_key_address(name)

    encoded = cbor.dumps(state)

    addresses = context.set_state({address: encoded})

    if not addresses:
        raise InternalError('State error')