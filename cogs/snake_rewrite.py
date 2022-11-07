from __future__ import annotations

import discord
from discord.ext import commands

from typing import TYPE_CHECKING, Any, Optional
from contextlib import contextmanager
from random import randint
from copy import deepcopy
import numpy as np
import time
import logging

if TYPE_CHECKING:
    from main import MoistBot

logger = logging.getLogger('discord.' + __name__)


class SnakeGameContainer:
    """Container for a snake game holding the current game state and logic"""

    assets = {
        "empty": "🟪",
        "apple": "🟥",
        "snake_head": "🟢",
        "snake_body": "🟩",
    }

    def __init__(self, size_x: int = 10, size_y: int = 10):
        """Initial game variables"""

        # Initial game state
        self.field_size: tuple[int, int] = (size_x, size_y)
        self.max_field_size: int = abs(self.field_size[0]) * abs(self.field_size[1])

        self.empty_field = np.empty(self.field_size, dtype="unicode_")

        self.field = self.empty_field.copy()
        self.rendered_field: str | None = None

        # Initial game objects
        self.snake_head: tuple[int, ...] = tuple(
            map(lambda x: round(x / 2), self.field_size)
        )
        self.snake_body = np.empty(shape=(self.max_field_size, 2), dtype='int8')
        self.snake_body[:3] = np.array([[self.snake_head[0] + o, self.snake_head[1]] for o in range(1, 3)], dtype='int8')

        # self.snake_body = np.array([
        #     [self.snake_head[0] + o, self.snake_head[1]] for o in range(1, 3)
        # ])
        self.apple: tuple[int, ...] = (abs(self.snake_head[0] - 3), self.snake_head[1])

        # Game info
        self.game_score: int = 0
        self.alive: bool = True

    def _move_snake(self, x: int, y: int, has_eaten: bool = False) -> None:
        """Increment `self.snake_head` by `x` or `y`"""

        # Value checks
        if x == 0 and y == 0:
            raise ValueError("Both arguments cannot be 0.")
        elif abs(x) > 1 or abs(y) > 1:
            raise ValueError("Cannot move more than 1 tile at once.")

        self.snake_body.insert(0, self.snake_head)

        if not has_eaten:
            self.snake_body.pop()

        sx, sy = self.snake_head
        self.snake_head = (sx + x, sy + y)

    def move_snake(self, x: int = 0, y: int = 0) -> None:
        """Move the snake, respawn apples and do movement checks"""

        # If the snake is about to eat an apple
        has_eaten: bool = (
            self.snake_head[0] + x == self.apple[0]
            and self.snake_head[1] + y == self.apple[1]
        )
        if has_eaten:
            self.game_score += 1

        self._move_snake(x, y, has_eaten)

        # Respawn apple
        while self.apple == self.snake_head or self.apple in self.snake_body:
            self.apple = (
                randint(0, self.field_size[0] - 1),
                randint(0, self.field_size[1] - 1),
            )

        # Movement checks #
        sx, sy = self.snake_head
        if (
            # If the snake hit its own body
            self.snake_head in self.snake_body
            # If the snake hit a wall
            or sx+1 > self.field_size[0] or sy+1 > self.field_size[1]
            or sx < 0 or sy < 0
        ):
            self.game_over()

    @contextmanager
    def _render(self) -> str:
        """Flatten the current field into a single string"""

        self.rendered_field = "\n".join("".join(e) for e in self.field)
        try:
            yield self.rendered_field
        finally:
            # We need to reset the field to its original form
            # for future render passes
            # TODO: Do the thing u wanted to do so the thing does the do of the todo yes do the todo
            self.field = deepcopy(self.empty_field)

    def render(self) -> str:
        """Add game objects and invoke ``self._render``"""

        for obj in self.snake_body:
            self.field[obj[1]][obj[0]] = self.assets["snake_body"]

        self.field[self.snake_head[1]][self.snake_head[0]] = self.assets["snake_head"]
        self.field[self.apple[1]][self.apple[0]] = self.assets["apple"]

        with self._render() as r:
            return r

    def game_over(self):
        """This is called when the player dies.

        The game can technically persist after this
        so ending the game is optional.
        """
        self.alive = False


labels = {
    "up": "Up",
    "left": "Left",
    "down": "Down",
    "right": "Right",
    "quit": "Quit"
}


