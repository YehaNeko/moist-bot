import discord
# from discord import app_commands
from discord.ext import commands
from config import TOKEN, GUILD

import traceback
import asyncio
import logging
import sys
import os

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


class MoistBot(commands.Bot):
    def __init__(self):
        allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=True)
        intents = discord.Intents(
            emojis_and_stickers=True,
            guilds=True,
            invites=True,
            members=True,
            message_content=True,
            messages=True,
            reactions=True,
            typing=True,
            webhooks=True,
            bans=False,
            presences=False,
            dm_typing=False,
            guild_typing=False,
            integrations=False,
            voice_states=False,
        )
        super().__init__(
            case_insensitive=True,
            command_prefix=commands.when_mentioned_or("water "),
            allowed_mentions=allowed_mentions,
            intents=intents
        )
        self.synced: bool = False
        self.presence_changed: bool = False

    async def load_cogs(self) -> None:
        for filename in os.listdir(r"./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                except commands.ExtensionError as e:
                    print(f'Failed to load extension {filename}.', file=sys.stderr)
                    traceback.print_exc()

    async def setup_hook(self):
        await asyncio.create_task(self.load_cogs())


client = MoistBot()


@client.command(hidden=True)
@commands.is_owner()
async def reload(ctx: commands.Context, ext: str = "cmds"):
    await client.reload_extension(f"cogs.{ext}")
    await ctx.reply(f":repeat: Reloaded {ext}.")
@reload.error
async def on_error(ctx, error: commands.CommandError):
    if isinstance(getattr(error, "original", error), (commands.ExtensionNotLoaded, commands.ExtensionNotFound)):
        await ctx.reply(":anger: Idiot, that's not a cog.")
    else:
        await ctx.reply(f":anger: Reloading raised an exception: `{type(error.__class__)}`\n"
                        f'"{error}"')


@client.command(hidden=True)
@commands.is_owner()
async def load(ctx: commands.Context, ext: str):
    await client.load_extension(f"cogs.{ext}")
    await ctx.reply(f":white_check_mark: Loaded {ext}.")
@load.error
async def on_error(ctx, error: commands.CommandError):
    if isinstance(getattr(error, "original", error), (commands.ExtensionAlreadyLoaded, commands.ExtensionNotFound)):
        await ctx.reply(f":anger: Unable to load cog.")
    else:
        await ctx.reply(f":anger: Loading raised an exception: `{type(error.__class__)}`\n"
                        f'"{error}"')


@client.command(hidden=True)
@commands.is_owner()
async def unload(ctx: commands.Context, ext: str):
    await client.unload_extension(f"cogs.{ext}")
    await ctx.reply(f":white_check_mark: Unloaded {ext}.")
@unload.error
async def on_error(ctx, error: commands.CommandError):
    if isinstance(getattr(error, "original", error), (commands.ExtensionNotLoaded, commands.ExtensionNotFound)):
        await ctx.reply(":anger: Unable to find cog.")


@client.group(hiddden=True)
@commands.is_owner()
async def debug(ctx):
    pass


@debug.command(name="unloadappcmd", hidden=True)
@commands.is_owner()
async def unload_app_cmd(ctx: commands.Context, cmd: str, resync: bool = False):
    unloaded = client.tree.remove_command(cmd, guild=discord.Object(id=GUILD))

    if bool(resync):
        await client.tree.sync(guild=discord.Object(id=GUILD))
        await ctx.reply(f":white_check_mark: Unloaded and re-synced `{unloaded}`.")
    else:
        await ctx.reply(f":white_check_mark: Unloaded `{unloaded}`.\n"
                        ":warning: Re-sync is required.")

@unload_app_cmd.error
async def on_error(ctx, _):
    await ctx.reply(":anger: Unable to unload.")


@debug.command(name="syncappcmds", hidden=True)
@commands.is_owner()
async def sync_app_cmds(ctx: commands.Context):
    synced = await client.tree.sync(guild=discord.Object(id=GUILD))
    await ctx.reply(":white_check_mark: Synced:\n`%s`" % "\n".join([repr(sync) for sync in synced]))
@unload_app_cmd.error
async def on_error(ctx, error: commands.CommandError):
    await ctx.reply(":anger: Unable to sync application commands.")


@commands.Bot.listen(client)
async def on_ready():
    if not client.presence_changed:
        await client.change_presence(activity=discord.Game(f"with {len(client.guilds)} mosturized servers"))
        print(f"\nLogged in as {client.user}\n"
              "-------------\n")
        client.presence_changed = True
    else:
        print("\nRelogged in after disconnect!\n"
              "-------------\n")

    await client.wait_until_ready()
    if not client.synced:
        await client.tree.sync(guild=discord.Object(id=GUILD))
        client.synced = True


client.run(TOKEN)
