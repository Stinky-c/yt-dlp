from logging import Logger
from typing import Any, Callable, Type
import yt_dlp

# TODO:
# optional max file size
# extra hooks?


class FallbackLogger(Logger):
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


def callback(filepath, callback_data):
    """Filepath is mandatory, callback_data if not provide in main call returns None"""
    pass


def main(
    url: str | list[str],
    output_tmpl: str = "%(title)s.%(ext)s",
    output_dir: str = "./",
    custom_selector: callable = None,
    callback: Callable = callback,
    callback_data: Any = None,
    MAX_FILESIZE_A: int = 1048576,
    MAX_FILESIZE_V: int = 7340032,
    logger: Logger = FallbackLogger("yt-dlp"),
) -> None:
    """downloads videos based on too many shitty things that i hate

    Args:
        url (str | list[str]): A list of urls to download
        output_tmpl (str, optional): yt-dlp templating lang. Defaults to "%(title)s.%(ext)s".
        output_dir (str, optional): the output directory. Defaults to "./".
        custom_selector (callable, optional): Custom selector in case current one not good enough. Defaults to format_selector.
        callback (Callable, optional): A post hook. Defaults to callback.
        callback_data (Any, optional): Data passed along side the callback. Defaults to None.
    """

    def format_selector(ctx):
        formats = ctx.get("formats")[::-1]

        # video_ext
        # audio_ext
        if formats[0].get("filesize_approx", False):
            file_size = "filesize_approx"
        else:
            file_size = "filesize"
        best_video = next(
            f
            for f in formats
            if (
                f["video_ext"] == "mp4"
                and f["audio_ext"] == "none"
                and f[file_size] < MAX_FILESIZE_V
            )
        )

        audio_ext = {"mp4": "m4a", "webm": "webm"}[best_video["ext"]]
        best_audio = next(
            f
            for f in formats
            if (
                f["acodec"] != "none"
                and f["vcodec"] == "none"
                and f[file_size] < MAX_FILESIZE_A
                and f["ext"] == audio_ext
            )
        )

        yield {
            "format_id": f'{best_video["format_id"]}+{best_audio["format_id"]}',
            "ext": best_video["ext"],
            "requested_formats": [best_video, best_audio],
            "protocol": f'{best_video["protocol"]}+{best_audio["protocol"]}',
        }

    custom_selector = format_selector if custom_selector is None else custom_selector
    OUT_PATH = output_dir + output_tmpl
    ydl_opts = {
        "logger": logger,
        "format": custom_selector,
        "outtmpl": {"default": OUT_PATH},
        "restrictfilenames": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.add_post_hook(callback, callback_data)
        ydl.download(url)
