# Ultroid - UserBot
# Copyright (C) 2021-2022 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://github.com/TeamUltroid/pyUltroid/blob/main/LICENSE>.

import asyncio
import inspect
import re
import sys
from io import BytesIO
from pathlib import Path
from time import gmtime, strftime
from traceback import format_exc

from telethon import Button
from telethon import __version__ as telever
from telethon import events
from telethon.errors.common import AlreadyInConversationError
from telethon.errors.rpcerrorlist import (
    AuthKeyDuplicatedError,
    BotInlineDisabledError,
    BotMethodInvalidError,
    ChatSendInlineForbiddenError,
    ChatSendMediaForbiddenError,
    ChatSendStickersForbiddenError,
    FloodWaitError,
    MessageDeleteForbiddenError,
    MessageIdInvalidError,
    MessageNotModifiedError,
    UserIsBotError,
)
from telethon.events import MessageEdited, NewMessage
from telethon.utils import get_display_name

from .. import *
from ..dB import DEVLIST
from ..dB._core import LIST, LOADED
from ..functions.admins import admin_check
from ..functions.helper import bash
from ..functions.helper import time_formatter as tf
from ..version import __version__ as pyver
from ..version import ultroid_version as ult_ver
from . import SUDO_M, owner_and_sudos
from ._wrappers import eod

MANAGER = udB.get_key("MANAGER")
TAKE_EDITS = udB.get_key("TAKE_EDITS")
black_list_chats = udB.get_key("BLACKLIST_CHATS")
allow_sudo = SUDO_M.should_allow_sudo


def compile_pattern(data, hndlr):
    if data.startswith("^"):
        data = data[1:]
    if data.startswith("."):
        data = data[1:]
    if hndlr in [" ", "NO_HNDLR"]:
        # No Hndlr Feature
        return re.compile("^" + data)
    return re.compile("\\" + hndlr + data)


