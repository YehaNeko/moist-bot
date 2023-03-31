import json
from discord.ext import commands

with open(r"./functions/SheetToJson/output_advinfosheet.json", "r") as f:
    data = json.load(f)


async def get_gun_params(gun: str):
    try:
        key = gun.replace("-", "").replace(" ", "").upper()
        values = data["data"][key]

        params = {}
        params["close_damage"], params["long_damage"] =\
            values["BASE DAMAGE"].split(" - ")

        params["close_range"], params["long_range"] = list(
            map(int, values["DAMAGE RANGE"].split(" - "))
        )

        params["multiplier"] = float(
            values["MULTIPLIERS"].split(" / ")[1].strip("x")
        )

        params["rpm"] = [
            int(val)
            for val in values["FIRE RATE"].replace(".", "").replace(",", "").split(" ")
            if val.isdigit()
        ][0]

    except (KeyError, ValueError):
        raise commands.BadArgument()

    return params
