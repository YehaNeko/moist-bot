import discord
from discord.ext import commands

import datetime


class AvatarEmbed(discord.Embed):
    def __init__(self, has_guild_avatar: bool = False):
        super().__init__(
            type="image",
            color=discord.Color.random(),
            timestamp=datetime.datetime.utcnow() if not has_guild_avatar else None,
        )


class Avatar(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def avatar(self, ctx: commands.Context, *, user: str = None):
        """ Display a user's avatar. """
        user = await commands.MemberConverter().convert(ctx, user) if user else ctx.author

        embeds = []
        avatar_url = user.guild_avatar.url if (has_guild_avatar := hasattr(user, "guild_avatar")) else user.avatar.url

        # First embed
        embed = AvatarEmbed(has_guild_avatar)\
            .set_author(
            name=user.display_name + "'s avatar",
            url=avatar_url
        )\
            .set_image(
            url=avatar_url
        )

        embeds.append(embed)

        # Second embed
        if has_guild_avatar:
            avatar_url = user.avatar.url  # Get base avatar
            embed2 = AvatarEmbed()\
                .set_author(
                name=user.display_name + "'s base avatar",
                url=avatar_url
            )\
                .set_image(
                url=avatar_url
            )

            embeds.append(embed2)

        # Send embeds
        await ctx.reply(embeds=embeds)


async def setup(client):
    await client.add_cog(Avatar(client))
