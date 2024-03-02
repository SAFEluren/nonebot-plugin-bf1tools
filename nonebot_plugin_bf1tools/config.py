from nonebot import require
from pydantic import BaseModel

require('nonebot_plugin_localstore')
import nonebot_plugin_localstore as store

data_dir = store.get_data_dir(__package__)
databases = f'{data_dir}/keywords.db'


class Config(BaseModel):
    api_url: str = "http://127.0.0.1:10086/"
    plugin_enabled: bool = True
