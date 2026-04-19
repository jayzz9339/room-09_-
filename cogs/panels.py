
import os
import discord
from discord.ext import commands
from discord import app_commands

from core import DEFAULT_SETTINGS, DEFAULT_BOSSES, load_json

def allowed(interaction):
    settings = load_json("settings.json", DEFAULT_SETTINGS)
    target = int(os.getenv("GUILD_ID", settings.get("guild_id", 0) or 0))
    return not target or (interaction.guild and interaction.guild.id == target)

class RolePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="받을 역할을 고르세요",
        custom_id="room09:role_select",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="게임", value="게임"),
            discord.SelectOption(label="음악", value="음악"),
            discord.SelectOption(label="잡담", value="잡담"),
            discord.SelectOption(label="공지", value="공지"),
        ],
    )
    async def select_role(self, interaction: discord.Interaction, select: discord.ui.Select):
        if not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("실패", ephemeral=True)
        role_name = select.values[0]
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role is None:
            role = await interaction.guild.create_role(name=role_name, reason="self role")
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            return await interaction.response.send_message(f"{role_name} 역할 제거", ephemeral=True)
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"{role_name} 역할 지급", ephemeral=True)

class RPGPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="현재상황", style=discord.ButtonStyle.secondary, custom_id="room09:scene")
    async def scene(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("RPG")
        await cog.scene.callback(cog, interaction)

    @discord.ui.button(label="내정보", style=discord.ButtonStyle.secondary, custom_id="room09:myinfo")
    async def myinfo(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("General")
        await cog.myinfo.callback(cog, interaction)

    @discord.ui.button(label="일일퀘스트", style=discord.ButtonStyle.primary, custom_id="room09:dailyquests")
    async def dailyquests(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("General")
        await cog.dailyquests.callback(cog, interaction)

    @discord.ui.button(label="상점", style=discord.ButtonStyle.success, custom_id="room09:shop")
    async def shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("RPG")
        await cog.shop.callback(cog, interaction)

class BossPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="보스 정보", style=discord.ButtonStyle.secondary, custom_id="room09:bossinfo")
    async def info(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("RPG")
        await cog.bossinfo.callback(cog, interaction, "")

    @discord.ui.button(label="보스 공격", style=discord.ButtonStyle.danger, custom_id="room09:bossattack")
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("RPG")
        await cog.bossattack.callback(cog, interaction, "")

    @discord.ui.button(label="보스 이미지", style=discord.ButtonStyle.primary, custom_id="room09:bossimage")
    async def image(self, interaction: discord.Interaction, button: discord.ui.Button):
        bosses = load_json("bosses.json", DEFAULT_BOSSES)
        _, boss = next(iter(bosses.items()))
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{boss['name']} 이미지 요청",
                description="실제 자동 생성은 외부 이미지 API 연결 후 사용 가능\n\n"
                            f"프롬프트:\n`{boss.get('image_prompt', boss['name'])}`",
                color=discord.Color.dark_magenta(),
            ),
            ephemeral=True,
        )

class Panels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(RolePanelView())
        self.bot.add_view(RPGPanelView(self.bot))
        self.bot.add_view(BossPanelView(self.bot))

    @app_commands.command(name="역할패널", description="셀프 역할 패널")
    async def rolepanel(self, interaction: discord.Interaction):
        if not allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        await interaction.response.send_message("원하는 역할을 골라주세요.", view=RolePanelView())

    @app_commands.command(name="rpg패널", description="RPG 패널")
    async def rpgpanel(self, interaction: discord.Interaction):
        if not allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        await interaction.response.send_message("RPG 패널", view=RPGPanelView(self.bot))

    @app_commands.command(name="보스패널", description="보스 패널")
    async def bosspanel(self, interaction: discord.Interaction):
        if not allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        await interaction.response.send_message("보스전 패널", view=BossPanelView(self.bot))

async def setup(bot):
    await bot.add_cog(Panels(bot))
