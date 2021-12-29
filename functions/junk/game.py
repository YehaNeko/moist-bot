import _weakref
import random
import discord
from discord.ext import commands


class GameObject:

    # Asset key must be the same as {self.name} #
    assets = {
        "obj": ":purple_square:",
        "player": ":flushed:",
        "box": ":brown_square:"
    }
    instances = []  # Keep track of instance names

    def __init__(self, name, x, y):
        self.x: int = x
        self.y: int = y
        self.name: str = name
        self.asset = str(GameObject.assets.get(f"{self.name}"))
        self.__class__.instances.append(_weakref.proxy(self))

    def __repr__(self):
        return self.name

    def __len__(self):
        return len(self.asset)

    @classmethod
    def get_instances(cls):
        return cls.instances

    def move_up(self):
        self.y -= 1
        self.x -= 1  # Comp for index offset

    def move_down(self):
        self.y += 1
        self.x += 1  # Comp for index offset

    def move_left(self):
        self.x -= 1

    def move_right(self):
        self.x += 1

    def setcords(self, x, y):
        self.x = x
        self.y = y

    def randomcords(self, max_x, max_y):
        self.x = random.randint(0, max_x)
        self.y = random.randint(0, max_y)


class EmptyGameObject(GameObject):  # Not finished so not used

    def __init__(self, name, x, y):
        super().__init__(name, x, y)
        self.name = name
        self.asset = str(EmptyGameObject.assets.get(f"{self.name}"))


player = GameObject("player", 0, 0)
# box = GameObject("box", 0, 0)
# obj = EmptyGameObject("obj", 0, 0)


def start(x, y):
    player.randomcords(x, y)
    # box.randomcords(x, y)
    # player.setcords(4, 1)  # Debugging
    # box.setcords(1, 1)  # Debugging

    Game.game_running = True

    return draw_v5(x, y)


def stop():
    Game.game_running = False


def index_offset():
    pass


def draw_v5(x, y):
    line_list = []

    # # Empty game scene # #
    for _ in range(0, (x+1) * (y+1)):
        line_list.append(GameObject.assets.get("obj"))  # Final
        # line_list.append(f"[{_}]")  # Debug

    # # Draw game # #
    objs_alr_added = 0  # TODO account for index offset with draw order.
    for instance in GameObject.get_instances():
        for index in range(0, (x+1) * (y+1)):

            # First check if any cordinate is 0 #
            if instance.x == 0 or instance.y == 0:

                # If GameObject x is 0 but y is valid #
                if instance.x == 0 and instance.y > 0:
                    if index == instance.y * x:

                        line_list.insert(index + 1 - objs_alr_added, instance.asset)  # TODO it's actually minus obj_alr_added ya dufus. Fix for all cases!
                        objs_alr_added += 1
                        print(f"{instance.name} fell under catagory GameObject x is 0 but y is valid with index: {index}.")   # Debugging

                # If GameObject y is 0 but x is valid #
                elif instance.y == 0 and instance.x > 0:
                    if index == instance.x:

                        line_list.insert(index - objs_alr_added, instance.asset)
                        objs_alr_added += 1
                        print(f"{instance.name} fell under catagory GameObject y is 0 but x is valid with index: {index}.")   # Debugging

                # If GameObject x and y is 0 #
                elif instance.x == 0 and instance.y == 0:
                    if index == instance.x + instance.y:

                        line_list.insert(index - objs_alr_added, instance.asset)
                        objs_alr_added += 1
                        print(f"{instance.name} fell under catagory GameObject x and y is 0 with index: {index}.")   # Debugging

            # Calculate index #
            elif index == instance.x + (instance.y * x):

                line_list.insert(index + 1 - objs_alr_added, instance.asset)
                objs_alr_added += 1
                print(f"{instance.name} fell under catagory calculate idex with index: {index}.")   # Debugging

            else:
                pass

    # Remove extra #
    for _ in range(objs_alr_added):
        line_list.pop(len(line_list) - 1)

    # Add new lines #
    index = 0
    offset = 0
    for _ in range(1, y+1):
        index += x + 1 + offset
        line_list.insert(index, "\n")
        offset = 1 if offset == 0 else 1    # What the fuck??

    # Finalize #
    line = "".join(line_list)

    return line


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
class Game(commands.Cog):

    debugging: bool = True
    game_running: bool = False
    crnt_game_x: int
    crnt_game_y: int
    gamer = int

    def __init__(self, client):
        self.client = client

    @commands.command(enabled=False, brief="WIP rendiring engine")
    async def start(self, ctx, size_x: int, size_y: int):
        Game.crnt_game_x = size_x
        Game.crnt_game_y = size_y
        Game.gamer = ctx.author.id

        error = ctx.reply("Message over character limit.")
        # Check if game size is too big #
        # if size_x or size_y > 200:
        #     return await error
        if (size_x + size_y) * len(GameObject.assets.get("obj")) + len(player) > 2000:
            return await error
        # Else draw game #

        await ctx.send(start(size_x-1, size_y-1))     # -1 to adjust for indexes starting at 0
        await ctx.send("Send w, a, s, d to move around.")

        # Debug #
        if Game.debugging:
            await ctx.send(f"(DEBUG)  Player position is at x: {player.x + 1}, y: {player.y + 1}.")

    @commands.command(enabled=False, brief="Stop game")
    async def stop(self, ctx):
        stop()
        await ctx.send("Game stopped.")

    @commands.Cog.listener()
    async def on_message(self, message):

        if Game.game_running and message.author.id == Game.gamer:    # TODO Also check channel

            if message.content.lower() == "w":
                player.move_up()
                await message.channel.send(draw_v5(Game.crnt_game_x, Game.crnt_game_y))

            elif message.content.lower() == "s":
                player.move_down()
                await message.channel.send(draw_v5(Game.crnt_game_x, Game.crnt_game_y))

            elif message.content.lower() == "a":
                player.move_left()
                await message.channel.send(draw_v5(Game.crnt_game_x, Game.crnt_game_y))

            elif message.content.lower() == "d":
                player.move_right()
                await message.channel.send(draw_v5(Game.crnt_game_x, Game.crnt_game_y))

            # Debug #
            if Game.debugging and message.author.id == Game.gamer:
                await message.channel.send(f"(DEBUG)  Player position is at x: {player.x + 1}, y: {player.y + 1}.")
        else:
            pass


def setup(client):
    client.add_cog(Game(client))
