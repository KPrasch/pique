import datetime
from typing import Dict, Set

from eth_utils import keccak
from hexbytes import HexBytes
from web3 import Web3, HTTPProvider
from web3.datastructures import AttributeDict

from quirkbot.embeds import create_event_embed
from quirkbot.log import LOGGER
from quirkbot.utils import _read_abi


class EventType:
    def __init__(self, w3_type, description: str):
        self._type = w3_type
        self.description = description

    def get_logs(self, *args, **kwargs):
        return self._type.get_logs(*args, **kwargs)

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


class Event:
    def __init__(
        self,
        event_type: str,
        from_address: str,
        to_address: str,
        value: int,
        log_index: int,
        tx_index: int,
        tx_hash: HexBytes,
        contract_address: str,
        block_hash: HexBytes,
        block_number: int,
    ):
        self.event_type = event_type
        self.from_address = from_address
        self.to_address = to_address
        self.value = value
        self.log_index = log_index
        self.tx_index = tx_index
        self.tx_hash = tx_hash
        self.contract_address = contract_address
        self.block_hash = block_hash
        self.block_number = block_number
        self.timestamp = datetime.datetime.now()

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
    def from_attr_dict(cls, attr_dict: AttributeDict) -> "Event":
        args = attr_dict["args"]
        return cls(
            event_type=attr_dict["event"],
            from_address=args["from"],
            to_address=args["to"],
            value=args["value"],
            log_index=attr_dict["logIndex"],
            tx_index=attr_dict["transactionIndex"],
            tx_hash=attr_dict["transactionHash"],
            contract_address=attr_dict["address"],
            block_hash=attr_dict["blockHash"],
            block_number=attr_dict["blockNumber"],
        )


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


def _load_web3_event_types(
    config: Dict, providers: Dict[int, HTTPProvider]
) -> Set[EventType]:
    events = set()
    for event in config["publishers"]:
        contract_address = event["address"]
        event_names = event["events"]
        chain_id = event["chain_id"]
        abi_filepath = event["abi_file"]
        description = event["description"]

        event_abi = _read_abi(abi_filepath)
        w3 = Web3(providers[chain_id])
        for event_name in event_names:
            contract = w3.eth.contract(address=contract_address, abi=event_abi)
            event_type = EventType(
                w3_type=contract.events[event_name](),
                description=description
            )

            events.add(event_type)
    return events


async def send_event_message(subscriber, event):
    LOGGER.info(f"Sending event #{event.id[:8]} to channel #{subscriber.channel_id}")
    embed = create_event_embed(event)
    await subscriber.channel.send(embed=embed)
