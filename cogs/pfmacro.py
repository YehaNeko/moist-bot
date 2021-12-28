import discord
from discord.ext import commands
import os


class Pfmacro(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(enabled=False)
    async def pfmacrotest(self, ctx, rpm, shots):

        with open("macro.ahk", "w") as f:
            f.write(f"test\n"
                    f"rpm is {rpm}\n"
                    f"shots is {shots}"
                    )

        await ctx.reply(file=discord.File("macro.ahk"))
        os.remove("macro.ahk")


def setup(client):
    client.add_cog(Pfmacro(client))
