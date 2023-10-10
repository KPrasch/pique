import json
from contextlib import asynccontextmanager

from cytoolz import memoize

from quirk.networks import NETWORKS


@memoize
def get_infura_url(chain_id, infura_api_key: str) -> str:
    name = NETWORKS[chain_id]
    return f"https://{name}.infura.io/v3/{infura_api_key}"


@memoize
def _read_abi(filepath):
    with open(filepath, "r") as f:
        return json.loads(f.read())


@asynccontextmanager
async def async_lock(lock):
    await lock.acquire()
    try:
        yield
    finally:
        lock.release()
