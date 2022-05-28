import discord
from discord.ext import commands
from discord import ui

import asyncio


class PromptTest(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(hidden=True, aliases=["prompt", "test"])
    @commands.is_owner()
    async def prompt_test(self, ctx: commands.Context):
        await asyncio.sleep(10)
        await ctx.reply("Done.")


async def setup(client):
    await client.add_cog(PromptTest(client))
