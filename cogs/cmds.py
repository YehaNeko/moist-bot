from __future__ import annotations

import discord
from discord.ext import commands
from discord.utils import escape_mentions

import time
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from main import MoistBot
    from cogs.utils.context import Context


class Cmds(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

    @commands.command()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def ping(self, ctx: Context, *, msg: Union[escape_mentions, str] = 'Pong!'):
        before = time.monotonic()
        message = await ctx.reply(f'{msg}')
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f'{msg} in {int(ping)}ms')

    """
    @commands.command()
    async def ping(self, ctx, *, msg: str = 'Pong!'):
        await ctx.reply(f'{msg} in {round(self.client.latency) * 1000}ms')
    """

    @commands.command()
    async def stutter(self, ctx: Context, *, msg: Union[escape_mentions, str]):
        stuttered_msg = '  '.join(f'{word[0]}-{word[0]}-{word}' for word in msg.split(' '))

        if len(stuttered_msg) >= 2000:
            await ctx.reply(':warning: Message over character limit.')
            return

        await ctx.reply(stuttered_msg)

    @commands.is_owner()
    @commands.command(hidden=True)
    async def quote(self, ctx: Context, at_who: Union[discord.User, str], *, msg: Union[escape_mentions, str]):
        if isinstance(at_who, discord.User):
            at_who = at_who.mention
        else:
            at_who = escape_mentions(at_who)

        await ctx.reply(f'{msg}\n\n' f' - **{at_who}**')

    @commands.command()
    async def say(self, ctx: Context, *, msg: Union[escape_mentions, str]):
        await ctx.send(msg)

    @commands.is_owner()
    @commands.command(name='methods', brief='Used for debugging', hidden=True)
    async def get_methods(self, ctx, user: discord.Member):
        await ctx.reply(
            f'id: {user.id}\n'
            f'Mention: {user.mention}\n'
            f'Raw: {user}\n'
            f'Nick: {user.nick}\n'
            f'Name: {user.name}\n'
            f'Display name: {user.display_name}\n'
            f'Discriminator: {user.discriminator}\n'
            f'Avatar: {user.avatar}'
        )

    @commands.is_owner()
    @commands.command(enabled=True, name='updatestatus', hidden=True)
    async def update_status(self, ctx: Context):
        """Update the bot's status"""
        guilds = len(self.client.guilds)
        await self.client.change_presence(activity=discord.Game(f'with {guilds} mosturized servers'))
        await ctx.send('Updated status.')

    # Event listeners
    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message):
    #
    #     # Don't reply to self
    #     if message.author == self.client.user:
    #         return
    #
    #     if message.content.lower() == 'water':
    #         await message.channel.send('water')


# Activate cog
async def setup(client: MoistBot) -> None:
    await client.add_cog(Cmds(client))
