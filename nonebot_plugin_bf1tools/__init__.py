import json

import loguru
import nonebot
from nonebot import get_plugin_config
from nonebot import require
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Adapter
from .commands import scoreCommand, addKeyword, removeKeyword, listKeyword, shout2game, request_api, setInterval
from .config import Config
require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

driver = nonebot.get_driver()


@driver.on_bot_connect
async def _():
    onebot_adapter = nonebot.get_adapter(Adapter)
    bots = onebot_adapter.bots
    global bot
    bot = nonebot.get_bot()
    loguru.logger.debug("onebot has been loaded")


# 基于装饰器的方式

__plugin_meta__ = PluginMetadata(
    name='战地1-群聊工具',
    description='Onebot 战地1 群聊工具插件',
    usage='''''',

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


async def is_enable() -> bool:
    return plugin_config.marne_plugin_enabled


@scheduler.scheduled_job("cron", minute='*/2', id="job_0")
async def broadcast_score():
    loguru.logger.debug("broadcast score")
    parsed_data = json.loads(await request_api("Server/GetServerData"))
    respone_code = parsed_data['code']
    if respone_code == 500:
        loguru.logger.debug(f"{parsed_data['message']}")
        return
    game_time = parsed_data['data']['gameTime']
    game_mode = parsed_data['data']['gameMode']
    team1_name = parsed_data['data']['team1']['name']
    team1_score = parsed_data['data']['team1']['allScore']
    team2_name = parsed_data['data']['team2']['name']
    team2_score = parsed_data['data']['team2']['allScore']


    if game_mode == "Conquest0":
        pass
    else:
        return
    msg = Message([MessageSegment.text(f'{team1_name}: {team1_score} / {team2_name}: {team2_score}')])
    score_difference = None
    if team1_score > team2_score:
        score_difference = team1_score - team2_score
    elif team1_score < team2_score:
        score_difference = team2_score - team1_score
    else:
        score_difference = team1_score - team2_score
    msg.append(f"\n游戏时间: {game_time} 分差: {score_difference}")
    # await cmd_score.send(msg, reply_message=True)
    await bot.send_group_msg(group_id=719232286, message=msg)

    pass


all = {
    "shou2game", "cmd_score", "addKeyword", "removeKeyword", "listKeyword"
}
