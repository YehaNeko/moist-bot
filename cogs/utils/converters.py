from __future__ import annotations

from io import BytesIO
from urllib.parse import urlparse
from urllib import error as url_error
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from cogs.utils.context import Context


def is_url(text: str) -> bool:
    try:
        result = urlparse(text)
        return all((result.scheme, result.netloc))
    except url_error.URLError:
        return False


async def get_media_from_ctx(
    ctx: Context,
    arg: Optional[str] = None,
    buffer: Optional[BytesIO] = None
) -> BytesIO | bool:

    buffer = buffer or BytesIO()
    reply = ctx.replied_message
    bot = ctx.bot
    media = b''

    # Fetch media bytes
    if arg and is_url(arg):
        media = await bot.http.get_from_cdn(arg)
    elif reply:
        if reply.attachments:
            media = await reply.attachments[0].read(use_cached=True)
        elif is_url(reply.content):
            media = await bot.http.get_from_cdn(reply.content)

    if not media:
        return False

    buffer.write(media)
    buffer.seek(0)
    return buffer
