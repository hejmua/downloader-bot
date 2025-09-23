import os
import re
import asyncio
import aiofiles
import logging
from typing import Optional
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_PATH = os.path.join(PROJECT_ROOT, 'tools')


async def run_yt_dlp(url: str, output_template: str) -> dict:
    """
    Performs asynchronous execution of yt-dlp for processing audio content
    Returns a dictionary with operation results including metadata and file path
    """
    import yt_dlp

    ffmpeg_executable = await get_ffmpeg_path()
    logger.info(f"FFmpeg path: {ffmpeg_executable}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extract_flat': False,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    if ffmpeg_executable:
        ydl_opts['ffmpeg_location'] = os.path.dirname(ffmpeg_executable)
        logger.info(f"FFmpeg path set: {os.path.dirname(ffmpeg_executable)}")

    try:
        logger.info(f"Starting download: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            logger.info(f"Track info received: {info.get('title', 'Unknown')}")

            filename = ydl.prepare_filename(info)
            logger.info(f"Original filename: {filename}")

            mp3_filename = filename.rsplit('.', 1)[0] + '.mp3'
            logger.info(f"Expected MP3 name: {mp3_filename}")

            final_filename = mp3_filename if os.path.exists(mp3_filename) else filename
            if os.path.exists(final_filename):
                logger.info(f"Final file: {final_filename} (size: {os.path.getsize(final_filename)} bytes)")

            return {
                'success': True,
                'filename': final_filename,
                'info': info,
                'error': None
            }

    except Exception as e:
        logger.error(f"Error in run_yt_dlp: {e}")
        return {
            'success': False,
            'filename': None,
            'info': None,
            'error': str(e)
        }


async def get_ffmpeg_path() -> Optional[str]:
    """
    Determines the path to ffmpeg executable in the system
    Priority is given to local installation in the project's tools folder
    """
    try:
        logger.info(f"Searching for FFmpeg in: {TOOLS_PATH}")

        if not os.path.exists(TOOLS_PATH):
            logger.warning(f"Tools folder not found: {TOOLS_PATH}")
            return None

        possible_names = ['ffmpeg.exe', 'ffmpeg'] if os.name == 'nt' else ['ffmpeg']

        for name in possible_names:
            ffmpeg_path = os.path.join(TOOLS_PATH, name)
            logger.info(f"Checking path: {ffmpeg_path}")
            if os.path.exists(ffmpeg_path):
                logger.info(f"FFmpeg found: {ffmpeg_path}")
                return ffmpeg_path

        import shutil
        logger.info("Searching for FFmpeg in system PATH")
        system_ffmpeg = shutil.which('ffmpeg')
        if system_ffmpeg:
            logger.info(f"FFmpeg found in system: {system_ffmpeg}")
            return system_ffmpeg

        logger.warning("FFmpeg not found in tools folder or system")
        return None

    except Exception as e:
        logger.error(f"Error searching for ffmpeg: {e}")
        return None


async def add_metadata_to_mp3(filepath: str, track_info: dict) -> bool:
    """
    Adds ID3 metadata to MP3 file including title, artist and cover art
    Supports standard tags and various encoding processing
    """
    try:
        if not os.path.exists(filepath):
            logger.error(f"File does not exist for metadata addition: {filepath}")
            return False

        logger.info(f"Adding metadata to file: {filepath}")

        try:
            audio = MP3(filepath, ID3=ID3)
        except:
            audio = MP3(filepath)
            audio.add_tags(ID3=ID3)

        if audio.tags is None:
            audio.add_tags()

        title = track_info.get('title', '').strip()
        artist = track_info.get('uploader', '').strip() or track_info.get('creator', '').strip()

        if title:
            audio.tags.add(TIT2(encoding=3, text=title))
            logger.info(f"Title added: {title}")
        if artist:
            audio.tags.add(TPE1(encoding=3, text=artist))
            logger.info(f"Artist added: {artist}")

        genre = track_info.get('genre', '')
        if genre:
            audio.tags.add(TALB(encoding=3, text=genre))
            logger.info(f"Genre added: {genre}")

        thumbnail = track_info.get('thumbnail')
        if thumbnail:
            logger.info(f"Adding cover art: {thumbnail}")
            await add_cover_art(audio, thumbnail)

        audio.save()
        logger.info("Metadata successfully added")
        return True

    except Exception as e:
        logger.error(f"Error adding metadata: {e}")
        return False


async def add_cover_art(audio, thumbnail_url: str):
    """
    Downloads and adds track cover art from URL to ID3 tags
    Handles various image formats and network errors
    """
    try:
        import aiohttp
        logger.info(f"Downloading cover art: {thumbnail_url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail_url) as response:
                if response.status == 200:
                    cover_data = await response.read()
                    audio.tags.add(APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=cover_data
                    ))
                    logger.info("Cover art successfully added")
                else:
                    logger.warning(f"Failed to download cover art: status {response.status}")
    except Exception as e:
        logger.error(f"Error adding cover art: {e}")


def sanitize_filename(filename: str) -> str:
    """
    Cleans filename from invalid characters for cross-platform compatibility
    Replaces spaces and limits filename length
    """
    cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
    cleaned = cleaned.replace(' ', '_')
    return cleaned[:100]


async def download_soundcloud(url: str, dest_folder: str) -> str:
    """
    Main handler for SoundCloud content download
    Manages the entire process from download to metadata addition
    Automatically switches to fallback mode when ffmpeg is unavailable
    """
    try:
        logger.info(f"Starting SoundCloud download: {url}")
        logger.info(f"Destination folder: {dest_folder}")

        os.makedirs(dest_folder, exist_ok=True)
        logger.info("Folder created/verified")

        ffmpeg_path = await get_ffmpeg_path()
        if not ffmpeg_path:
            logger.warning("FFmpeg not found, will use download without conversion")

        output_template = os.path.join(dest_folder, '%(title)s.%(ext)s')
        logger.info(f"Output file template: {output_template}")

        result = await run_yt_dlp(url, output_template)

        if not result['success']:
            if "ffmpeg" in result['error'].lower():
                logger.warning("FFmpeg error, trying to download without conversion")
                return await download_without_conversion(url, dest_folder)
            raise Exception(f"yt-dlp error: {result['error']}")

        if not result['filename']:
            raise Exception("Filename not returned")

        if not os.path.exists(result['filename']):
            logger.warning(f"File does not exist: {result['filename']}")
            files_in_dir = os.listdir(dest_folder)
            logger.info(f"Files in folder: {files_in_dir}")

            for file in files_in_dir:
                if file.endswith(('.mp3', '.m4a', '.webm', '.mp4')):
                    found_file = os.path.join(dest_folder, file)
                    logger.info(f"File found: {found_file}")
                    result['filename'] = found_file
                    break
            else:
                raise Exception("File was not created")

        logger.info(f"File successfully downloaded: {result['filename']}")

        if result['info']:
            logger.info("Adding metadata...")
            await add_metadata_to_mp3(result['filename'], result['info'])

        logger.info(f"Download completed: {result['filename']}")
        return result['filename']

    except ImportError:
        error_msg = "yt-dlp not installed. Install: pip install yt-dlp"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Error downloading from SoundCloud: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


async def download_without_conversion(url: str, dest_folder: str) -> str:
    """
    Fallback download mode without format conversion
    Used when system ffmpeg is unavailable or conversion errors occur
    """
    import yt_dlp

    logger.info("Downloading without conversion")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(dest_folder, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            logger.info(f"File downloaded without conversion: {filename}")

            await add_metadata_to_mp3(filename, info)

            return filename

    except Exception as e:
        logger.error(f"Error downloading without conversion: {e}")
        raise Exception(f"Error downloading without conversion: {str(e)}")


def is_soundcloud_url(url: str) -> bool:
    """
    SoundCloud URL validator with support for various subdomains and protocols
    Uses regular expressions for precise platform identification
    """
    patterns = [
        r'https?://soundcloud\.com/',
        r'https?://on\.soundcloud\.com/',
        r'https?://m\.soundcloud\.com/',
    ]

    for pattern in patterns:
        if re.match(pattern, url, re.IGNORECASE):
            return True
    return False


async def check_ffmpeg_availability() -> bool:
    """
    Checks ffmpeg availability in the system
    Returns readiness status for audio conversion
    """
    ffmpeg_path = await get_ffmpeg_path()
    available = ffmpeg_path is not None and os.path.exists(ffmpeg_path)
    logger.info(f"FFmpeg available: {available}")
    return available


async def send_audio_to_telegram(bot, chat_id, file_path, caption=""):
    """
    Sends audio file to Telegram via aiogram with correct format
    Handles exceptions and logs media sending process
    """
    try:
        from aiogram.types import FSInputFile

        audio_file = FSInputFile(file_path)
        await bot.send_audio(
            chat_id=chat_id,
            audio=audio_file,
            caption=caption
        )

        logger.info(f"Audio sent: {os.path.basename(file_path)}")

    except Exception as e:
        logger.error(f"Error sending audio to Telegram: {e}")
        raise