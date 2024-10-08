from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NamedTuple, Tuple, TypedDict, Union

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from cogs.utils.converters import remove_decimal

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Optional, Self, Sequence

    from main import MoistBot


N = Union[int, float]
Vec2 = Tuple[N, N]
Vec3 = Tuple[N, N, N]

Vec2Tuple = Tuple[Vec2, Vec2]
Vec3Tuple = Tuple[Vec3, Vec3]

Vec2Pack = Tuple[Vec2, Vec2, Vec2]
RecoilArg = Tuple[Vec3Tuple, ...]


class NewRecoilStat(NamedTuple):
    mean: Vec3
    variance: Vec3


class OldRecoilStat(NamedTuple):
    min: Vec3
    max: Vec3


class RecoilKwargs(TypedDict):
    cam: Optional[OldRecoilStat | NewRecoilStat]
    trans: Optional[OldRecoilStat | NewRecoilStat]
    rot: Optional[OldRecoilStat | NewRecoilStat]


class InputRecoilKwargs(TypedDict):
    cam: Optional[str]
    trans: Optional[str]
    rot: Optional[str]


class RecoilConverter:
    cam: Optional[Vec3Tuple]
    trans: Optional[Vec3Tuple]
    rot: Optional[Vec3Tuple]

    def __init__(
        self,
        cam: Optional[Vec3Tuple] = None,
        trans: Optional[Vec3Tuple] = None,
        rot: Optional[Vec3Tuple] = None,
    ):
        self.cam: Optional[Vec3Tuple] = cam
        self.trans: Optional[Vec3Tuple] = trans
        self.rot: Optional[Vec3Tuple] = rot

    @staticmethod
    def _calc_mean(args: Vec2) -> float:
        _min, _max = args
        return (_min + _max) / 2

    @staticmethod
    def _calc_variance(args: Vec2) -> float:
        mean, _min = args
        return round(abs(mean - _min), 3)

    @staticmethod
    def _calc_min(args: Vec2) -> float:
        mean, variance = args
        return mean - variance

    @staticmethod
    def _calc_max(args: Vec2) -> float:
        mean, variance = args
        return mean + variance

    @classmethod
    def calc_mean_and_variance(cls, min_v3: Vec3, max_v3: Vec3) -> NewRecoilStat:
        min_and_max: Vec2Pack = zip(min_v3, max_v3)
        mean: Vec3 = tuple(map(cls._calc_mean, min_and_max))  # type: ignore

        mean_and_min: Vec2Pack = zip(mean, min_v3)
        variance: Vec3 = tuple(map(cls._calc_variance, mean_and_min))  # type: ignore
        return NewRecoilStat(mean, variance)

    @classmethod
    def calc_min_and_max(cls, mean_v3: Vec3, variance_v3: Vec3) -> OldRecoilStat:
        mean_and_variance: Vec2Pack = zip(mean_v3, variance_v3)
        _min: Vec3 = tuple(map(cls._calc_min, mean_and_variance))  # type: ignore

        mean_and_variance: Vec2Pack = zip(mean_v3, variance_v3)
        _max: Vec3 = tuple(map(cls._calc_max, mean_and_variance))  # type: ignore

        return OldRecoilStat(_min, _max)

    @classmethod
    def from_old(cls, kwargs: RecoilKwargs) -> Self:
        new_kwargs: RecoilKwargs = {
            k: cls.calc_mean_and_variance(*v)
            for k, v in kwargs.items()
            if v is not None
        }
        return cls(**new_kwargs)

    @classmethod
    def from_new(cls, kwargs: RecoilKwargs) -> Self:
        new_kwargs: RecoilKwargs = {
            k: cls.calc_min_and_max(*v)
            for k, v in kwargs.items()
            if v is not None
        }
        return cls(**new_kwargs)


