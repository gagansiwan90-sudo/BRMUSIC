import asyncio
import importlib
import os
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

# Raise the file descriptor limit on Linux
if sys.platform != "win32":
    try:
        import resource
        _soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        _target = min(65536, _hard)
        if _soft < _target:
            resource.setrlimit(resource.RLIMIT_NOFILE, (_target, _hard))
    except Exception:
        pass

import config
from BrandrdXMusic import LOGGER, app, userbot
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import sudo
from BrandrdXMusic.plugins import ALL_MODULES
from BrandrdXMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS

# ──────────────────────────────────────────────
# HTTP Server — must bind BEFORE asyncio starts
# ──────────────────────────────────────────────

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"BrandrdXMusic Bot is running")

    def log_message(self, format, *args):
        pass  # silence access logs


def start_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"[HTTP] Health-check server listening on port {port}", flush=True)
    server.serve_forever()


# ──────────────────────────────────────────────
# Bot initialisation (async)
# ──────────────────────────────────────────────

async def init():
    try:
        # Validate assistant string variables
        if not any([
            config.STRING1, config.STRING2, config.STRING3,
            config.STRING4, config.STRING5,
        ]):
            LOGGER(__name__).error("Assistant client variables not defined, exiting...")
            return

        # Load banned users
        try:
            for user_id in await get_gbanned():
                BANNED_USERS.add(user_id)
            for user_id in await get_banned_users():
                BANNED_USERS.add(user_id)
        except Exception:
            pass

        await sudo()
        await app.start()

        for all_module in ALL_MODULES:
            try:
                importlib.import_module("BrandrdXMusic.plugins" + all_module)
            except Exception as e:
                LOGGER("BrandrdXMusic.plugins").error(f"Failed to load plugin {all_module}: {e}")

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

        try:
            await idle()
        except KeyboardInterrupt:
            LOGGER("BrandrdXMusic").info("Received stop signal...")
        except Exception as e:
            LOGGER("BrandrdXMusic").error(f"Error during idle: {e}")

        await app.stop()
        await userbot.stop()
        LOGGER("BrandrdXMusic").info("Stopping Brandrd Music Bot...")

    except Exception as e:
        LOGGER("BrandrdXMusic").error(f"Critical error in init: {e}", exc_info=True)
        raise


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # 1️⃣  Start HTTP server in background thread FIRST
    #     Render scans for open ports almost immediately after launch.
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    time.sleep(1)  # give the socket a moment to bind

    # 2️⃣  Then start the async bot loop
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(init())
    except KeyboardInterrupt:
        LOGGER("BrandrdXMusic").info("Bot stopped by user (Ctrl+C)")
    except SystemExit as e:
        LOGGER("BrandrdXMusic").error(f"Bot exited with system error: {e}")
        raise
    except Exception as e:
        LOGGER("BrandrdXMusic").error(f"Unexpected error: {e}", exc_info=True)
    finally:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.stop()
        except Exception:
            pass
