import os
from pathlib import Path
from typing import NamedTuple, Set, Dict

import yaml
from dotenv import load_dotenv
from jinja2 import Template
from web3 import Web3

from pique._utils import _read_file, get_infura_url
from pique.constants import defaults
from pique.log import LOGGER
from pique.scanner.events import _load_config_events


def _load_partial_config(path: Path) -> dict:
    config_str = _read_file(path)
    # Partially load YAML to dictionary just to get the env path
    partial_config = yaml.safe_load(config_str)
    return partial_config


def load_config(path: Path) -> dict:
    # Step 0: Load partial config to find .env path
    partial_config = _load_partial_config(path)
    dotenv_rel_path = partial_config.get("env", defaults.DEFAULT_DOTENV_FILEPATH)
    dotenv_path = path.parent / dotenv_rel_path

    # Step 1: Load environment variables
    load_dotenv(dotenv_path)
    env_vars = {key: os.environ.get(key, "") for key in os.environ}

    # Step 2: Load entire file into a string
    config_str = _read_file(path)

    # Step 3: Use Jinja2 to render the template
    template = Template(config_str)
    rendered_config_str = template.render(**env_vars)

    # Step 4: Convert the string back to dictionary
    config_dict = yaml.safe_load(rendered_config_str)

    return config_dict


class PiqueConfig(NamedTuple):
    name: str
    infura_api_key: str
    chain_ids: Set[int]
    batch_size: int
    loop_interval: int
    start_block: int
    contracts: list
    discord: dict
    events: dict
    providers: Dict[int, Web3.HTTPProvider]

    @classmethod
    def from_dict(cls, config: Dict):
        try:
            pique_config = config["pique"]
            contracts_config = config["contracts"]
            contracts = contracts_config["track"]
            discord = config["discord"]
            name = pique_config["name"]
            infura_api_key = contracts_config["infura"]
            chain_ids = {contract["chain_id"] for contract in contracts}
        except KeyError as e:
            message = "missing required key in configuration file."
            LOGGER.error(message)
            raise e

        batch_size = contracts_config.get("batch_size", defaults.BATCH_SIZE)
        loop_interval = contracts_config.get("loop_interval", defaults.LOOP_INTERVAL)
        start_block = contracts_config.get("start_block", defaults.START_BLOCK)

        providers = {
            cid: Web3.HTTPProvider(get_infura_url(cid, infura_api_key))
            for cid in chain_ids
        }
        events = _load_config_events(contracts, providers=providers)

        return cls(
            name,
            infura_api_key,
            chain_ids,
            batch_size,
            loop_interval,
            start_block,
            contracts,
            discord,
            events,
            providers,
        )
