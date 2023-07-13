from __future__ import annotations

import discord
from discord.ext import commands
import discord.utils
from config import GUILD_OBJECT

import os
import logging
from typing import TYPE_CHECKING, Optional, Literal, Annotated

if TYPE_CHECKING:
    from main import MoistBot


logger = logging.getLogger('discord.' + __name__)

class OwnerOnly(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot= client

    async def cog_check(self, ctx: commands.Context) -> bool:
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner('You do not own this bot.')
        return True

    @commands.is_owner()
    @commands.command(hidden=True)
    async def reload(self, ctx: commands.Context, ext: str = 'cmds'):
        await self.client.reload_extension(f'cogs.{ext}')
        await ctx.reply(f':repeat: Reloaded {ext}.')

    @reload.error
    async def on_error(self, ctx, error: commands.CommandError):
        if isinstance(getattr(error, 'original', error), (commands.ExtensionNotLoaded, commands.ExtensionNotFound)):
            await ctx.reply(":anger: Idiot, isn't a cog.")
        else:
            logger.exception(f'Reloading raised an exception: `{type(error.__class__)}`\n', exc_info=error.__traceback__)
            await ctx.reply(f':anger: Reloading raised an exception: `{type(error.__class__)}`\n'
                            f"'{error}'")

    @commands.is_owner()
    @commands.command(hidden=True)
    async def load(self, ctx: commands.Context, ext: str):
        await self.client.load_extension(f'cogs.{ext}')
        await ctx.reply(f':white_check_mark: Loaded {ext}.')

    @load.error
    async def on_error(self, ctx, error: commands.CommandError):
        if isinstance(getattr(error, 'original', error), (commands.ExtensionAlreadyLoaded, commands.ExtensionNotFound)):
            await ctx.reply(f':anger: Unable to load cog.')
        else:
            logger.exception('Loading raised an exception', exc_info=error.__traceback__)
            await ctx.reply(f':anger: Loading cog raised an exception: `{type(error.__class__)}`\n'
                            f"'{error}'")

    @commands.is_owner()
    @commands.command(hidden=True)
    async def unload(self, ctx: commands.Context, ext: str):
        await self.client.unload_extension(f'cogs.{ext}')
        await ctx.reply(f':white_check_mark: Unloaded {ext}.')

    @unload.error
    async def on_error(self, ctx, error: commands.CommandError):
        if isinstance(getattr(error, 'original', error), (commands.ExtensionNotLoaded, commands.ExtensionNotFound)):
            await ctx.reply(':anger: Unable to find cog.')

    @commands.is_owner()
    @commands.group(hiddden=True)
    async def debug(self, _ctx):
        pass

    @commands.is_owner()
    @debug.command(name='unloadappcmd', hidden=True)
    async def unload_app_cmd(self, ctx: commands.Context, cmd: str, resync: bool = False):
        unloaded = self.client.tree.remove_command(cmd, guild=GUILD_OBJECT)

        if resync:
            await self.client.tree.sync(guild=GUILD_OBJECT)
            await ctx.reply(f':white_check_mark: Unloaded and re-synced `{unloaded}`.')
        else:
            await ctx.reply(f':white_check_mark: Unloaded `{unloaded}`.\n'
                            ':warning: Re-sync is required.')

    @unload_app_cmd.error
    async def on_error(self, ctx: commands.Context, _):
        await ctx.reply(':anger: Unable to unload.')

    @commands.is_owner()
    @debug.command(name='syncappcmds', hidden=True)
    async def sync_app_cmds(self, ctx: commands.Context, guild: Optional[Literal['guild', 'global']] = 'guild'):
        if guild == 'global':
            _guild = None
            guild = 'global guilds'
        elif guild == 'guild':
            _guild = GUILD_OBJECT
            guild = 'current guild'
        else:
            raise commands.BadArgument()

        synced = await self.client.tree.sync(guild=_guild)
        await ctx.reply(f':white_check_mark: Synced in *{guild}*:\n`%s`' % '\n'.join(repr(sync) for sync in synced))

    @unload_app_cmd.error
    async def on_error(self, ctx, _error: commands.CommandError):
        await ctx.reply(':anger: Unable to sync application commands.')

    @commands.is_owner()
    @debug.command(name='copyglobal', hidden=True)
    async def copy_global_to_test_guild(self, ctx: commands.Context, resync: bool = True):

        self.client.tree.copy_global_to(guild=GUILD_OBJECT)
        await ctx.reply(':white_check_mark: Copied global app commands to *test guild*')

        if resync:
            await self.client.tree.sync(guild=GUILD_OBJECT)
            await ctx.invoke(self.sync_app_cmds, guild='guild')  # type: ignore

    @commands.is_owner()
    @debug.command(name='getappcmds', hidden=True)
    async def get_app_cmds(self, ctx: commands.Context, guild: Optional[Literal['guild', 'global']] = 'guild'):
        if guild == 'global':
            _guild = None
            guild = 'global guilds'
        elif guild == 'guild':
            _guild = GUILD_OBJECT
            guild = 'current guild'
        else:
            raise commands.BadArgument()

        cmds = await self.client.tree.fetch_commands(guild=_guild)
        await ctx.reply(f':white_check_mark: Fetched {len(cmds)} command(s) in **{guild}**:\n ' +
                        ('`%s`' % '\n'.join(repr(cmd) for cmd in cmds) if cmds else ''))

    @commands.is_owner()
    @debug.command(hidden=True)
    async def clear(self, ctx: commands.Context):
        os.system('cls||clear')
        await ctx.message.add_reaction('✅')
        logger.info('Console cleared.')

    @commands.is_owner()
    @commands.guild_only()
    @debug.command(hidden=True)
    async def give_role(
        self,
        ctx: commands.Context,
        role: Annotated[discord.Role, commands.RoleConverter], *,
        member: Annotated[discord.Member, commands.MemberConverter] = commands.Author
    ):
        """Give someone a role."""

        try:
            await member.add_roles(role)
        except discord.Forbidden:
            await ctx.reply(':no_entry: lol I dont have the perms for that xd')
        else:
            await ctx.reply(
                ':white_check_mark: Successfully given role `%s` to `%s`'
                % (role.name, member.name + '#' + member.discriminator)
            )

    @debug.group(hidden=True, invoke_without_command=True)
    async def emoji(self, _ctx: commands.Context):
        pass

    @emoji.command()
    async def add(self, ctx: commands.Context, alias: str, emoji_link: str):
        emoji: bytes = await self.client.http.get_from_cdn(emoji_link)
        await ctx.guild.create_custom_emoji(name=alias, image=emoji)
        await ctx.reply(f':white_check_mark: Added emoji :{alias}:')

    @add.error
    async def on_error(self, ctx: commands.Context, error: discord.DiscordException):
        error = getattr(error, 'original', error)

        if isinstance(error, discord.Forbidden):
            await ctx.reply(':no_entry: lol I dont have the perms for that xd')

        elif isinstance(error, discord.HTTPException):
            await ctx.reply(':warning: Unable to resolve emoji')

        else:
            logger.exception('Unable to add emoji', exc_info=error.__traceback__)
            await ctx.reply(":no_entry: I can't do that :(")


    @emoji.command(aliases=['del', 'delete'])
    async def remove(self, ctx: commands.Context, alias: str):
        emoji = discord.utils.get(ctx.guild.emojis, name=alias)
        await ctx.guild.delete_emoji(emoji)
        await ctx.reply(':white_check_mark: Deleted emoji.')

async def setup(client: MoistBot):
    await client.add_cog(OwnerOnly(client))