def ultroid_cmd(
    pattern=None, manager=False, ultroid_bot=ultroid_bot, asst=asst, **kwargs
):
    owner_only = kwargs.get("owner_only", False)
    groups_only = kwargs.get("groups_only", False)
    admins_only = kwargs.get("admins_only", False)
    fullsudo = kwargs.get("fullsudo", False)
    only_devs = kwargs.get("only_devs", False)
    func = kwargs.get("func", lambda e: not e.via_bot_id)

    def decor(dec):
        async def wrapp(ult):
            if owner_only and not ult.out:
                return
            chat = ult.chat
            if not ult.out:
                if ult.sender_id not in owner_and_sudos():
                    return
                if fullsudo and ult.sender_id not in SUDO_M.fullsudos:
                    return await eod(ult, "`Full Sudo User Required...`", time=15)
            if hasattr(chat, "title"):
                if (
                    "#noub" in chat.title.lower()
                    and not (chat.admin_rights or chat.creator)
                    and not (ult.sender_id in DEVLIST)
                ):
                    return
            if admins_only:
                if ult.is_private:
                    return await eod(ult, "`Use this in group/channel.`")
                if not (chat.admin_rights or chat.creator):
                    return await eod(ult, "`I am not an admin.`")
            if only_devs and not udB.get_key("I_DEV"):
                return await eod(
                    ult,
                    f"**⚠️ Developer Restricted!**\nIf you know what this does, and want to proceed, use\n`{HNDLR}setdb I_DEV True`.\n\nThis Might Be Dangerous.",
                    time=10,
                )
            if groups_only and ult.is_private:
                return await eod(ult, "`Use this in Group/Channel.`")
            try:
                await dec(ult)
            except FloodWaitError as fwerr:
                await asst.send_message(
                    udB.get_key("LOG_CHANNEL"),
                    f"`FloodWaitError:\n{str(fwerr)}\n\nSleeping for {tf((fwerr.seconds + 10)*1000)}`",
                )
                await ultroid_bot.disconnect()
                await asyncio.sleep(fwerr.seconds + 10)
                await ultroid_bot.connect()
                await asst.send_message(
                    udB.get_key("LOG_CHANNEL"),
                    "`Bot is working again`",
                )
                return
            except ChatSendInlineForbiddenError:
                return await eod(ult, "`Inline Locked In This Chat.`")
            except (ChatSendMediaForbiddenError, ChatSendStickersForbiddenError):
                return await eod(
                    ult, "`Sending media or sticker is not allowed in this chat.`"
                )
            except (BotMethodInvalidError, UserIsBotError):
                return await eod(ult, "This Command Can't be used by Bot!")
            except AlreadyInConversationError:
                return await eod(
                    ult,
                    "Conversation Is Already On, Kindly Wait Sometime Then Try Again.",
                )
            except (BotInlineDisabledError) as er:
                return await eod(ult, f"`{er}`")
            except (
                MessageIdInvalidError,
                MessageNotModifiedError,
                MessageDeleteForbiddenError,
            ) as er:
                LOGS.exception(er)
            except AuthKeyDuplicatedError as er:
                LOGS.exception(er)
                await asst.send_message(
                    udB.get_key("LOG_CHANNEL"),
                    "كـود تيرمكـس الخـاص بك تم انتهـائه .. قم بعمل كود جديد من 👇",
                    buttons=[
                        Button.url("بوت تيرمكس", "t.me/Zedthonnbot?start="),
                        Button.url(
                            "موقع تيرمكس",
                            "https://replit.com/@ZTHONAR/stringsession",
                        ),
                    ],
                )
                sys.exit()
            except events.StopPropagation:
                raise events.StopPropagation
            except KeyboardInterrupt:
                pass
            except Exception as e:
                LOGS.exception(e)
                date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                naam = get_display_name(chat)
                ftext = (
                    "**✘ تقـرير خطـأ زدثـــون 𝗭𝗧𝗵𝗼𝗻 ✘** `قم باعادة توجيه هذه الرسـاله الى` @zzzzl1l\n\n"
                )
                ftext += "**اصـدار المكتبـه:** `" + str(pyver)
                ftext += "`\n**اصـدار زدثـــون:** `" + str(ult_ver)
                ftext += "`\n**اصـدار تيليـثـون:** `" + str(telever)
                ftext += f"`\n**اصـدار الاستضـافه:** `{HOSTED_ON}`\n\n"
                ftext += "--------بـدء سجـل تتبـع زدثـــون 𝗭𝗧𝗵𝗼𝗻--------\n"
                ftext += "\n**التـاريخ:** `" + date
                ftext += "`\n**الكـروب:** `" + str(ult.chat_id) + "` " + str(naam)
                ftext += "\n**الايـدي:** `" + str(ult.sender_id)
                ftext += "`\n**التتبـع:** `" + str(ult.is_reply)
                ftext += "`\n\n**تقـرير الحـدث:**`\n"
                ftext += str(ult.text)
                ftext += "`\n\n**تفاصيـل التتبـع:**`\n"
                ftext += str(format_exc())
                ftext += "`\n\n**نـص الخطـأ:**`\n"
                ftext += str(sys.exc_info()[1])
                ftext += "`\n\n--------نهـاية سجـل تتبـع زدثـــون 𝗭𝗧𝗵𝗼𝗻--------"
                ftext += "\n\n\n**آخـر 5 ملفـات تـم جلبهـا:**`\n"

                stdout, stderr = await bash('git log --pretty=format:"%an: %s" -5')
                result = stdout + (stderr or "")

                ftext += result + "`"

                if len(ftext) > 4096:
                    with BytesIO(ftext.encode()) as file:
                        file.name = "logs.txt"
                        error_log = await asst.send_file(
                            udB.get_key("LOG_CHANNEL"),
                            file,
                            caption="**✘ تقـرير خطـأ زدثـــون 𝗭𝗧𝗵𝗼𝗻 ✘** `قم باعادة توجيه هذه الرساله الى` @zzzzl1l\n\n",
                        )
                else:
                    error_log = await asst.send_message(
                        udB.get_key("LOG_CHANNEL"),
                        ftext,
                    )
                if ult.out:
                    await ult.edit(
                        f"<b><a href={error_log.message_link}>[An error occurred]</a></b>",
                        link_preview=False,
                        parse_mode="html",
                    )

        cmd = None
        blacklist_chats = False
        chats = None
        if black_list_chats:
            blacklist_chats = True
            chats = list(black_list_chats)
        _add_new = allow_sudo and HNDLR != SUDO_HNDLR
        if _add_new:
            if pattern:
                cmd = compile_pattern(pattern, SUDO_HNDLR)
            ultroid_bot.add_event_handler(
                wrapp,
                NewMessage(
                    pattern=cmd,
                    incoming=True,
                    forwards=False,
                    func=func,
                    chats=chats,
                    blacklist_chats=blacklist_chats,
                ),
            )
        if pattern:
            cmd = compile_pattern(pattern, HNDLR)
        ultroid_bot.add_event_handler(
            wrapp,
            NewMessage(
                outgoing=True if _add_new else None,
                pattern=cmd,
                forwards=False,
                func=func,
                chats=chats,
                blacklist_chats=blacklist_chats,
            ),
        )
        if TAKE_EDITS:

            def func_(x):
                return not x.via_bot_id and not (x.is_channel and x.chat.broadcast)

            ultroid_bot.add_event_handler(
                wrapp,
                MessageEdited(
                    pattern=cmd,
                    forwards=False,
                    func=func_,
                    chats=chats,
                    blacklist_chats=blacklist_chats,
                ),
            )
        if manager and MANAGER:
            allow_all = kwargs.get("allow_all", False)
            allow_pm = kwargs.get("allow_pm", False)
            require = kwargs.get("require", None)

            async def manager_cmd(ult):
                if not allow_all and not (await admin_check(ult, require=require)):
                    return
                if not allow_pm and ult.is_private:
                    return
                try:
                    await dec(ult)
                except Exception as er:
                    if chat := udB.get_key("MANAGER_LOG"):
                        text = f"**#MANAGER_LOG\n\nChat:** `{get_display_name(ult.chat)}` `{ult.chat_id}`"
                        text += f"\n**التتبـع :** `{ult.is_reply}`\n**الامـر :** {ult.text}\n\n**الخطـأ :** `{er}`"
                        try:
                            return await asst.send_message(
                                chat, text, link_preview=False
                            )
                        except Exception as er:
                            LOGS.exception(er)
                    LOGS.info(f"• MANAGER [{ult.chat_id}]:")
                    LOGS.exception(er)

            if pattern:
                cmd = compile_pattern(pattern, "/")
            asst.add_event_handler(
                manager_cmd,
                NewMessage(
                    pattern=cmd,
                    forwards=False,
                    incoming=True,
                    func=func,
                    chats=chats,
                    blacklist_chats=blacklist_chats,
                ),
            )
        if DUAL_MODE and not (manager and DUAL_HNDLR == "/"):
            if pattern:
                cmd = compile_pattern(pattern, DUAL_HNDLR)
            asst.add_event_handler(
                wrapp,
                NewMessage(
                    pattern=cmd,
                    incoming=True,
                    forwards=False,
                    func=func,
                    chats=chats,
                    blacklist_chats=blacklist_chats,
                ),
            )
        file = Path(inspect.stack()[1].filename)
        if "addons/" in str(file):
            if LOADED.get(file.stem):
                LOADED[file.stem].append(wrapp)
            else:
                LOADED.update({file.stem: [wrapp]})
        if pattern:
            if LIST.get(file.stem):
                LIST[file.stem].append(pattern)
            else:
                LIST.update({file.stem: [pattern]})
        return wrapp

    return decor
