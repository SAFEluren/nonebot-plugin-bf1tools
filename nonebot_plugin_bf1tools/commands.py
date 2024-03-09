import asyncio
import json
import os
import re
import socket
import sqlite3

import httpx
import loguru
from nonebot import get_plugin_config
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent
from nonebot.internal.matcher import Matcher
from nonebot.params import CommandArg
from zhconv import convert
from nonebot import require

require('nonebot_plugin_localstore')
import nonebot_plugin_localstore as store
from .config import Config

require("nonebot_plugin_access_control_api")
from nonebot_plugin_access_control_api.service import create_plugin_service

plugin_service = create_plugin_service("nonebot_plugin_bf1tools")
group_admincmd = plugin_service.create_subservice("admincmd")
group_usercmd = plugin_service.create_subservice("usercmd")

SOCKET_IP = "127.0.0.1"
SOCKET_RECVMSG_PORT = 52001
SOCKET_SENDMSG_UDP_PORT = 51001

plugin_config = get_plugin_config(Config)
data_dir = store.get_data_dir("nonebot_plugin_bf1tools")
databases = f"{data_dir}/databases.db"

addKeyword = on_command('addkeyword', aliases={"添加关键字", "增加关键字"})
addKeyword_service = group_admincmd.create_subservice('addKeyword')

removeKeyword = on_command('removekeyword', aliases={"移除关键字", "删除关键字"})
removeKeyword_service = group_admincmd.create_subservice('removeKeyword')

listKeyword = on_command('listkeyword', aliases={"关键字列表", "列出关键字"})
listKeyword_service = group_admincmd.create_subservice('listKeyword')

setInterval = on_command('setinterval', aliases={"设置间隔", "修改间隔"})
setInterval_service = group_admincmd.create_subservice('setInterval')

scoreCommand = on_command('score', aliases={"比分", "分数", "point"})
score_service = group_usercmd.create_subservice('scoreCommand')

shout2game = on_command('sendmsg', aliases={"喊话", "shout"})
shout2game_service = group_admincmd.create_subservice('shou2game')


class BF1Tools:

    def __init__(self):
        self.conn = sqlite3.connect(databases)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    async def init(self):
        sql = """create table if not exists keywords(
            id integer primary key autoincrement,
            keywords text not null
        )
        """
        self.cursor.execute(sql)
        self.conn.commit()

    async def checkdb(self):
        try:
            # 查询表中的主键 id 和关键词
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keywords'")
            result = await self.cursor.fetchone()
            if result is None:
                # 如果表不存在，则执行初始化操作
                await self.init()
        except sqlite3.Error as e:
            # 如果发生异常，输出错误信息
            print("Error:", e)

    @staticmethod
    async def shouToGame(content):
        if isinstance(content, str):
            message = f"#Chat.Send#{content}".encode('utf-8')
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_socket:
                    send_socket.sendto(message, (SOCKET_IP, SOCKET_SENDMSG_UDP_PORT))
            except Exception as e:
                loguru.logger.error(e)
            return


async def request_api(api_path="Server/GetServerData"):
    api_url = plugin_config.api_url + api_path
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{api_url}')
            content = response.text
            return response.text

    except (httpx.HTTPStatusError, httpx.ConnectTimeout) as e:
        print(f'HTTP error occurred: {e}')


def is_pure_digit(message):
    pattern = r"^\d+$"
    return re.match(pattern, message)


async def init():
    conn = sqlite3.connect(databases)
    cursor = conn.cursor()
    sql = """create table if not exists keywords(
        id integer primary key autoincrement,
        keywords text not null
    )
    """
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()


async def checkdb():
    conn = sqlite3.connect(databases)
    try:
        # 创建一个游标对象
        cur = conn.cursor()

        # 查询表中的主键 id 和关键词
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keywords'")
        result = cur.fetchone()
        if result is None:
            # 如果表不存在，则执行初始化操作
            await init()
    except sqlite3.Error as e:
        # 如果发生异常，输出错误信息
        print("Error:", e)
    finally:
        # 关闭游标对象和数据库连接
        cur.close()
        conn.close()


@addKeyword.handle()
@addKeyword_service.patch_handler()
async def adkw(event: GroupMessageEvent, args: Message = CommandArg()):
    session = event.group_id
    message = args.extract_plain_text()
    await checkdb()
    # 连接到 SQLite 数据库
    try:
        conn = sqlite3.connect(databases)
        cur = conn.cursor()
        cur.execute("SELECT keywords FROM keywords WHERE keywords=?", (message,))
        result = cur.fetchone()
        loguru.logger.debug(result)
        if result is None:
            cur.execute("INSERT INTO keywords (keywords) VALUES (?)", (message,))
            conn.commit()
            await addKeyword.finish("执行成功", reply_message=True)
        else:
            await addKeyword.finish("已有该关键字", reply_message=True)

    except sqlite3.Error as e:
        print("Error:", e)
        return False
    cur.close()
    conn.close()


@removeKeyword.handle()
@removeKeyword_service.patch_handler()
async def rmkw(event: GroupMessageEvent, args: Message = CommandArg()):
    session = event.group_id
    keyword_id = args.extract_plain_text()
    if len(args) == 1 & keyword_id.isdigit():
        pass
    else:
        await removeKeyword.finish('格式错误，仅允许纯数字')
        return

    try:
        conn = sqlite3.connect(databases)
        cursor = conn.cursor()
        # 执行 SQL 删除操作
        cursor.execute("DELETE FROM keywords WHERE id=?", (keyword_id,))
        conn.commit()
        await removeKeyword.finish(f"已成功移除主键为 {keyword_id} 的键值对。", reply_message=True)
    except sqlite3.OperationalError as e:
        await removeKeyword.finish("删除失败，请查看日志", reply_message=True)
        raise e
    finally:
        # 关闭游标和数据库连接
        cursor.close()
        conn.close()


