from __future__ import annotations

import discord
from discord.ext import commands

import os
import io
from PIL import Image
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import MoistBot
    from cogs.utils.context import Context


overlay = Image.open('./assets/pride.png').convert('RGBA')


class Gay(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

    @commands.command()
    async def gay(self, ctx: Context, user: str = None, opacity: str = None):
        """Show your gay pride!

        Totally doesn't rip off dank memer.
        """

        # Parse arguments
        try:
            user_conv = await commands.MemberConverter().convert(ctx, user)
        except commands.MemberNotFound:
            user_conv = ctx.author
            if opacity is None:
                opacity = float(user.strip('%')) / 100
        except TypeError:
            user_conv = ctx.author

        if isinstance(opacity, str):
            opacity = float(opacity.strip('%')) / 100
        elif opacity is None:
            opacity = 0.4

        img = await user_conv.avatar.read()

        # Image stuff uwu
        img = Image.open(io.BytesIO(img))
        img = img.convert('RGBA')

        global overlay
        overlay_sized = overlay.resize(img.size, Image.BICUBIC)

        blend = Image.blend(img, overlay_sized, opacity)
        blend.save('./assets/img.png', 'PNG')

        # Send image
        await ctx.reply(file=discord.File('./assets/img.png'))
        os.remove('./assets/img.png')


async def setup(client: MoistBot) -> None:
    await client.add_cog(Gay(client))
