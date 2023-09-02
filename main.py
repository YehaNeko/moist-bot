from __future__ import annotations

import discord
from config import TOKEN
from discord.ext import commands
from cogs.utils.context import Context

import logging
from logging.handlers import RotatingFileHandler

import os
import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from discord import Message, Interaction


logger = logging.getLogger('discord.' + __name__)
sep = '-' * 12


def _get_prefix(bot, message):
    extras = ['water ', 'Water ']
    return commands.when_mentioned_or(*extras)(bot, message)


class MoistBot(commands.Bot):
    def __init__(self):
        allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=True)
        intents = discord.Intents(
            emojis_and_stickers=True,
            message_content=True,
            reactions=True,
            webhooks=True,
            messages=True,
            invites=True,
            members=True,
            guilds=True,
        )
        super().__init__(
            allowed_mentions=allowed_mentions,
            command_prefix=_get_prefix,  # type: ignore
            case_insensitive=True,
            intents=intents
        )
        self.started_at: Optional[datetime] = None
        self.synced: bool = True

    async def load_cogs(self) -> None:
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                except commands.ExtensionError:
                    logger.exception(f'Failed to load extension {filename}\n')

    async def setup_hook(self):
        await asyncio.create_task(self.load_cogs())

    async def get_context(self, origin: Message | Interaction, /, *, cls: Context = Context) -> Context:
        return await super().get_context(origin, cls=cls)  # type: ignore

    async def on_ready(self):
        guilds = len(self.guilds)
        await self.change_presence(activity=discord.Game(f'with {guilds} moisturised servers'))

        if not self.started_at:
            self.started_at = discord.utils.utcnow()
            logger.info(f'\nLogged in as {self.user}\n{sep}\n')
        else:
            logger.info(f'\nRelogged in after disconnect!\n{sep}\n')
        
        if not self.synced:
            await self.wait_until_ready()
            await self.tree.sync(guild=None)  # noqa
            self.synced = True


client = MoistBot()


# Prevent multiple bot logins
if __name__ == '__main__':

    # Setup file logging
    max_bytes = 32 * 1024 * 1024  # 32 MiB
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    file_handler = RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        mode='w',
        maxBytes=max_bytes,
        backupCount=356
    )
    file_handler.setFormatter(logging.Formatter(
        '[{asctime}] [{levelname:<8}] {name}: {message}',
        dt_fmt,
        style='{')
    )

    file_logger = logging.getLogger('discord')
    file_logger.setLevel(logging.DEBUG)
    file_logger.addHandler(file_handler)

    # Run bot
    client.run(TOKEN)
