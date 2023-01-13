from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands
from config import GUILD_OBJECT

import io
from typing import Union, Tuple, Optional, TYPE_CHECKING
from PIL import Image, ImageDraw, ImageFilter

if TYPE_CHECKING:
    from main import MoistBot

FLAG_UA = Image.open("./assets/Ukraine flag.png").convert("RGBA")


class ImageGen:
    def __init__(self, avatar: Image.Image, ring: Union[int, float] = 7, upscale: int = 4):
        self.avatar: Image.Image = avatar
        self.flag_ua: Image.Image = FLAG_UA.copy()
        self.RING: Union[int, float] = ring
        self.UPSCALE: int = upscale

        # Original resolution
        self.width, self.height = self.avatar.size
        self.ring_w, self.ring_h = (self.width * self.RING) / 100, (self.height * self.RING) / 100  # Ring bounds

        # Upscaled resolution to smooth ellipse mask
        self.u_width, self.u_height = self.width * self.UPSCALE, self.height * self.UPSCALE
        self.u_ring_w, self.u_ring_h = (self.u_width * self.RING) / 100, (self.u_height * self.RING) / 100
        # Ring bounds

        # Rounded
        self.r_ring_w, self.r_ring_h = round(self.ring_w), round(self.ring_h)
        self.r_width, self.r_height = (self.width - self.r_ring_w), (self.height - self.r_ring_h)

        # Upscale rounded
        self.ru_width, self.ru_height = (self.r_width * self.UPSCALE), (self.r_height * self.UPSCALE)

        # Resize if needed
        if self.flag_ua.size != self.avatar.size:
            self.flag_ua = self.flag_ua.resize(self.avatar.size, Image.BICUBIC)

    @staticmethod
    def _gen_mask(
            *,
            start_size: Tuple[int, int],
            x1y1: Tuple[int, int],
            x2y2: Tuple[int, int],
            final_size: Tuple[int, int],
            descale: Optional[Union[int, float]] = 0
    ) -> Image.Image:
        """Generate a smooth ellipse mask"""

        # Upscaled ellipse mask
        mask = Image.new("L", start_size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((x1y1[0] + descale, x1y1[1] + descale, x2y2[0] - descale, x2y2[1] - descale), fill=255)

        mask = mask.resize(final_size, Image.BICUBIC)  # Downscale to smooth ellipse mask
        mask = mask.filter(ImageFilter.SMOOTH)  # Smooth edges
        return mask

    def proportional(self) -> Image.Image:
        """Proportional ring generator"""

        masked_avatar = Image.new("RGBA", (self.r_width, self.r_height), (255, 255, 255, 0))
        avatar = self.avatar.resize((self.r_width, self.r_height), Image.LANCZOS)

        masked_avatar = Image.composite(
            avatar,
            masked_avatar,
            mask=self._gen_mask(
                start_size=(self.ru_width, self.ru_height),
                x1y1=(0, 0),
                x2y2=(self.ru_width, self.ru_width),
                final_size=(self.r_width, self.r_height)
            )
        )

        self.flag_ua.paste(
            masked_avatar,
            box=(round(self.ring_w / 2), round(self.ring_h / 2)),
            mask=self._gen_mask(
                start_size=(self.ru_width, self.ru_height),
                x1y1=(0, 0),
                x2y2=(self.ru_width, self.ru_width),
                final_size=(self.r_width, self.r_height),
                descale=4
            )
        )

        return self.flag_ua

    def subtractive(self) -> Image.Image:
        """Subtractive ring generator"""

        img = Image.composite(
            self.avatar,
            self.flag_ua,
            mask=self._gen_mask(
                start_size=(self.u_width, self.u_height),
                x1y1=(self.u_ring_w, self.u_ring_h),
                x2y2=(self.u_height - self.u_ring_w, self.u_height - self.u_ring_h),
                final_size=self.avatar.size
            )
        )
        return img


class Ukraine(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot = client
        self.execute = self.client.loop.run_in_executor

    # # Method called by discord.py
    # async def cog_command_error(self, ctx: commands.Context, error):
    #     pass

    @staticmethod
    def _get_buffer(avatar) -> io.BytesIO:
        buffer = io.BytesIO()
        img = ImageGen(avatar).proportional()
        img.save(buffer, "png")
        buffer.seek(0)
        return buffer

    @commands.hybrid_command()
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.describe(user="Optionally select a user")
    async def ukraine(self, ctx: commands.Context, *, user: discord.User = commands.Author):
        """Generates a Ukrainian colored ring border around someone's avatar"""

        async with ctx.typing():
            try:
                # Get avatar
                avatar: bytes = await user.display_avatar.with_format("png").with_size(2048).read()
                avatar: Image.Image = Image.open(io.BytesIO(avatar))

                # Avoid blocking TODO: should probably use some form of multiprocessing instead
                img_buffer = await self.execute(None, self._get_buffer, avatar)

                # Send image
                await ctx.reply(file=discord.File(fp=img_buffer, filename="image.png"))

            finally:
                # Free memory
                img_buffer.close()
                avatar.close()
                del img_buffer, avatar


async def setup(client):
    await client.add_cog(Ukraine(client))


async def teardown(client):
    client.tree.remove_command('ukraine')
