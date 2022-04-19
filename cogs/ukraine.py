from discord.ext import commands
import discord

import io
from typing import Union
from PIL import Image, ImageDraw, ImageFilter

FLAG_UA = Image.open("./assets/Ukraine flag.png").convert("RGBA")


class ImageGen:
    def __init__(self, avatar: Image.Image, ring: Union[int, float] = 7,  upscale: int = 4):
        self.avatar = avatar
        self.flag_ua = FLAG_UA.copy()
        self.RING = ring
        self.UPSCALE = upscale

        # Original resolution
        self.width, self.height = self.avatar.size
        self.ring_w, self.ring_h = (self.width * self.RING) / 100, (self.height * self.RING) / 100  # Ring bounds

        # Upscaled resolution to smooth ellipse mask
        self.u_width, self.u_height = self.width * self.UPSCALE, self.height * self.UPSCALE
        self.u_ring_w, self.u_ring_h = (self.u_width * self.RING) / 100, (self.u_height * self.RING) / 100  # Ring bounds

        # Rounded
        self.r_ring_w, self.r_ring_h = round(self.ring_w), round(self.ring_h)
        self.r_width, self.r_height = (self.width - self.r_ring_w), (self.height - self.r_ring_h)

        # Upscaled rounded
        self.s_width, self.s_height = (self.r_width * self.UPSCALE), (self.r_height * self.UPSCALE)

        # Resize if needed
        if self.avatar.size != self.flag_ua.size:
            self.flag_ua = self.flag_ua.resize(self.avatar.size, Image.BICUBIC)

    def gen_mask(self, descale: Union[int, float] = 0) -> Image.Image:
        """ Generate a smooth ellipse mask """

        # Upscaled ellipse mask
        mask = Image.new("L", (self.s_width, self.s_height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0 + descale, 0 + descale, self.s_width - descale, self.s_height - descale), fill=255)

        mask = mask.resize((self.r_width, self.r_height), Image.BICUBIC)  # Downscale to smooth ellipse mask
        mask = mask.filter(ImageFilter.SMOOTH)  # Smooth edges
        return mask

    def proportional(self) -> Image.Image:
        """ Proportional ring generator """

        masked_avatar = Image.new("RGBA", (self.r_width, self.r_height), (255, 255, 255, 0))
        avatar = self.avatar.resize((self.r_width, self.r_height), Image.LANCZOS)
        masked_avatar = Image.composite(avatar, masked_avatar, mask=self.gen_mask())

        self.flag_ua.paste(masked_avatar, box=(round(self.ring_w / 2), round(self.ring_h / 2)),
                           mask=self.gen_mask(4))

        return self.flag_ua

    def subtractive(self) -> Image.Image:
        """ Subtractive ring generator """

        # Circle mask for the avatar
        mask = Image.new("L", (self.u_width, self.u_height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((self.u_ring_w, self.u_ring_h, self.u_height - self.u_ring_w, self.u_height - self.u_ring_h),
                     fill=255)

        # Downscale to smooth ellipse mask
        mask = mask.resize(self.avatar.size, Image.LANCZOS)
        mask = mask.filter(ImageFilter.SMOOTH)  # Smooth edges

        img = Image.composite(self.avatar, self.flag_ua, mask)
        return img


class Ukraine(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.execute = self.client.loop.run_in_executor

    # Method called by discord.py
    async def cog_command_error(self, ctx: commands.Context,  error):
        if isinstance(error, commands.MemberNotFound):
            await ctx.reply(f"User `{error.argument}` not found")

    @staticmethod
    def _get_buffer(avatar) -> io.BytesIO:
        buffer = io.BytesIO()
        img = ImageGen(avatar).proportional()
        img.save(buffer, "png")
        buffer.seek(0)
        return buffer

    @commands.command(enabled=True)
    async def ukraine(self, ctx: commands.Context, *, user: str = None):
        async with ctx.typing():
            user = await commands.MemberConverter().convert(ctx, user) if user else ctx.author
            try:
                # Get avatar
                avatar = await user.display_avatar.with_format("png").with_size(2048).read()
                avatar = Image.open(io.BytesIO(avatar))

                # Avoid blocking
                img_buffer = await self.execute(None, self._get_buffer, avatar)

                # Send image
                await ctx.reply(file=discord.File(fp=img_buffer, filename="image.png"))

            finally:
                img_buffer.close()
                avatar.close()


async def setup(client):
    await client.add_cog(Ukraine(client))
