"""
Background Discord bot module.

Runs a discord.py Client in a dedicated daemon thread with its own asyncio
event loop. Flask routes call the synchronous helper functions exposed here
to read from the bot's in-memory cache instead of making REST API calls.
"""

import asyncio
import threading
import logging
import os
from dotenv import load_dotenv

import discord

load_dotenv(override=True)

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level globals
# ---------------------------------------------------------------------------
_bot: discord.Client | None = None
_loop: asyncio.AbstractEventLoop | None = None
_ready_event = threading.Event()          # set once on_ready fires


# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------

def _create_bot() -> discord.Client:
    """Create a discord.Client with the required intents."""
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        logger.info("Bot is ready! Logged in as %s", client.user)
        logger.info("Bot is in %d guild(s)", len(client.guilds))
        for g in client.guilds:
            logger.info("  - %s (id: %s, members: %d)", g.name, g.id, g.member_count or 0)
        _ready_event.set()

    return client


def _run_bot_in_thread(loop: asyncio.AbstractEventLoop, client: discord.Client):
    """Target function for the daemon thread — runs the bot forever."""
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client.start(BOT_TOKEN))


def start_bot() -> None:
    """
    Launch the background bot.  Safe to call multiple times — only the first
    call actually starts the thread.
    """
    global _bot, _loop

    if _bot is not None:
        return  # already started

    _bot = _create_bot()
    _loop = asyncio.new_event_loop()

    thread = threading.Thread(
        target=_run_bot_in_thread,
        args=(_loop, _bot),
        daemon=True,
        name="discord-bot",
    )
    thread.start()
    logger.info("Discord bot thread started (daemon).")


# ---------------------------------------------------------------------------
# Thread-safe async bridge
# ---------------------------------------------------------------------------

def run_coroutine(coro):
    """
    Schedule an async coroutine on the bot's event loop from a synchronous
    Flask context.  Returns the result (blocks until the coroutine finishes).
    """
    if _loop is None or _loop.is_closed():
        raise RuntimeError("Bot event loop is not running.")
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=10)


# ---------------------------------------------------------------------------
# Synchronous helpers for Flask routes
# ---------------------------------------------------------------------------

def is_bot_ready() -> bool:
    """Return True once the bot has fired on_ready and the cache is warm."""
    return _ready_event.is_set()


def is_bot_in_guild(guild_id) -> bool:
    """Check whether the bot is a member of the given guild (from cache)."""
    if _bot is None or not is_bot_ready():
        return False
    return _bot.get_guild(int(guild_id)) is not None


def get_guild_from_cache(guild_id):
    """Return the discord.Guild object or None."""
    if _bot is None or not is_bot_ready():
        return None
    return _bot.get_guild(int(guild_id))


def get_guild_name(guild_id) -> str | None:
    """Return the guild name from cache, or None if unavailable."""
    guild = get_guild_from_cache(guild_id)
    if guild is not None:
        return guild.name
    return None


def get_guild_channels(guild_id):
    """
    Return a list of text channel dicts (id, name, type) from cache,
    matching the shape of the REST API response so callers can swap in
    with minimal changes.
    """
    guild = get_guild_from_cache(guild_id)
    if guild is None:
        return None
    return [
        {"id": str(ch.id), "name": ch.name, "type": 0}
        for ch in guild.text_channels
    ]


def get_repo_name_from_cache(guild_id) -> str | None:
    """
    Read the repo name from the bot-internal-config channel via the bot's
    own connection (uses channel.history which goes through the bot's more
    generous rate-limit bucket).

    Returns the repo name string, or None if the channel/message doesn't exist.
    """
    guild = get_guild_from_cache(guild_id)
    if guild is None:
        return None

    config_channel = discord.utils.get(
        guild.text_channels, name="bot-internal-config"
    )
    if config_channel is None:
        return None

    # Async call bridged to sync via a small helper coroutine
    async def _read_config():
        messages = [msg async for msg in config_channel.history(limit=1)]
        if messages:
            import json
            data = json.loads(messages[0].content)
            return data.get("repo")
        return None

    try:
        return run_coroutine(_read_config())
    except Exception as e:
        logger.warning("Failed to read bot-internal-config in guild %s: %s", guild_id, e)

    return None


def detect_bots_in_guild(guild_id) -> list[dict]:
    """
    Return a list of bot members in the given guild.
    Each entry is a dict with 'id', 'name', and 'discriminator'.
    Returns an empty list if the guild is not cached or the bot isn't present.
    """
    guild = get_guild_from_cache(guild_id)
    if guild is None:
        return []
    return [
        {"id": str(m.id), "name": m.name, "discriminator": m.discriminator}
        for m in guild.members
        if m.bot
    ]


def get_bot_user_id() -> int | None:
    """Return the bot's own user ID, or None if not ready."""
    if _bot is None or _bot.user is None:
        return None
    return _bot.user.id
