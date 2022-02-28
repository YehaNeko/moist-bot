import discord
from discord.ext import commands
from typing import Any, Callable, Union, Optional
from itertools import chain

# Additional
from functions.additionals.pfgun.CacheManager import cache_arg, get_params
from functions.additionals.pfgun.dicts import *
from functions.additionals.pfgun.SheetReader import get_gun_params


class PfGunEmbed(discord.Embed):
    def __init__(self, ctx: commands.Context):
        super().__init__(
            title="Damage ranges",
            url="https://youtu.be/dQw4w9WgXcQ",
            color=0x00ff40
        )
        self.set_footer(text="Prototype")
        self.set_author(
            name="Requested by " + ctx.author.display_name,
            icon_url=ctx.author.avatar.url
        )

    def gen_embed(self,
                  close_damage: str,
                  long_damage: str,
                  close_range: float,
                  long_range: float,
                  multiplier: float,
                  rpm: float = None

                  ) -> discord.Embed:
        """
        Generate embed fields
        """
        r1 = close_range
        r2 = long_range

        # Remove decimal places
        def remove_decimal(d):
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
                _d1 = remove_decimal(dps(_d1))
                _d2 = remove_decimal(dps(_d2))

                return f"\n {_d1} to {_d2}"
            return ""

        """ Command logic """

        def calculate_range(shot, dmg_close, dmg_long):
            """ Main function for calculating damage ranges """
            dmg_shot = float(shots_to_damage.get(int(shot)))

            # Calculate range
            studs_to_kill = ((dmg_close - dmg_shot) / ((dmg_close - dmg_long) / (r2 - r1))) + r1
            studs_to_kill = round(studs_to_kill, 2)

            # if studs to kill range is smaller than the close range value it's invalid
            if studs_to_kill < r1:
                return None

            # standard range
            elif r1 < studs_to_kill < r2 or studs_to_kill == r1:
                return studs_to_kill, shot

            # if studs to kill range is bigger than the maximum range value it means it's infinite
            elif studs_to_kill >= r2:
                return None, shot

        def shotgun_case():
            d1 = close_damage
            d2 = long_damage

            # separate damage values from pellets
            d1, pellets = [float(d1) for d1 in d1.split("x")]
            d2 = float(d2.split("x")[0]) if "x" in d2 else d2

            # Update embed
            self.add_field(name="1 tap ranges:", value=":100:", inline=False)

            def dmg(d, shots):
                dmg_float = (d * multiplier) * shots
                return remove_decimal(dmg_float)

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
                    self.add_field(
                        name=f"{s} pellets",
                        value=f"0 to **∞** studs"
                              f"\n{dmg1} to {dmg2} damage"
                              f"{add_dps(dmg1, dmg2)} DPS",
                        inline=False,
                    )

                # limited range
                else:
                    self.add_field(
                        name=f"{s} pellets",
                        value=f"0 to {ranges[0]} studs"
                              f"\n{dmg1} to {dmg2} damage"
                              f"{add_dps(dmg1, dmg2)} DPS",
                        inline=False,
                    )

        def normal_case():
            prev_range_value = 0

            for s in range(1, len(shots_to_damage) + 1):
                ranges = calculate_range(s,
                                         float(close_damage) * multiplier,
                                         float(long_damage) * multiplier)

                # invalid range
                if ranges is None:
                    continue

                # break after reaching infinite range
                elif ranges[0] is None:
                    self.add_field(
                        name=f"{ranges[1]} shot",
                        value=f"{prev_range_value} to **∞** studs"
                              f"{add_ttk(rpm, ranges[1])}",
                        inline=False,
                    )
                    break

                # standard range
                else:
                    self.add_field(
                        name=f"{ranges[1]} shot",
                        value=f"{prev_range_value} to {remove_decimal(ranges[0])} studs"
                              f"{add_ttk(rpm, ranges[1])}",
                        inline=False,
                    )
                    prev_range_value = remove_decimal(ranges[0])

        # Check case
        if "x" in close_damage or "x" in long_damage:
            shotgun_case()  # checks for pellets but only uses value from close_range
        else:
            normal_case()

        return self


