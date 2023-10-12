import asyncio
import datetime
from typing import Dict, List

from eth_utils import keccak
from hexbytes import HexBytes
from web3 import Web3, HTTPProvider
from web3.datastructures import AttributeDict

from pique.constants import defaults
from pique._utils import _read_abi
from pique.log import LOGGER


class Event:
    def __init__(
        self,
        contract_name: str,
        color: int,
        description: str,
        chain_id: int,
        event_type: str,
        log_index: int,
        tx_index: int,
        tx_hash: HexBytes,
        contract_address: str,
        block_hash: HexBytes,
        block_number: int,
        args: Dict = None,
    ):
        self.contract_name = contract_name
        self.color = color
        self.description = description
        self.chain_id = chain_id
        self.event_type = event_type
        self.log_index = log_index
        self.tx_index = tx_index
        self.tx_hash = tx_hash
        self.contract_address = contract_address
        self.block_hash = block_hash
        self.block_number = block_number
        self.timestamp = datetime.datetime.now()
        self.args = args or {}

    @property
    def id(self):
        """Returns a unique ID for this event."""
        tx_hash = self.tx_hash
        log_index = self.log_index
        if isinstance(log_index, int):
            log_index_bytes = log_index.to_bytes(4, byteorder="big")
        else:
            log_index_bytes = log_index
        concatenated_data = tx_hash + log_index_bytes
        unique_id = keccak(concatenated_data)
        return unique_id.hex()

    @classmethod
    def from_dict(cls, _dict: AttributeDict, *args, **kwargs) -> "Event":
        return cls(
            event_type=_dict["event"],
            log_index=_dict["logIndex"],
            tx_index=_dict["transactionIndex"],
            tx_hash=_dict["transactionHash"],
            contract_address=_dict["address"],
            block_hash=_dict["blockHash"],
            block_number=_dict["blockNumber"],
            args=_dict.get('args', {}),  # TODO: use custom arg parser
            *args, **kwargs
        )


class EventContainer:
    def __init__(
            self,
            w3_type,
            contract_name: str,
            description: str,
            color: int
    ):
        self._type = w3_type
        self.contract_name = contract_name
        self.description = description
        self.color = color

        self.latest_scanned_block = w3_type.w3.eth.block_number
        self.lock = asyncio.Lock()

    def get_logs(self, *args, **kwargs) -> List[Event]:
        event_data = self._type.get_logs(*args, **kwargs)
        events = []
        for data in event_data:
            event = Event.from_dict(
                data,
                description=self.description,
                chain_id=self.chain_id,
                color=self.color,
                contract_name=self.contract_name
            )
            events.append(event)
        return events

    @property
    def w3(self):
        return self._type.w3

    @property
    def name(self):
        return self._type.abi["name"]

    @property
    def abi(self):
        return self._type.abi

    @property
    def chain_id(self):
        return self.w3.eth.chain_id

    @property
    def address(self):
        return self._type.address


def humanize_event(event: Event):
    message = (
        f"Event: {event.event_type}",
        f" | Block Number: {event.block_number}",
        f" | Log Index: {event.log_index}",
        f" | Transaction Index: {event.tx_index}",
        f" | Transaction Hash: {event.tx_hash.hex()}",
        f" | Contract Address: {event.contract_address}",
        f" | Block Hash: {event.block_hash.hex()}",
    )
    return "\n".join(message)


def log_event(event_instance):
    LOGGER.debug(humanize_event(event_instance))


def _load_config_events(
    contracts, providers: Dict[int, HTTPProvider]
) -> List[EventContainer]:
    events = list()
    for contract in contracts:

        # Read contract data from config
        contract_address = contract["address"]
        contract_name = contract["name"]
        event_names = contract["events"]
        chain_id = contract["chain_id"]
        abi_filepath = contract["abi_file"]
        description = contract.get("description", "")
        color = contract.get("color", defaults.EMBED_COLOR)
        event_abi = _read_abi(abi_filepath)

        # Create web3 instance and event container
        w3 = Web3(providers[chain_id])
        for name in event_names:
            contract = w3.eth.contract(address=contract_address, abi=event_abi)
            event_container = EventContainer(
                w3_type=contract.events[name](),
                description=description,
                color=color,
                contract_name=contract_name,
            )

            events.append(event_container)
    return events