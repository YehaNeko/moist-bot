from __future__ import annotations

import os
import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING
from concurrent.futures import ProcessPoolExecutor

import discord
import discord.utils
from discord.ext import commands

import aiohttp
import asqlite

from config import TOKEN
from cogs.utils.context import Context
from utils.setup_logging import setup_logging

if TYPE_CHECKING:
    from discord import Interaction, Message


logger = logging.getLogger('discord.' + __name__)
extras = ('water ', 'Water ')
sep = '-' * 12


def _get_prefix(bot, message):
    return commands.when_mentioned_or(*extras)(bot, message)


class MoistBot(commands.Bot):
    executor: ProcessPoolExecutor
    session: aiohttp.ClientSession
    pool: asqlite.Pool

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
        self.started_at: datetime = discord.utils.utcnow()
        self.cooldowns: dict[int, datetime] = {}
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

    async def get_context(
        self, origin: Message | Interaction, /, *, cls: Context = Context  # type: ignore
    ) -> Context:
        return await super().get_context(origin, cls=cls)  # type: ignore

    async def process_commands(self, message: Message, /) -> None:
        if message.author.bot:
            return

        ctx: Context = await self.get_context(message)

        if ctx.command is not None:
            logger.debug(
                f'Command in guild \'{ctx.guild}\', by {ctx.author}, with command \'{ctx.command}\'\n'
            )

        await self.invoke(ctx)

    async def start(self, token: str = TOKEN, *, reconnect: bool = True) -> None:
        await super().start(token=token, reconnect=reconnect)

    async def close(self) -> None:
        await super().close()
        self.executor.shutdown()
        await self.session.close()
        await self.pool.close()
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


async def setup_db_tables(conn: asqlite.Connection) -> None:
    async with conn:
        query = """--sql
            CREATE TABLE
                IF NOT EXISTS pfg_param_cache (
                    user_id INTEGER PRIMARY KEY,
                    damages TEXT DEFAULT '[]', -- JSON array
                    ranges TEXT DEFAULT '[]', -- JSON array
                    multiplier REAL DEFAULT 1.0,
                    rpm REAL
                )
        """
        await conn.execute(query)


async def run_bot() -> None:
    with setup_logging():

        # Setup database
        pool = await asqlite.create_pool('moist.db')

        async with pool.acquire() as conn:
            await setup_db_tables(conn)

        # Start the bot
        async with MoistBot() as client:
            client.pool = pool
            await client.start()


# Prevent multiple bot logins
if __name__ == '__main__':
    asyncio.run(run_bot())
