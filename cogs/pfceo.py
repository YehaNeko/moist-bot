import discord
from discord.ext import commands

import json
import datetime

with open(r"./functions/SheetToJson/output.json", 'r') as f:
    data = json.load(f)


class Pfceo(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def pfceo(self, ctx, *, gun: str):
        key = gun.replace("-", "").replace(" ", "").upper()
        values = data["data"][key]

        """ Create embed """
        embed = discord.Embed(
            title=values["WEAPONS"],
            url="https://docs.google.com/spreadsheets/d/1TRQbmrl8HOilGz2ZVTgbQy_lm6c8gIE6hwT-A33Y_SY/",
            color=discord.Colour.random(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(
            name="Requested by " + ctx.author.display_name,
            icon_url=ctx.author.avatar
        )

        embed.add_field(name="Roblox username   ", value=values["ROBLOX"], inline=True)
        embed.add_field(name="Discord", value=values["DISCORD"], inline=True)
        embed.add_field(name="Kills", value=values["KILLS"], inline=False)
        embed.add_field(name="Last Updated", value=values["LAST UPDATED"], inline=True)
        embed.add_field(name="Updated by", value=values["UPDATED BY"], inline=True)

        await ctx.reply(embed=embed)


async def setup(client):
    await client.add_cog(Pfceo(client))
