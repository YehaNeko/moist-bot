from __future__ import annotations

import discord
from discord.ext import commands

from math import log10
from itertools import chain
from typing_extensions import Self
from typing import TYPE_CHECKING, Union, Optional

# Additional
from cogs.pfgun_utils.dicts import *
from cogs.pfgun_utils.CacheManager import cache_arg, get_params

if TYPE_CHECKING:
    from main import MoistBot
    from cogs.utils.context import Context


"""
THIS CODE IS ABSOLUTE SLOP THAT I WROTE A LONG TIME AGO.
I WILL REWRITE THIS EVENTUALLY.
MEOW.
"""


class PfGunEmbed(discord.Embed):
    def __init__(self, ctx: Context):
        super().__init__(
            title='Damage ranges',
            url='https://youtu.be/dQw4w9WgXcQ',
            color=0x00ff40
        )
        self.set_footer(text='dev forgor to set the footer text xd')
        self.set_author(
            name='Requested by ' + ctx.author.display_name,
            icon_url=ctx.author.display_avatar.url
        )

    def gen_embed(
            self,
            close_damage: int | str,
            long_damage: int | str,
            close_range: float,
            long_range: float,
            multiplier: float,
            rpm: float = None  # type: ignore

    ) -> Self:
        """Generate embed fields"""
        r1 = close_range
        r2 = long_range

        # Remove decimal places
        def remove_decimal(d: float) -> int | float:
            return round(d) if int(str(d).split('.')[1]) == 0 else round(d, 2)

        # Add time to kill
        def add_ttk(_rpm, _shot) -> str:
            if rpm:
                ttk = (60 * (_shot - 1)) / _rpm
                return '\n' + str(round(ttk, 5)) + 's to kill' if ttk != 0 else ''
            return ''

        # Add damage per second
        def add_dps(_d1, _d2) -> str:
            dps: callable = lambda d: (rpm / 60) * d

            if rpm:
                _d1 = remove_decimal(dps(_d1))
                _d2 = remove_decimal(dps(_d2))
                return f'\n {_d1} to {_d2}'
            return ''

        ''' Command logic '''
        def calculate_range(shot: int, dmg_close: float, dmg_long: float) -> float:
            """Main function for calculating damage ranges"""
            dmg_shot = float(shots_to_damage.get(int(shot)))

            # Calculate range
            studs_to_kill = ((dmg_close - dmg_shot) / ((dmg_close - dmg_long) / (r2 - r1))) + r1
            studs_to_kill = round(studs_to_kill, 2)

            return studs_to_kill

        def shotgun_case():
            d1 = close_damage
            d2 = long_damage

            # separate damage values from pellets
            d1, pellets, *_ = (float(d1) for d1 in d1.split('x'))
            d2 = float(d2.split('x')[0] if 'x' in d2 else d2)

            # Update embed
            self.add_field(name='1 tap ranges:', value=':100:', inline=False)

            def dmg(d, shots) -> int | float:
                dmg_float = (d * multiplier) * shots
                return remove_decimal(dmg_float)

            for s in range(1, round(pellets) + 1):  # +1 cuz THAT'S HOW MAFIA WORKS
                # get values
                dmg1 = dmg(d1, s)
                dmg2 = dmg(d2, s)
                studs_to_kill = calculate_range(1, dmg1, dmg2)

                # if studs to kill range is smaller than the close range value it's invalid
                if studs_to_kill < r1:
                    continue

                # inf range
                elif studs_to_kill >= r2:
                    self.add_field(
                        name=f'{s} pellets',
                        value=f'0 to **∞** studs'
                              f'\n{dmg1} to {dmg2} damage'
                              f'{add_dps(dmg1, dmg2)} DPS',
                        inline=False,
                    )

                # limited range
                self.add_field(
                    name=f'{s} pellets',
                    value=f'0 to {studs_to_kill} studs'
                          f'\n{dmg1} to {dmg2} damage'
                          f'{add_dps(dmg1, dmg2)} DPS',
                    inline=False,
                )

        def normal_case():
            prev_range_value = 0

            for s in range(1, len(shots_to_damage) + 1):
                studs_to_kill = calculate_range(
                    s,
                    float(close_damage) * multiplier,
                    float(long_damage) * multiplier
                )

                # if studs to kill range is smaller than the close range value it's invalid
                if studs_to_kill < r1:
                    continue

                # break after reaching infinite range
                elif studs_to_kill >= r2:
                    self.add_field(
                        name=f'{s} shot',
                        value=f'{prev_range_value} to **∞** studs{add_ttk(rpm, s)}',
                        inline=False,
                    )
                    break

                # standard range
                # if r1 < studs_to_kill < r2 or studs_to_kill == r1:
                self.add_field(
                    name=f'{s} shot',
                    value=f'{prev_range_value} to {remove_decimal(studs_to_kill)} studs{add_ttk(rpm, s)}',
                    inline=False,
                )
                prev_range_value = remove_decimal(studs_to_kill)

        # Check case
        if 'x' in close_damage or 'x' in long_damage:
            shotgun_case()  # checks for pellets but only uses value from close_range
        else:
            normal_case()

        return self


