import discord
from discord.ext import commands
import json

with open("whitelist.json") as d:
    data = json.load(d)

from exaroton import Exaroton
exa = Exaroton("vHN2DxdsADfOkCVZU4tPlEGdYsGBf5e2Z1W87Ji24RBnsY1ngFw8VkvpNtvsvSPyNM1G9alr2cqzCTdIrjuC6qb2ajHc2brRBGG4")


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
    def __init__(self, client):
        self.client = client
    global data

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, NotWhitelisted):
            await ctx.reply("You are not whitelisted.")

    @commands.group(enabled=True, hidden=True)
    async def mcserver(self, ctx):
        pass

    @mcserver.command(clean_params=True)
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

    @mcserver.command(clean_params=True)
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

    @mcserver.command(clean_params=True)
    @is_whitelisted()
    async def start(self, ctx: commands.Context):
        """Starts minecraft server"""
        exa.start("4ksE0Nc5qCNb7ZYn")

        await ctx.reply("Server started.")

    @mcserver.command(clean_params=True)
    @is_whitelisted()
    async def list(self, ctx):
        """Raw current whitelist"""
        await ctx.reply(f"Current raw whitelist: `{str(data['whitelisted'])}`")


def setup(client):
    client.add_cog(Mcserver(client))
