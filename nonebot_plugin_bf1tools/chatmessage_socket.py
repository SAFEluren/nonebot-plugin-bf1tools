import socket
import loguru

from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from zhconv import convert

from nonebot_plugin_bf1tools import shou2game

SOCKET_IP = "127.0.0.1"
SOCKET_RECVMSG_PORT = 52001
SOCKET_SENDMSG_UDP_PORT = 51001


#
# async def process_message(message):
#     message_data = json.loads(message)
#     clan = message_data['clan']
#     name = message_data['name']
#     content = message_data['content']
#     pid = message_data['pid']
#     message_text = ''
#     if clan is not None:
#         message_text += f"[{clan}]"
#     message_text += f"{name}(PID:{pid}): {content} "
#     loguru.logger.info(message_text)
#     try:
#         conn = await aiosqlite.connect(databases)
#         cursor = await conn.cursor()
#         await cursor.execute("SELECT keywords FROM keywords")
#         rows = await cursor.fetchall()
#         keywords = [row[0] for row in rows]
#         matched_keywords = [keyword for keyword in keywords if keyword in content]
#         if matched_keywords:
#             msg = (f"消息中包含以下关键字:\n{matched_keywords}"
#                    f"\n--------------------"
#                    f"\n以下是聊天原文"
#                    f"\n{message_text}"
#                    f"\n--------------------")
#             await bot.send_group_msg(group_id=1006447496, message=msg)
#             loguru.logger.info("消息中包含以下关键字:", matched_keywords)
#     except sqlite3.Error as e:
#         loguru.logger.error("查询数据库时出错:", e)
#     finally:
#         await cursor.close()
#         await conn.close()
#


async def shouToGame(content):
    if isinstance(content, str):
        content = convert(content, 'zh-tw')
        message = f"#Chat.Send#{content}".encode('utf-8')
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_socket:
                send_socket.sendto(message, (SOCKET_IP, SOCKET_SENDMSG_UDP_PORT))
        except Exception as e:
            loguru.logger.error(e)
        return




@shou2game.handle()
async def sendmsg(event: GroupMessageEvent, args: Message = CommandArg()):
    message = args.extract_plain_text()
    sessionID = event.user_id
    await shouToGame(content=message)
    loguru.logger.info(f"[{sessionID}]发送了以下内容到服务器:{message}")
    msg = Message([MessageSegment.text(f'已发送以下消息到服务器:\n{message}')])
    await shou2game.send(msg, reply_message=True)
