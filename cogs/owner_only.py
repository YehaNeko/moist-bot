from __future__ import annotations

import discord
import discord.utils
from discord.ext import commands
from config import GUILD_OBJECT

import os
import logging
from yarl import URL
from typing import TYPE_CHECKING, Optional, Literal, Annotated

if TYPE_CHECKING:
    from main import MoistBot
    from utils.context import Context


logger = logging.getLogger('discord.' + __name__)


class OwnerOnly(commands.Cog):
    """Debug commands that only the bot owner can use"""

    def __init__(self, client: MoistBot):
        self.client: MoistBot = client
        self.last_ext = 'cmds'
        self._last_result: Optional[Any] = None
        self.sessions: set[int] = set()
        self.last_ext: str = 'cmds'

    async def cog_check(self, ctx: Context) -> bool:
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner('You do not own this bot.')
        return True

    @staticmethod
    def cleanup_code(content: str) -> str:
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @staticmethod
    def get_syntax_error(e: SyntaxError) -> str:
        if e.text is None:
            return f'```py\n{e.__class__.__name__}: {e}\n```'
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.is_owner()
    @commands.command(hidden=True)
    async def reload(self, ctx: Context, ext: Optional[str] = None):
        """Reload a cog."""

        # If not provided, use the last extension used
        if ext is None:
            ext = self.last_ext

        try:
            await self.client.reload_extension(f'cogs.{ext}')

        except (commands.ExtensionNotLoaded, commands.ExtensionNotFound):
            return await ctx.reply(":anger: specified cog name doesn't exits bozo")

        except commands.ExtensionFailed as e:
            msg = f'Reloading raised an exception: `{type(e.__class__)}`\n'
            logger.exception(msg, exc_info=e.__traceback__)
            return await ctx.reply(f':anger: {msg}\n`{e}`')

        await ctx.reply(f':repeat: Reloaded {ext}.')
        self.last_ext = ext

    @commands.is_owner()
    @commands.command(hidden=True)
    async def load(self, ctx: Context, ext: str):
        """Load a cog."""

        try:
            await self.client.load_extension(f'cogs.{ext}')

        except (commands.ExtensionAlreadyLoaded, commands.ExtensionNotFound):
            return await ctx.reply(":anger: specified cog is already loaded or doesn't exits bozo")

        except commands.ExtensionFailed as e:
            msg = f'Loading raised an exception: `{type(e.__class__)}`\n'
            logger.exception(msg, exc_info=e.__traceback__)
            return await ctx.reply(f':anger: {msg}\n`{e}`')

        await ctx.reply(f':white_check_mark: Loaded {ext}.')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def unload(self, ctx: Context, ext: str):
        """Unload a cog."""

        try:
            await self.client.unload_extension(f'cogs.{ext}')
        except (commands.ExtensionNotFound, commands.ExtensionNotLoaded):
            return await ctx.reply(":anger: specified cog name doesn't exits bozo")

        await ctx.reply(f':white_check_mark: Unloaded {ext}.')

    @commands.is_owner()
    @commands.group(hiddden=True)
    async def debug(self, ctx: Context):
        pass

    @debug.command(name='copyglobal', hidden=True)
    async def copy_global_to_test_guild(self, ctx: Context, resync: Optional[bool] = True):
        self.client.tree.copy_global_to(guild=GUILD_OBJECT)
        await ctx.reply(':white_check_mark: Copied global app commands to **test guild**')

        if resync:
            try:
                await self.client.tree.sync(guild=GUILD_OBJECT)
            except discord.DiscordException:
                logger.exception('Unable to sync application commands.')
                return await ctx.reply(':anger: Unable to sync application commands.')

            await ctx.invoke(self.sync_app_cmds, guild='guild')  # type: ignore

    @debug.command(name='unloadappcmd', hidden=True)
    async def unload_app_cmd(self, ctx: Context, cmd: str, resync: Optional[bool] = False):
        """Unload an application command."""
        unloaded = self.client.tree.remove_command(cmd)

        if resync:
            try:
                await self.client.tree.sync()
            except discord.DiscordException:
                logger.exception('Unable to sync application commands.')
                return await ctx.reply(':anger: Unable to sync application commands.')

            await ctx.reply(f':white_check_mark: Unloaded and re-synced `{unloaded}`.')
        else:
            await ctx.reply(f':white_check_mark: Unloaded `{unloaded}`.\n:warning: Re-sync is required.')

    @debug.command(name='syncappcmds', hidden=True)
    async def sync_app_cmds(self, ctx: Context, guild: Optional[Literal['guild', 'global']] = 'guild'):
        """Sync application commands."""

        place = ''
        if guild == 'global':
            guild = None
            place = 'global guilds'

        elif guild == 'guild':
            guild = GUILD_OBJECT
            place = 'current guild'

        try:
            synced = await self.client.tree.sync(guild=guild)
        except commands.CommandError:
            logger.exception('Unable to sync application commands.')
            return await ctx.reply(':anger: Unable to sync application commands.')

        fmt = '\n'.join(repr(cmd) for cmd in synced) if synced else 'None'
        await ctx.reply(f':white_check_mark: Synced in **{place}**:\n`{fmt}`')

    @debug.command(name='getappcmds', hidden=True)
    async def get_app_cmds(self, ctx: Context, guild: Optional[Literal['guild', 'global']] = 'guild'):
        """Fetch currently registered application commands."""

        place = ''
        if guild == 'global':
            guild = None
            place = 'global guilds'

        elif guild == 'guild':
            guild = GUILD_OBJECT
            place = 'current guild'

        cmds = await self.client.tree.fetch_commands(guild=guild)

        fmt = '\n'.join(repr(cmd) for cmd in cmds) if cmds else 'None'
        await ctx.reply(f':white_check_mark: Fetched {len(cmds)} command(s) in **{place}**:\n`{fmt}`')

    @debug.command(hidden=True)
    async def clear(self, ctx: Context):
        os.system('cls||clear')
        await ctx.message.add_reaction('✅')
        logger.info('Console cleared.')

    @commands.guild_only()
    @debug.command(hidden=True)
    async def give_role(
        self,
        ctx: Context,
        role: discord.Role,
        *,
        member: Optional[discord.Member] = commands.Author,
    ):
        """Give someone a role."""

        try:
            await member.add_roles(role)
        except discord.Forbidden:
            return await ctx.reply(':no_entry: lol I dont have the perms for that xd')

        await ctx.reply(f':white_check_mark: Successfully given role `{role.name}` to `{member}`')

    @debug.group(hidden=True)
    async def emoji(self, _ctx: Context):
        pass

    @emoji.command()
    async def add(self, ctx: Context, alias: str, emoji_link: Annotated[str, URL]):
        """Create a custom Emoji for the guild."""
        emoji: bytes = await self.client.http.get_from_cdn(emoji_link)
        await ctx.guild.create_custom_emoji(name=alias, image=emoji)
        await ctx.reply(f':white_check_mark: Added emoji :{alias}:')

    @add.error
    async def on_error(self, ctx: Context, error: discord.DiscordException):
        error = getattr(error, 'original', error)

        if isinstance(error, discord.Forbidden):
            await ctx.reply(':no_entry: lol I dont have the perms for that xd')

        elif isinstance(error, discord.HTTPException):
            logger.exception('Unable to add emoji', exc_info=error.__traceback__)
            await ctx.reply(':warning: Unable to resolve emoji')

        else:
            logger.exception('Unable to add emoji', exc_info=error.__traceback__)
            await ctx.reply(":no_entry: I can't do that :(")

    @emoji.command(aliases=['del', 'delete'])
    async def remove(self, ctx: Context, alias: str):
        """Delete a custom Emoji from the guild"""
        # error handling? never heard of it :3
        emoji = discord.utils.get(ctx.guild.emojis, name=alias)
        await ctx.guild.delete_emoji(emoji)
        await ctx.reply(':white_check_mark: Deleted emoji.')


async def setup(client: MoistBot):
    await client.add_cog(OwnerOnly(client))
