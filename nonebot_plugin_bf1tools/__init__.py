import nonebot
from nonebot import get_plugin_config
from nonebot import require
from nonebot.adapters.onebot.v11 import Adapter
from nonebot.plugin import PluginMetadata

require('nonebot_plugin_localstore')
import nonebot_plugin_localstore as store
from nonebot.adapters.onebot.v11 import Adapter

from .commands import cmd_score,addKeyword,removeKeyword,listKeyword,shou2game

# from .chatmessage_socket import receiveChatMessageSocket
from .config import Config

__plugin_meta__ = PluginMetadata(
    name='战地1-群聊工具',
    description='Onebot 战地1 群聊工具插件',
    usage='''
    score 
    
    ''',

    type='application',
    # 发布必填，当前有效类型有：`library`（为其他插件编写提供功能），`application`（向机器人用户提供功能）。

    homepage='https://github.com/SAFEluren/nonebot-plugin-bf1tools',
    # 发布必填。

    config=Config,
    # 插件配置项类，如无需配置可不填写。

    supported_adapters={'~onebot.v11'},
    # 支持的适配器集合，其中 `~` 在此处代表前缀 `nonebot.adapters.`，其余适配器亦按此格式填写。
    # 若插件可以保证兼容所有适配器（即仅使用基本适配器功能）可不填写，否则应该列出插件支持的适配器。
)

plugin_config = get_plugin_config(Config)
data_dir = store.get_data_dir('bf1tools')


async def is_enable() -> bool:
    return plugin_config.marne_plugin_enabled


all = {
    "shou2game", "cmd_score", "addKeyword", "removeKeyword", "listKeyword"
}