class ConvertModal(discord.ui.Modal):
    """Base class for the conversion modal.
    This class is meant to be subclassed cannot be used directly.
    """

    full_name_kwargs: InputRecoilKwargs
    recoil_param: Sequence[str]
    converter: Callable[[RecoilKwargs], RecoilConverter]

    converted_name_kwargs = InputRecoilKwargs(
        cam='Camera recoil (X, Y, Z)',
        trans='Translational recoil (X, Y, Z)',
        rot='Rotational recoil (X, Y, Z)',
    )

    def __init__(self, **kwargs) -> None:
        self.__modal_children_items__ |= {
            k: discord.ui.TextInput(
                label=str(v),
                placeholder='eg.\n1 2 3\n4 5 6',
                style=discord.TextStyle.long,
                min_length=11,
                max_length=60,
                required=False,
            )
            for k, v in self.full_name_kwargs.items()
        }

        super().__init__(**kwargs)

    @staticmethod
    def serialize_arg(arg: str) -> tuple[float, ...]:
        args = (i.replace(',', '') for i in arg.split(' '))
        args = tuple(float(i) for i in filter(None, args))
        return args

    @classmethod
    def process_input(cls, arg: str) -> Optional[tuple[tuple[float, ...], ...]]:
        args = arg.split('\n', maxsplit=2)[:2]

        try:
            args = tuple(cls.serialize_arg(i) for i in args)
        except Exception:  # noqa
            args = None

        # Sanity check
        if args and len(args) != len(cls.recoil_param):
            args = None

        return args

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        kwargs: RecoilKwargs = {
            k: self.process_input(getattr(self, k).value)
            for k in self.converted_name_kwargs.keys()
        }

        # Sanity check
        if not any(kwargs.values()):
            await interaction.response.send_message(
                ':warning: At least one field needs to be filled in.',
                ephemeral=True
            )

        embed = discord.Embed(title='Recoil Conversion')
        stats: RecoilConverter = self.converter(kwargs)
        footer = ['Values given for conversion:']

        for k, v in self.converted_name_kwargs.items():
            stat = getattr(stats, k, None)
            if stat is None:
                continue

            value = '\n'.join(
                f'{p.title()}: {", ".join(str(remove_decimal(i)) for i in getattr(stat, p))}'
                for p in self.recoil_param
            )
            footer.append('{0}: {1}, {2}'.format(k.title(), *kwargs[k]))  # type: ignore

            embed.add_field(
                name=v,
                value=value,
                inline=False,
            )

        embed.set_footer(text='\n'.join(footer))
        await interaction.response.send_message(embed=embed)


class ConvertOldToNewModal(ConvertModal, title='Convert old -> new'):
    recoil_param = [k for k in NewRecoilStat.__dict__.keys() if not k.startswith('_')]
    converter = RecoilConverter.from_old

    full_name_kwargs = InputRecoilKwargs(
        cam='Min and max cam recoil (X, Y, Z)',
        trans='Min and max trans recoil (X, Y, Z)',
        rot='Min and max rot recoil (X, Y, Z)',
    )


class ConvertNewToOldModal(ConvertModal, title='Convert new -> old'):
    recoil_param = [k for k in OldRecoilStat.__dict__.keys() if not k.startswith('_')]
    converter = RecoilConverter.from_new

    full_name_kwargs = InputRecoilKwargs(
        cam='Mean and variance cam recoil (X, Y, Z)',
        trans='Mean and variance trans recoil (X, Y, Z)',
        rot='Mean and variance rot recoil (X, Y, Z)',
    )


map_conversion_names = {0: 'old to new', 1: 'new to old'}
map_conversion = {0: ConvertOldToNewModal, 1: ConvertNewToOldModal}


class PFRecoilConverter(commands.Cog):
    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

    @commands.cooldown(rate=1, per=6, type=commands.BucketType.user)
    @app_commands.rename(conversion_type='conversion-type')
    @app_commands.choices(
        conversion_type=[
            app_commands.Choice(value=k, name=v)
            for k, v in map_conversion_names.items()
        ]
    )
    @app_commands.command(name='pf-convert')
    async def pf_convert(
        self,
        interaction: Interaction,
        conversion_type: Literal[0, 1]
    ):
        conversion = map_conversion[conversion_type]
        await interaction.response.send_modal(conversion())


async def setup(client: MoistBot) -> None:
    await client.add_cog(PFRecoilConverter(client))