class SnakeGameView(discord.ui.View):
    def __init__(
        self,
        *,
        ctx: commands.Context,
        game_instance: SnakeGameContainer,
        timeout: Optional[float] = 15,
        message: discord.Message = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self.ctx: commands.Context = ctx
        self.game_instance: SnakeGameContainer = game_instance
        self.message: discord.Message | None = message
        self.opposite_button: discord.ui.Button | None = None
        self.last_opposite_button: discord.ui.Button | None = None
        self._i_check: int = 0

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        self._i_check = time.perf_counter_ns()
        if interaction.user and interaction.user.id == self.ctx.author.id:
            return True
        else:
            await interaction.response.send_message(
                "This game button is not for you.", ephemeral=True
            )
            return False

    async def on_error(self, interaction: discord.Interaction, error: Any, item: Any) -> None:
        logger.exception('Ignoring exception in view %r for item %r', self, item)
        await self._on_game_over("An unknown error occurred!")

    async def on_timeout(self) -> None:
        await self._on_game_over("Took too long to move!")

    async def _on_game_over(self, message: str = "You died!"):
        """Function for when the game has ended"""
        await self.message.edit(
            content=self.game_instance.rendered_field
            + f"\n{message} Final score: {self.game_instance.game_score}",
            view=None,
        )
        self.stop()

    def _set_opposite_button(self, label: str):
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label == labels[label]:
                self.opposite_button = item

    @discord.ui.button(label=labels["quit"], style=discord.ButtonStyle.red, row=0)
    async def quit(self, _interaction: discord.Interaction, _button: discord.ui.Button):
        self.game_instance.alive = False
        await self._on_game_over("You quit!")

    @discord.ui.button(label=labels["up"], style=discord.ButtonStyle.primary, row=0)
    async def up(self, interaction: discord.Interaction, _button: discord.ui.Button):
        self._set_opposite_button("down")
        await self.on_button_interaction(interaction, y=-1)

    @discord.ui.button(label="\u2800", style=discord.ButtonStyle.gray, row=0, disabled=True)
    async def empty1(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label=labels["left"], style=discord.ButtonStyle.primary, row=1)
    async def left(self, interaction: discord.Interaction, _button: discord.ui.Button):
        self._set_opposite_button("right")
        await self.on_button_interaction(interaction, x=-1)

    @discord.ui.button(label=labels["down"], style=discord.ButtonStyle.primary, row=1)
    async def down(self, interaction: discord.Interaction, _button: discord.ui.Button):
        self._set_opposite_button("up")
        await self.on_button_interaction(interaction, y=1)

    @discord.ui.button(label=labels["right"], style=discord.ButtonStyle.primary, row=1)
    async def right(self, interaction: discord.Interaction, _button: discord.ui.Button):
        self._set_opposite_button("left")
        await self.on_button_interaction(interaction, x=1)

    async def on_button_interaction(self, interaction: discord.Interaction,  **kwargs):
        """Callback function of every movement button.
        This handles updating the game and disabling buttons.
        """
        await self.ctx.bot.loop.create_task(interaction.response.defer())

        # Disable opposite movement button so that
        # the snake can't move into itself
        if self.opposite_button is not self.last_opposite_button:
            self.opposite_button.disabled = True
            if self.last_opposite_button:
                self.last_opposite_button.disabled = False
        self.last_opposite_button = self.opposite_button

        self.game_instance.move_snake(**kwargs)

        # Edit original message to the updated game state
        if self.game_instance.alive:
            await self.message.edit(
                content=self.game_instance.render(), view=self
            )
        else:
            await self._on_game_over()
        # logger.info(f"Interaction took {(time.perf_counter_ns() - self._i_check)/1000000}ms")


class SnakeGameRew(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

    @commands.command()
    async def snakerew(self, ctx: commands.Context, x: int = 10, y: int = 10):
        """Play a snake game on discord!"""

        game_instance = SnakeGameContainer(x, y)
        view = SnakeGameView(ctx=ctx, game_instance=game_instance)
        view.message = await ctx.send(game_instance.render(), view=view)

        await view.wait()
        del game_instance, view


async def setup(client: MoistBot):
    await client.add_cog(SnakeGameRew(client))


"""
If this file is opened in a terminal,
the game runs with keyboard controls.
"""
if __name__ == "__main__":
    import keyboard
    import os

    # Init
    game = SnakeGameContainer(20, 20)
    print(game.render())

    last_event_name = None
    while True:
        # Block till the next event
        event = keyboard.read_event()

        # When a key is pressed
        if event.event_type == keyboard.KEY_DOWN:

            # Check each movement key and move the snake accordingly
            if event.name == "w" and not last_event_name == "s":
                game.move_snake(y=-1)
            elif event.name == "a" and not last_event_name == "d":
                game.move_snake(x=-1)
            elif event.name == "s" and not last_event_name == "w":
                game.move_snake(y=1)
            elif event.name == "d" and not last_event_name == "a":
                game.move_snake(x=1)
            else:
                continue
            last_event_name = event.name

            # Quit if the player has died
            if not game.alive:
                print(f"You died! Final score: {game.game_score}")
                quit()

            os.system("cls||clear")
            print(game.render())