class Pfgun(commands.Cog):
    def __init__(self, client):
        self.client = client

    @staticmethod
    async def get_user_id(ctx, user: Union[discord.Member, str]) -> str:
        """ Returns string of user.id or ctx.author.id """

        if user is not None and not isinstance(user, discord.Member):
            user = await commands.MemberConverter().convert(ctx, user)

        else:
            user = ctx.author

        return str(user.id)

    @commands.group(brief="Phantom Forces damage range calculator", invoke_without_command=True)
    async def pfgun(self,
                    ctx: commands.Context,
                    close_damage: str,
                    long_damage: str,
                    close_range: float,
                    long_range: float,
                    multiplier: float,
                    rpm: float = None):
        """ Main command """

        embed = PfGunEmbed(ctx).gen_embed(*ctx.args[2:])
        await ctx.reply(embed=embed)

        """ Save to cache """
        if ctx.invoked_with == "pfgun":  # Check if the command wasn't invoked by a subcommand
            cache_arg(ctx.args[1:])  # Args without command object

    @pfgun.command(clean_params=True)
    async def hp(self, ctx, user: Optional[Union[discord.Member, str]] = None):
        """ Applies modifiers to parameters and invokes main command """

        """ Load from cache """
        user = await self.get_user_id(ctx, user)
        params = await get_params(user)

        embed = PfGunEmbed(ctx)

        # Update embed
        embed.set_footer(text="Showing values for HP ammo type")

        def aproximate_r1(_r1):
            return 35 + (_r1 * 0.165)

        params["close_damage"] = str(float(params["close_damage"]) * 1.2)
        params["long_damage"] = str(round(float(params["long_damage"]) * (5 / 6), 2))
        params["long_range"] = params["long_range"] * 0.9

        r1_temp = r1_convert.get(params["close_range"])
        if r1_temp is not None:
            params["close_range"] = r1_temp
        else:
            params["close_range"] = aproximate_r1(params["close_range"])
            embed.add_field(
                name="DISCLAIMER",
                value=r"__Close damage range approximated due to the actual formula being unknown.__"
                      f"\nError margin: +- 1 stud",
                inline=False,
            )
        embed.gen_embed(**params)

        await ctx.reply(embed=embed)

    @pfgun.command(clean_params=True)
    async def ap(self, ctx, user: Optional[Union[discord.Member, str]] = None):
        """ Applies modifiers to parameters and invokes main command """

        """ Load from cache """
        user = await self.get_user_id(ctx, user)
        params = await get_params(user)

        embed = PfGunEmbed(ctx)

        # Update embed
        embed.set_footer(text="Showing values for AP ammo type")

        params["close_range"] = params["close_range"] * 0.5

        embed.gen_embed(**params)

        await ctx.reply(embed=embed)

    @pfgun.command(aliases=["last", "clean", "prev", "previous", "unmod", "unmodified"], clean_params=True)
    async def normal(self, ctx, user: Optional[Union[discord.Member, str]] = None):
        """ Invokes main command without modifiers """

        """ Load from cache """
        user = await self.get_user_id(ctx, user)
        params = await get_params(user)

        embed = PfGunEmbed(ctx).gen_embed(**params)

        # Update embed
        embed.set_footer(text="Showing unmodified values")

        await ctx.reply(embed=embed)

    @pfgun.command(clean_params=True)
    async def gun(self, ctx, *, gun):
        """
        Loads values from *PF Advance Statistics* sheet and invokes main command
        Values from this command are cached
        """
        params = await get_gun_params(gun)
        embed = PfGunEmbed(ctx).gen_embed(**params)

        # Update embed
        embed.set_footer(text=f"Multiplier: {params['multiplier']}\tRPM: {params['rpm']}")

        # Cache
        cache_arg(list(chain.from_iterable([[ctx], params.values()])))

        await ctx.reply(embed=embed)

    @pfgun.command(clean_params=True)
    async def rpm(self, ctx, rpm: Union[int, float]):
        """ Changes *rpm* parameter and invokes main command """
        params = await get_params(str(ctx.author.id))
        embed = PfGunEmbed(ctx)

        # Apply modifiers
        params["rpm"] = rpm

        # Update embed
        embed.set_footer(text=f"Multiplier: {params['multiplier']}\tRPM: {params['rpm']}")

        await ctx.reply(embed=embed)

        # Cache
        cache_arg(list(chain.from_iterable([[ctx], params.values()])))

    @pfgun.command(aliases=["m", "multiplier"], clean_params=True)
    async def multi(self, ctx, multiplier: float):
        """ Changes *multiplier* parameter and invokes main command """
        params = await get_params(str(ctx.author.id))
        embed = PfGunEmbed(ctx)

        # Apply modifiers
        params["multiplier"] = multiplier

        # Update embed
        embed.set_footer(text=f"Multiplier: {params['multiplier']}\tRPM: {params['rpm']}")

        # Cache
        cache_arg(list(chain.from_iterable([[ctx], params.values()])))

        await ctx.reply(embed=embed)


def setup(client):
    client.add_cog(Pfgun(client))
