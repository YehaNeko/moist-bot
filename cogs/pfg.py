from __future__ import annotations

import re
from typing import (
    TYPE_CHECKING,
    NamedTuple,
    Annotated,
    TypeAlias,
    Optional,
    Sequence,
    overload,
    Literal,
    Union,
    Self
)

import orjson
import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    import sqlite3

    from main import MoistBot
    from utils.context import Context


N: TypeAlias = Union[int, float]
G: TypeAlias = Literal[1, -1, 0]
shots_to_damage: dict[int, N] = {
    1: 100,
    2: 50,
    3: 33.34,
    4: 25,
    5: 20,
    6: 16.67,
    7: 14.29,
    8: 12.5,
    9: 11.12,
    10: 10,
    11: 9.1,
    12: 8.34,
}


FLOAT_REGEX = re.compile(r'[-+]?[0-9]*\.?[0-9]+')

NO_PREV_DATA_EMBED = discord.Embed(
    title=':x: Error',
    description='No previous command has been run.',
    color=discord.Color.red()
)


@overload
def remove_decimal(number: int, ndigits: int = 2) -> int:
    ...


@overload
def remove_decimal(number: float, ndigits: int = 2) -> N:
    ...


def remove_decimal(number: N, ndigits: int = 2) -> N:
    if isinstance(number, int):
        return number
    elif number.is_integer():
        return int(number)
    else:
        return round(number, ndigits)


class FloatSequenceTransformer(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, value: str) -> tuple[N, ...]:
        return tuple(map(float, re.findall(FLOAT_REGEX, value)))


# fmt: off
class PfgFlags(commands.FlagConverter, prefix='', delimiter='=', case_insensitive=True):
    damages: str = commands.flag(aliases=['dmg', 'd'], description='The damages of your gun separated by spaces.')
    ranges: str = commands.flag(aliases=['range', 'r'], description='The ranges of your gun separated by spaces.')
    multiplier: Annotated[N, Optional[N]] = commands.flag(aliases=['multi', 'm'], default=1, description='The multiplier to use. (Default: 1)')
    rpm: Optional[N] = commands.flag(description='The rpm of your gun. (Optional)')
# fmt: on


class PfgPoint(NamedTuple):
    shots: int
    range: N
    ttk: Optional[N]


