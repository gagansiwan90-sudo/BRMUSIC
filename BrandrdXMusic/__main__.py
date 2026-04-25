import asyncio
import importlib
import os
import signal
import sys
from contextlib import suppress

from aiohttp import web
from pyrogram import idle as pyrogram_idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from BrandrdXMusic import LOGGER, app, userbot
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import sudo
from BrandrdXMusic.plugins import ALL_MODULES
from BrandrdXMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS

# Raise file descriptor limit on Linux
if sys.platform != "win32":
    try:
        import resource
        _soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        _target = min(65536, _hard)
        if _soft < _target:
            resource.setrlimit(resource.RLIMIT_NOFILE, (_target, _hard))
    except Exception:
        pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  KEEP-ALIVE SERVER (aiohttp — async, no threading)
#  Render Web Service ke liye port open karna zaroori
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def keep_alive():
    async def handle(request):
        return web.Response(
            text="<h2>BrandrdXMusic Bot is alive!</h2>",
            content_type="text/html"
        )

    async def health(request):
        return web.json_response({"status": "ok", "bot": "BrandrdXMusic"})

    webapp = web.Application()
    webapp.router.add_get("/", handle)
    webapp.router.add_get("/health", health)

    runner = web.AppRunner(webapp)
    await runner.setup()

    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    LOGGER(__name__).info(f"[KeepAlive] Server started on port {port}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  IDLE — signal ka wait karo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def idle():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        with suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)

    await stop_event.wait()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def main():
    # ── Keep-alive PEHLE — Render port scan karta hai turant
    await keep_alive()

    # ── Assistant string validate karo
    if not any([config.STRING1, config.STRING2, config.STRING3,
                config.STRING4, config.STRING5]):
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        return

    # ── Banned users load karo
    try:
        for user_id in await get_gbanned():
            BANNED_USERS.add(user_id)
        for user_id in await get_banned_users():
            BANNED_USERS.add(user_id)
    except Exception:
        pass

    # ── Bot start karo
    await sudo()
    await app.start()

    for module in ALL_MODULES:
        try:
            importlib.import_module("BrandrdXMusic.plugins" + module)
        except Exception as e:
            LOGGER("BrandrdXMusic.plugins").error(f"Failed to load plugin {module}: {e}")
    LOGGER("BrandrdXMusic.plugins").info("Successfully Imported Modules...")

    await userbot.start()
    await Hotty.start()

    try:
        await Hotty.stream_call("https://graph.org/file/e999c40cb700e7c684b75.mp4")
    except NoActiveGroupCall:
        LOGGER("BrandrdXMusic").error(
            "Please turn on the videochat of your log group/channel.\n"
            "Bot will continue without VC test..."
        )
    except Exception:
        pass

    await Hotty.decorators()
    LOGGER("BrandrdXMusic").info("BrandrdXMusic Bot started successfully!")

    # ── Idle — stop signal tak rukho
    await idle()

    # ── Cleanup
    await app.stop()
    await userbot.stop()
    LOGGER("BrandrdXMusic").info("Stopping Brandrd Music Bot...")


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        LOGGER("BrandrdXMusic").info("Bot stopped by user.")
    
