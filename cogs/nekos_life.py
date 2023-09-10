from __future__ import annotations

import discord
from discord.ext import commands
from discord.utils import escape_mentions

import nekos
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main import MoistBot
    from utils.context import Context


class MediaEmbed(discord.Embed):
    def __init__(self, ctx: Context, url: str, **kwargs):
        command = ctx.command.name.replace('_', ' ')
        author = ctx.author

        super().__init__(
            color=author.accent_color or author.color,
            **kwargs
        )

        user = ctx.args[1]
        print(ctx.kwargs, user, sep='\n')
        if user is not None:
            fmt = f'{author.display_name} sends {command}s to {user.display_name}!'
        else:
            fmt = f'{author.display_name}\'s {command}'

        self.set_author(
            icon_url=author.display_avatar,
            name=fmt,
        ).set_image(
            url=url
        )


# The predicate taken from `commands.is_nsfw()`
def is_nsfw(ctx: Context) -> bool:
    ch = ctx.channel
    if ctx.guild is None or (
        isinstance(ch, (discord.TextChannel, discord.Thread, discord.VoiceChannel)) and ch.is_nsfw()
    ):
        return True
    raise commands.NSFWChannelRequired(ch)


async def _get_data(ctx: Context, *args, func_name: Optional[str] = None) -> str:
    """Generic callback for `neko` command."""
    if func_name is not None:
        cmd = func_name
        args = (ctx.command.name, )
    else:
        cmd = ctx.command.name

    data = await ctx.bot.loop.run_in_executor(None, getattr(nekos, cmd), *args)
    return data


async def _neko_img_callback(ctx: Context, user: Optional[discord.Member] = None):
    """Generic callback for `nekos.img()` function."""
    url = await _get_data(ctx, func_name='img')
    await ctx.reply(embed=MediaEmbed(ctx, url))


async def _neko_endpoint_callback(ctx: Context):
    """Generic callback for `nekos` functions."""
    data = await _get_data(ctx)
    await ctx.reply(data)


class Neko(commands.Cog):
    """Get images from the `nekos.life` api!"""

    # All possible entries for `img` endpoint
    img_entries = {
        'wallpaper',
        'ngif',
        'tickle',
        'feed',
        'gecg',
        'gasm',
        'slap',
        'avatar',
        'lizard',
        'waifu',
        'pat',
        '8ball',
        'neko',
        'cuddle',
        'fox_girl',
        'hug',
        'smug',
        'goose',
        'woof',
        # 'lewd'  # Unused
    }
    nsfw_img_entries = {'kiss', 'spank'}
    endpoint_entries = {
        ('textcat', 'Get a cat kaomoji.'),
        ('why', 'Why?'),
        ('name', 'Get a random name.'),
        ('cat', 'Meow.'),
        ('fact', 'Did you know...?'),
    }

    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

        # Create `nekos.img()` commands
        self.cmds = [
            commands.Command(_neko_img_callback, name=e, cog=self, brief=f'Get an image of type `{e}`.')
            for e in self.img_entries
        ]

        # Create `nekos` commands
        for entry, brief in self.endpoint_entries:
            self.cmds.append(
                commands.Command(_neko_endpoint_callback, name=entry, cog=self, brief=brief),
            )

        # Create nsfw `nekos.img()` commands
        for e in self.nsfw_img_entries:
            self.cmds.append(
                commands.Command(
                    _neko_img_callback,
                    name=e,
                    cog=self,
                    checks=[is_nsfw],
                    brief=f'Get an image of type `{e}`.\n **NSFW only.**',
                )
            )

        # Bulk register commands
        for cmd in self.cmds:
            self.neko.add_command(cmd)

    @property
    def display_emoji(self) -> discord.PartialEmoji:
        return discord.PartialEmoji(name='\U0001f43e')

    @commands.cooldown(rate=1, per=1, type=commands.BucketType.user)
    @commands.group()
    async def neko(self, ctx: Context):
        """Get images from the `nekos.life` api!"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @neko.command()
    async def owoify(self, ctx: Context, *, text: str):
        """Input text to be owofied!"""
        data = await _get_data(ctx, escape_mentions(text))
        await ctx.reply(data)

    @neko.command()
    async def spoiler(self, ctx: Context, *, text: str):
        """Input text to be spoiled per letter!"""
        data = await _get_data(ctx, escape_mentions(text))
        await ctx.reply(data)


async def setup(client: MoistBot):
    await client.add_cog(Neko(client))
