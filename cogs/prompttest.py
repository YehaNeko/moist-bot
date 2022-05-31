import discord
from discord.ext import commands
from discord import ui, app_commands
from config import GUILD


def check_if_it_is_me(interaction: discord.Interaction) -> bool:
    return interaction.user.id == 150560836971266048


class PromptTest(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        self.client.tree.add_command(self.prompt_test, guild=discord.Object(id=GUILD))

    @app_commands.command(name="prompt", description="Testing application command.")
    @app_commands.describe(test_var="A variable used to test inputs.")
    @app_commands.rename(test_var="test-variable")
    @app_commands.check(check_if_it_is_me)
    async def prompt_test(self, interaction: discord.Interaction, test_var: str = "placeholder"):
        await interaction.response.send_message("This is a test\n" + test_var,
                                                ephemeral=True)


async def setup(client):
    await client.add_cog(PromptTest(client))


async def teardown(client: commands.Bot):
    client.tree.remove_command("prompt")
