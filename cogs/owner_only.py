from __future__ import annotations

import discord
import discord.utils
from discord.ext import commands
from config import GUILD_OBJECT

import io
import os
import asyncio
import inspect
import logging
import textwrap
import traceback
from yarl import URL
from contextlib import redirect_stdout
from typing import TYPE_CHECKING, Optional, Literal, Annotated, Any

# Extra imports for eval command
import math
import time
import datetime

if TYPE_CHECKING:
    from main import MoistBot
    from utils.context import Context


logger = logging.getLogger('discord.' + __name__)
# noinspection PyBroadException


class OwnerOnly(commands.Cog):
    """Debug commands that only the bot owner can use"""

    def __init__(self, client: MoistBot):
        self.client: MoistBot = client
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
            await ctx.reply(f':anger: {msg}\n`{e}`')
            return

        await ctx.reply(f':repeat: Reloaded {ext}.')
        self.last_ext = ext

    @commands.is_owner()
    @commands.command(hidden=True)
    async def load(self, ctx: Context, ext: str):
        """Load a cog."""

        try:
            await self.client.load_extension(f'cogs.{ext}')

        except (commands.ExtensionAlreadyLoaded, commands.ExtensionNotFound):
            await ctx.reply(":anger: specified cog is already loaded or doesn't exits bozo")
            return

        except commands.ExtensionFailed as e:
            msg = f'Loading raised an exception: `{type(e.__class__)}`\n'
            logger.exception(msg, exc_info=e.__traceback__)
            await ctx.reply(f':anger: {msg}\n`{e}`')
            return

        await ctx.reply(f':white_check_mark: Loaded {ext}.')

    @commands.is_owner()
    @commands.command(hidden=True)
    async def unload(self, ctx: Context, ext: str):
        """Unload a cog."""

        try:
            await self.client.unload_extension(f'cogs.{ext}')
        except (commands.ExtensionNotFound, commands.ExtensionNotLoaded):
            await ctx.reply(":anger: specified cog name doesn't exits bozo")
            return

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
                await ctx.reply(':anger: Unable to sync application commands.')
                return

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
                await ctx.reply(':anger: Unable to sync application commands.')
                return

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
            await ctx.reply(':anger: Unable to sync application commands.')
            return

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
            await ctx.reply(':no_entry: lol I dont have the perms for that xd')
            return

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

    @commands.command(hidden=True, name='eval')
    async def _eval(self, ctx: Context, *, body: str):
        """Evaluates a code"""

        """
        I'm sorry but this was way too cool not to yoink :3
        https://github.com/Rapptz/RoboDanny/blob/a52a212d1fff1024fb00c14b9e125071f87e0323/cogs/admin.py#L215C31-L215C31
        """

        env = {
            'client': self.client,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result,
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except Exception:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command(hidden=True)
    async def repl(self, ctx: Context):
        """Launches an interactive REPL session."""

        """
        This is so cool I couldn't resist qwq
        https://github.com/Rapptz/RoboDanny/blob/a52a212d1fff1024fb00c14b9e125071f87e0323/cogs/admin.py#L262
        """

        variables = {
            'ctx': ctx,
            'client': self.client,
            'message': ctx.message,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            '_': None,
        }

        if ctx.channel.id in self.sessions:
            await ctx.send('Already running a REPL session in this channel. Exit it with `quit`.')
            return

        self.sessions.add(ctx.channel.id)
        await ctx.send('Enter code to execute or evaluate. `exit()` or `quit` to exit.')

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content.startswith('`')

        while True:
            try:
                response = await self.client.wait_for('message', check=check, timeout=10.0 * 60.0)
            except asyncio.TimeoutError:
                await ctx.send('Exiting REPL session.')
                self.sessions.remove(ctx.channel.id)
                break

            cleaned = self.cleanup_code(response.content)

            if cleaned in ('quit', 'exit', 'exit()'):
                await ctx.send('Exiting.')
                self.sessions.remove(ctx.channel.id)
                return

            executor = exec
            code = ''
            if cleaned.count('\n') == 0:
                # single statement, potentially 'eval'
                try:
                    code = compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as e:
                    await ctx.send(self.get_syntax_error(e))
                    continue

            variables['message'] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception as e:
                value = stdout.getvalue()
                fmt = f'```py\n{value}{traceback.format_exc()}\n```'
            else:
                value = stdout.getvalue()
                if result is not None:
                    fmt = f'```py\n{value}{result}\n```'
                    variables['_'] = result
                elif value:
                    fmt = f'```py\n{value}\n```'

            try:
                if fmt is not None:
                    if len(fmt) > 2000:
                        await ctx.send('Content too big to be printed.')
                    else:
                        await ctx.send(fmt)
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                await ctx.send(f'Unexpected error: `{e}`')


async def setup(client: MoistBot) -> None:
    await client.add_cog(OwnerOnly(client))
