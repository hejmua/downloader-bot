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


async def download_youtube(url: str, dest_folder: str) -> str:
    """
    Asynchronous YouTube content downloader including Shorts and standard videos
    Uses optimized yt-dlp parameters for maximum quality
    Returns the path to the downloaded media file in MP4 format
    """
    logger.info(f"Starting YouTube download for URL: {url}")
    logger.debug(f"Destination folder: {dest_folder}")

    loop = asyncio.get_event_loop()

    def run():
        try:
            outtmpl = os.path.join(dest_folder, "%(id)s.%(ext)s")
            ydl_opts = {**YTDL_OPTS, "outtmpl": outtmpl}

            logger.debug(f"YT-DLP options: {ydl_opts}")

            with YoutubeDL(ydl_opts) as ydl:
                logger.info("Extracting video info...")
                video_info = ydl.extract_info(url, download=True)

                filename = ydl.prepare_filename(video_info)
                file_size = os.path.getsize(filename) if os.path.exists(filename) else 0

                logger.info(f"Download completed: {filename} ({file_size} bytes)")
                logger.debug(f"Video info: {video_info.get('title', 'Unknown title')} "
                             f"(duration: {video_info.get('duration', 'N/A')}s)")

                return filename

        except Exception as e:
            logger.error(f"YouTube download error for URL {url}: {e}", exc_info=True)
            raise

    try:
        result = await loop.run_in_executor(None, run)
        logger.info(f"YouTube download successful: {result}")
        return result

    except asyncio.CancelledError:
        logger.warning(f"YouTube download cancelled for URL: {url}")
        raise
    except Exception as e:
        logger.error(f"Async YouTube download failed for URL {url}: {e}", exc_info=True)
        raise