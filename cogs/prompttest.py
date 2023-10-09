from __future__ import annotations

import discord
from discord.ext import commands
from discord import app_commands

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from main import MoistBot


def check_if_it_is_me(interaction: discord.Interaction) -> bool:
    return interaction.user.id == 150560836971266048


class PromptTest(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

    @app_commands.rename(who="who-to-greet")
    @app_commands.describe(who="Select someone to greet")
    @app_commands.checks.cooldown(rate=1, per=10)
    @app_commands.command(name="hello", description="Testing application command.")
    async def prompt_hello(self, interaction: discord.Interaction, *, who: Optional[discord.User] = commands.Author):
        await interaction.response.send_message(f"Hello **{who.display_name}**!")


async def setup(client: MoistBot) -> None:
    return
    await client.add_cog(PromptTest(client))
