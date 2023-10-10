import json
import os
import re
from contextlib import asynccontextmanager
from typing import Dict, Union

import yaml
from cytoolz import memoize
from web3 import Web3, HTTPProvider
from web3.contract.base_contract import BaseContractEvent

from quirk.events import EventType
from quirk.log import LOGGER
from quirk.networks import NETWORKS
import os
import yaml

from dotenv import load_dotenv

VARIABLE_PATTERN = r"{{\s*(\w+)\s*}}"


@asynccontextmanager
async def async_lock(lock):
    await lock.acquire()
    try:
        yield
    finally:
        lock.release()


def load_config(file_path) -> Dict:
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def get_infura_url(chain_id, infura_api_key: str) -> str:
    name = NETWORKS[chain_id]
    return f'https://{name}.infura.io/v3/{infura_api_key}'


def _load_web3_event_types(
        config: Dict,
        providers: Dict[int, HTTPProvider]
) -> Dict[str, BaseContractEvent]:
    events = {}
    for event in config['publishers']:
        contract_address = event['address']
        event_names = event['events']
        chain_id = event['chain_id']
        abi_filepath = event['abi_file']
        description = event['description']

        event_abi = _read_abi(abi_filepath)
        w3 = Web3(providers[chain_id])
        for event_name in event_names:
            contract = w3.eth.contract(address=contract_address, abi=event_abi)
            event_type = EventType(
                w3_type=contract.events[event_name](),
                description=description
            )

            events[event_name] = event_type
    return events


@memoize
def _read_abi(filepath):
    with open(filepath, "r") as f:
        return json.loads(f.read())


def humanize_event(event_instance):
    message = (
        f"Event: {event_instance.event_type}",
        f" | Block Number: {event_instance.block_number}",
        f" | Log Index: {event_instance.log_index}",
        f" | Transaction Index: {event_instance.tx_index}",
        f" | Transaction Hash: {event_instance.tx_hash.hex()}",
        f" | Contract Address: {event_instance.contract_address}",
        f" | Block Hash: {event_instance.block_hash.hex()}",
        f" | From: {event_instance.from_address}",
        f" | To: {event_instance.to_address}",
        f" | Value: {Web3.from_wei(event_instance.value, 'ether')}",
    )
    return "\n".join(message)


def log_event(event_instance):
    LOGGER.debug(humanize_event(event_instance))
