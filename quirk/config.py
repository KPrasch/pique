import os
import re
from typing import Dict, Union

import yaml
from dotenv import load_dotenv

VARIABLE_PATTERN = r"{{\s*(\w+)\s*}}"


def replace_placeholders(yaml_dict):
    for key, value in yaml_dict.items():
        if isinstance(value, dict):
            replace_placeholders(value)
        elif isinstance(value, str):
            # Search for all placeholders and replace them with actual env vars
            for match in re.findall(VARIABLE_PATTERN, value):
                env_value = os.environ.get(match, "")
                value = value.replace(f"{{{{ {match} }}}}", env_value)
            yaml_dict[key] = value


def load_config(file_path: str) -> Dict:
    load_dotenv()

    with open(file_path, "r") as f:
        yaml_content = yaml.safe_load(f)

    replace_placeholders(yaml_content)

    def set_env_vars(data: Union[Dict, list], prefix: str = ""):
        if isinstance(data, dict):
            for key, value in data.items():
                new_prefix = f"{prefix}{key}_" if prefix else f"{key}_"
                set_env_vars(value, new_prefix)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_prefix = f"{prefix}{i}_"
                set_env_vars(item, new_prefix)
        else:
            env_key = prefix.rstrip("_").upper()
            os.environ[env_key] = str(data)

    set_env_vars(yaml_content)

    return yaml_content
