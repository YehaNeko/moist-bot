import discord
import re
import os
from discord.ext import commands

client = commands.Bot(command_prefix="water ")

TOKEN = "ODQ5MzM2NzU2NjA3MTIzNDk2.YLZsfg.JR-X_FCuzElj8iY3e0nVCWq9hY8"
target = ""

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")


@client.command()
async def reload(ctx, ext="Commands"):
    client.reload_extension(f"cogs.{ext}")



def stutter_message_filter(msg):
    stuttered_list = []

    for word in str(msg).split(" "):
        stuttered_word = f"{word[0:1]}-{word[0:1]}-{word} "
        stuttered_list.append(stuttered_word)
    stuttered_msg = "".join(stuttered_list)

    return "Message over character limit." if len(stuttered_msg) > 2000 else stuttered_msg


def replace_with(what, _with, msg):
    filtered_list = []

#    version_id = re.compile(r"version-\w+")  # autofill id
#
#    version_folder = re.compile(r"version-\w+").findall(str())  # Find version folder

    for word in msg.split(" "):
        if what == word:
            word = _with
            filtered_list.append(word + " ")
        else:
            filtered_list.append(word + " ")

    filtered = "".join(filtered_list)

    return "Message over character limit." if len(filtered) > 2000 else filtered


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))


@client.command()
async def ping(ctx):
    print("ping triggered")
    await ctx.reply(f'Pong! In {round(client.latency * 1000)}ms')


@client.command(aliases=["stutter"])
async def stutter_filter(ctx, *, msg):
    await ctx.reply(stutter_message_filter(msg))


@client.command()
async def replace(ctx, what, _with, *, msg):
    await ctx.reply(replace_with(what, _with, msg))


@client.command()
async def say(ctx, *, msg):
    await ctx.reply(msg)


@client.command()
async def target(ctx, user):
    global target
    target = user

    if "<" in target:
        target = int(target[3:-1])

    await ctx.reply(f"The target is {user}")


@client.command()
async def print_target(ctx):
    await ctx.reply(f"The target is {target}")


@client.command()
async def get_methods(ctx):
    await ctx.reply(
        f"id: {ctx.author.id}\n"
        f"Mention: {ctx.author.mention}\n"
        f"Raw: {ctx.author}\n"
        f"Nick: {ctx.author.nick}\n"
        f"Name: {ctx.author.name}\n"
        f"Display name: {ctx.author.display_name}\n"
        f"Discriminator: {ctx.author.discriminator}\n"
        f"Avatar: {ctx.author.avatar_url_as(format=None, static_format='png', size=512)}"
    )


@client.listen()
async def on_message(message):
    if message.author == client.user:
        return

    if target == message.author.id:
        await message.channel.send(stutter_message_filter(message.content))


@client.listen()
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower() == "water":
        await message.channel.send("water")


client.run(TOKEN)
