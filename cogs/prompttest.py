import discord
from discord.ext import commands
from discord import app_commands


def check_if_it_is_me(interaction: discord.Interaction) -> bool:
    return interaction.user.id == 150560836971266048


class PromptTest(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    @app_commands.command(name="hello", description="Testing application command.")
    @app_commands.describe(who="Select someone to greet")
    @app_commands.rename(who="who-to-greet")
    @app_commands.checks.cooldown(rate=1, per=10)
    async def prompt_hello(self, interaction: discord.Interaction, who: discord.User):
        await interaction.response.send_message(f"Hello **{who.display_name}**!")

async def setup(client: commands.Bot):
    return
    await client.add_cog(PromptTest(client))


async def teardown(client: commands.Bot):
    client.tree.remove_command("hello")
