from __future__ import annotations

import discord
from discord.ext import commands

import nekos
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import MoistBot
    from utils.context import Context


async def _neko_img_callback(ctx: Context):
    """Generic callback for `nekos.img()` function."""
    t = ctx.command.name
    img = await ctx.bot.loop.run_in_executor(None, nekos.img, t)
    await ctx.reply(img)


class Neko(commands.Cog):
    """Get images from the `nekos.life` api!"""

    # All possible entries for `img` endpoint
    entries = {
        "wallpaper",
        "ngif",
        "tickle",
        "feed",
        "gecg",
        "gasm",
        "slap",
        "avatar",
        "lizard",
        "waifu",
        "pat",
        "8ball",
        "kiss",
        "neko",
        "spank",
        "cuddle",
        "fox_girl",
        "hug",
        "smug",
        "goose",
        "woof",
        # 'lewd', Provides 1 image
    }

    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

        # Bulk register commands for `img` endpoint
        for entry in self.entries:
            self.neko.add_command(
                commands.Command(
                    _neko_img_callback,
                    name=entry,
                    cog=self,
                    parent=self.neko,
                    brief=f"Get an image of type `{entry}`.",
                )
            )

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f43e')

    @staticmethod
    async def _neko_callback(ctx: Context, *args) -> None:
        """Generic callback for `neko` command."""
        data = await ctx.bot.loop.run_in_executor(
            None, getattr(nekos, ctx.command.name), *args
        )
        await ctx.reply(data)

    @commands.group()
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.user)
    async def neko(self, ctx: Context):
        """Get images from the `nekos.life` api!"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @neko.command(rest_is_raw=True)
    async def owoify(self, ctx: Context, *, text: str):
        """Input text to be owofied!"""
        await self._neko_callback(ctx, text)

    @neko.command(rest_is_raw=True)
    async def spoiler(self, ctx: Context, *, text: str):
        """Input text to be spoiled per letter!"""
        await self._neko_callback(ctx, text)

    @neko.command()
    async def cat(self, ctx: Context):
        """Get an image of type `cat`."""
        await self._neko_callback(ctx)

    @neko.command()
    async def textcat(self, ctx: Context):
        """Get a cat kaomoji."""
        await self._neko_callback(ctx)

    @neko.command()
    async def why(self, ctx: Context):
        """Why?"""
        await self._neko_callback(ctx)

    @neko.command()
    async def fact(self, ctx: Context):
        """Did you know...?"""
        await self._neko_callback(ctx)

    @neko.command()
    async def name(self, ctx: Context):
        """Get a random name."""
        await self._neko_callback(ctx)


async def setup(client: MoistBot):
    await client.add_cog(Neko(client))
