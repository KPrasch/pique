import os
import re
from pathlib import Path
from typing import Dict, Union

from dotenv import load_dotenv

from quirkbot.utils import load_yml

VARIABLE_PATTERN = r"\{\{\w*(.*?)\w*\}\}"


def replace_placeholders(yaml_dict, env_vars):
    for key, value in yaml_dict.items():
        if isinstance(value, dict):
            replace_placeholders(value, env_vars)
        elif isinstance(value, str):
            # Search for all placeholders and replace them with actual env vars
            for match in re.findall(VARIABLE_PATTERN, value):
                match = match.strip()
                if match in env_vars:
                    env_value = env_vars[match]
                    value = value.replace(f"{{{{ {match} }}}}", env_value)
            yaml_dict[key] = value


def set_env_vars(data: Union[Dict, list], prefix: str = ""):
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}{key}_" if prefix else f"{key}_"
            set_env_vars(value, new_prefix)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_prefix = f"{prefix}{i}_"
            set_env_vars(item, new_prefix)


def load_config(path: Path) -> Dict:

    yaml_content = load_yml(path)
    dotenv_path = yaml_content.get("env", path.parent / ".env")
    load_dotenv(dotenv_path)

    env_vars = {key: os.environ.get(key, "") for key in os.environ}
    replace_placeholders(yaml_content, env_vars)
    set_env_vars(yaml_content)

    return yaml_content
