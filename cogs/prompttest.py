import discord
from discord.ext import commands
from discord import app_commands

from typing import Optional


def check_if_it_is_me(interaction: discord.Interaction) -> bool:
    return interaction.user.id == 150560836971266048


class PromptTest(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        self.client.tree.add_command(self.prompt_hello, guild=None, override=True)

    @app_commands.command(name="hello", description="Testing application command.")
    @app_commands.describe(who="Select someone to greet")
    @app_commands.rename(who="who-to-greet")
    async def prompt_hello(self, interaction: discord.Interaction, who: Optional[discord.User] = None):
        await interaction.response.send_message(f"Hello **{who.display_name}**!")


async def setup(client):
    await client.add_cog(PromptTest(client))


async def teardown(client: commands.Bot):
    client.tree.remove_command("hello")
