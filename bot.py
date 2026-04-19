
import os
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv

from core import ensure_data_files, load_json, DEFAULT_SETTINGS, apply_branding_if_possible

load_dotenv()
ensure_data_files()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class Room09Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        cogs = [
            "cogs.general",
            "cogs.admin",
            "cogs.rpg",
            "cogs.panels",
            "cogs.ai_stub",
            "cogs.tickets",
        ]
        for cog in cogs:
            await self.load_extension(cog)

        settings = load_json("settings.json", DEFAULT_SETTINGS)
        guild_id = int(os.getenv("GUILD_ID", settings.get("guild_id", 0) or 0))
        if guild_id:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Synced to guild {guild_id}")
        else:
            await self.tree.sync()
            print("Synced globally")

    async def on_ready(self):
        print(f"Logged in as {self.user} ({self.user.id})")
        try:
            await apply_branding_if_possible(self)
        except Exception:
            traceback.print_exc()

bot = Room09Bot()

if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN 환경변수가 없습니다.")
    bot.run(token)
