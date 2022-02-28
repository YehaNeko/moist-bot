from discord.ext import commands
import discord
from pytube import YouTube
import io


class Convert(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client
        self.execute: callable = self.client.loop.run_in_executor

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def mp3(self, ctx: commands.Context, *, url):
        async with ctx.typing():

            def get_buffer():
                # Get audio stream
                audio_stream = YouTube(url).streams.get_audio_only()

                # Check file size
                if audio_stream.filesize_approx > 8_388_608:
                    return None

                # Download
                buffer = io.BytesIO()
                audio_stream.stream_to_buffer(buffer)
                buffer.seek(0)
                return buffer, audio_stream.title

            # Gets the buffer in separate thread
            if result := await self.execute(None, get_buffer):
                buffer, title = result
            else:
                # File too big
                await ctx.reply("File is over 8mb and cannot be sent.")

            try:
                await ctx.reply(file=discord.File(fp=buffer, filename=title + ".mp3"))

            # This shouldn't happen
            except discord.HTTPException:
                await ctx.reply("HTTP Error.")

            buffer.close()


def setup(client):
    client.add_cog(Convert(client))