class PfgCalculator:
    shots_to_damage = shots_to_damage

    def __init__(
        self,
        damages: Sequence[N],
        ranges: Sequence[N],
        multiplier: N,
        rpm: Optional[N] = None,
    ):
        d_len, r_len = len(damages), len(ranges)
        if d_len != r_len:
            raise ValueError('Damages and ranges must be the same length.')
        elif d_len < 2:
            raise ValueError('At least two data points are required.')

        self.damages: Sequence[N] = damages
        self.ranges: Sequence[N] = ranges
        self.multiplier: N = multiplier
        self.rpm: Optional[N] = rpm

        # Apply multiplier
        self.damages = [damage * self.multiplier for damage in damages]

        # Create data points
        self.data_points: Sequence[tuple[N, N]] = tuple(zip(self.damages, self.ranges))
        self.len_data_points = d_len  # Since damages and ranges are the same length

        # Precompute max values
        self._max_damage = max(self.damages)
        self._max_range = max(self.ranges)

    @classmethod
    def from_pfg_args(cls, args: PfgFlags) -> Self:
        return cls(args.damages, args.ranges, args.multiplier, args.rpm)  # type: ignore

    @classmethod
    def from_data_points(
        cls,
        data_points: Sequence[tuple[N, N]],
        *,
        multiplier: N = 1,
        rpm: Optional[N] = None,
    ) -> Self:
        damages, ranges = zip(*data_points)
        return cls(damages, ranges, multiplier, rpm)

    @staticmethod
    def _calculate_ttk(shots: N, rpm: Optional[N] = None) -> Optional[float]:
        if not rpm:
            return None

        ttk = 60 * (shots - 1) / rpm
        ttk = round(ttk, 5)
        return ttk or None

    def _create_output_data(self, data_points: Sequence[tuple[int, N]]) -> list[PfgPoint]:
        return [
            PfgPoint(
                shots=shots,
                range=remove_decimal(range_),
                ttk=self._calculate_ttk(shots=shots, rpm=self.rpm),
            )
            for shots, range_ in data_points
        ]

    def evaluate_damage_to_shots(self, value: N) -> Optional[N]:
        """Evaluates the damage value to determine the corresponding number of shots needed.

        Args:
            value (N): The damage value to evaluate.

        Returns:
            Optional[N]: The number of shots needed to inflict the given damage value.
                         Returns None if the damage value is less than the minimum damage.
        """

        # First value
        prev_damage = self.shots_to_damage[1]
        if value >= prev_damage:
            return 1

        # Find which segment x belongs to
        for i, damage in self.shots_to_damage.items():
            if prev_damage > value >= damage:
                return i
            prev_damage = damage

    def evaluate_shots_to_kill(self, d: N) -> list[tuple[G, N]]:
        matches = []
        g: G = 0

        # Iterate over the data points
        # We skip the last data point to avoid an IndexError
        for i, data_point in enumerate(self.data_points[:-1]):
            d0, r0 = data_point
            d1, r1 = self.data_points[i + 1]

            # Check if y is within the y-range of the current segment
            if min(d0, d1) <= d <= max(d0, d1):

                # If the graph is decreasing
                if d0 > d1 and d != d1:
                    g = 1
                # If the graph is increasing
                elif d0 < d1:
                    g = 0

                # Avoid dividing by zero
                if d0 != d1:
                    match = r0 + (d - d0) * (r1 - r0) / (d1 - d0)
                    matches.append((g, match))

                # If y1 and y2 are equal and x1 is not already in the list,
                # add x1 to the list
                elif len(matches) == 0 or r0 != matches[-1]:
                    matches.append((g, r0))

        return matches

    def calculate_progression(self) -> list[PfgPoint]:
        progression = []

        # Weapon start
        first_shots_to_kill = self.evaluate_damage_to_shots(self.damages[0])
        if first_shots_to_kill is not None:
            progression.append((first_shots_to_kill, 0))

        # Weapon progression
        for i, damage in self.shots_to_damage.items():
            points = self.evaluate_shots_to_kill(damage)

            for g, studs in points:
                point = i + g, round(studs, 2)
                if progression[-1][0] != point[0]:
                    progression.append(point)

        # Sort the list by the ranges
        progression.sort(key=lambda x: x[1])

        # This is a hack but,
        # we need to filter out consecutive duplicates where
        # the first value of a point matches the last one in the list
        progression = [
            point
            for i, point in enumerate(progression)
            if i == 0 or progression[i - 1][0] != point[0]
        ]

        # Final step - create the output
        progression = self._create_output_data(progression)

        return progression

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'damages={self.damages}, '
            f'ranges={self.ranges}, '
            f'multiplier={self.multiplier}, '
            f'rpm={self.rpm})'
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PfgCalculator):
            return NotImplemented
        return (
            self.damages == other.damages
            and self.ranges == other.ranges
            and self.multiplier == other.multiplier
            and self.rpm == other.rpm
        )


class PfgEmbed(discord.Embed):
    def __init__(
        self, data_points: Sequence[PfgPoint], multiplier: N, rpm: Optional[N] = None
    ):
        super().__init__(title='PF Gun STK Calculator - Multipoint')
        self.data_points: Sequence[PfgPoint] = data_points
        self.multiplier: N = remove_decimal(multiplier)
        self.rpm: Optional[N] = remove_decimal(rpm) if rpm is not None else None
        self._create_field_items()

    def _create_field_items(self) -> None:
        data_points = self.data_points

        # Iterate over the data points
        len_data_points = len(data_points)
        for i, data_point in enumerate(data_points):

            # Initialise field items
            field_name_extra = ' \t\t\t➡️'
            field_items = []

            # Add range
            if i + 1 < len_data_points:
                next_range = data_points[i + 1].range

            # Last data point
            else:
                next_range = '∞'
                field_name_extra = ''

            field_items.append(f'**{data_point.range}** to **{next_range}** studs')

            # Add ttk if applicable
            if data_point.ttk is not None:
                field_items.append(f'{data_point.ttk}s to kill')

            # Add field and join field items
            self.add_field(
                name=f'{data_point.shots} shot{field_name_extra}',
                value='\n'.join(field_items),
                inline=True,
            )

        self.set_footer(text=f"Multiplier: {self.multiplier}\tRPM: {self.rpm}")


