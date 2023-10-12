import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from jinja2 import Template

from pique import defaults
from pique._utils import _read_file


def _load_partial_config(path: Path) -> dict:
    config_str = _read_file(path)
    # Partially load YAML to dictionary just to get the env path
    partial_config = yaml.safe_load(config_str)
    return partial_config


def load_config(path: Path) -> dict:
    # Step 0: Load partial config to find .env path
    partial_config = _load_partial_config(path)
    dotenv_rel_path = partial_config.get('env', defaults.DEFAULT_DOTENV_FILEPATH)
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
