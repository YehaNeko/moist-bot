from __future__ import annotations

import discord
from discord.ext import commands

from random import randint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import MoistBot
    from cogs.utils.context import Context


class Pp(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

        self.rigged = [
            150560836971266048,
            311184299623972864,
            1022178996827455498,
        ]

    @commands.command()
    async def pp(self, ctx: Context, *, user: discord.User = commands.Author):
        """Measure your pp."""

        # NOT RIGGED
        size = randint(0, 30) if user.id not in self.rigged else randint(200, 500)
        peepee = '8' + '='*size + 'D'

        embed = discord.Embed(
            color=discord.Color.magenta(),
        ).set_author(
            name=user.display_name + '\'s pp',
            icon_url=user.display_avatar.url
        ).add_field(
            name=f'{size}cm long',
            value=peepee
        )

        await ctx.reply(embed=embed)


async def setup(client: MoistBot) -> None:
    await client.add_cog(Pp(client))
