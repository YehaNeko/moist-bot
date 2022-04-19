import typing
import time
import discord
from discord.ext import commands


class Cmds(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def ping(self, ctx, *, args: str = "Pong!"):
        before = time.monotonic()
        message = await ctx.reply(f"{args}")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"{args} in {int(ping)}ms")

    """
    @commands.command()
    async def ping(self, ctx, *, args: str = "Pong!"):
        await ctx.reply(f"{args} in {round(self.client.latency) * 1000}ms")
    """

    @commands.command(name="stutter")
    async def stutter_filter(self, ctx, *, msg):
        await ctx.reply(stutter_message_filter(msg))

    @commands.command()
    async def quote(self, ctx, at_who: typing.Union[discord.Member, str], *, msg):
        at_who = at_who.replace("-", " ") if isinstance(at_who, str) else at_who.mention
        await ctx.reply(f"{msg}\n\n" f" - **{at_who}**")

    @commands.command()
    async def say(self, ctx, *, msg):
        await ctx.send(msg)

    @commands.command(name="methods", brief="Used for debugging", hidden=True)
    async def get_methods(self, ctx, user: discord.Member):
        await ctx.reply(
            f"id: {user.id}\n"
            f"Mention: {user.mention}\n"
            f"Raw: {user}\n"
            f"Nick: {user.nick}\n"
            f"Name: {user.name}\n"
            f"Display name: {user.display_name}\n"
            f"Discriminator: {user.discriminator}\n"
            f"Avatar: {user.avatar}"
        )

    @commands.command(enabled=True, name="updatestatus", brief="Used for debugging", hidden=True)
    async def update_status(self, ctx):

        await self.client.change_presence(
            activity=discord.Game(f"with {len(self.client.guilds)} mosturized servers")
        )
        await ctx.send("Updated status")

    # Event listeners
    @commands.Cog.listener()
    async def on_message(self, message):

        # Don't reply to self
        if message.author == self.client.user:
            return

        if message.content.lower() == "water":
            await message.channel.send("water")


# Activate cog
async def setup(client):
    await client.add_cog(Cmds(client))


# Helper functions
def stutter_message_filter(msg):
    stuttered_list = []

    for word in str(msg).split(" "):
        stuttered_word = f"{word[0:1]}-{word[0:1]}-{word} "
        stuttered_list.append(stuttered_word)
    stuttered_msg = "".join(stuttered_list)

    return (
        "Message over character limit." if len(stuttered_msg) > 2000 else stuttered_msg
    )