class Pfgun(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

    @commands.group(invoke_without_command=True)
    async def pfgun(
            self,
            ctx: Context,
            close_damage: str,
            long_damage: str,
            close_range: float,
            long_range: float,
            multiplier: float = 1.0,
            rpm: Optional[float] = None  # type: ignore
    ):
        """Phantom Forces damage range calculator."""

        embed = PfGunEmbed(
            ctx
        ).gen_embed(
            *ctx.args[2:]
        ).set_footer(
            text=f"Multiplier: {multiplier}\tRPM: {rpm}"
        )
        await ctx.reply(embed=embed)

        ''' Save to cache '''
        if ctx.invoked_with == 'pfgun':  # Check if the command wasn't invoked by a subcommand
            cache_arg(ctx.args[1:])  # Args without command object

    @pfgun.command()
    async def hp(self, ctx: Context, *, user: Optional[discord.User] = commands.Author):
        """Applies modifiers to parameters and invokes main command"""

        ''' Load from cache '''
        user = str(user.id)
        params = await get_params(user)

        # Update embed
        embed = PfGunEmbed(
            ctx
        ).set_footer(
            text='Showing values for HP ammo type'
        )

        # Apply modifiers
        params['close_damage'] = str(float(params['close_damage']) * 1.2)
        params['long_damage'] = str(round(float(params['long_damage']) * (5 / 6), 2))
        params['close_range'] = 25.325 * log10(params['close_range'])
        params['long_range'] *= 0.9

        # Update embed
        embed.gen_embed(**params)

        await ctx.reply(embed=embed)

    @pfgun.command()
    async def ap(self, ctx: Context, *, user: Optional[discord.User] = commands.Author):
        """ Applies modifiers to parameters and invokes main command """

        ''' Load from cache '''
        user = str(user.id)
        params = await get_params(user)

        # Apply modifiers
        params['close_range'] *= 0.5

        # Update embed
        embed = PfGunEmbed(
            ctx
        ).gen_embed(
            **params
        ).set_footer(
            text='Showing values for AP ammo type'
        )

        await ctx.reply(embed=embed)

    @pfgun.command(aliases=['last', 'clean', 'prev', 'previous', 'unmod', 'unmodified'])
    async def normal(self, ctx: Context, *, user: Optional[discord.User] = commands.Author):
        """ Invokes main command without modifiers """

        ''' Load from cache '''
        user = str(user.id)
        params = await get_params(user)

        # Update embed
        embed = PfGunEmbed(
            ctx
        ).gen_embed(
            **params
        ).set_footer(
            text=f"Multiplier: {params['multiplier']}\tRPM: {params['rpm']}"
        )

        await ctx.reply(embed=embed)

    # @pfgun.command(clean_params=True)
    # async def gun(self, ctx, *, gun):
    #     """
    #     Loads values from *PF Advance Statistics* sheet and invokes main command
    #     Values from this command are cached
    #     """
    #     params = await get_gun_params(gun)
    #
    #     # Update embed
    #     embed = PfGunEmbed(ctx)\
    #         .gen_embed(**params)\
    #         .set_footer(text=f"Multiplier: {params['multiplier']}\tRPM: {params['rpm']}")
    #
    #     await ctx.reply(embed=embed)
    #
    #     # Cache
    #     cache_arg(list(chain.from_iterable([[ctx], params.values()])))

    @pfgun.command()
    async def rpm(self, ctx: Context, rpm: Union[int, float]):
        """Changes *rpm* parameter and invokes main command"""
        params = await get_params(str(ctx.author.id))

        # Apply modifiers
        params['rpm'] = rpm

        # Update embed
        embed = PfGunEmbed(
            ctx
        ).gen_embed(
            **params
        ).set_footer(
            text=f"Multiplier: {params['multiplier']}\tRPM: {params['rpm']}"
        )

        await ctx.reply(embed=embed)

        # Cache
        cache_arg(list(chain.from_iterable([[ctx], params.values()])))

    @pfgun.command(aliases=['m', 'multiplier'])
    async def multi(self, ctx: Context, multiplier: float):
        """Changes *multiplier* parameter and invokes main command"""
        params = await get_params(str(ctx.author.id))

        # Apply modifiers
        params['multiplier'] = multiplier

        # Update embed
        embed = PfGunEmbed(
            ctx
        ).gen_embed(
            **params
        ).set_footer(
            text=f"Multiplier: {params['multiplier']}\tRPM: {params['rpm']}"
        )

        await ctx.reply(embed=embed)

        # Cache
        cache_arg(list(chain.from_iterable([[ctx], params.values()])))

    @pfgun.command(hidden=True)
    @commands.is_owner()
    async def eval(self, ctx: Context, *, code: str):
        """Local eval command"""
        return_val = eval(code)
        await ctx.reply(':white_check_mark: Exec returned: `%s`' % return_val)

    @commands.command(name='ranges', brief='Info about damage')
    async def gun_ranges(self, ctx: Context):
        """Small command for showing damage needed for every shot to kill"""

        ''' Create embed '''
        embed = discord.Embed(
            title='Damage ranges',
            url='https://youtu.be/dQw4w9WgXcQ',
            color=0x00ff40
        ).set_author(
            name='Requested by ' + ctx.author.display_name,
            icon_url=ctx.author.avatar.url,
        ).set_footer(
            text='Values rounded to 2nd decimal place'
        )

        ''' Command logic '''
        for s in range(1, len(shots_to_damage) + 1):

            next_value = shots_to_damage.get(s)

            if s == 1:
                embed.add_field(
                    name=f'{s} shot',
                    value=f'**∞** to {next_value} damage',
                    inline=False,
                )
                continue

            current_value = float(shots_to_damage.get(s - 1))
            embed.add_field(
                name=f'{s} shot',
                value=f'{round(current_value - 0.01, 2)} to {next_value} damage',
                inline=False,
            )

            if len(shots_to_damage) - 1 == s:
                break

        await ctx.reply(embed=embed)


async def setup(client: MoistBot) -> None:
    await client.add_cog(Pfgun(client))
