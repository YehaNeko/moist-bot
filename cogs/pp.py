import discord
from discord.ext import commands
import random


class Pp(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="pp")
    async def pp(self, ctx):
        msg_list = ["8"]

        for _ in range(random.randint(0, 200)):
            msg_list.append("=")

        msg_list.append("D")
        msg = "".join(msg_list)

        await ctx.reply(msg)


def setup(client):
    client.add_cog(Pp(client))
