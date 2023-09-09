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
from contextlib import contextmanager
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
            enable_debug_events=True,
            case_insensitive=True,
            intents=intents,
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

    async def process_commands(self, message: Message, /) -> None:
        if message.author.bot:
            return

        ctx: Context = await self.get_context(message)

        if ctx.command is not None:
            logger.debug(f'Command in guild \'{ctx.guild}\', by {ctx.author}, with command \'{ctx.command}\'\n')

        await self.invoke(ctx)

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

    @contextmanager
    def setup_logging():
        log = logging.getLogger()
    
        try:
            discord.utils.setup_logging(level=logging.DEBUG)
            # __enter__
            logging.getLogger('discord').setLevel(logging.INFO)
            logging.getLogger('discord.http').setLevel(logging.WARNING)
            logging.getLogger('discord.gateway').setLevel(logging.DEBUG)
            # logging.getLogger('discord.state').addFilter(RemoveNoise())

            # Set stream handlers to INFO level
            for handler in log.handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setLevel(logging.INFO)

            # Setup file logging
            max_bytes = 32 * 1024 * 1024  # 32 MiB
            dt_fmt = '%Y-%m-%d %H:%M:%S'
            fmt = '[{asctime}] [{levelname:<8}] {name}: {message}'

            file_handler = RotatingFileHandler(
                filename='discord.log', encoding='utf-8', mode='w', maxBytes=max_bytes, backupCount=356
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(
                logging.Formatter(fmt, dt_fmt, style='{')
            )
            log.addHandler(file_handler)
    
            yield
        finally:
            # __exit__
            handlers = log.handlers[:]
            for handler in handlers:
                handler.close()
                log.removeHandler(handler)

    # Run bot
    with setup_logging():
        client.run(TOKEN, log_handler=None)
