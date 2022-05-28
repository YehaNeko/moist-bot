import discord
from discord.ext import commands

from datetime import datetime
import asyncio
import psutil

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import MoistBot
else:
    MoistBot = discord.Client


class Health(commands.Cog):
    def __init__(self, bot: MoistBot):
        self.bot = bot
        self.process = psutil.Process()

    @commands.command(hidden=True, aliases=["health"])
    @commands.is_owner()
    async def bothealth(self, ctx):
        """Various bot health monitoring tools."""

        # This uses a lot of private methods because there is no
        # clean way of doing this otherwise.

        HEALTHY = discord.Colour(value=0x43B581)
        UNHEALTHY = discord.Colour(value=0xF04947)
        WARNING = discord.Colour(value=0xF09E47)

        embed = discord.Embed(title='Bot Health Report', colour=HEALTHY, timestamp=datetime.utcnow())
        description = []

        all_tasks = asyncio.all_tasks(loop=self.bot.loop)
        event_tasks = [
            t for t in all_tasks
            if 'Client._run_event' in repr(t) and not t.done()
        ]
        future_tasks = [
            t for t in event_tasks
            if 'Future pending' in repr(t)
        ]

        embed.add_field(
            name='Events Waiting',
            value=f'Total: {len(event_tasks)}\n'
                  f'Future task: {len(future_tasks)}',
            inline=False
        )

        memory_usage = self.process.memory_full_info().uss / 1024 ** 2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        embed.add_field(
            name='Process',
            value=f'{cpu_usage:.2f}% CPU\n'
                  f'{memory_usage:.2f} MiB',
            inline=False)

        global_rate_limit = not self.bot.http._global_over.is_set()
        description.append(f'Global Rate Limit: {global_rate_limit}')

        if global_rate_limit:
            embed.colour = UNHEALTHY

        embed.description = '\n'.join(description)
        await ctx.reply(embed=embed)


async def setup(client):
    await client.add_cog(Health(client))
