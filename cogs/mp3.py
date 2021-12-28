from discord.ext import commands
import discord
from pytube import YouTube
import os


class Convert(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def mp3(self, ctx, *, url):
        with ctx.typing():

            url = YouTube(url)

            filename = str(url.streams.get_audio_only().download())
            filepath_edited = filename.removesuffix(".mp4") + ".mp3"

            os.rename(filename, filepath_edited)
            try:
                await ctx.reply(file=discord.File(filepath_edited))

            except discord.HTTPException:
                await ctx.reply("File too big.")

        os.remove(filepath_edited)


def setup(client):
    client.add_cog(Convert(client))