class PfgunRewrite(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

    async def _save_params_to_db(
        self,
        user_id: int,
        damages: Sequence[N],
        ranges: Sequence[N],
        multiplier: N = 1,
        rpm: Optional[N] = None,
    ) -> None:
        async with self.client.pool.acquire() as conn:
            async with conn:
                query = """--sql
                    INSERT OR REPLACE INTO pfg_param_cache (user_id, damages, ranges, multiplier, rpm)
                    VALUES (?, ?, ?, ?, ?)
                """
                await conn.execute(
                    query, user_id, orjson.dumps(damages), orjson.dumps(ranges), multiplier, rpm
                )

    async def _get_params_from_db(self, user_id: int) -> Optional[sqlite3.Row]:
        async with self.client.pool.acquire() as conn:
            async with conn:
                query = """--sql
                    SELECT damages, ranges, multiplier, rpm
                    FROM pfg_param_cache
                    WHERE user_id = ?
                """
                return await conn.fetchone(query, user_id)

    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @commands.hybrid_group(invoke_without_command=True, fallback='calculate')
    async def pfg(self, ctx: Context, *, args: PfgFlags):
        """PF Gun STK Calculator - Multipoint."""

        pfg_calc = PfgCalculator.from_pfg_args(args)
        data_points = pfg_calc.calculate_progression()

        embed = PfgEmbed(data_points, args.multiplier, args.rpm)
        await ctx.reply(embed=embed)

        # Save params to db
        await self._save_params_to_db(
            ctx.author.id, args.damages, args.ranges, args.multiplier, args.rpm
        )

    # @pfg.command()
    # @app_commands.describe(
    #     damages='The damage values of your gun separated by spaces.',
    #     ranges='The range values of your gun separated by spaces.',
    #     multiplier='The multiplier to use.',
    #     rpm='The RPM to use.',
    # )
    # async def calculate(
    #     self,
    #     ctx: Context,
    #     damages: tuple[float, ...],
    #     ranges: tuple[float, ...],
    #     multiplier: float = 1.0,
    #     rpm: Optional[float] = None,
    # ):
    #     """PF Gun STK Calculator - Multipoint."""
    #
    #     pfg_calc = PfgCalculator(damages, ranges, multiplier, rpm)
    #     data_points = pfg_calc.calculate_progression()
    #
    #     embed = PfgEmbed(data_points, multiplier, rpm)
    #     await ctx.reply(embed=embed)
    #
    #     # Save params to db
    #     await self._save_params_to_db(
    #         ctx.author.id, damages, ranges, multiplier, rpm
    #     )

    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.describe(multiplier='The multiplier to use.')
    @pfg.command(aliases=['multi', 'm'])
    async def multiplier(self, ctx: Context, multiplier: float):
        """Change the multiplier paramater of your previous command."""

        # Get parameters
        row = await self._get_params_from_db(ctx.author.id)

        if not row:
            await ctx.reply(embed=NO_PREV_DATA_EMBED)
            return

        # Setup parameters
        damages = orjson.loads(row['damages'])
        ranges = orjson.loads(row['ranges'])
        multiplier = multiplier  # Just explicitly showing this
        rpm = row['rpm']

        pfg_calc = PfgCalculator(damages, ranges, multiplier, rpm)
        data_points = pfg_calc.calculate_progression()

        embed = PfgEmbed(data_points, multiplier, rpm)
        await ctx.reply(embed=embed)

        # Save params to db
        await self._save_params_to_db(ctx.author.id, damages, ranges, multiplier, rpm)

    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    @app_commands.describe(rpm='The RPM to use.')
    @pfg.command()
    async def rpm(self, ctx: Context, rpm: float):
        """Change the RPM paramater of your previous command."""

        # Get parameters
        row = await self._get_params_from_db(ctx.author.id)

        if not row:
            await ctx.reply(embed=NO_PREV_DATA_EMBED)
            return

        # Setup parameters
        damages = orjson.loads(row['damages'])
        ranges = orjson.loads(row['ranges'])
        multiplier = row['multiplier']
        rpm = rpm  # Just explicitly showing this

        pfg_calc = PfgCalculator(damages, ranges, multiplier, rpm)
        data_points = pfg_calc.calculate_progression()

        embed = PfgEmbed(data_points, multiplier, rpm)
        await ctx.reply(embed=embed)

        # Save params to db
        await self._save_params_to_db(ctx.author.id, damages, ranges, multiplier, rpm)


async def setup(client: MoistBot) -> None:
    await client.add_cog(PfgunRewrite(client))
