import discord
from discord.ext import commands
from config import TOKEN

import logging
import traceback
import sys
import os

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


class MoistBot(commands.Bot):
    def __init__(self):
        allowed_mentions = discord.AllowedMentions(roles=False, everyone=False, users=True, replied_user=True)
        intents = discord.Intents(
            emojis_and_stickers=True,
            guilds=True,
            invites=True,
            members=True,
            message_content=True,
            messages=True,
            reactions=True,
            scheduled_events=True,
            typing=True,
            webhooks=True,
            bans=False,
            presences=False,
            dm_typing=False,
            guild_typing=False,
            integrations=False,
            voice_states=False,
        )
        super(MoistBot, self).__init__(
            command_prefix="water ",
            allowed_mentions=allowed_mentions,
            intents=intents
        )

        for filename in os.listdir(r"./cogs"):
            if filename.endswith(".py"):
                try:
                    self.load_extension(f"cogs.{filename[:-3]}")
                except Exception as e:
                    print(f'Failed to load extension {filename}.', file=sys.stderr)
                    traceback.print_exc()


client = MoistBot()


@client.command()
async def reload(ctx, ext="cmds"):
    if ctx.author.id == 150560836971266048:

        client.reload_extension(f"cogs.{ext}")
        await ctx.reply(f"Reloaded {ext}.")

    else:
        await ctx.reply("You don't have permission to use this.")
@reload.error
async def on_error(ctx, error):
    if isinstance(getattr(error, 'original', error), (discord.ExtensionNotLoaded, discord.ExtensionNotFound)):
        await ctx.reply(f"Idiot, that's not a cog.")

    else:
        await ctx.reply(f"Raised {type(error)}:\n"
                        f'"{error}"')


@commands.Bot.listen(client)
async def on_ready():
    await client.change_presence(activity=discord.Game(f"with {len(client.guilds)} mosturized servers"))
    print(f"Logged in as {client.user}")

client.run(TOKEN)
