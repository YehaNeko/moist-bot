import discord
from discord.ext import commands
from config import GUILD_OBJECT

import os
import logging
from typing import TYPE_CHECKING, Optional, Literal, Annotated


logger = logging.getLogger('discord.' + __name__)

class OwnerOnly(commands.Cog):
    def __init__(self, client):
        self.client  = client

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, ext: str = 'cmds'):
        await self.client.reload_extension(f'cogs.{ext}')
        await ctx.reply(f':repeat: Reloaded {ext}.')

    @reload.error
    async def on_error(self, ctx, error: commands.CommandError):
        if isinstance(getattr(error, 'original', error), (commands.ExtensionNotLoaded, commands.ExtensionNotFound)):
            await ctx.reply(":anger: Idiot, isn't a cog.")
        else:
            await ctx.reply(f':anger: Reloading raised an exception: `{type(error.__class__)}`\n'
                            f"'{error}'")

    @commands.command(hidden=True)
    @commands.is_owner()
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

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx: commands.Context, ext: str):
        await self.client.unload_extension(f'cogs.{ext}')
        await ctx.reply(f':white_check_mark: Unloaded {ext}.')

    @unload.error
    async def on_error(self, ctx, error: commands.CommandError):
        if isinstance(getattr(error, 'original', error), (commands.ExtensionNotLoaded, commands.ExtensionNotFound)):
            await ctx.reply(':anger: Unable to find cog.')

    @commands.group(hiddden=True)
    @commands.is_owner()
    async def debug(self, _ctx):
        pass

    @debug.command(name='unloadappcmd', hidden=True)
    @commands.is_owner()
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

    @debug.command(name='syncappcmds', hidden=True)
    @commands.is_owner()
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

    @debug.command(name='copyglobal', hidden=True)
    @commands.is_owner()
    async def copy_global_to_test_guild(self, ctx: commands.Context, resync: bool = True):

        self.client.tree.copy_global_to(guild=GUILD_OBJECT)
        await ctx.reply(':white_check_mark: Copied global app commands to *test guild*')

        if resync:
            await self.client.tree.sync(guild=GUILD_OBJECT)
            await ctx.invoke(self.sync_app_cmds, guild='guild')  # type: ignore

    @debug.command(name='getappcmds', hidden=True)
    @commands.is_owner()
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

    @debug.command(hidden=True)
    @commands.is_owner()
    async def clear(self, ctx: commands.Context):
        os.system('cls||clear')
        await ctx.message.add_reaction('✅')
        logger.info('Console cleared.')

    @debug.command(hidden=True)
    @commands.is_owner()
    @commands.guild_only()
    async def give_role(
            self,
            ctx: commands.Context,
            role: Annotated[discord.Role, commands.RoleConverter],
            *,
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


async def setup(client: commands.Bot):
    await client.add_cog(OwnerOnly(client))