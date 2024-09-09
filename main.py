import asyncio
import re
import uuid
import multiprocessing
from pathlib import Path
from io import BytesIO
import urllib
from urllib.parse import urlparse
from telegram.ext import CommandHandler, ApplicationBuilder, PicklePersistence, ContextTypes, MessageHandler, filters, \
    CallbackQueryHandler, CallbackContext
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram._files._basemedium import _BaseMedium
import threading
import youtube_dl

from util import extract_message_media

DOWNLOAD_DIR = Path("downloads/")
PERSISTENCE_DATA_FILE = Path("./bot_data.dat")

app = (ApplicationBuilder()
       .token("6831160891:AAFkTy55jXxqpN5Si1GkodT8IRQa9q8RRhc")
       .persistence(PicklePersistence(filepath=PERSISTENCE_DATA_FILE, update_interval=60))
       .build())

cache = {'youtube': {'threads': {}}}

NO_MEDIA_KEYBOARD = lambda msg_id: InlineKeyboardMarkup([
    [InlineKeyboardButton("Download from youtube (to drive)", callback_data=f'yt_dr {msg_id}')],
    [InlineKeyboardButton("Download from youtube (to telegram)", callback_data=f'yt_tg {msg_id}')],
    [InlineKeyboardButton("❌ CANCEL ❌", callback_data="cancel")]
])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_message("Hallo👋🏻")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ Canceled")
    splited = query.data.split(' ')
    if len(splited) > 1:
        uid = splited[-1]
        del cache['youtube'][uid]
    await update.effective_message.delete()


async def handler_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    media = extract_message_media(update.message)
    if media is None:
        uid = uuid.uuid4().hex
        cache['youtube'][uid] = update.message.text
        await update.effective_chat.send_message("‼️ no file in message!", reply_to_message_id=update.message.id)
                                                 # reply_markup=NO_MEDIA_KEYBOARD(uid))
        return
    file = await media.get_file()
    try:
        file_type = file.file_path.split('/')[-1].split('.')[-1]
        await update.effective_chat.send_message("⌛ Downloading please wait!")
    except Exception as e:
        file_type = ''
        await update.effective_chat.send_message("⚠️ can't find files extension!\n⌛ Downloading please wait!")
    await update.effective_chat.send_action(ChatAction.UPLOAD_DOCUMENT)
    file = await file.download_to_drive(DOWNLOAD_DIR.joinpath(uuid.uuid4().hex + '.' + file_type))
    await update.effective_chat.send_message(f"✅ file saved to: {file.relative_to(DOWNLOAD_DIR).as_posix()!r}")

#
# async def download_youtube(update: Update, context: CallbackContext):
#     query = update.callback_query
#     uid = query.data.split(' ')[1]
#     to_drive = query.data.split(' ')[0] == 'yt_dr'
#     text: str = cache['youtube'].pop(uid)
#     if not re.match(r'https://(www\.)?youtube\.com|https://youtu\.be', text):
#         await query.answer("Message content is not youtube URI!", show_alert=True)
#         await query.edit_message_reply_markup(None)
#         return
#     await query.answer("download will be started soon..")
#     youtube_dl.downloader.FileDownloader
#     thread = threading.Thread(target=download_youtube_file, args=(yt, context.bot, update.effective_chat.id))
#     thread.start()
#     cache['youtube']['threads'][text] = thread
#
#
# def progress(a, b, c):
#     print(a, b, c)
#
#
# def download_youtube_file(youtube: pytube.YouTube, bot: Bot, chat_id: int) -> str:
#     streams = youtube.streams
#     file = streams.filter(progressive=True, file_extension='mp4').asc().first()
#     try:
#         file = file.download()
#     except Exception as exc:
#         print(exc)
#         asyncio.run(bot.send_message(chat_id, "failed to download youtube file!"))

app.add_handler(CommandHandler('start', start))
app.add_handler(MessageHandler(filters=(filters.ALL & (~filters.COMMAND)), callback=handler_new_message))
app.add_handler(CallbackQueryHandler(callback=cancel, pattern="^(cancel)$"))
app.add_handler(CallbackQueryHandler(callback=download_youtube, pattern="^(yt_)"))

app.run_polling(allowed_updates=[Update.CALLBACK_QUERY, Update.MESSAGE, Update.INLINE_QUERY])
