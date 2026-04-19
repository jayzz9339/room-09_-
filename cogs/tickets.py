
import os
import discord
from discord.ext import commands
from discord import app_commands

from core import DEFAULT_SETTINGS, load_json, save_json, is_adminish

def allowed(interaction):
    settings = load_json("settings.json", DEFAULT_SETTINGS)
    target = int(os.getenv("GUILD_ID", settings.get("guild_id", 0) or 0))
    return not target or (interaction.guild and interaction.guild.id == target)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="티켓 닫기", style=discord.ButtonStyle.danger, custom_id="room09:ticket_close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        tickets = load_json("tickets.json", {})
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        if str(interaction.channel_id) not in tickets:
            return await interaction.response.send_message("이 채널은 티켓이 아닙니다.", ephemeral=True)
        owner_id = tickets[str(interaction.channel_id)]["owner_id"]
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("권한 확인 실패", ephemeral=True)
        if interaction.user.id != owner_id and not is_adminish(interaction.user, settings):
            return await interaction.response.send_message("티켓 소유자나 관리자만 닫을 수 있습니다.", ephemeral=True)
        tickets.pop(str(interaction.channel_id), None)
        save_json("tickets.json", tickets)
        await interaction.response.send_message("티켓을 닫습니다.", ephemeral=True)
        await interaction.channel.delete(reason="Ticket closed")

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="티켓 열기", style=discord.ButtonStyle.primary, custom_id="room09:ticket_open")
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        tickets = load_json("tickets.json", {})
        if not settings.get("ticket_enabled", True):
            return await interaction.response.send_message("티켓 기능이 비활성화되어 있습니다.", ephemeral=True)
        category_id = settings.get("ticket_category_id", 0)
        if not category_id:
            return await interaction.response.send_message("티켓 카테고리가 설정되지 않았습니다.", ephemeral=True)
        category = interaction.guild.get_channel(category_id)
        if not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message("티켓 카테고리를 찾을 수 없습니다.", ephemeral=True)

        for cid, info in tickets.items():
            if info.get("owner_id") == interaction.user.id:
                existing = interaction.guild.get_channel(int(cid))
                if existing:
                    return await interaction.response.send_message(f"이미 열린 티켓이 있습니다: {existing.mention}", ephemeral=True)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        for role in interaction.guild.roles:
            if role.name in {settings.get("gm_role_name", "GM"), settings.get("admin_role_name", "관리자")}:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}".lower().replace(" ", "-")[:25],
            category=category,
            overwrites=overwrites,
            topic=f"ticket_owner:{interaction.user.id}",
        )
        tickets[str(channel.id)] = {"owner_id": interaction.user.id}
        save_json("tickets.json", tickets)
        await interaction.response.send_message(f"티켓이 생성되었습니다: {channel.mention}", ephemeral=True)
        await channel.send(f"{interaction.user.mention} 문의 내용을 적어주세요.", view=CloseTicketView())

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketPanelView())
        self.bot.add_view(CloseTicketView())

    @app_commands.command(name="티켓패널", description="티켓 생성 패널 전송")
    async def ticketpanel(self, interaction: discord.Interaction):
        if not allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        if not (isinstance(interaction.user, discord.Member) and is_adminish(interaction.user, settings)):
            return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        await interaction.response.send_message("문의가 있으면 아래 버튼을 눌러 티켓을 열어주세요.", view=TicketPanelView())

async def setup(bot):
    await bot.add_cog(Tickets(bot))
