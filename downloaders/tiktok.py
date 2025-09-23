import os
import asyncio
from yt_dlp import YoutubeDL
import logging

# Logging settings
logger = logging.getLogger(__name__)

YTDL_OPTS = {
    "format": "best[ext=mp4]/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
}


async def download_tiktok(url: str, dest_folder: str) -> str:
    """
    Asynchronous content downloader for TikTok platform
    Uses yt-dlp to process various TikTok video formats
    Returns the absolute path to the downloaded media file
    """
    logger.info(f"Starting TikTok download for URL: {url}")
    logger.debug(f"Destination folder: {dest_folder}")

    loop = asyncio.get_event_loop()

    def run():
        try:
            download_opts = {
                **YTDL_OPTS,
                "outtmpl": os.path.join(dest_folder, "%(id)s.%(ext)s")
            }

            logger.debug(f"YT-DLP options for TikTok: {download_opts}")

            with YoutubeDL(download_opts) as ydl:
                logger.info("Extracting TikTok video info...")
                video_info = ydl.extract_info(url, download=True)

                filename = ydl.prepare_filename(video_info)
                file_size = os.path.getsize(filename) if os.path.exists(filename) else 0

                logger.info(f"TikTok download completed: {filename} ({file_size} bytes)")

                # Логируем дополнительную информацию о видео
                if video_info:
                    logger.debug(f"TikTok video info: {video_info.get('title', 'Unknown title')} "
                                 f"(duration: {video_info.get('duration', 'N/A')}s, "
                                 f"uploader: {video_info.get('uploader', 'N/A')})")

                return filename

        except Exception as e:
            logger.error(f"TikTok download error for URL {url}: {e}", exc_info=True)
            raise

    try:
        result = await loop.run_in_executor(None, run)
        logger.info(f"TikTok download successful: {result}")
        return result

    except asyncio.CancelledError:
        logger.warning(f"TikTok download cancelled for URL: {url}")
        raise
    except Exception as e:
        logger.error(f"Async TikTok download failed for URL {url}: {e}", exc_info=True)
        raise