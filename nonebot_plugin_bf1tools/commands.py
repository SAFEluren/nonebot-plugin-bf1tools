import json
import sqlite3

import httpx
import loguru
from nonebot import get_plugin_config
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment, GroupMessageEvent
from nonebot.params import CommandArg

from nonebot_plugin_bf1tools.config import Config
from .config import databases

plugin_config = get_plugin_config(Config)

addKeyword = on_command('addkeyword', aliases={"添加关键字", "增加关键字"})
removeKeyword = on_command('removekeyword', aliases={"移除关键字", "删除关键字"})
listKeyword = on_command('listkeyword', aliases={"关键字列表", "列出关键字"})


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


async def get_index(keyword):
    conn = sqlite3.connect(databases)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM keywords WHERE keywords=?", (keyword,))
        result = cur.fetchone()
        if result:
            return result[0]
        else:
            return None

    except sqlite3.Error as e:
        print("Error:", e)
        return False
    finally:
        cur.close()
        conn.close()


@addKeyword.handle()
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


async def request_api(api_path):
    api_url = plugin_config.api_url + api_path
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{api_url}')
            content = response.text
            return response.text

    except (httpx.HTTPStatusError, httpx.ConnectTimeout) as e:
        print(f'HTTP error occurred: {e}')


cmd_score = on_command('score', aliases={"比分", "分数", "point"})


@cmd_score.handle()
async def score(event: GroupMessageEvent):
    session = event.group_id
    parsed_data = json.loads(await request_api("Server/GetServerData"))

    gameId = parsed_data['data']['gameId']
    timestamp = parsed_data['timestamp']
    game_name = parsed_data['data']['name']
    game_time = parsed_data['data']['gameTime']
    game_mode = parsed_data['data']['gameMode2']
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
    msg.append(f"\n游戏模式: {game_mode}")
    msg.append(f"\n游戏时间: {game_time}")
    msg.append(f"\n地图名称: {map_name}")
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
        await cmd_score.send(msg, reply_message=True)
        return

    msg.append(f"\n分差: {score_difference}")
    msg.append(f"\n优势方: {leading_team}")
    msg.append(f"\n劣势方: {trailing_team}")
    msg.append(f"\n--------------------")
    msg.append(f"\n{timestamp}")
    await cmd_score.send(msg, reply_message=True)
