
import os
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands

from core import (
    DEFAULT_SETTINGS, DEFAULT_USERS, DEFAULT_BRANDING, HELP_CATEGORIES,
    ensure_user, get_users, load_json, save_json,
    apply_level_up, assign_daily_quests, progress_user_stats, claim_daily_rewards,
    check_unlocks, is_adminish, make_presence, apply_branding_if_possible, help_overview_text
)

HELP_CATEGORY_CHOICES = [
    app_commands.Choice(name="기본", value="기본"),
    app_commands.Choice(name="RPG", value="RPG"),
    app_commands.Choice(name="보스전", value="보스전"),
    app_commands.Choice(name="패널", value="패널"),
    app_commands.Choice(name="이미지", value="이미지"),
    app_commands.Choice(name="관리", value="관리"),
    app_commands.Choice(name="관리자 확장", value="관리자 확장"),
    app_commands.Choice(name="브랜딩", value="브랜딩"),
]

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_buckets = {}

    def allowed(self, interaction: discord.Interaction):
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        target = int(os.getenv("GUILD_ID", settings.get("guild_id", 0) or 0))
        return not target or (interaction.guild and interaction.guild.id == target)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        ensure_user(member.id, member.display_name)
        cid = settings.get("welcome_channel_id", 0)
        if cid:
            ch = member.guild.get_channel(cid)
            if ch:
                msg = settings.get("welcome_message", "{mention} 님, 환영합니다.")
                await ch.send(msg.format(mention=member.mention, user=member.name, server=member.guild.name))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        users = get_users()
        user = users.get(str(message.author.id)) or ensure_user(message.author.id, message.author.display_name)
        assign_daily_quests(user)

        bucket = self.message_buckets.setdefault(message.author.id, [])
        now = datetime.utcnow()
        bucket[:] = [t for t in bucket if (now - t).total_seconds() < 10]
        bucket.append(now)
        if len(bucket) > settings.get("spam_limit_per_10s", 6):
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention} 너무 빠른 도배는 제한됩니다.", delete_after=4)
                return
            except Exception:
                pass

        lowered = message.content.lower()
        for word in settings.get("forbidden_words", []):
            if word and word.lower() in lowered:
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} 금지어 포함으로 삭제되었습니다.", delete_after=4)
                    return
                except Exception:
                    pass

        progress_user_stats(user, "messages", 1)
        if settings.get("leveling_enabled", True):
            user["xp"] += 10
            user["coins"] += 2
            leveled = apply_level_up(user)
            if leveled:
                await message.channel.send(f"🎉 {message.author.mention} 레벨 업! 현재 레벨: {user['level']}")

        rewards = claim_daily_rewards(user)
        titles, achievements = check_unlocks(user)
        users[str(message.author.id)] = user
        save_json("users.json", users)

        if rewards:
            await message.channel.send(f"✅ {message.author.mention} 퀘스트 보상 수령: {', '.join(rewards)}")
        if titles:
            await message.channel.send(f"🏷️ {message.author.mention} 새 칭호 획득: {', '.join(titles)}")
        if achievements:
            await message.channel.send(f"🏆 {message.author.mention} 도전과제 달성: {', '.join(achievements)}")

    @app_commands.command(name="핑", description="봇 응답 확인")
    async def ping(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        await interaction.response.send_message(f"퐁! `{round(self.bot.latency * 1000)}ms`", ephemeral=True)

    @app_commands.command(name="도움말", description="카테고리별 전체 명령어 보기")
    @app_commands.describe(카테고리="보고 싶은 명령어 카테고리")
    @app_commands.choices(카테고리=HELP_CATEGORY_CHOICES)
    async def help_cmd(self, interaction: discord.Interaction, 카테고리: app_commands.Choice[str] | None = None):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if 카테고리 is None:
            embed = discord.Embed(title="전체 명령어 카테고리", description=help_overview_text(), color=discord.Color.blurple())
            embed.set_footer(text="/도움말 카테고리:기본 같은 식으로 상세 목록을 볼 수 있습니다.")
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        items = HELP_CATEGORIES.get(카테고리.value, [])
        lines = [f"`{cmd}` — {desc}" for cmd, desc in items]
        embed = discord.Embed(title=f"{카테고리.value} 명령어", description="\n".join(lines) if lines else "없음", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="명령어", description="전체 명령어 표를 한 번에 보기")
    async def commands_table(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        pages = []
        for category, items in HELP_CATEGORIES.items():
            lines = [f"`{cmd}` — {desc}" for cmd, desc in items]
            pages.append(discord.Embed(title=f"{category} 명령어", description="\n".join(lines), color=discord.Color.green()))
        await interaction.response.send_message(embed=pages[0], ephemeral=True)
        for e in pages[1:]:
            await interaction.followup.send(embed=e, ephemeral=True)

    @app_commands.command(name="내정보", description="내 정보 확인")
    async def myinfo(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = get_users()
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        assign_daily_quests(user)
        title_name = user.get("equipped_title") or "없음"
        inv_text = ", ".join(f"{k} x{v}" for k, v in user["inventory"].items()) if user["inventory"] else "없음"
        embed = discord.Embed(title=f"{interaction.user.display_name} 정보", color=discord.Color.green())
        embed.add_field(name="레벨", value=str(user["level"]))
        embed.add_field(name="XP", value=str(user["xp"]))
        embed.add_field(name="코인", value=str(user["coins"]))
        embed.add_field(name="칭호", value=title_name)
        embed.add_field(name="HP", value=f"{user['rpg']['hp']} / {user['rpg']['max_hp']}", inline=False)
        embed.add_field(name="능력치", value=f"힘 {user['rpg']['str']} / 민첩 {user['rpg']['agi']} / 지능 {user['rpg']['int']} / 방어 {user['rpg']['def']}", inline=False)
        embed.add_field(name="인벤토리", value=inv_text, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        users[str(interaction.user.id)] = user
        save_json("users.json", users)

    @app_commands.command(name="일일보상", description="하루 1회 코인 수령")
    async def daily(self, interaction: discord.Interaction):
        from core import today_str
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        if not settings.get("daily_enabled", True):
            return await interaction.response.send_message("일일 보상이 비활성화되어 있습니다.", ephemeral=True)
        users = get_users()
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        if user["daily_last_claim"] == today_str():
            return await interaction.response.send_message("오늘은 이미 수령했습니다.", ephemeral=True)
        reward = 80 + user["level"] * 5
        user["daily_last_claim"] = today_str()
        user["coins"] += reward
        users[str(interaction.user.id)] = user
        save_json("users.json", users)
        await interaction.response.send_message(f"일일 보상 수령 완료: +{reward} 코인", ephemeral=True)

    @app_commands.command(name="일일퀘스트", description="오늘의 퀘스트 확인")
    async def dailyquests(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = get_users()
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        assign_daily_quests(user)
        rewards = claim_daily_rewards(user)
        users[str(interaction.user.id)] = user
        save_json("users.json", users)
        lines = []
        for q in user["daily_quests"]:
            state = "✅" if q["claimed"] else f"{q['progress']}/{q['target']}"
            lines.append(f"- {q['name']} : {state}")
        if rewards:
            lines.append("")
            lines.append("이번에 수령한 보상: " + ", ".join(rewards))
        await interaction.response.send_message(embed=discord.Embed(title="일일 퀘스트", description="\n".join(lines) if lines else "없음"), ephemeral=True)

    @app_commands.command(name="칭호목록", description="보유 칭호 확인")
    async def titlelist(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = get_users()
        titles = load_json("titles.json", {})
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        owned = user.get("owned_titles", [])
        if not owned:
            return await interaction.response.send_message("보유 칭호가 없습니다.", ephemeral=True)
        text = "\n".join([f"- {titles.get(code, {}).get('name', code)}" for code in owned])
        await interaction.response.send_message(embed=discord.Embed(title="보유 칭호", description=text), ephemeral=True)

    @app_commands.command(name="칭호장착", description="칭호 장착")
    async def equiptitle(self, interaction: discord.Interaction, 코드: str):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = get_users()
        titles = load_json("titles.json", {})
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        if 코드 not in user.get("owned_titles", []):
            return await interaction.response.send_message("해당 칭호를 보유하지 않았습니다.", ephemeral=True)
        user["equipped_title"] = titles.get(코드, {}).get("name", 코드)
        users[str(interaction.user.id)] = user
        save_json("users.json", users)
        await interaction.response.send_message(f"칭호 장착 완료: {user['equipped_title']}", ephemeral=True)

    @app_commands.command(name="도전과제", description="달성한 도전과제 확인")
    async def achievements(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = get_users()
        achievements = load_json("achievements.json", {})
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        owned = user.get("claimed_achievements", [])
        if not owned:
            return await interaction.response.send_message("달성한 도전과제가 없습니다.", ephemeral=True)
        text = "\n".join([f"- {achievements.get(code, {}).get('name', code)}" for code in owned])
        await interaction.response.send_message(embed=discord.Embed(title="달성 도전과제", description=text), ephemeral=True)

    @app_commands.command(name="랭킹", description="레벨 랭킹")
    async def ranking(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = list(get_users().values())
        users.sort(key=lambda x: (x["level"], x["xp"], x["coins"]), reverse=True)
        lines = [f"{i+1}. {u['name']} - Lv.{u['level']} / {u['coins']}코인" for i, u in enumerate(users[:10])]
        await interaction.response.send_message(embed=discord.Embed(title="랭킹", description="\n".join(lines) if lines else "없음"))

    @app_commands.command(name="브랜드확인", description="봇 브랜딩 설정 확인")
    async def brandinfo(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        branding = load_json("branding.json", DEFAULT_BRANDING)
        embed = discord.Embed(title="브랜딩 설정", color=discord.Color.blurple())
        for k, v in branding.items():
            embed.add_field(name=k, value=str(v), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="브랜드설정", description="봇 이름/상태/프로필 설정")
    async def brandset(self, interaction: discord.Interaction, 이름: str = "", 상태문구: str = "", 상태종류: str = "", 시작시적용: bool = False):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        if not (isinstance(interaction.user, discord.Member) and is_adminish(interaction.user, settings)):
            return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        branding = load_json("branding.json", DEFAULT_BRANDING)
        if 이름:
            branding["bot_display_name"] = 이름
        if 상태문구:
            branding["status_text"] = 상태문구
        if 상태종류:
            branding["presence_type"] = 상태종류
        branding["apply_on_startup"] = 시작시적용
        save_json("branding.json", branding)
        await self.bot.change_presence(activity=make_presence(branding))
        await interaction.response.send_message("브랜딩 설정을 저장했습니다. 이름/아이콘은 `/브랜드적용` 또는 재시작 시 적용됩니다.", ephemeral=True)

    @app_commands.command(name="브랜드아이콘경로", description="봇 아이콘 파일 경로 저장")
    async def brandicon(self, interaction: discord.Interaction, 경로: str):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        if not (isinstance(interaction.user, discord.Member) and is_adminish(interaction.user, settings)):
            return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        branding = load_json("branding.json", DEFAULT_BRANDING)
        branding["icon_path"] = 경로
        save_json("branding.json", branding)
        await interaction.response.send_message(f"아이콘 경로 저장 완료: `{경로}`", ephemeral=True)

    @app_commands.command(name="브랜드적용", description="저장된 봇 이름/아이콘/상태 적용 시도")
    async def brandapply(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        if not (isinstance(interaction.user, discord.Member) and is_adminish(interaction.user, settings)):
            return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        try:
            await apply_branding_if_possible(self.bot)
            await interaction.response.send_message("브랜딩 적용 시도를 완료했습니다. 디스코드 제한 때문에 이름/아이콘 반영이 늦거나 실패할 수 있습니다.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"적용 실패: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(General(bot))
