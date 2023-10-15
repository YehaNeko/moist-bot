from __future__ import annotations

from typing import TYPE_CHECKING

from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES

if TYPE_CHECKING:
    from main import MoistBot


class JishakuDebugCog(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    pass


async def setup(client: MoistBot):
    await client.add_cog(JishakuDebugCog(bot=client))
