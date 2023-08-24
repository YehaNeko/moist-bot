from __future__ import annotations

import discord
from discord.ext import commands
from typing import TYPE_CHECKING, Optional

from random import randint, choice
import pyperclip
pyperclip.determine_clipboard()

if TYPE_CHECKING:
    from main import MoistBot


class Meow(commands.Cog):
    words = r'nya~ meow mrow nyah~ mew mrooowww meoow mrrrp mrp meoww nyaaaaa~ :3 uwu owo tehe owu UwU OwO tehe rawr purr'
    word_list = words.split(' ')

    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

    @commands.command()
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.user)
    async def meow(self, ctx: commands.Context, random_size: Optional[int]):
        """Generate a random meow"""
        random_size = random_size or randint(15, 130)

        # Initially limit length
        if random_size > 500:
            return await ctx.reply(':warning: I can\'t meow that long >~<')

        random_words = [choice(self.word_list) for _ in range(random_size)]
        random_sentence = ' '.join(random_words)

        if len(random_sentence) > 2000:
           return await ctx.reply(':warning: I can\'t meow that long >~<')

        # Automatically copy the contents to the clipboard for bot owners :3
        if await self.client.is_owner(ctx.author):
            pyperclip.copy(random_sentence)

        await ctx.reply(random_sentence)


async def setup(client: MoistBot):
    await client.add_cog(Meow(client))
