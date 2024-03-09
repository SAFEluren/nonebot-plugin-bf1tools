import re

import httpx
from nonebot import require
require('nonebot_plugin_localstore')
import nonebot_plugin_localstore as store

data_dir = store.get_data_dir(__package__)
databases = f"{data_dir}/databases.db"


