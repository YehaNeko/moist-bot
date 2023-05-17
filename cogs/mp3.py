import discord
from discord.ext import commands

from pytube import YouTube
import pytube.exceptions

import io
import logging

logger = logging.getLogger('discord.' + __name__)


class FileTooBig(commands.CommandError):
    pass


class Mp3(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client
        self.execute = self.client.loop.run_in_executor

    @staticmethod
    def _get_buffer(url) -> tuple[io.BytesIO, str]:
        # Get audio stream
        audio_stream = YouTube(url).streams.get_audio_only()

        # Check file size
        if audio_stream.filesize_approx > 8_388_608:
            raise FileTooBig()

        # Download
        buffer = io.BytesIO()
        audio_stream.stream_to_buffer(buffer)
        buffer.seek(0)
        return buffer, audio_stream.title

    @commands.command(hidden=True)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    @commands.is_owner()
    async def mp3(self, ctx: commands.Context, *, url: str):
        """Youtube mp3 downloader"""

        async with ctx.typing():
            # Gets buffer in separate thread to avoid blocking
            buffer, title = await self.execute(None, self._get_buffer, url)
            await ctx.reply(file=discord.File(fp=buffer, filename=title + ".mp3"))
            buffer.close()

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        error = getattr(error, 'original', error)

        # File too big
        if isinstance(error, FileTooBig):
            await ctx.reply("File is over 8mb and cannot be sent.")

        # Pytube regex error
        elif isinstance(error, pytube.exceptions.RegexMatchError):
            await ctx.reply(f"Cannot find video url `{ctx.kwargs['url']}`.")

        # Pytube base error
        elif isinstance(error, pytube.exceptions.PytubeError):
            logging.exception(type(error), exc_info=error)
            await ctx.reply(f"Cannot download the video.")

        # This shouldn't happen
        elif isinstance(error, discord.HTTPException):
            logging.exception(type(error), exc_info=error)
            await ctx.reply("HTTP Error.")


async def setup(client):
    await client.add_cog(Mp3(client))
