from __future__ import annotations

import discord
from discord.ext import commands

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

# Custom errors
from cogs.mp3 import FileTooBig
from asyncprawcore.exceptions import AsyncPrawcoreException

if TYPE_CHECKING:
    from main import MoistBot
    from cogs.utils.context import Context


logger = logging.getLogger('discord.' + __name__)


class ErrorHandler(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        """The event triggered when an error is raised while invoking a command."""

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        # cog = ctx.cog
        # if cog:
        #     if cog._get_overridden_method(cog.cog_command_error) is not None:
        #         return

        ignored = (
            commands.DisabledCommand,
            commands.CommandNotFound,
            commands.NotOwner,
            FileTooBig,
        )

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.CommandOnCooldown):
            seconds = round(error.retry_after)
            tm_in = discord.utils.utcnow() + timedelta(seconds=seconds)
            tm_fmt = discord.utils.format_dt(tm_in, 'R')

            return await ctx.reply(
                f':warning: You are on cooldown. Try again {tm_fmt}.',
                delete_after=seconds,
                ephemeral=True
            )

        # elif isinstance(error, commands.DisabledCommand):
        #     await ctx.reply(f':no_entry_sign: `{ctx.command}` has been disabled.', ephemeral=True)
        #     return

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(f':no_entry_sign: `{ctx.command}` can\'t be used in Private Messages.')
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.reply(f':warning: Missing required parameter `{error.param.name}`.', ephemeral=True)

        elif isinstance(error, commands.MemberNotFound):
            return await ctx.reply(f':warning: Member `{error.argument}` not found.', ephemeral=True)

        elif isinstance(error, commands.BadLiteralArgument):
            literals = error.literals
            param = error.param

            to_string = [repr(l) for l in literals]
            if len(to_string) > 2:
                fmt = '{}, or {}'.format(', '.join(to_string[:-1]), to_string[-1])
            else:
                fmt = ' or '.join(to_string)
            
            return await ctx.reply(f':warning: Parameter `{param.displayed_name or param.name}` can only be {fmt}.')

        elif isinstance(error, commands.BadArgument):
            if str(error):
                return await ctx.reply(str(error), ephemeral=True)

        elif isinstance(error, commands.NSFWChannelRequired):
            return await ctx.reply(f':no_entry_sign: `{ctx.command}` can only be used in NSFW channels.')

        elif isinstance(error, commands.CheckFailure):
            if str(error):
                return await ctx.reply(f':warning: {str(error)}', ephemeral=True)
            return await ctx.reply(":warning: You are unable to run this command.", ephemeral=True)

        elif isinstance(error, AsyncPrawcoreException):
            return await ctx.reply(':anger: I cannot find that subreddit D:', ephemeral=True)

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            logger.exception(
                f'Error in guild \'{ctx.guild}\', triggered by {ctx.author}, with command \'{ctx.command}\'\n',
                exc_info=error,
            )
            return await ctx.reply(f':anger: Command raised unhandled error:\n`{error}`', ephemeral=True)


async def setup(client) -> None:
    await client.add_cog(ErrorHandler(client))

# Modified from https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612
