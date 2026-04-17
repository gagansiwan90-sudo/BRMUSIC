import asyncio
import importlib
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from BrandrdXMusic import LOGGER, app, userbot
from BrandrdXMusic.core.call import Hotty
from BrandrdXMusic.misc import sudo
from BrandrdXMusic.plugins import ALL_MODULES
from BrandrdXMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS

# HTTP Health Check Server for Render (port detect fix)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'BrandrdXMusic Bot is running')
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def run_http_server():
    """HTTP server for Render port detection"""
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    LOGGER(__name__).info(f"🌐 HTTP Health server started on port {port}")
    server.serve_forever()

async def init():
    # Start HTTP server thread FIRST (Render requirement)
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    LOGGER(__name__).info("🌐 HTTP server thread started for Render")

    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        return

    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("BrandrdXMusic.plugins" + all_module)
    LOGGER("BrandrdXMusic.plugins").info("Successfully Imported Modules...")
    
    await userbot.start()
    await Hotty.start()
    
    try:
        await Hotty.stream_call("https://graph.org/file/e999c40cb700e7c684b75.mp4")
    except NoActiveGroupCall:
        LOGGER("BrandrdXMusic").error(
            "Please turn on the videochat of your log group/channel.
"
            "Bot will continue without VC test..."
        )
    except:
        pass
    
    await Hotty.decorators()
    LOGGER("BrandrdXMusic").info(
        "🎉 BrandrdXMusic Bot Started Successfully! Join @BRANDRD_BOT for support"
    )
    
    # Keep both HTTP server + bot running
    await idle()
    
    # Cleanup (won't reach here normally)
    await app.stop()
    await userbot.stop()
    LOGGER("BrandrdXMusic").info("Stopping Brandrd Music Bot...")

if __name__ == "__main__":
    try:
        asyncio.run(init())  # Modern asyncio syntax
    except KeyboardInterrupt:
        LOGGER("BrandrdXMusic").info("Bot stopped by user")
