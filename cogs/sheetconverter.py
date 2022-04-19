import discord
from discord.ext import commands
import json
import os
from functions.SheetToJson.SheetToJson import sheet_to_json
cwd = os.getcwd()


class SheetConverter(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name="loadsheet")
    async def load_sheet(self, ctx, output: bool = False):
        if ctx.author.id == 150560836971266048:

            attachment = ctx.message.attachments[0]
            file = os.path.join(cwd, attachment.filename)
            await attachment.save(fp=file)

            # TODO: load from output.json instead
            with open("sheet.json", "w") as s:
                data = json.loads(sheet_to_json(file, output_to_file=output))
                json.dump(data, s, indent=2)

            await ctx.reply(file=discord.File("sheet.json"))

            os.remove("sheet.json")
            os.remove(file)


async def setup(client):
    await client.add_cog(SheetConverter(client))
