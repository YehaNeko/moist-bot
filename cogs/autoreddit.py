from __future__ import annotations

import discord
from config import REDDIT_APP
from discord.utils import MISSING
from discord.ext import commands, tasks
from discord import app_commands, DMChannel, TextChannel

import json
import logging
import asyncpraw
from asyncpraw import reddit
from typing import TYPE_CHECKING, AsyncIterator, Annotated, Any, Union

if TYPE_CHECKING:
    from main import MoistBot
    from cogs.utils.context import Context


logger = logging.getLogger("discord." + __name__)
INTERVAL_OVERRIDE = None

# TODO: add bypass check
"""
This code is VERY unfinished and it probably won't ever be finished.
Unlucky.
"""


class ResolveChannel(commands.Converter, app_commands.Transformer):
    """Resolves channel mentions (eg. '<#123456789101112>') | discord.abc.User -> TextChannel | DMChannel"""

    async def convert(self, ctx: Context, value: Any) -> TextChannel | DMChannel:
        """Called for commands.Command context"""
        try:
            channel = await commands.TextChannelConverter().convert(ctx, value)
        except commands.BadArgument:
            pass
        else:
            return channel

        try:
            user = await commands.MemberConverter().convert(ctx, value)
        except commands.BadArgument as e:
            raise commands.BadArgument(":anger: Unable to resolve the specified channel.") from e
        else:
            # Make sure the resolved user isn't someone other than the author
            if ctx.author.id != user.id:
                raise commands.BadArgument(":warning: You can only mention yourself here.")

            return user.dm_channel or await user.create_dm()

    async def transform(self, interaction: discord.Interaction, value: discord.abc.Messageable) -> discord.abc.Messageable:
        """Called for discord.Interaction context"""
        ctx = await interaction.client.get_context(interaction)
        return await self.convert(ctx, str(value))

    @property
    def type(self) -> discord.AppCommandOptionType:
        return discord.AppCommandOptionType.channel


class MockupDeletedRedditor(object):
    name, icon_img = "[deleted]", None


deleted_redditor = MockupDeletedRedditor()  # noqa


class RedditPostEmbed(discord.Embed):
    def __init__(self, submission: reddit.Submission, op: reddit.Redditor):
        super().__init__(title=submission.title, url=submission.url)
        self.set_image(url=submission.url)
        self.set_author(name=f"posted by u/{op.name}", icon_url=op.icon_img)


class RedditPostTask(tasks.Loop):
    def __init__(
        self,
        subreddit: reddit.Subreddit,
        channel: TextChannel | DMChannel,
        *args,
        **kwargs,
    ) -> None:
        self.subreddit: reddit.Subreddit = subreddit
        self.channel: TextChannel | DMChannel = channel
        self.submissions: AsyncIterator = subreddit.hot(limit=None)  # noqa
        super().__init__(self.send_post, *args, **kwargs)

        self._current_submission: reddit.Submission | None = None
        # self.add_exception_type(AsyncPrawcoreException, )
        self.error(self.on_error)

    async def send_post(self) -> None:
        """Callback func for tasks"""

        submission: reddit.Submission = await anext(self.submissions)
        await submission.load()
        self._current_submission = submission

        # Filter out posts
        if (
            submission.over_18 and not (isinstance(self.channel, DMChannel) or self.channel.nsfw)
            or submission.stickied
            or submission.pinned
            or submission.distinguished == "moderator"
            or not hasattr(submission, "post_hint")
            or submission.post_hint != "image"
        ):
            return await self.send_post()

        # Acquire redditor
        op: reddit.Redditor = submission.author
        op = await op.load() if op else deleted_redditor

        # Send post
        await self.channel.send(embed=RedditPostEmbed(submission, op))
        logger.info(self.channel)

    async def on_error(self, *args: Any):
        exception: Exception = args[-1]
        logger.error('Unhandled exception in internal background task %r.', self.coro.__name__, exc_info=exception)
        logger.warning('The bellow submission caused an exception: \n%s', json.dumps(self._current_submission.__dict__))


class RedditAutoPost(commands.Cog):
    # Keep weak references to running tasks
    running_tasks: dict[int, RedditPostTask] = {}

    # Acquire reddit object
    reddit = asyncpraw.Reddit(**REDDIT_APP)
    reddit.read_only = True

    max_interval = INTERVAL_OVERRIDE or 2.5

    def __init__(self, client: MoistBot):
        self.client: MoistBot = client

    async def cog_unload(self) -> None:
        for t in self.running_tasks.values():
            t.cancel()

    @commands.hybrid_group(
        name="autoreddit",
        brief="Automatically send posts from reddit",
        fallback="start",
    )
    @app_commands.describe(
        subreddit_name="The name of the subreddit you want posted (without the r/).",
        channel="The text channel where you want the reddit posts sent.",
        interval="Interval in seconds between posts (must be more than 2.5s).",
    )
    @app_commands.rename(subreddit_name="subreddit-name")
    @commands.cooldown(rate=1, per=10)
    @commands.check_any(
        commands.is_owner(),
        commands.has_permissions(manage_channels=True)
    )
    async def auto_send_reddit(
        self,
        ctx: Context,
        subreddit_name: str,
        channel: Annotated[Union[DMChannel, TextChannel, discord.User], ResolveChannel],
        interval: float,
    ):
        """Have the bot automatically send posts from any subreddit"""

        # Get subreddit
        subreddit = await self.reddit.subreddit(subreddit_name, fetch=True)

        # No horny
        if subreddit.over18 and not (isinstance(channel, DMChannel) or channel.nsfw):
            raise commands.BadArgument(":warning: NSFW subreddits can only be posted in NSFW channels.")

        # Limit interval (<2.5s)
        if interval < self.max_interval:
            raise commands.BadArgument(":anger: Interval cannot be lower than 2.5s!")

        # Setup reddit poster task
        task = RedditPostTask(
            subreddit,
            channel,
            seconds=interval,
            minutes=MISSING,
            hours=MISSING,
            time=MISSING,
            count=None,
            reconnect=True,
        )
        task.start()
        self.running_tasks.update({channel.id: task})

        # Create and send embed
        embed = discord.Embed(
            title=":white_check_mark: Auto-reddit bound to channel (click to jump!)",
            description=f"I will be sending posts from **r/{subreddit_name}** every **{interval}** seconds in  <#{channel.id}>",
            url=channel.jump_url,
            color=discord.Color.green(),
        ).set_author(
            name=f"Set by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.reply(embed=embed)

    @auto_send_reddit.command()
    async def stop(
        self,
        ctx: Context,
        channel: Annotated[Union[DMChannel, TextChannel, discord.User], ResolveChannel],
    ):
        """Stop sending reddit posts in a channel"""

        # Ensure running task in selected channel
        if channel.id not in self.running_tasks.keys():
            await ctx.reply(":warning: I am not auto-posting in that channel!")

        self.running_tasks[channel.id].cancel()
        self.running_tasks.pop(channel.id)

        embed = discord.Embed(
            title=":white_check_mark: Auto-reddit unbound to channel (click to jump!)",
            description=f"I will stop sending posts in  <#{channel.id}>",
            url=channel.jump_url,
            color=discord.Color.red(),
        ).set_author(
            name=f"Stopped by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )

        await ctx.reply(embed=embed)


async def setup(client: MoistBot) -> None:
    await client.add_cog(RedditAutoPost(client))
