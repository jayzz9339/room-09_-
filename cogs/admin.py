
import os

import discord
from discord.ext import commands
from discord import app_commands

from core import (
    DEFAULT_SETTINGS, DEFAULT_RPG, DEFAULT_MONSTERS, DEFAULT_BOSSES, DEFAULT_STORY,
    load_json, save_json, get_users, ensure_user, is_adminish
)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def allowed(self, interaction):
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        target = int(os.getenv("GUILD_ID", settings.get("guild_id", 0) or 0))
        return not target or (interaction.guild and interaction.guild.id == target)

    def admin_only(self, interaction):
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        return isinstance(interaction.user, discord.Member) and is_adminish(interaction.user, settings)

    @app_commands.command(name="채널설정", description="시스템 채널 저장")
    async def setchannel(self, interaction: discord.Interaction, kind: str, channel: discord.abc.GuildChannel):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction):
            return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        mapping = {
            "welcome":"welcome_channel_id", "log":"log_channel_id", "announce":"announce_channel_id",
            "ticket_category":"ticket_category_id", "ticket_panel":"ticket_panel_channel_id", "image":"image_channel_id"
        }
        if kind not in mapping:
            return await interaction.response.send_message("kind: welcome/log/announce/ticket_category/ticket_panel/image", ephemeral=True)
        settings[mapping[kind]] = channel.id
        save_json("settings.json", settings)
        await interaction.response.send_message(f"{kind} 채널을 {channel.mention} 으로 저장했습니다.", ephemeral=True)

    @app_commands.command(name="환영문구", description="환영 문구 설정")
    async def setwelcome(self, interaction: discord.Interaction, 문구: str):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        settings["welcome_message"] = 문구
        save_json("settings.json", settings)
        await interaction.response.send_message("저장했습니다.", ephemeral=True)

    @app_commands.command(name="금지어추가", description="금지어 추가")
    async def addbad(self, interaction: discord.Interaction, 단어: str):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        if 단어 not in settings["forbidden_words"]:
            settings["forbidden_words"].append(단어)
            save_json("settings.json", settings)
        await interaction.response.send_message(f"금지어 `{단어}` 추가 완료", ephemeral=True)

    @app_commands.command(name="금지어제거", description="금지어 제거")
    async def delbad(self, interaction: discord.Interaction, 단어: str):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        if 단어 in settings["forbidden_words"]:
            settings["forbidden_words"].remove(단어)
            save_json("settings.json", settings)
        await interaction.response.send_message(f"금지어 `{단어}` 제거 완료", ephemeral=True)

    @app_commands.command(name="공지", description="임베드 공지")
    async def announce(self, interaction: discord.Interaction, 제목: str, 내용: str):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        target = interaction.channel
        cid = settings.get("announce_channel_id", 0)
        if cid and interaction.guild:
            target = interaction.guild.get_channel(cid) or interaction.channel
        await target.send(embed=discord.Embed(title=제목, description=내용, color=discord.Color.dark_teal()))
        await interaction.response.send_message("공지 전송 완료", ephemeral=True)

    @app_commands.command(name="투표", description="간단 투표")
    async def poll(self, interaction: discord.Interaction, 제목: str):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        await interaction.response.send_message("투표 생성 완료", ephemeral=True)
        msg = await interaction.channel.send(embed=discord.Embed(title=f"📊 {제목}", description="👍 / 👎 반응"))
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

    @app_commands.command(name="경고", description="경고 부여")
    async def warn(self, interaction: discord.Interaction, 대상: discord.Member, 사유: str):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        users = get_users()
        user = users.get(str(대상.id)) or ensure_user(대상.id, 대상.display_name)
        user["warns"] += 1
        users[str(대상.id)] = user
        save_json("users.json", users)
        await interaction.response.send_message(f"{대상.mention} 경고 1회 부여. 현재 {user['warns']}회 / 사유: {사유}", ephemeral=True)

    @app_commands.command(name="청소", description="메시지 삭제")
    async def purge(self, interaction: discord.Interaction, 개수: app_commands.Range[int, 1, 100]):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message("텍스트 채널에서만 가능합니다.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=개수)
        await interaction.followup.send(f"{len(deleted)}개 삭제 완료", ephemeral=True)

    @app_commands.command(name="아이템추가", description="상점 아이템 추가")
    async def add_item(self, interaction: discord.Interaction, 코드: str, 이름: str, 가격: int, 효과: str, 수치: int, 등급: str = "common"):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        rpg = load_json("rpg.json", DEFAULT_RPG)
        rpg["shop"][코드] = {"name": 이름, "price": 가격, "effect": 효과, "amount": 수치, "rarity": 등급}
        save_json("rpg.json", rpg)
        await interaction.response.send_message(f"아이템 `{이름}` 추가 완료", ephemeral=True)

    @app_commands.command(name="아이템삭제", description="상점 아이템 삭제")
    async def del_item(self, interaction: discord.Interaction, 코드: str):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        rpg = load_json("rpg.json", DEFAULT_RPG)
        if 코드 in rpg["shop"]:
            del rpg["shop"][코드]
            save_json("rpg.json", rpg)
        await interaction.response.send_message(f"아이템 `{코드}` 삭제 완료", ephemeral=True)

    @app_commands.command(name="몬스터추가", description="몬스터 추가")
    async def add_monster(self, interaction: discord.Interaction, 코드: str, 이름: str, hp: int, atk: int, def_: int, 보상코인: int, 보상xp: int, 드랍: str = ""):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        monsters = load_json("monsters.json", DEFAULT_MONSTERS)
        drops = [x.strip() for x in 드랍.split(",") if x.strip()]
        monsters[코드] = {"name": 이름, "hp": hp, "atk": atk, "def": def_, "coin_reward": 보상코인, "xp_reward": 보상xp, "drops": drops}
        save_json("monsters.json", monsters)
        await interaction.response.send_message(f"몬스터 `{이름}` 추가 완료", ephemeral=True)

    @app_commands.command(name="몬스터삭제", description="몬스터 삭제")
    async def del_monster(self, interaction: discord.Interaction, 코드: str):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        monsters = load_json("monsters.json", DEFAULT_MONSTERS)
        if 코드 in monsters:
            del monsters[코드]
            save_json("monsters.json", monsters)
        await interaction.response.send_message(f"몬스터 `{코드}` 삭제 완료", ephemeral=True)

    @app_commands.command(name="보스추가", description="보스 추가")
    async def add_boss(self, interaction: discord.Interaction, 코드: str, 이름: str, hp: int, atk: int, def_: int, 이미지프롬프트: str = ""):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        bosses = load_json("bosses.json", DEFAULT_BOSSES)
        bosses[코드] = {
            "name": 이름, "max_hp": hp, "hp": hp, "atk": atk, "def": def_, "alive": True, "participants": {},
            "image_prompt": 이미지프롬프트 or 이름,
            "pattern_index": 0,
            "patterns": [
                {"name": "기본 공격", "bonus_atk": 0, "text": f"{이름}이 공격한다."},
                {"name": "격노", "bonus_atk": 6, "text": f"{이름}이 격노 상태가 되었다."},
            ],
        }
        save_json("bosses.json", bosses)
        await interaction.response.send_message(f"보스 `{이름}` 추가 완료", ephemeral=True)

    @app_commands.command(name="보스삭제", description="보스 삭제")
    async def del_boss(self, interaction: discord.Interaction, 코드: str):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        bosses = load_json("bosses.json", DEFAULT_BOSSES)
        if 코드 in bosses:
            del bosses[코드]
            save_json("bosses.json", bosses)
        await interaction.response.send_message(f"보스 `{코드}` 삭제 완료", ephemeral=True)

    @app_commands.command(name="칭호추가", description="칭호 추가")
    async def add_title(self, interaction: discord.Interaction, 코드: str, 이름: str, 설명: str, 조건타입: str, 목표: int):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        titles = load_json("titles.json", {})
        titles[코드] = {"name": 이름, "description": 설명, "condition_type": 조건타입, "target": 목표}
        save_json("titles.json", titles)
        await interaction.response.send_message(f"칭호 `{이름}` 추가 완료", ephemeral=True)

    @app_commands.command(name="도전과제추가", description="도전과제 추가")
    async def add_achievement(self, interaction: discord.Interaction, 코드: str, 이름: str, 설명: str, 조건타입: str, 목표: int, 코인보상: int = 0, xp보상: int = 0):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        achievements = load_json("achievements.json", {})
        achievements[코드] = {"name": 이름, "description": 설명, "condition_type": 조건타입, "target": 목표, "coin_reward": 코인보상, "xp_reward": xp보상}
        save_json("achievements.json", achievements)
        await interaction.response.send_message(f"도전과제 `{이름}` 추가 완료", ephemeral=True)

    @app_commands.command(name="퀘스트추가", description="일일 퀘스트 템플릿 추가")
    async def add_quest(self, interaction: discord.Interaction, 코드: str, 이름: str, 조건타입: str, 목표: int, 코인: int, xp: int):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        quests = load_json("quests.json", {"templates":[]})
        quests["templates"].append({"code": 코드, "name": 이름, "type": 조건타입, "target": 목표, "coin": 코인, "xp": xp})
        save_json("quests.json", quests)
        await interaction.response.send_message(f"퀘스트 `{이름}` 추가 완료", ephemeral=True)

    @app_commands.command(name="장면변경", description="현재 장면 변경")
    async def set_scene(self, interaction: discord.Interaction, 내용: str):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        rpg = load_json("rpg.json", DEFAULT_RPG)
        rpg["scene"] = 내용
        save_json("rpg.json", rpg)
        await interaction.response.send_message("장면 변경 완료", ephemeral=True)

    @app_commands.command(name="스토리선택지추가", description="챕터 선택지 추가")
    async def add_story_choice(self, interaction: discord.Interaction, 챕터: int, 라벨: str, 결과: str):
        if not self.allowed(interaction): return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if not self.admin_only(interaction): return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        story = load_json("story.json", DEFAULT_STORY)
        chapter_key = str(챕터)
        if chapter_key not in story["chapters"]:
            story["chapters"][chapter_key] = {"title": f"챕터 {챕터}", "summary": "", "choices": []}
        story["chapters"][chapter_key]["choices"].append({"label": 라벨, "result": 결과})
        save_json("story.json", story)
        await interaction.response.send_message("선택지 추가 완료", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
