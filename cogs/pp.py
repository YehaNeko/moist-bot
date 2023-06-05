import discord
from discord.ext import commands

from random import randint


class Pp(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def pp(self, ctx, *, user = None):
        """ Measure your pp. """
        user: discord.Member = await commands.MemberConverter().convert(ctx, user) if user else ctx.author

        embed = discord.Embed(
            color=discord.Color.magenta(),
        )
        embed.set_author(
            name=user.display_name + "'s pp",
            icon_url=user.display_avatar.url
        )

        # NOT RIGGED
        rigged = [150560836971266048, 311184299623972864, 1022178996827455498, ]
        size = randint(0, 30) if user.id not in rigged else randint(200, 500)

        peepee = "8" + "="*size + "D"
        embed.add_field(name=f"{size}cm long", value=peepee)

        await ctx.reply(embed=embed)


async def setup(client):
    await client.add_cog(Pp(client))
