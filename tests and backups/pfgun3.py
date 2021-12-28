import discord
from discord.ext import commands
import json
from typing import Any, Callable, Union


class Pfgun(commands.Cog):
# class Temp:
    def __init__(self, client):
        self.client = client

    shots_to_damage = {
        1: "100",
        2: "50",
        3: "33.34",
        4: "25",
        5: "20",
        6: "16.67",
        7: "14.29",
        8: "12.5",
        9: "11.12",
        10: "10",
        11: "9.1",
        12: "8.34",
    }
    """ Create embed """
    embed = discord.Embed(
        title="Damage ranges", url="https://youtu.be/dQw4w9WgXcQ", color=0x00FF40
    )
    embed.set_footer(text="Prototype")

    @commands.group(
        brief="Phantom Forces damage range calcualtor", invoke_without_command=True
    )
    async def pfgun(
        self,
        ctx,
        close_damage: str,
        long_damage: str,
        close_range: float,
        long_range: float,
        multiplier: float,
        rpm: float = None,
    ):
        """Main command, calculates ranges and generates embed"""

        d1 = close_damage
        d2 = long_damage
        r1 = close_range
        r2 = long_range

        # Embed start
        self.embed.set_author(
            name="Requested by " + ctx.author.display_name,
            icon_url=ctx.author.avatar_url_as(
                format=None, static_format="jpg", size=256
            ),
        )
        prev_range_value = 0

        """ Save to cache """
        if (
            ctx.invoked_with == "pfgun"
        ):  # Check if the command was not invoked by a subcommand
            with open("pfgun_cache.json", "r") as f:
                data = json.load(f)

                user = str(ctx.author.id)
                users = {}
                args = {
                    "d1": d1,
                    "d2": d2,
                    "r1": r1,
                    "r2": r2,
                    "multiplier": multiplier,
                    "rpm": rpm,
                }

                # Get rid of old arguments if user alredy in cache
                for num, u in enumerate(data["users"]):
                    if user in u:
                        del data["users"][num]
                        break

                # Add arguments as dict
                users[user] = args
                data["users"].append(users)

            # Save to file
            with open("pfgun_cache.json", "w") as f:
                json.dump(data, f, indent=4)

        """ Helper functions """

        # Remove decimal places
        def rmv_dcml(d):
            return round(d) if int(str(d).split(".")[1]) == 0 else round(d, 2)

        # Add time to kill
        def add_ttk(_rpm, _shot):
            if rpm is not None:
                ttk = (60 * (_shot - 1)) / _rpm
                return "\n" + str(round(ttk, 5)) + "s to kill" if ttk != 0 else ""
            return ""

        # Add damage per second
        def add_dps(_d1, _d2):
            dps: Callable[[Any], Union[float, int]] = lambda d: (rpm / 60) * d

            if rpm is not None:
                _d1 = rmv_dcml(dps(_d1))
                _d2 = rmv_dcml(dps(_d2))

                return f"\n {_d1} to {_d2}"
            return ""

        """ Command logic """

        def calculate_range(shot, dmg_close, dmg_long):
            """Main function for calculatoing damage ranges"""

            # damage drop per stud
            dmg_drop_per_stud = (dmg_close - dmg_long) / (r2 - r1)

            # leftover damage
            excess_dmg = dmg_close - float(self.shots_to_damage.get(int(shot)))

            # converts leftover damage into studs
            studs_after_close_range_dmg = excess_dmg / dmg_drop_per_stud

            # studs to kill range
            studs_to_kill = studs_after_close_range_dmg + r1
            studs_to_kill = round(studs_to_kill, 2)

            # if studs to kill range is smaller than the close range value it's invalid
            if studs_to_kill < r1:
                return None

            # standard range
            elif r1 < studs_to_kill < r2 or studs_to_kill == r1:
                return studs_to_kill, shot

            # if studs to kill range is bigger than the maximum range value it means it's infinate
            elif studs_to_kill >= r2:
                return None, shot

        """ Shotgun case """
        if "x" in d1 or "x" in d2:  # checks for pellets but only uses value from d1

            # seperate damage values from pellets
            d1, pellets = [float(d1) for d1 in d1.split("x")]
            d2 = float(d2.split("x")[0]) if "x" in d2 else d2

            # Update embed
            self.embed.add_field(name="1 tap ranges:", value=":100:", inline=False)

            def dmg(d, shots):
                dmg_float = (d * multiplier) * shots
                return rmv_dcml(dmg_float)

            for s in range(1, round(pellets) + 1):  # +1 cuz THAT'S HOW MAFIA WORKS

                # get values
                dmg1 = dmg(d1, s)
                dmg2 = dmg(d2, s)
                ranges = calculate_range(1, dmg1, dmg2)

                # invalid range
                if ranges is None:
                    continue

                # inf range
                elif ranges[0] is None:
                    self.embed.add_field(
                        name=f"{s} pellets",
                        value=f"0 to **∞** studs"
                        f"\n{dmg1} to {dmg2} damage"
                        f"{add_dps(dmg1, dmg2)} DPS",
                        inline=False,
                    )

                # limited range
                else:
                    self.embed.add_field(
                        name=f"{s} pellets",
                        value=f"0 to {ranges[0]} studs"
                        f"\n{dmg1} to {dmg2} damage"
                        f"{add_dps(dmg1, dmg2)} DPS",
                        inline=False,
                    )

            """ Normal case """
        else:
            for s in range(1, len(self.shots_to_damage) + 1):
                ranges = calculate_range(
                    s, float(d1) * multiplier, float(d2) * multiplier
                )

                # invalid range
                if ranges is None:
                    continue

                # break after reaching infinate range
                elif ranges[0] is None:
                    self.embed.add_field(
                        name=f"{ranges[1]} shot",
                        value=f"{prev_range_value} to **∞** studs"
                        f"{add_ttk(rpm, ranges[1])}",
                        inline=False,
                    )
                    break

                # standard range
                else:
                    self.embed.add_field(
                        name=f"{ranges[1]} shot",
                        value=f"{prev_range_value} to {rmv_dcml(ranges[0])} studs"
                        f"{add_ttk(rpm, ranges[1])}",
                        inline=False,
                    )
                    prev_range_value = rmv_dcml(ranges[0])

        # Send embed
        await ctx.reply(embed=self.embed)

        # Reset embed
        self.embed.clear_fields()
        self.embed.set_footer(text="Prototype")

    @staticmethod
    def get_params(user):
        """Returns parameters of specified user from cache"""

        with open("pfgun_cache.json", "r") as f:
            data = json.load(f)

            for u in data["users"]:
                if user in u:
                    return u[user]

    @staticmethod
    def get_user_id(ctx, user: Union[discord.Member, str, None]):
        """Returns id of mentioned user or author"""

        if not isinstance(user, discord.Member):
            user = ctx.author
        return str(user.id)

    @pfgun.command(clean_params=True)
    async def hp(self, ctx, user: Union[discord.Member, str] = None):
        """Applies modifiers to parameters and invokes main command"""

        # Update embed
        self.embed.set_footer(text="Showing values for HP ammo type")

        """ Load from cache """
        user = self.get_user_id(ctx, user)
        params = self.get_params(user)

        r1_convert = {
            18.7: 32.21,  # MP5SD lb
            20: 32.95,
            21.25: 33.61,
            22: 34.00,
            25: 35.40,
            25.5: 35.62,  # VECTOR lb
            30: 37.41,
            32: 38.12,
            35: 39.10,
            40: 40.57,
            45: 41.81,
            48: 42.58,
            50: 43.03,
            51: 43.25,
            52: 43.46,
            55: 44.08,
            59.5: 44.49,
            60: 45.08,
            63.75: 45.70,
            63.9: 45.73,
            65: 45.91,
            70: 46.73,
            75: 47.49,
            80: 48.20,
            88: 49.25,  # SL-8
            90: 49.49,
            97.5: 50.37,
            100: 50.65,
            110: 51.70,
            120: 52.66,
        }

        def aproximate_r1(_r1):
            return 35 + (_r1 * 0.165)

        d1 = float(params["d1"]) * 1.2
        d2 = round(float(params["d2"]) * (5 / 6), 2)

        r1_temp = r1_convert.get(params["r1"])
        if r1_temp is not None:
            r1 = r1_temp
        else:
            r1 = aproximate_r1(params["r1"])
            self.embed.add_field(
                name=f"DISCLAMER",
                value=f"__Close damage range aproximated due to the actual formula being unknown.__\n"
                r"Error margin: +- 1 stud",
                inline=False,
            )

        r2 = params["r2"] * 0.9
        multiplier = params["multiplier"]
        rpm = params["rpm"]

        await ctx.invoke(
            ctx.bot.get_command("pfgun"),
            close_damage=str(d1),
            long_damage=str(d2),
            close_range=r1,
            long_range=r2,
            multiplier=multiplier,
            rpm=rpm,
        )

    @pfgun.command(clean_params=True)
    async def ap(self, ctx, user: Union[discord.Member, str] = None):
        """Applies modifiers to parameters and invokes main command"""

        self.embed.set_footer(text="Showing values for AP ammo type")  # Update embed
        user = self.get_user_id(ctx, user)

        """ Load from cache """
        params = self.get_params(user)

        d1 = params["d1"]
        d2 = params["d2"]
        r1 = params["r1"] * 0.5
        r2 = params["r2"]
        multiplier = params["multiplier"]
        rpm = params["rpm"]

        await ctx.invoke(
            ctx.bot.get_command("pfgun"),
            close_damage=str(d1),
            long_damage=str(d2),
            close_range=r1,
            long_range=r2,
            multiplier=multiplier,
            rpm=rpm,
        )

    @pfgun.command(
        aliases=["last", "clean", "prev", "previous", "unmod", "unmodified"],
        clean_params=True,
    )
    async def normal(self, ctx, user: Union[discord.Member, str] = None):
        """reinvokes main command without modifiers"""

        # Update embed
        self.embed.set_footer(text="Showing unmodified values")  # Update embed
        user = self.get_user_id(ctx, user)

        """ Load from cache """
        params = self.get_params(user)

        # TODO: delete this and just put it in the invoke
        d1 = params["d1"]
        d2 = params["d2"]
        r1 = params["r1"]
        r2 = params["r2"]
        multiplier = params["multiplier"]
        rpm = params["rpm"]
        #

        await ctx.invoke(
            ctx.bot.get_command("pfgun"),
            close_damage=str(d1),
            long_damage=str(d2),
            close_range=r1,
            long_range=r2,
            multiplier=multiplier,
            rpm=rpm,
        )

    @commands.command(name="ranges", brief="Info about damage")
    async def gun_ranges(self, ctx):
        """Small command for showing damage needed for every shot to kill"""

        """ Create embed """
        embed = discord.Embed(
            title="Damage ranges", url="https://youtu.be/dQw4w9WgXcQ", color=0x00FF40
        )
        embed.set_author(
            name="Requested by " + ctx.author.display_name,
            icon_url=ctx.author.avatar_url_as(
                format=None, static_format="jpg", size=256
            ),
        )
        embed.set_footer(text="Values rounded to 2nd decimal place")

        """ Command logic """
        for s in range(1, len(self.shots_to_damage) + 1):

            next_value = self.shots_to_damage.get(s)

            if s == 1:
                embed.add_field(
                    name=f"{s} shot",
                    value=f"**∞** to {next_value} damage",
                    inline=False,
                )
                continue

            current_value = float(self.shots_to_damage.get(s - 1))
            embed.add_field(
                name=f"{s} shot",
                value=f"{round(current_value - 0.01, 2)} to {next_value} damage",
                inline=False,
            )

            if len(self.shots_to_damage) - 1 == s:
                break

        await ctx.reply(embed=embed)


# def setup(client):
#     client.add_cog(Pfgun(client))
