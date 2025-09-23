import asyncio
import os
import tempfile
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from downloaders.tiktok import download_tiktok
from downloaders.youtube import download_youtube
from downloaders.soundcloud import download_soundcloud
from downloaders.soundcloud import send_audio_to_telegram

# env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

progress_message = None



async def update_progress_message(chat_id, text, message_id=None):
    """
    Updates the processing status message with Markdown formatting
    Returns the ID of the updated or created message
    """
    progress_text = f"🔄 *{text}*"

    logger.info(f"Progress update for chat {chat_id}: {text}")

    if message_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=progress_text,
                parse_mode="Markdown"
            )
            return message_id
        except Exception as e:
            logger.warning(f"Failed to edit progress message: {e}")

    msg = await bot.send_message(
        chat_id=chat_id,
        text=progress_text,
        parse_mode="Markdown"
    )
    return msg.message_id


async def send_success_message(chat_id, platform, filename):
    """Sends a standardized success message after content download"""
    success_messages = {
        "tiktok": "🎵 *TikTok video successfully downloaded!*",
        "youtube": "🎥 *YouTube video downloaded!*",
        "soundcloud": "🎧 *SoundCloud track ready!*"
    }

    text = f"{success_messages.get(platform, '✅ *File is ready!*')}\n\n📁 *{filename}*"

    logger.info(f"Successfully processed {platform} file: {filename} for chat {chat_id}")

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown"
    )


async def choose_downloader(url: str, dest_folder: str, chat_id: int, progress_msg_id: int) -> str:
    """Determines the appropriate downloader based on domain and starts the download process"""
    logger.info(f"Choosing downloader for URL: {url}")

    if "tiktok.com" in url or "vm.tiktok.com" in url:
        await update_progress_message(chat_id, "Downloading from TikTok...", progress_msg_id)
        logger.info(f"Selected TikTok downloader for URL: {url}")
        return await download_tiktok(url, dest_folder), "tiktok"
    elif "youtube.com" in url or "youtu.be" in url:
        await update_progress_message(chat_id, "Downloading from YouTube...", progress_msg_id)
        logger.info(f"Selected YouTube downloader for URL: {url}")
        return await download_youtube(url, dest_folder), "youtube"
    elif "soundcloud.com" in url:
        await update_progress_message(chat_id, "Downloading from SoundCloud...", progress_msg_id)
        logger.info(f"Selected SoundCloud downloader for URL: {url}")
        return await download_soundcloud(url, dest_folder), "soundcloud"
    else:
        error_msg = f"Unsupported source: {url}"
        logger.warning(error_msg)
        raise ValueError(error_msg)


def get_start_keyboard():
    """Creates an inline keyboard for the start message with content examples"""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="🎬 TikTok Example",
            url="https://vm.tiktok.com/ZM2jp5x8E/"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="🎥 YouTube Example",
            url="https://youtu.be/dQw4w9WgXcQ"
        ),
        types.InlineKeyboardButton(
            text="🎵 SoundCloud Example",
            url="https://soundcloud.com/likewaterofficial/likewater"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="💡 How to Use",
            callback_data="help"
        )
    )
    return builder.as_markup()


