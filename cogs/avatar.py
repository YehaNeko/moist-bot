from __future__ import annotations

import discord
from discord.ext import commands
from typing import TYPE_CHECKING, Annotated, Union

if TYPE_CHECKING:
    from main import MoistBot

class AvatarEmbed(discord.Embed):
    def __init__(
        self,
        avatar_url: str,
        user: Union[discord.User, discord.Member],
        *,
        source: str = 'base'
    ):
        super().__init__(
            type='image',
            color=discord.Color.random(),
        )
        self.set_image(url=avatar_url)
        self.set_author(
            name="%s's %s avatar" % (user.display_name, source),
            url=avatar_url,
            icon_url=avatar_url
        )


class Avatar(commands.Cog):
    def __init__(self, client):
        self.client: MoistBot = client

    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @commands.command()
    async def avatar(
        self,
        ctx: commands.Context,
        *,
        user: Annotated[Union[discord.User, discord.Member], commands.MemberConverter] = commands.Author
    ):
        """Display a user's avatar."""

        has_ga: bool = hasattr(user, 'guild_avatar') and user.guild_avatar
        embeds: list[discord.Embed] = []

        # user: discord.Member
        # Second embed with guild avatar (if exists)
        if has_ga:
            avatar_url = user.guild_avatar.url
            embed_guild = AvatarEmbed(avatar_url, user, source='guild')
            embeds.append(embed_guild)

        # First embed with base avatar
        avatar_url = user.avatar.url
        embed_base = AvatarEmbed(avatar_url, user)
        embeds.insert(0, embed_base)

        # Send embeds
        await ctx.reply(embeds=embeds)


async def setup(client: MoistBot):
    await client.add_cog(Avatar(client))
