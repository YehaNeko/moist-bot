from __future__ import annotations

import discord
from discord.ext import commands

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from main import MoistBot


class Context(commands.Context):
    prefix: str
    command: commands.Command[Any, ..., Any]
    bot: MoistBot

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        # we need this for our cache key strategy
        return '<Context>'

    @discord.utils.cached_property
    def replied_reference(self) -> Optional[discord.MessageReference]:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved.to_reference()
        return None

    @discord.utils.cached_property
    def replied_message(self) -> Optional[discord.Message]:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved
        return None

    @staticmethod
    def tick(opt: Optional[bool], label: Optional[str] = None) -> str:
        lookup = {
            True: '<:greenTick:330090705336664065>',
            False: '<:redTick:330090723011592193>',
            None: '<:greyTick:563231201280917524>',
        }
        emoji = lookup.get(opt, '<:redTick:330090723011592193>')
        if label is not None:
            return f'{emoji}: {label}'
        return emoji
