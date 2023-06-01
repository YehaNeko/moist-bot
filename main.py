import discord
from discord.ext import commands
from config import TOKEN

import logging
from logging.handlers import RotatingFileHandler

import asyncio
import os

logger = logging.getLogger('discord.' + __name__)


def _get_prefix(bot, message):
    extras = ['water ', 'Water ']
    return commands.when_mentioned_or(*extras)(bot, message)

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
            command_prefix=_get_prefix,  # type: ignore
            allowed_mentions=allowed_mentions,
            intents=intents
        )
        self.synced: bool = True
        self.presence_changed: bool = False

    async def load_cogs(self) -> None:
        for filename in os.listdir(r'./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                except commands.ExtensionError as e:
                    logger.exception(f'Failed to load extension {filename}\n')

    async def setup_hook(self):
        await asyncio.create_task(self.load_cogs())


client = MoistBot()


@commands.Bot.listen(client)
async def on_ready():
    change_activity = client.change_presence(activity=discord.Game(f'with {len(client.guilds)} mosturized servers'))

    await change_activity
    if not client.presence_changed:
        client.presence_changed = True
        logger.info(f'\nLogged in as {client.user}\n'
                    '-------------\n')
    else:
        logger.info('\nRelogged in after disconnect!\n'
                    '-------------\n')

    await client.wait_until_ready()
    if not client.synced:
        await client.tree.sync(guild=None)
        client.synced = True

# Setup file logging
max_bytes = 32 * 1024 * 1024  # 32 MiB
file_logger = logging.getLogger('discord')
file_logger.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler(filename='discord.log', encoding='utf-8', mode='w', maxBytes=max_bytes, backupCount=356)
dt_fmt = '%Y-%m-%d %H:%M:%S'
file_handler.setFormatter(logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{'))
file_logger.addHandler(file_handler)

# Run bot
if __name__ == '__main__':
    client.run(TOKEN)
