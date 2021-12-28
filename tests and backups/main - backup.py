import discord
from discord.ext import commands

client = commands.Bot(command_prefix="water ")

TOKEN = "ODQ5MzM2NzU2NjA3MTIzNDk2.YLZsfg.JR-X_FCuzElj8iY3e0nVCWq9hY8"
target = ""


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))


@client.command()
async def ping(ctx):
    print("ping triggered")
    await ctx.send(f'Pong! In {round(client.latency * 1000)}ms')


@client.command()
async def say(ctx, msg):
    await ctx.send(msg)


@client.command()
async def target(ctx, user):
    global target
    target = user

    if "!" in target:
        targets_p = []
        for i in target.split("!", 1):
            targets_p.append(i)
        target = "".join(map(str, targets_p))

    await ctx.send(f"The target is {target}")


@client.command()
async def print_target(ctx):
    await ctx.send(f"The target is {target}")


@client.command()
async def get_methods(ctx):
    await ctx.send(f"id: {ctx.author.id}\n"
                   f"Mention: {ctx.author.mention}\n"
                   f"Raw: {ctx.author}")


@client.listen()
async def on_message(message):
    if message.author == client.user:
        return

    if message.author.mention == target:
        stuttered_list = []

        for word in str(message.content).split(" "):  # [2:]:
            stuttered_word = f"{word[0:1]}-{word[0:1]}-{word} "
            stuttered_list.append(stuttered_word)

        stuttered_msg = "".join(map(str, stuttered_list))
        await message.channel.send(stuttered_msg)


@client.listen()
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower() == "water":
        await message.channel.send("water")


client.run(TOKEN)
# @client.event
# async def on_message(message):
#     global target
#     if message.author == client.user:
#         return
#
#     msg = message.content
#     send = message.channel.send
#
#     if msg.lower() == "water":
#         await send(f"real fucking water {message.author.mention}")
#
#     if msg == "print target":
#         print("Target is " + str(target))
#
#     if msg.startswith("water target"):
#         target = str(msg).split(" ")[2]
#
#         if "!" in target:
#             targets_p = []
#             for i in target.split("!", 1):
#                 targets_p.append(i)
#             target = "".join(map(str, targets_p))
#
#         print(target)
#         await send(f"The target is {target}")
#
#     if message.author.mention == target:
#         stuttered_list = []
#
#         for word in str(msg).split(" "):    # [2:]:
#             stuttered_word = f"{word[0:1]}-{word[0:1]}-{word} "
#             stuttered_list.append(stuttered_word)
#
#         stuttered_msg = "".join(map(str, stuttered_list))
#
#         await send(stuttered_msg)


