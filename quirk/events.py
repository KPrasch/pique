import datetime

from eth_utils import keccak
from hexbytes import HexBytes
from web3.datastructures import AttributeDict


class EventType:
    def __init__(self, w3_type, description: str):
        self.w3_type = w3_type
        self.description = description

    def __getattr__(self, item):
        if hasattr(self.w3_type, item):
            return getattr(self.w3_type, item)
        else:
            return getattr(self, item)


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
            block_number: int
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
            log_index_bytes = log_index.to_bytes(4, byteorder='big')
        else:
            log_index_bytes = log_index
        concatenated_data = tx_hash + log_index_bytes
        unique_id = keccak(concatenated_data)
        return unique_id.hex()

    @classmethod
    def from_attr_dict(cls, attr_dict: AttributeDict) -> 'Event':
        args = attr_dict['args']
        return cls(
            event_type=attr_dict['event'],
            from_address=args['from'],
            to_address=args['to'],
            value=args['value'],
            log_index=attr_dict['logIndex'],
            tx_index=attr_dict['transactionIndex'],
            tx_hash=attr_dict['transactionHash'],
            contract_address=attr_dict['address'],
            block_hash=attr_dict['blockHash'],
            block_number=attr_dict['blockNumber']
        )
