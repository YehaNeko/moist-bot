import discord
from discord.ext import commands

import json
with open("whitelist.json") as d:
    data = json.load(d)

from config import EXAROTON_TOKEN
from exaroton import Exaroton

exa = Exaroton(EXAROTON_TOKEN)
server_key = "4ksE0Nc5qCNb7ZYn"


class NotWhitelisted(commands.CheckFailure):
    pass


def is_whitelisted():
    async def predicate(ctx):
        global data
        with open("whitelist.json") as f:
            data = json.load(f)

        if ctx.author.id not in data["whitelisted"]:
            raise NotWhitelisted()
        return True

    return commands.check(predicate)


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == 150560836971266048

    return commands.check(predicate)


class Mcserver(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.execute = self.client.loop.run_in_executor

    async def cog_command_error(self, ctx: commands.Context, error):
        if isinstance(error, NotWhitelisted):
            await ctx.reply("You are not whitelisted.")

    @commands.group(enabled=True, hidden=True)
    async def mcserver(self, ctx):
        pass

    @mcserver.command()
    @is_owner()
    async def add(self, ctx: commands.Context, *, user: commands.MemberConverter):
        """Adds user to whitelist"""
        user: discord.Member

        # Check if already whitelisted
        if user.id in data["whitelisted"]:
            return await ctx.reply(f"{user.display_name} is already whitelisted.")

        # Add to whitelist
        data["whitelisted"].append(user.id)
        with open("whitelist.json", "w") as f:
            json.dump(data, f, indent=3)

        await ctx.reply(f"Whitelisted `{user.display_name}`.")

    @add.error
    async def on_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.reply("You don't have permission to use this command.")

    @mcserver.command()
    @is_whitelisted()
    async def remove(self, ctx: commands.Context, *, user: discord.Member = None):
        """Removes user from whitelist"""

        # Check and remove from whitelist
        try:
            data["whitelisted"].remove(user.id)
        except ValueError:
            return await ctx.reply(f"`{user.display_name}` is already not whitelisted.")

        with open("whitelist.json", "w") as f:
            json.dump(data, f, indent=3)

        await ctx.reply(f"`{user.display_name}` was removed from the whitelist.")

    @remove.error
    async def on_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply("Missing user to whitelist.")

    @mcserver.command()
    @is_whitelisted()
    async def start(self, ctx: commands.Context):
        """Starts minecraft server"""
        await self.execute(None, exa.start, "4ksE0Nc5qCNb7ZYn")

        await ctx.reply("Server started.")

    @mcserver.command()
    @is_whitelisted()
    async def execute(self, ctx, *, cmd):
        """Execute a command on the server"""
        await self.execute(None, exa.command, server_key, cmd)

        await ctx.reply(f"Executed `{cmd}`.")

    @mcserver.command(enabled=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def say(self, ctx, *, text):
        """ Public say command """
        await self.execute(None, exa.command, server_key,
                           'tellraw @a [{"bold":true, "text":"%s "}, ' % ctx.author.display_name +
                           '{"bold":false, "text":"says: %s"}]' % text
                           )

        await ctx.reply(f"Said `{text}`.")

    @mcserver.command()
    @is_whitelisted()
    async def list(self, ctx):
        """Raw current whitelist"""
        await ctx.reply(f"Current raw whitelist: `{str(data['whitelisted'])}`")


def setup(client):
    client.add_cog(Mcserver(client))
