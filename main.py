from __future__ import annotations

import discord
from config import TOKEN
from discord.ext import commands
from cogs.utils.context import Context
from utils.setup_logging import setup_logging

import logging

import os
import asyncio
import aiohttp
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from discord import Message, Interaction


logger = logging.getLogger('discord.' + __name__)
extras = ('water ', 'Water ')
sep = '-' * 12


def _get_prefix(bot, message):
    return commands.when_mentioned_or(*extras)(bot, message)


class MoistBot(commands.Bot):
    executor: ProcessPoolExecutor
    session: aiohttp.ClientSession

    def __init__(self):
        allowed_mentions = discord.AllowedMentions(
            everyone=False, roles=False, users=True, replied_user=True
        )
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
            help_attrs=dict(hidden=True),
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

    async def setup_hook(self) -> None:
        self.executor = ProcessPoolExecutor(max_workers=4)
        self.session = aiohttp.ClientSession()
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

    async def start(self, token: str = TOKEN, *, reconnect: bool = True) -> None:
        await super().start(token=token, reconnect=reconnect)

    async def close(self) -> None:
        await self.session.close()
        await super().close()
        logger.info('Bot closed.')

    async def on_ready(self) -> None:
        guilds = len(self.guilds)
        await self.change_presence(
            activity=discord.Game(f'with {guilds} moisturised servers')
        )

        if not self.started_at:
            self.started_at = discord.utils.utcnow()
            logger.info(f'\nLogged in as {self.user}\n{sep}\n')
        else:
            logger.info(f'\nRelogged in after disconnect!\n{sep}\n')

        if not self.synced:
            await self.wait_until_ready()
            await self.tree.sync(guild=None)  # noqa
            self.synced = True
            logger.info('Application commands synced.')

    @property
    def setup_logging(self):
        return setup_logging

    @property
    def config(self):
        return __import__('config')


async def run_bot() -> None:
    with setup_logging():
        async with MoistBot() as client:
            await client.start()


# Prevent multiple bot logins
if __name__ == '__main__':
    asyncio.run(run_bot())
