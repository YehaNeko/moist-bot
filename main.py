import discord
from discord.ext import commands
import os
from config import *
os.chdir(".")

client = commands.Bot(command_prefix="water ")

for filename in os.listdir(r"./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")


@client.command()
async def reload(ctx, ext="cmds"):
    if ctx.author.id == 150560836971266048:

        client.reload_extension(f"cogs.{ext}")
        await ctx.reply(f"Reloaded {ext}.")

    else:
        await ctx.reply("You don't have permission to use this.")
@reload.error
async def on_error(ctx, error):

    if isinstance(getattr(error, 'original', error), (discord.ExtensionNotLoaded, discord.ExtensionNotFound)):
        await ctx.reply(f"Idiot, that's not a cog.")

    else:
        await ctx.reply(f"Raised {type(error)}:\n"
                        f'"{error}"')


@commands.Bot.listen(client)
async def on_ready():
    await client.change_presence(activity=discord.Game(f"with {len(client.guilds)} mosturized servers"))
    print(f"Logged in as {client.user}")

client.run(TOKEN)
