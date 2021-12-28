import discord
from discord.ext import commands
import json
import os

with open(r"./functions/SheetToJson/output_advinfosheet.json", 'r') as f:
    data = json.load(f)


class Pfsheettest(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(hidden=True, enabled=False)
    async def pfsheettest(self, ctx, *gun: str):

        gun = "".join(gun)
        key = gun.replace("-", "").replace(" ", "").upper()
        values = data["data"][key]

        """ Create embed """
        embed = discord.Embed(title="test", url="https://docs.google.com/spreadsheets/d/1TRQbmrl8HOilGz2ZVTgbQy_lm6c8gIE6hwT-A33Y_SY/", color=discord.Colour.random())
        embed.set_footer(text=embed.timestamp)
        embed.set_author(
            name="Requested by " + ctx.author.display_name,
            icon_url=ctx.author.avatar
        )

        embed.add_field(name="Gun", value=values["PRIMARIES"], inline=True)
        embed.add_field(name="Base damage", value=values["BASE DAMAGE"], inline=True)

        await ctx.reply(embed=embed)


def setup(client):
    client.add_cog(Pfsheettest(client))
