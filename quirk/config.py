from quirk.utils import load_yml
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Union


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


def load_config(file_path: Path) -> Dict:
    load_dotenv(file_path.parent / ".env")
    env_vars = {key: os.environ.get(key, "") for key in os.environ}
    yaml_content = load_yml(file_path)
    replace_placeholders(yaml_content, env_vars)
    set_env_vars(yaml_content)
    return yaml_content
