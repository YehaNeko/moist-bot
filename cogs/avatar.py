from __future__ import annotations

import discord
from discord.ext import commands
from typing import TYPE_CHECKING, Annotated, Union

if TYPE_CHECKING:
    from main import MoistBot
    from utils.context import Context


class AvatarEmbed(discord.Embed):
    def __init__(
        self,
        avatar_url: str,
        user: Union[discord.User, discord.Member],
        *,
        source: str = 'base',
    ):
        super().__init__(type='image', color=discord.Color.random())
        self.set_image(url=avatar_url)
        self.set_author(
            name=f'{user.display_name}\'s {source} avatar',
            url=avatar_url,
            icon_url=avatar_url,
        )


class Avatar(commands.Cog):
    def __init__(self, client):
        self.client: MoistBot = client

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f465')

    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @commands.command()
    async def avatar(
        self,
        ctx: commands.Context,
        *,
        user: Annotated[Union[discord.User, discord.Member], commands.MemberConverter] = commands.Author,
    ):
        """Display a user's avatar."""

        # user: discord.Member
        embeds: list[discord.Embed] = []

        # First embed with base avatar
        avatar_url = user.avatar.url
        embed = AvatarEmbed(avatar_url, user)
        embeds.append(embed)

        # Second embed with guild avatar (if exists)
        has_ga: bool = hasattr(user, 'guild_avatar') and user.guild_avatar
        if has_ga:
            avatar_url = user.guild_avatar.url
            embed = AvatarEmbed(avatar_url, user, source='guild')
            embeds.append(embed)

        # Send embeds
        await ctx.reply(embeds=embeds)


async def setup(client: MoistBot):
    await client.add_cog(Avatar(client))
