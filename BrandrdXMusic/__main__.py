import asyncio
import importlib
import os
import sys
import threading
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

# HTTP Server for Render health checks
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for Render health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'BrandrdXMusic Bot is running')
    
    def log_message(self, format, *args):
        """Suppress log messages to keep console clean"""
        pass

def run_http_server():
    """Run a simple HTTP server for Render health checks"""
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    LOGGER(__name__).info(f"🌐 HTTP health check server started on port {port}")
    server.serve_forever()

async def init():
    try:
        # Step 1: Validate required environment variables
        if (
            not config.STRING1
            and not config.STRING2
            and not config.STRING3
            and not config.STRING4
            and not config.STRING5
        ):
            LOGGER(__name__).error("Assistant client variables not defined, exiting...")
            return

        # Step 2: Start HTTP server in a separate thread (for Render)
        http_thread = threading.Thread(target=run_http_server, daemon=True)
        http_thread.start()
        LOGGER(__name__).info("🌐 HTTP server thread started for Render health checks")

        # Step 3: Load banned users from database
        try:
            users = await get_gbanned()
            for user_id in users:
                BANNED_USERS.add(user_id)
            users = await get_banned_users()
            for user_id in users:
                BANNED_USERS.add(user_id)
        except:
            pass

        # Step 4: Start sudo setup
        await sudo()
        
        # Step 5: Start the main bot client
        await app.start()
        
        # Step 6: Load all plugin modules
        for all_module in ALL_MODULES:
            try:
                importlib.import_module("BrandrdXMusic.plugins" + all_module)
            except Exception as e:
                LOGGER("BrandrdXMusic.plugins").error(f"Failed to load plugin {all_module}: {e}")
        LOGGER("BrandrdXMusic.plugins").info("Successfully Imported Modules...")
        
        # Step 7: Start assistant/userbot clients
        await userbot.start()
        
        # Step 8: Initialize voice call handler
        await Hotty.start()
        
        # Step 9: Test VC (optional)
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
        
        # Step 10: Setup decorators
        await Hotty.decorators()
        
        LOGGER("BrandrdXMusic").info(
            "🎉 BrandrdXMusic Bot started successfully! Ready to play music! 🎵
"
            "Join @BRANDRD_BOT for support"
        )

        # Step 11: Keep the bot running
        try:
            await idle()
        except KeyboardInterrupt:
            LOGGER("BrandrdXMusic").info("Received stop signal...")
        except Exception as e:
            LOGGER("BrandrdXMusic").error(f"Error during idle: {e}")
        
        # Step 12: Cleanup
        await app.stop()
        await userbot.stop()
        LOGGER("BrandrdXMusic").info("Stopping Brandrd Music Bot...")
        
    except Exception as e:
        LOGGER("BrandrdXMusic").error(f"Critical error in init: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(init())
    except KeyboardInterrupt:
        LOGGER("BrandrdXMusic").info("Bot stopped by user (Ctrl+C)")
    except SystemExit as e:
        LOGGER("BrandrdXMusic").error(f"Bot exited with system error: {e}")
        raise
    except Exception as e:
        LOGGER("BrandrdXMusic").error(f"Unexpected error caused bot to stop: {e}", exc_info=True)
    finally:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.stop()
        except:
            pass
