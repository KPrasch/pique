import json
from contextlib import asynccontextmanager

import yaml
from cytoolz import memoize

from quirkbot.networks import NETWORKS


@memoize
def load_yml(file_path):
    with open(file_path, "r") as f:
        yaml_content = yaml.full_load(f)
    return yaml_content


@memoize
def _read_abi(filepath):
    with open(filepath, "r") as f:
        return json.loads(f.read())


@memoize
def get_infura_url(chain_id, infura_api_key: str) -> str:
    name = NETWORKS[chain_id]
    return f"https://{name}.infura.io/v3/{infura_api_key}"


@asynccontextmanager
async def async_lock(lock):
    await lock.acquire()
    try:
        yield
    finally:
        lock.release()