def get_help_keyboard():
    """Creates an inline keyboard for the help page with a back button"""
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="🔙 Back",
            callback_data="back_to_start"
        )
    )
    return builder.as_markup()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Handler for the /start command - welcome message with functionality description"""
    logger.info(f"Start command received from user {message.from_user.id} ({message.from_user.username})")

    welcome_text = (
        "✨ *Welcome to Downloader Bot!*\n\n"
        "🎯 *I can help you download content from popular platforms:*\n\n"
        "• 🎵 *TikTok* — videos and music\n"
        "• 🎥 *YouTube* — videos and Shorts\n"
        "• 🎧 *SoundCloud* — tracks and podcasts\n\n"
        "📥 *Just send me a link* to the content you want,\n"
        "and I'll process it quickly!\n\n"
        "👇 *Examples of supported links:*"
    )

    await message.answer(
        text=welcome_text,
        parse_mode="Markdown",
        reply_markup=get_start_keyboard()
    )


@dp.callback_query(lambda c: c.data == "help")
async def process_help(callback_query: CallbackQuery):
    """Callback handler for displaying usage instructions"""
    logger.info(f"Help callback from user {callback_query.from_user.id}")

    help_text = (
        "📖 *Usage Instructions:*\n\n"
        "1. *Copy the link:*\n"
        "   • TikTok → \"Share\" → \"Copy link\"\n"
        "   • YouTube → from address bar\n"
        "   • SoundCloud → from address bar\n\n"
        "2. *Send the link* to me in chat\n"
        "3. *Wait for processing* — I'll download the file\n"
        "4. *Receive the ready file!*\n\n"
        "⚡ *Fast, simple, convenient!*"
    )

    try:
        await callback_query.message.edit_text(
            text=help_text,
            parse_mode="Markdown",
            reply_markup=get_help_keyboard()
        )
    except Exception as e:
        logger.error(f"Error editing help message: {e}")
        await callback_query.message.answer(
            text=help_text,
            parse_mode="Markdown",
            reply_markup=get_help_keyboard()
        )

    await callback_query.answer()


@dp.callback_query(lambda c: c.data == "back_to_start")
async def process_back(callback_query: CallbackQuery):
    """Callback handler for returning to the start message"""
    logger.info(f"Back to start callback from user {callback_query.from_user.id}")

    welcome_text = (
        "✨ *Welcome to MediaDownloader Bot!*\n\n"
        "🎯 *I can help you download content from popular platforms:*\n\n"
        "• 🎵 *TikTok* — videos and music\n"
        "• 🎥 *YouTube* — videos and Shorts\n"
        "• 🎧 *SoundCloud* — tracks and podcasts\n\n"
        "📥 *Just send me a link* to the content you want,\n"
        "and I'll process it quickly!\n\n"
        "👇 *Examples of supported links:*"
    )

    try:
        await callback_query.message.edit_text(
            text=welcome_text,
            parse_mode="Markdown",
            reply_markup=get_start_keyboard()
        )
    except Exception as e:
        logger.error(f"Error editing back message: {e}")
        await callback_query.message.answer(
            text=welcome_text,
            parse_mode="Markdown",
            reply_markup=get_start_keyboard()
        )

    await callback_query.answer()


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Handler for the /help command - displays brief bot usage instructions"""
    logger.info(f"Help command received from user {message.from_user.id}")

    help_text = (
        "🤖 *MediaDownloader Bot - Help*\n\n"
        "📥 *Supported platforms:*\n"
        "• TikTok - videos\n"
        "• YouTube - videos, Shorts\n"
        "• SoundCloud - music\n\n"
        "🚀 *How to use:*\n"
        "1. Copy a link from the desired platform\n"
        "2. Send the link to the bot\n"
        "3. Get the ready file!\n\n"
        "⚡ *The bot is free and works 24/7*"
    )

    await message.answer(help_text, parse_mode="Markdown")


@dp.message()
async def handle_link(message: Message):
    """Main handler for incoming messages - analyzes links and starts the download process"""
    global progress_message

    url = message.text.strip()
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username

    logger.info(f"Message received from user {user_id} (@{username}): {url}")

    if not url.startswith(('http://', 'https://')):
        logger.warning(f"Invalid URL format from user {user_id}: {url}")
        await message.answer(
            "❌ *Please send a valid link.*\n\n"
            "Examples:\n"
            "• https://vm.tiktok.com/...\n"
            "• https://youtu.be/...\n"
            "• https://soundcloud.com/...",
            parse_mode="Markdown"
        )
        return

    progress_msg_id = await update_progress_message(chat_id, "Checking link...")

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            logger.info(f"Starting download process for URL: {url}")
            file_path, platform = await choose_downloader(url, tmpdir, chat_id, progress_msg_id)
            await update_progress_message(chat_id, "Sending file...", progress_msg_id)

        except Exception as e:
            error_text = f"❌ *Error:* {str(e)}"
            logger.error(f"Download error for URL {url}: {e}", exc_info=True)
            await update_progress_message(chat_id, error_text, progress_msg_id)
            return

        if not os.path.exists(file_path):
            logger.error(f"File not found after download: {file_path}")
            await update_progress_message(chat_id, "❌ File not found", progress_msg_id)
            return

        filesize = os.path.getsize(file_path)
        MAX_SIZE = 49 * 1024 * 1024

        file_extension = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)

        logger.info(f"Download completed: {filename} ({filesize} bytes)")

        try:
            if filesize <= MAX_SIZE:
                await bot.delete_message(chat_id, progress_msg_id)

                if file_extension == '.mp3':
                    logger.info(f"Sending audio file: {filename}")
                    await send_audio_to_telegram(bot, chat_id, file_path)
                else:
                    logger.info(f"Sending video file: {filename}")
                    video = FSInputFile(file_path)
                    await message.answer_video(video=video)

                await send_success_message(chat_id, platform, filename)
                logger.info(f"File successfully sent to user {user_id}")

            else:
                error_msg = f"File too large: {filesize} bytes (max {MAX_SIZE})"
                logger.warning(error_msg)
                await update_progress_message(
                    chat_id,
                    "❌ File is too large for Telegram (maximum 50MB)",
                    progress_msg_id
                )

        except Exception as e:
            error_text = f"❌ *Sending error:* {str(e)}"
            logger.error(f"Error sending file {filename}: {e}", exc_info=True)
            await update_progress_message(chat_id, error_text, progress_msg_id)


async def main():
    """Main function for bot initialization and startup"""
    logger.info("🤖 Bot starting...")
    print("🤖 Bot started...")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Bot crashed: {e}", exc_info=True)
        raise
    finally:
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())