from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Iterator
from contextlib import contextmanager
from numpy.random import default_rng
from inspect import cleandoc
from functools import wraps
import numpy as np
import logging
import time

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from main import MoistBot

logger = logging.getLogger('discord.' + __name__)
DO_PERF_TIMING: bool = False


class SnakeGameContainer(object):
    """Container for a snake game holding the current game state and logic"""

    __slots__ = [
        'field_size', 'max_field_size', 'empty_field', 'field', 'rendered_field', 'init_snake_body_len',
        'snake_head', 'moved_snake_head', 'snake_body', 'apple', 'game_score', 'alive', 'snake_body_size',
        'perf_move_snake_begin', 'perf_move_snake_end', 'perf_render_begin', 'perf_render_end',
    ]

    assets = {
        'empty': '🟪',
        'apple': '🟥',
        'snake_head': '🟢',
        'snake_body': '🟩',
    }
    rng = default_rng()
    perf_timing: bool = DO_PERF_TIMING

    @staticmethod
    def perf_timer(begin_out: str = '', end_out: str = ''):
        def inner(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                self: SnakeGameContainer = args[0]

                # Skip
                if not self.perf_timing:
                    func(*args, **kwargs)
                    return

                if begin_out:
                    setattr(self, begin_out, time.perf_counter_ns())
                func(*args, **kwargs)
                if end_out:
                    setattr(self, end_out, time.perf_counter_ns())

            return wrapper
        return inner

    def __init__(self, size_x: int = 10, size_y: int = 10):
        """Initial game variables"""
        if size_x < 0 or size_y < 0:
            raise ValueError("A size value cannot be negative.")

        # Initial game state
        self.field_size = np.array((size_x, size_y), dtype='uint8')
        self.max_field_size: int = self.field_size.prod()

        self.empty_field = np.full(self.field_size, self.assets['empty'], dtype='unicode_')
        self.field = self.empty_field.copy()
        self.rendered_field: str = ''

        # Initial game objects
        self.init_snake_body_len: int = 2

        self.snake_head = np.array(
            tuple(map(lambda x: round(x / 2), self.field_size)),
            dtype='uint8'
        )
        self.moved_snake_head = self.snake_head.copy()  # Temp default value

        # By default, generates initial snake bodies to the right of `self.snake_head`,
        # lengthened with `self.init_snake_body_len`
        self.snake_body = np.full((self.max_field_size, 2), -1, dtype='int8')
        self.snake_body[: self.init_snake_body_len] = np.array(
            [
                [self.snake_head[0] + o, self.snake_head[1]]
                for o in range(1, self.init_snake_body_len + 1)
            ],
            dtype='int8',
        )

        self.apple = np.array((abs(self.snake_head[0] - 3), self.snake_head[1]), dtype='uint8')

        # Game info
        self.game_score: int = 0
        self.alive: bool = True
        self.snake_body_size: int = self.init_snake_body_len

        # Perf timings
        self.perf_move_snake_begin: int = 0
        self.perf_move_snake_end: int = 0
        self.perf_render_begin: int = 0
        self.perf_render_end: int = 0

    def _move_snake(self, x: int, y: int, has_eaten: bool = False) -> None:
        """Increment `self.snake_head` by `x` or `y`"""

        # Value checks
        if x == y == 0:
            raise ValueError("Both arguments cannot be 0.")
        elif x + y > 1:
            raise ValueError("Cannot move more than 1 tile at once.")

        self.snake_body = np.roll(self.snake_body, 1, axis=0)
        self.snake_body.put((0, 1), self.snake_head)

        if not has_eaten:
            self.snake_body[self.snake_body_size + 1] = (-1, -1)

        self.snake_head = self.moved_snake_head

    @perf_timer('perf_move_snake_begin', 'perf_move_snake_end')
    def move_snake(self, x: int = 0, y: int = 0) -> None:
        """Move the snake, respawn apples and do movement checks.
        This essentially works as the event loop.
        """

        # If the snake is about to eat an apple
        self.moved_snake_head = self.snake_head.copy() + (x, y)
        if has_eaten := np.array_equal(self.moved_snake_head, self.apple):
            self.game_score += 1
            self.snake_body_size += 1

        self._move_snake(x, y, has_eaten)

        # Win condition
        if self.snake_body_size + 1 == self.max_field_size:
            self.win_game()
            return

        # Respawn apple
        while (
                np.any(np.all(self.apple == self.snake_body[: self.snake_body_size], axis=1)) or
                np.array_equal(self.apple, self.snake_head)
        ):
            self.apple[:] = np.array(
                    (self.rng.integers(0, self.field_size[0] - 1, dtype='uint8'),
                     self.rng.integers(0, self.field_size[1] - 1, dtype='uint8'))
            )   # TODO: needs to be checked for perf, may be just faster to use a tuple instead of a np.array

        # Movement checks #
        # Game over conditions
        if (
            # If the snake hit its own body
            np.any(np.all(self.snake_head == self.snake_body[: self.snake_body_size], axis=1))
            # If the snake hit a wall
            or np.any(self.snake_head + (1, 1) > self.field_size)
            or np.any(self.snake_head < (0, 0))
        ):
            self.game_over()

    @contextmanager
    def _render(self) -> Iterator[str]:
        """Flatten the current field array into a single string"""

        try:
            # TODO: use numpy funcs maybe idk
            self.rendered_field = '\n'.join(''.join(e) for e in self.field)
            yield self.rendered_field
        finally:
            # We need to reset the field to its original form
            # for future render passes
            self.field = self.empty_field.copy()
            self.perf_render_end = time.perf_counter_ns()

    def render(self) -> str:
        """Add game objects and invoke ``self._render``"""
        self.perf_render_begin: int = time.perf_counter_ns()

        for obj in self.snake_body[: self.snake_body_size]:
            self.field[obj[1], obj[0]] = self.assets['snake_body']

        self.field[self.snake_head[1], self.snake_head[0]] = self.assets['snake_head']
        self.field[self.apple[1], self.apple[0]] = self.assets['apple']

        with self._render() as r:
            return r

    def game_over(self) -> None:
        """This is called when the player dies.

        The game can technically persist after this
        so ending the game is optional.
        """
        self.alive = False

    def win_game(self) -> None:
        """TODO: make event
        """
        logger.info("win")
        self.game_over()


labels = {
    'up': 'Up',
    'left': 'Left',
    'down': 'Down',
    'right': 'Right',
    'quit': 'Quit'
}


class SnakeGameView(discord.ui.View):
    def __init__(
        self,
        *,
        ctx: commands.Context,
        game_instance: SnakeGameContainer,
        message: discord.Message = None,  # type: ignore
        timeout: Optional[float] = 15,
    ):
        super().__init__(timeout=timeout)
        self.ctx: commands.Context = ctx
        self.game_instance: SnakeGameContainer = game_instance
        self.message: discord.Message = message
        self.opposite_button: discord.ui.Button = None  # type: ignore
        self.last_opposite_button: discord.ui.Button = None  # type: ignore
        self._i_check: int = 0

        if self.game_instance.perf_timing:
            logger.info(
                "Interation \x1b[42;1mstarted\x1b[0m for \x1b[36;1m%s\x1b[0m \x1b[90m(%s)\x1b[0m \n"
                "in guild \x1b[36;1m%s\x1b[0m \x1b[90m(%s)\x1b[0m!",
                self.ctx.author.name + '#' + self.ctx.author.discriminator, self.ctx.author.id,
                *(self.ctx.guild.name, self.ctx.guild.id) if self.ctx.guild else (None, None)
            )

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
        logger.exception("Ignoring exception in view %r for item %r", self, item)
        await self._on_game_over("An unknown error occurred!")

    async def on_timeout(self) -> None:
        await self._on_game_over("Took too long to move!")

    async def _on_game_over(self, message: str = "You died!") -> None:
        """Function for when the game has ended"""
        await self.message.edit(
            content=self.game_instance.rendered_field
            + f"\n{message} Final score: {self.game_instance.game_score}",
            view=None,
        )
        self.stop()
        if self.game_instance.perf_timing:
            logger.info("Interation \x1b[41;1mended\x1b[0m for \x1b[36;1m%s\x1b[0m \x1b[90m(%s)\x1b[0m.",
                        self.ctx.author.name + '#' + self.ctx.author.discriminator, self.ctx.author.id)

    def _set_opposite_button(self, label: str) -> None:
        """Finds and sets the `discord.ui.Button` object
         that has the specified label from a str
         """
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.label == labels[label]:
                self.opposite_button = item
                break

    @discord.ui.button(label=labels['quit'], style=discord.ButtonStyle.red, row=0)
    async def quit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.game_instance.alive = False
        await self._on_game_over('You quit!')

    @discord.ui.button(label=labels['up'], style=discord.ButtonStyle.primary, row=0)
    async def up(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._set_opposite_button('down')
        await self.on_button_interaction(interaction, y=-1)

    @discord.ui.button(label="\u2800", style=discord.ButtonStyle.gray, row=0, disabled=True)
    async def empty1(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label=labels['left'], style=discord.ButtonStyle.primary, row=1)
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._set_opposite_button('right')
        await self.on_button_interaction(interaction, x=-1)

    @discord.ui.button(label=labels['down'], style=discord.ButtonStyle.primary, row=1)
    async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._set_opposite_button('up')
        await self.on_button_interaction(interaction, y=1)

    @discord.ui.button(label=labels['right'], style=discord.ButtonStyle.primary, row=1)
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        self._set_opposite_button('left')
        await self.on_button_interaction(interaction, x=1)

    async def on_button_interaction(self, interaction: discord.Interaction, **kwargs):
        """Callback function of every movement button.
        This handles updating the game and disabling buttons.
        """
        await interaction.response.defer()

        # Disable opposite movement button so that
        # the snake can't move into itself
        if self.opposite_button is not self.last_opposite_button:
            self.opposite_button.disabled = True
            if self.last_opposite_button:
                self.last_opposite_button.disabled = False
        self.last_opposite_button = self.opposite_button

        # Move
        self.game_instance.move_snake(**kwargs)

        # Edit original message to the updated game state
        perf_await_api_begin = time.perf_counter_ns()
        if self.game_instance.alive:
            await self.message.edit(content=self.game_instance.render(), view=self)
        else:
            await self._on_game_over()

        # Log perf timings
        perf_end = time.perf_counter_ns()
        if (g := self.game_instance).perf_timing:
            logger.info(cleandoc("""
            Interation \x1b[44mtimings\x1b[0m for \x1b[36;1m%s\x1b[0m \x1b[90m(%s)\x1b[0m,
            in guild \x1b[36;1m%s\x1b[0m \x1b[90m(%s)\x1b[0m:
            Interation start
            |    +>Event loop start
            |    | |
            |    | Event loop took %sms
            |    | 
            |    | Render cycle start
            |    | |
            |    | Render cycle took %sms
            |    +-> Frame latency %sms, %s fps (in theory)
            |    
            |    +>Await discord gateway api call
            |    |
            |    +->Discord gateway response in %sms
            |
            Full interaction (including overheads) took %sms"""),
            self.ctx.author.name + '#' + self.ctx.author.discriminator, self.ctx.author.id,
            *(self.ctx.guild.name, self.ctx.guild.id) if self.ctx.guild else (None, None),
            (a := g.perf_move_snake_end - g.perf_move_snake_begin) / 1_000_000,
            (b := g.perf_render_end - g.perf_render_begin) / 1_000_000,
            (c := a + b) / 1_000_000, round(10**9 / c),
            (perf_end - perf_await_api_begin) / 1_000_000,
            (perf_end - self._i_check) / 1_000_000)
            # TODO: holy shit this is absolute spaghetti code


active_snake_games: dict[int, SnakeGameView] = {}
class SnakeGame(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

    @commands.hybrid_command(with_app_command=False)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    @app_commands.describe(
        x="Game size along the *x* axis",
        y="Game size along the *y* axis"
    )
    async def snake(self, ctx: commands.Context, x: Optional[int] = 10, y: Optional[int] = 10):
        """Play a snake game on discord!"""

        # Size check
        if abs(x * y) >= 200:
            return await ctx.reply(":anger: Game size is too big!")

        game_instance = SnakeGameContainer(x, y)
        view = SnakeGameView(ctx=ctx, game_instance=game_instance)
        view.message = message = await ctx.send(game_instance.render(), view=view)
        active_snake_games.update({message.id: view})

        # Cleanup
        await view.wait()  # Blocking
        active_snake_games.pop(message.id)
        del game_instance, view

async def setup(client: MoistBot):
    await client.add_cog(SnakeGame(client))


"""
If this file is opened in a terminal,
the game runs with keyboard controls
(mostly used for debugging).
"""
if __name__ == '__main__':
    import keyboard

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
            if event.name == 'w' and not last_event_name == 's':
                game.move_snake(y=-1)
            elif event.name == 'a' and not last_event_name == 'd':
                game.move_snake(x=-1)
            elif event.name == 's' and not last_event_name == 'w':
                game.move_snake(y=1)
            elif event.name == 'd' and not last_event_name == 'a':
                game.move_snake(x=1)
            else:
                continue
            last_event_name = event.name

            # Quit if the player has died
            if not game.alive:
                print(f"You died! Final score: {game.game_score}")
                quit()

            print(game.render())
