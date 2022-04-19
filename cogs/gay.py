import discord
from discord.ext import commands
from PIL import Image
import os
import io
overlay = Image.open("./assets/pride.png")
overlay = overlay.convert("RGBA")


class Gay(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def gay(self, ctx, user: str = None, opacity: str = None):
        """
        Show your gay pride!

        Totally doesn't rip off dank memer.
        """

        # Parse arguments
        try:
            user_conv = await commands.MemberConverter().convert(ctx, user)
        except commands.MemberNotFound:
            user_conv = ctx.author
            if opacity is None:
                opacity = float(user.strip("%")) / 100
        except TypeError:
            user_conv = ctx.author

        if isinstance(opacity, str):
            opacity = float(opacity.strip("%")) / 100
        elif opacity is None:
            opacity = 0.4

        img = await user_conv.avatar.read()

        # Image stuff uwu
        img = Image.open(io.BytesIO(img))
        img = img.convert("RGBA")

        global overlay
        overlay_sized = overlay.resize(img.size, Image.BICUBIC)

        blend = Image.blend(img, overlay_sized, opacity)
        blend.save("./assets/img.png", "PNG")

        # Send image
        await ctx.reply(file=discord.File("./assets/img.png"))
        os.remove("./assets/img.png")


async def setup(client):
    await client.add_cog(Gay(client))
