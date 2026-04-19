
import os
import random

import discord
from discord.ext import commands
from discord import app_commands

from core import (
    DEFAULT_SETTINGS, DEFAULT_RPG, DEFAULT_MONSTERS, DEFAULT_BOSSES, DEFAULT_STORY,
    ensure_user, get_users, load_json, save_json, apply_level_up, assign_daily_quests,
    progress_user_stats, claim_daily_rewards, check_unlocks, item_apply, make_bar, is_adminish
)

class StoryChoiceView(discord.ui.View):
    def __init__(self, chapter_key: str):
        super().__init__(timeout=180)
        self.chapter_key = chapter_key
        story = load_json("story.json", DEFAULT_STORY)
        chapter = story["chapters"].get(chapter_key, {})
        for choice in chapter.get("choices", [])[:5]:
            self.add_item(StoryChoiceButton(choice["label"], choice["result"]))

class StoryChoiceButton(discord.ui.Button):
    def __init__(self, label_text: str, result_text: str):
        super().__init__(label=label_text[:80], style=discord.ButtonStyle.primary)
        self.result_text = result_text

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=discord.Embed(title="선택 결과", description=self.result_text, color=discord.Color.orange()), ephemeral=True)

class RPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def allowed(self, interaction):
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        target = int(os.getenv("GUILD_ID", settings.get("guild_id", 0) or 0))
        return not target or (interaction.guild and interaction.guild.id == target)

    @app_commands.command(name="참가", description="RPG에 참가")
    async def join(self, interaction: discord.Interaction, 힘: app_commands.Range[int,1,10], 민첩: app_commands.Range[int,1,10], 지능: app_commands.Range[int,1,10]):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        if 힘 + 민첩 + 지능 > 12:
            return await interaction.response.send_message("능력치 총합은 12 이하여야 합니다.", ephemeral=True)
        users = get_users()
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        user["rpg"]["joined"] = True
        user["rpg"]["str"] = 힘
        user["rpg"]["agi"] = 민첩
        user["rpg"]["int"] = 지능
        user["rpg"]["hp"] = user["rpg"]["max_hp"]
        users[str(interaction.user.id)] = user
        save_json("users.json", users)
        await interaction.response.send_message(f"참가 완료. 힘 {힘} / 민첩 {민첩} / 지능 {지능}")

    @app_commands.command(name="현재상황", description="현재 스토리 상황")
    async def scene(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        rpg = load_json("rpg.json", DEFAULT_RPG)
        story = load_json("story.json", DEFAULT_STORY)
        chapter_key = str(rpg["chapter"])
        chapter = story["chapters"].get(chapter_key, {})
        desc = rpg["scene"]
        if chapter.get("summary"):
            desc += f"\n\n스토리: {chapter['summary']}"
        embed = discord.Embed(title=f"챕터 {rpg['chapter']} - {chapter.get('title', '')}", description=desc, color=discord.Color.orange())
        view = StoryChoiceView(chapter_key) if chapter.get("choices") else None
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="행동", description="행동 판정")
    async def action(self, interaction: discord.Interaction, 종류: str, 설명: str):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = get_users()
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        if not user["rpg"]["joined"]:
            return await interaction.response.send_message("/참가 먼저 해주세요.", ephemeral=True)
        assign_daily_quests(user)
        keys = {"힘":"str","민첩":"agi","지능":"int"}
        if 종류 not in keys:
            return await interaction.response.send_message("종류는 힘/민첩/지능", ephemeral=True)
        roll = random.randint(1, 20)
        total = roll + user["rpg"][keys[종류]]
        result = "대성공" if total >= 18 else "성공" if total >= 13 else "애매한 성공" if total >= 9 else "실패"
        user["xp"] += 15
        user["coins"] += 5
        progress_user_stats(user, "actions", 1)
        apply_level_up(user)
        rewards = claim_daily_rewards(user)
        titles, achievements = check_unlocks(user)
        users[str(interaction.user.id)] = user
        save_json("users.json", users)
        embed = discord.Embed(title=f"{interaction.user.display_name}의 행동", color=discord.Color.purple())
        embed.add_field(name="설명", value=설명, inline=False)
        embed.add_field(name="판정", value=f"d20({roll}) + {종류} = **{total}**", inline=False)
        embed.add_field(name="결과", value=result, inline=False)
        if rewards: embed.add_field(name="퀘스트 보상", value=", ".join(rewards), inline=False)
        if titles: embed.add_field(name="새 칭호", value=", ".join(titles), inline=False)
        if achievements: embed.add_field(name="새 도전과제", value=", ".join(achievements), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="탐색", description="몬스터 조우")
    async def encounter(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = get_users()
        monsters = load_json("monsters.json", DEFAULT_MONSTERS)
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        if not user["rpg"]["joined"]:
            return await interaction.response.send_message("/참가 먼저 해주세요.", ephemeral=True)
        code = random.choice(list(monsters.keys()))
        m = monsters[code]
        user["rpg"]["current_monster"] = code
        user["rpg"]["current_monster_hp"] = m["hp"]
        users[str(interaction.user.id)] = user
        save_json("users.json", users)
        embed = discord.Embed(title=f"몬스터 조우: {m['name']}", color=discord.Color.red())
        embed.add_field(name="HP", value=f"{m['hp']} / {m['hp']} [{make_bar(m['hp'], m['hp'])}]", inline=False)
        embed.add_field(name="공격력", value=str(m["atk"]))
        embed.add_field(name="방어력", value=str(m["def"]))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="공격", description="현재 몬스터 공격")
    async def attack(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = get_users()
        monsters = load_json("monsters.json", DEFAULT_MONSTERS)
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        code = user["rpg"].get("current_monster")
        if not code:
            return await interaction.response.send_message("먼저 /탐색 으로 몬스터를 만나세요.", ephemeral=True)
        m = monsters.get(code)
        if not m:
            return await interaction.response.send_message("몬스터 오류", ephemeral=True)
        player_hit = random.randint(1,20) + user["rpg"]["str"]
        damage = max(1, random.randint(6,12) + user["rpg"]["str"] - m["def"])
        desc = []
        if player_hit >= 11:
            user["rpg"]["current_monster_hp"] = max(0, user["rpg"]["current_monster_hp"] - damage)
            desc.append(f"명중! {damage} 피해")
        else:
            desc.append("공격이 빗나갔다")
        if user["rpg"]["current_monster_hp"] <= 0:
            user["coins"] += m["coin_reward"]
            user["xp"] += m["xp_reward"]
            progress_user_stats(user, "kills", 1)
            drop_text = "없음"
            if m.get("drops") and random.random() < 0.5:
                drop = random.choice(m["drops"])
                user["inventory"][drop] = user["inventory"].get(drop, 0) + 1
                drop_text = drop
            desc.append(f"✅ {m['name']} 처치! +{m['coin_reward']}코인 / +{m['xp_reward']}XP / 드랍: {drop_text}")
            user["rpg"]["current_monster"] = ""
            user["rpg"]["current_monster_hp"] = 0
        else:
            retaliate = max(1, random.randint(4, m["atk"]) - user["rpg"]["def"])
            if random.randint(1,20) + user["rpg"]["agi"] >= 16:
                desc.append("몬스터 반격 회피!")
            else:
                user["rpg"]["hp"] = max(0, user["rpg"]["hp"] - retaliate)
                desc.append(f"몬스터 반격! {retaliate} 피해")
        apply_level_up(user)
        rewards = claim_daily_rewards(user)
        titles, achievements = check_unlocks(user)
        users[str(interaction.user.id)] = user
        save_json("users.json", users)
        embed = discord.Embed(title=f"전투: {m['name']}", description="\n".join(desc), color=discord.Color.dark_red())
        if user["rpg"]["current_monster"]:
            embed.add_field(name="몬스터 HP", value=f"{user['rpg']['current_monster_hp']}/{m['hp']} [{make_bar(user['rpg']['current_monster_hp'], m['hp'])}]", inline=False)
        embed.add_field(name="내 HP", value=f"{user['rpg']['hp']}/{user['rpg']['max_hp']}", inline=False)
        if rewards: embed.add_field(name="퀘스트 보상", value=", ".join(rewards), inline=False)
        if titles: embed.add_field(name="새 칭호", value=", ".join(titles), inline=False)
        if achievements: embed.add_field(name="새 도전과제", value=", ".join(achievements), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="상점", description="상점 보기")
    async def shop(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        rpg = load_json("rpg.json", DEFAULT_RPG)
        embed = discord.Embed(title="상점", color=discord.Color.gold())
        for code, item in rpg["shop"].items():
            embed.add_field(name=f"{item['name']} ({code})", value=f"{item['price']} 코인 / {item['effect']} +{item['amount']} / {item.get('rarity','common')}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="구매", description="아이템 구매")
    async def buy(self, interaction: discord.Interaction, 아이템코드: str):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        rpg = load_json("rpg.json", DEFAULT_RPG)
        users = get_users()
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        item = rpg["shop"].get(아이템코드)
        if not item:
            return await interaction.response.send_message("없는 아이템", ephemeral=True)
        if user["coins"] < item["price"]:
            return await interaction.response.send_message("코인 부족", ephemeral=True)
        user["coins"] -= item["price"]
        user["inventory"][아이템코드] = user["inventory"].get(아이템코드, 0) + 1
        users[str(interaction.user.id)] = user
        save_json("users.json", users)
        await interaction.response.send_message(f"{item['name']} 구매 완료", ephemeral=True)

    @app_commands.command(name="사용", description="아이템 사용")
    async def use(self, interaction: discord.Interaction, 아이템코드: str):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = get_users()
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        if user["inventory"].get(아이템코드, 0) <= 0:
            return await interaction.response.send_message("보유한 아이템이 없습니다.", ephemeral=True)
        result = item_apply(user, 아이템코드)
        if "존재하지" not in result and "사용할 수 없습니다" not in result:
            user["inventory"][아이템코드] -= 1
            if user["inventory"][아이템코드] <= 0:
                del user["inventory"][아이템코드]
        users[str(interaction.user.id)] = user
        save_json("users.json", users)
        await interaction.response.send_message(result, ephemeral=True)

    @app_commands.command(name="보스정보", description="현재 보스 상태")
    async def bossinfo(self, interaction: discord.Interaction, 보스코드: str = ""):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        bosses = load_json("bosses.json", DEFAULT_BOSSES)
        if not 보스코드:
            보스코드 = next(iter(bosses.keys()))
        if 보스코드 not in bosses:
            return await interaction.response.send_message("없는 보스 코드입니다.", ephemeral=True)
        boss = bosses[보스코드]
        embed = discord.Embed(title=f"보스: {boss['name']}", color=discord.Color.dark_red())
        embed.add_field(name="HP", value=f"{boss['hp']}/{boss['max_hp']} [{make_bar(boss['hp'], boss['max_hp'])}]", inline=False)
        embed.add_field(name="상태", value="생존" if boss["alive"] else "처치됨", inline=False)
        top = sorted(boss["participants"].items(), key=lambda x: x[1], reverse=True)[:5]
        if top:
            embed.add_field(name="누적 피해 TOP", value="\n".join([f"<@{uid}> : {dmg}" for uid, dmg in top]), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="보스공격", description="현재 보스 공격")
    async def bossattack(self, interaction: discord.Interaction, 보스코드: str = ""):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = get_users()
        bosses = load_json("bosses.json", DEFAULT_BOSSES)
        user = users.get(str(interaction.user.id)) or ensure_user(interaction.user.id, interaction.user.display_name)
        if not 보스코드:
            보스코드 = next(iter(bosses.keys()))
        if 보스코드 not in bosses:
            return await interaction.response.send_message("없는 보스 코드입니다.", ephemeral=True)
        boss = bosses[보스코드]
        if not boss["alive"] or boss["hp"] <= 0:
            return await interaction.response.send_message("현재 살아있는 보스가 없습니다.", ephemeral=True)

        pattern = boss["patterns"][boss["pattern_index"] % len(boss["patterns"])] if boss.get("patterns") else {"name": "기본 공격", "bonus_atk": 0, "text": "보스가 공격한다."}
        boss["pattern_index"] = (boss.get("pattern_index", 0) + 1) % max(1, len(boss.get("patterns", [])))

        hit = random.randint(1,20) + user["rpg"]["str"]
        damage = max(1, random.randint(8,16) + user["rpg"]["str"] - boss["def"])
        desc = [f"패턴: **{pattern['name']}**", pattern["text"]]
        if hit >= 12:
            boss["hp"] = max(0, boss["hp"] - damage)
            boss["participants"][str(interaction.user.id)] = boss["participants"].get(str(interaction.user.id), 0) + damage
            progress_user_stats(user, "boss_hits", 1)
            user["stats"]["boss_damage"] += damage
            desc.append(f"보스에게 {damage} 피해!")
        else:
            desc.append("보스 공격이 빗나갔다.")

        retaliate = max(1, random.randint(6, boss["atk"] + pattern.get("bonus_atk", 0)) - user["rpg"]["def"])
        if random.randint(1,20) + user["rpg"]["agi"] >= 18:
            desc.append("보스 반격 회피!")
        else:
            user["rpg"]["hp"] = max(0, user["rpg"]["hp"] - retaliate)
            desc.append(f"보스 반격! {retaliate} 피해")

        if boss["hp"] <= 0:
            boss["alive"] = False
            desc.append("🏆 보스 처치 완료!")
            for uid, dealt in boss["participants"].items():
                pu = users.get(uid) or ensure_user(int(uid), uid)
                pu["coins"] += 120 + dealt // 3
                pu["xp"] += 100 + dealt // 4
                apply_level_up(pu)
                users[uid] = pu

        rewards = claim_daily_rewards(user)
        titles, achievements = check_unlocks(user)
        apply_level_up(user)
        users[str(interaction.user.id)] = user
        save_json("users.json", users)
        save_json("bosses.json", bosses)
        embed = discord.Embed(title=f"보스전: {boss['name']}", description="\n".join(desc), color=discord.Color.dark_red())
        embed.add_field(name="보스 HP", value=f"{boss['hp']}/{boss['max_hp']} [{make_bar(boss['hp'], boss['max_hp'])}]", inline=False)
        embed.add_field(name="내 HP", value=f"{user['rpg']['hp']}/{user['rpg']['max_hp']}", inline=False)
        if rewards: embed.add_field(name="퀘스트 보상", value=", ".join(rewards), inline=False)
        if titles: embed.add_field(name="새 칭호", value=", ".join(titles), inline=False)
        if achievements: embed.add_field(name="새 도전과제", value=", ".join(achievements), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="보스리스폰", description="보스 재소환")
    async def bossrespawn(self, interaction: discord.Interaction, 보스코드: str = ""):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        settings = load_json("settings.json", DEFAULT_SETTINGS)
        if not (isinstance(interaction.user, discord.Member) and is_adminish(interaction.user, settings)):
            return await interaction.response.send_message("관리자/GM만 가능합니다.", ephemeral=True)
        bosses = load_json("bosses.json", DEFAULT_BOSSES)
        targets = [보스코드] if 보스코드 else list(bosses.keys())
        for code in targets:
            if code in bosses:
                bosses[code]["hp"] = bosses[code]["max_hp"]
                bosses[code]["alive"] = True
                bosses[code]["participants"] = {}
                bosses[code]["pattern_index"] = 0
        save_json("bosses.json", bosses)
        await interaction.response.send_message("보스 리스폰 완료", ephemeral=True)

    @app_commands.command(name="보스랭킹", description="보스 누적 피해 랭킹")
    async def bossrank(self, interaction: discord.Interaction):
        if not self.allowed(interaction):
            return await interaction.response.send_message("이 서버 전용 봇입니다.", ephemeral=True)
        users = list(get_users().values())
        users.sort(key=lambda x: x["stats"].get("boss_damage", 0), reverse=True)
        lines = [f"{i+1}. {u['name']} - {u['stats'].get('boss_damage',0)} 피해" for i, u in enumerate(users[:10])]
        await interaction.response.send_message(embed=discord.Embed(title="보스 랭킹", description="\n".join(lines) if lines else "없음"))

async def setup(bot):
    await bot.add_cog(RPG(bot))
