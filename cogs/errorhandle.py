import sys
import traceback
import discord
from discord.ext import commands

# Custom errors
from cogs.mcserver import NotWhitelisted


class ErrorHandler(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """The event triggered when an error is raised while invoking a command."""

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound, NotWhitelisted,)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"You are on cooldown. Try again in {(seconds := round(error.retry_after))} seconds.",
                            delete_after=seconds + 1)

        elif isinstance(error, commands.DisabledCommand):
            await ctx.reply(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(f"Missing required parameter `{error.param.name}`.")

        elif isinstance(error, commands.MemberNotFound):
            await ctx.reply("Member not found.")

        elif isinstance(error, commands.BadArgument):
            await ctx.reply(f"Bad parameter in `{ctx.current_parameter}`.")

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print(
                f'Error in guild "{ctx.guild}", triggered by {ctx.author}, with command "{ctx.command}"',
                file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            print("\n\n")


async def setup(client):
    await client.add_cog(ErrorHandler(client))

# Modified from https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612
