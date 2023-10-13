import json
from contextlib import asynccontextmanager

from cytoolz import memoize

from pique.constants.networks import NETWORKS


@memoize
def _read_file(path):
    with open(path, "r") as f:
        config_str = f.read()
    return config_str


@memoize
def _read_abi(filepath):
    with open(filepath, "r") as f:
        return json.loads(f.read())


@memoize
def get_infura_url(chain_id, infura_api_key: str) -> str:
    name = NETWORKS[chain_id]["name"]
    return f"https://{name}.infura.io/v3/{infura_api_key}"


@asynccontextmanager
async def async_lock(lock):
    await lock.acquire()
    try:
        yield
    finally:
        lock.release()


# Function to decode event input arguments
def decode_event_input(event_signature, log_data, contract_abi, contract):
    event_abi = None
    for abi in contract_abi:
        if abi["type"] == "event" and abi["name"] == event_signature:
            event_abi = abi
            break

    if event_abi is None:
        return None

    return contract.events[event_signature]().processLog({"data": log_data})


def bytes_to_hex(output, output_types):
    if isinstance(output, list):
        raise NotImplementedError("List output types not supported yet")
    elif isinstance(output, bytes):
        return output.hex()
    else:
        return output


def find_read_functions_without_input(abi):
    read_functions = {}
    for item in abi:
        if item['type'] == 'function':
            is_view = item.get('stateMutability') == 'view'
            is_pure = item.get('stateMutability') == 'pure'
            is_constant = item.get('constant', False)

            # Check if function is read-only
            if is_view or is_pure or is_constant:
                inputs = item['inputs']
                if len(inputs) == 0:
                    read_functions[item['name']] = item

    return read_functions