@listKeyword.handle()
@removeKeyword_service.patch_handler()
async def lskw(event: GroupMessageEvent):
    session = event.group_id
    msg = Message([MessageSegment.text(f"查询成功")])
    msg.append("\n--------------------")
    try:
        conn = sqlite3.connect(databases)
        cursor = conn.cursor()
        # 查询所有关键字和它们的主键
        cursor.execute("SELECT id, keywords FROM keywords")
        rows = cursor.fetchall()
        # 构建字典，将关键字和主键对应起来
        keywords_dict = {id: keyword for id, keyword in rows}
        items_view = keywords_dict.items()
        for key, value in items_view:
            msg.append(f"\n{key}: {value}")
        loguru.logger.debug(items_view)

        await listKeyword.finish(msg, reply_message=True)
    except sqlite3.Error as e:
        # 如果发生异常，输出错误信息
        print("Error:", e)
        return None

    cursor.close()
    conn.close()


@scoreCommand.handle()
@score_service.patch_handler()
async def _(event: GroupMessageEvent):
    session = event.group_id
    parsed_data = json.loads(await request_api("Server/GetServerData"))
    httpstatuscode = parsed_data['code']
    message = parsed_data['message']
    if httpstatuscode != 200:
        await scoreCommand.finish(f"请求错误，HTTP状态码:{httpstatuscode}\n{message}", reply_message=True)
        return
    gameId = parsed_data['data']['gameId']
    timestamp = parsed_data['timestamp']
    game_name = parsed_data['data']['name']
    game_time = parsed_data['data']['gameTime']
    game_mode = parsed_data['data']['gameMode']
    game_mode2 = parsed_data['data']['gameMode2']
    map_name = parsed_data['data']['mapName2']
    team1_name = parsed_data['data']['team1']['name']
    team1_score = parsed_data['data']['team1']['allScore']
    team1_maxscore = parsed_data['data']['team1']['maxScore']
    team2_name = parsed_data['data']['team2']['name']
    team2_score = parsed_data['data']['team2']['allScore']
    team2_maxscore = parsed_data['data']['team2']['maxScore']

    msg = Message([MessageSegment.text(f'查询成功')])
    msg.append(f"\n服务器名:{game_name}")
    msg.append(f"\nGameID: {gameId}")
    msg.append(f"\n--------------------")
    msg.append(f"\n游戏时间: {game_time}")
    msg.append(f"\n地图名称: {map_name} [{game_mode2}]")
    if game_mode == "Conquest0":
        msg.append(f"\n{team1_name}: {team1_score} / {team1_maxscore}")
        msg.append(f"\n{team2_name}: {team2_score} / {team2_maxscore}")
        score_difference, leading_team, trailing_team = [None] * 3
        if team1_score > team2_score:
            leading_team = team1_name
            trailing_team = team2_name
            score_difference = team1_score - team2_score
        elif team1_score < team2_score:
            leading_team = team2_name
            trailing_team = team1_name
            score_difference = team2_score - team1_score
        elif team1_score == team2_score:
            msg.append(f"\n分差: 0")
            msg.append(f"\n--------------------")
            msg.append(f"\n{timestamp}")
            await scoreCommand.send(msg, reply_message=True)
            return

        msg.append(f"\n分差: {score_difference}")
        msg.append(f"\n优势方: {leading_team}")
        msg.append(f"\n劣势方: {trailing_team}")
        msg.append(f"\n--------------------")
    msg.append(f"\n{timestamp}")
    await scoreCommand.send(msg, reply_message=True)


@shout2game.handle()
@shout2game_service.patch_handler()
async def _(matcher: Matcher, event: GroupMessageEvent, args: Message = CommandArg()):
    message = args.extract_plain_text()
    message_conv = convert(f"[来自Q群]:{message}", 'zh-tw')
    loguru.logger.debug(f"{message_conv}")
    sessionID = event.user_id
    loguru.logger.debug(f"message_conv's len:{len(message_conv)}")
    if len(message_conv) > 256:
        split_string = [message_conv[i:i + 256] for i in range(0, len(message_conv), 256)]
        loguru.logger.debug("大于256")
        await shout2game.send("内容大于256字节，将自动分段发送", reply_message=True)
        # 输出拆分后的字符串
        for string in split_string:
            await asyncio.sleep(0.3)
            await BF1Tools.shouToGame(string)
            loguru.logger.debug(string)
            loguru.logger.info(f"[{sessionID}]已尝试发送以下内容到服务器:{string}")
            await shout2game.send(f'已尝试发送以下消息到服务器:\n{string}')
    else:
        await BF1Tools.shouToGame(content=message_conv)
        loguru.logger.info(f"[{sessionID}]已尝试发送以下内容到服务器:{message_conv}")
        await shout2game.finish(f'已尝试发送以下消息到服务器:\n{message_conv}', reply_message=True)

# @setInterval.handle()
# async def _(event: GroupMessageEvent, args: Message = CommandArg(), toml=None):
#     session = event.group_id
#     message = args.extract_plain_text()
#     if is_pure_digit(message):
#         pass
#     else:
#         await setInterval.finish(f"输入的不是纯数字", reply_message=True)
#     # file_path = data_dir / "config.toml"
#     if not os.path.exists(config_file):
#         # 创建配置文件
#         config = {"score_interval": 1}
#         toml.dump(config, config_file)
#
#     with open(config_file, "r") as f:
#         config = toml.load(f)
#     interval = min(int(message), 60)
#     config["score_interval"] = interval
#     toml.dump(config, "config.toml")
#
#     await setInterval.finish(f"已设置本群比分推送间隔为{interval}分钟")
