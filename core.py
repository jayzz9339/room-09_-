
from __future__ import annotations
import json
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

import discord

DATA_DIR = Path("data")
ASSETS_DIR = Path("assets")
KST = timezone(timedelta(hours=9))

DEFAULT_SETTINGS = {
    "guild_id": 0,
    "gm_role_name": "GM",
    "admin_role_name": "관리자",
    "welcome_channel_id": 0,
    "log_channel_id": 0,
    "announce_channel_id": 0,
    "ticket_category_id": 0,
    "ticket_panel_channel_id": 0,
    "image_channel_id": 0,
    "welcome_message": "{mention} 님, ROOM 09에 오신 것을 환영합니다.",
    "spam_limit_per_10s": 6,
    "forbidden_words": [],
    "leveling_enabled": True,
    "rpg_enabled": True,
    "daily_enabled": True,
    "ticket_enabled": True,
}

DEFAULT_BRANDING = {
    "bot_display_name": "",
    "status_text": "ROOM 09 가동 중",
    "presence_type": "playing",
    "icon_path": "assets/icon.png",
    "apply_on_startup": False,
}

DEFAULT_USERS = {}
DEFAULT_RPG = {
    "chapter": 1,
    "scene": "당신들은 ROOM 09에서 눈을 떴다.",
    "shop": {
        "medkit": {"name": "구급상자", "price": 50, "effect": "heal", "amount": 20, "rarity": "common"},
        "blade": {"name": "날붙이", "price": 80, "effect": "atk", "amount": 2, "rarity": "common"},
        "boots": {"name": "신발", "price": 80, "effect": "agi", "amount": 2, "rarity": "common"},
        "manual": {"name": "매뉴얼", "price": 80, "effect": "int", "amount": 2, "rarity": "common"},
        "shield": {"name": "보강 방패", "price": 120, "effect": "def", "amount": 2, "rarity": "rare"},
        "revive": {"name": "응급 제세동기", "price": 200, "effect": "revive", "amount": 40, "rarity": "epic"},
    }
}
DEFAULT_MONSTERS = {
    "slime": {"name": "슬라임", "hp": 40, "atk": 6, "def": 1, "coin_reward": 20, "xp_reward": 25, "drops": ["medkit"]},
    "hound": {"name": "실험체 사냥개", "hp": 70, "atk": 10, "def": 2, "coin_reward": 35, "xp_reward": 45, "drops": ["blade", "boots"]},
    "watcher": {"name": "감시자", "hp": 95, "atk": 12, "def": 4, "coin_reward": 50, "xp_reward": 60, "drops": ["manual", "shield"]},
}
DEFAULT_BOSSES = {
    "alpha": {
        "name": "ALPHA-09",
        "max_hp": 800,
        "hp": 800,
        "atk": 20,
        "def": 6,
        "alive": True,
        "participants": {},
        "image_prompt": "dark sci-fi biomechanical boss with glowing red core, cinematic game art",
        "pattern_index": 0,
        "patterns": [
            {"name": "충격파", "bonus_atk": 0, "text": "보스가 거대한 충격파를 방출했다."},
            {"name": "광선 난사", "bonus_atk": 4, "text": "보스의 광선이 공간을 찢는다."},
            {"name": "분노", "bonus_atk": 8, "text": "보스가 분노 상태에 돌입했다."},
        ],
    }
}
DEFAULT_TITLES = {}
DEFAULT_ACHIEVEMENTS = {}
DEFAULT_QUESTS = {
    "templates": [
        {"code": "chat_10", "name": "대화 10회", "type": "messages", "target": 10, "coin": 50, "xp": 40},
        {"code": "kill_1", "name": "몬스터 1회 처치", "type": "kills", "target": 1, "coin": 60, "xp": 50},
        {"code": "action_3", "name": "행동 3회", "type": "actions", "target": 3, "coin": 55, "xp": 45},
        {"code": "boss_hit_3", "name": "보스 3회 타격", "type": "boss_hits", "target": 3, "coin": 80, "xp": 70},
    ]
}
DEFAULT_TICKETS = {}
DEFAULT_STORY = {
    "chapters": {
        "1": {
            "title": "기상",
            "summary": "ROOM 09에서 눈을 뜬다.",
            "choices": [
                {"label": "문을 조사한다", "result": "문은 잠겨 있지만 오래된 흔적이 남아 있다."},
                {"label": "바닥을 살핀다", "result": "바닥에서 낡은 키카드를 발견했다."},
                {"label": "천장을 본다", "result": "천장에서 기계음이 울린다."},
            ],
        }
    }
}

FILES = {
    "settings.json": DEFAULT_SETTINGS,
    "branding.json": DEFAULT_BRANDING,
    "users.json": DEFAULT_USERS,
    "rpg.json": DEFAULT_RPG,
    "monsters.json": DEFAULT_MONSTERS,
    "bosses.json": DEFAULT_BOSSES,
    "titles.json": DEFAULT_TITLES,
    "achievements.json": DEFAULT_ACHIEVEMENTS,
    "quests.json": DEFAULT_QUESTS,
    "tickets.json": DEFAULT_TICKETS,
    "story.json": DEFAULT_STORY,
}

HELP_CATEGORIES = {
    "기본": [
        ("/핑", "봇 응답 확인"),
        ("/도움말", "카테고리별 전체 명령어 보기"),
        ("/명령어", "명령어 표를 한 번에 보기"),
        ("/내정보", "내 레벨/코인/능력치/인벤토리 확인"),
        ("/랭킹", "서버 레벨 랭킹 확인"),
        ("/일일보상", "하루 1회 코인 수령"),
        ("/일일퀘스트", "오늘 퀘스트 확인"),
        ("/칭호목록", "내가 보유한 칭호 보기"),
        ("/칭호장착", "보유 칭호 장착"),
        ("/도전과제", "달성한 도전과제 보기"),
    ],
    "RPG": [
        ("/참가", "RPG 시작 및 능력치 설정"),
        ("/현재상황", "현재 챕터와 스토리 확인"),
        ("/행동", "행동 판정"),
        ("/탐색", "랜덤 몬스터 조우"),
        ("/공격", "현재 몬스터 공격"),
        ("/상점", "상점 목록 보기"),
        ("/구매", "아이템 구매"),
        ("/사용", "아이템 사용"),
    ],
    "보스전": [
        ("/보스정보", "현재 보스 상태 확인"),
        ("/보스공격", "현재 보스 공격"),
        ("/보스랭킹", "보스 누적 피해 랭킹"),
        ("/보스리스폰", "보스 재소환(관리자)"),
    ],
    "패널": [
        ("/역할패널", "셀프 역할 패널"),
        ("/티켓패널", "티켓 열기 패널"),
        ("/rpg패널", "RPG 버튼 패널"),
        ("/보스패널", "보스 버튼 패널"),
    ],
    "이미지": [
        ("/맵이미지", "맵 이미지 프롬프트 생성"),
        ("/몬스터이미지", "몬스터 이미지 프롬프트 생성"),
        ("/보스이미지", "보스 이미지 프롬프트 생성"),
    ],
    "관리": [
        ("/채널설정", "시스템 채널 지정"),
        ("/환영문구", "환영 문구 설정"),
        ("/금지어추가", "금지어 추가"),
        ("/금지어제거", "금지어 제거"),
        ("/공지", "공지 임베드 전송"),
        ("/투표", "간단 투표 생성"),
        ("/경고", "유저 경고 부여"),
        ("/청소", "최근 메시지 삭제"),
    ],
    "관리자 확장": [
        ("/아이템추가", "상점 아이템 추가"),
        ("/아이템삭제", "상점 아이템 삭제"),
        ("/몬스터추가", "몬스터 추가"),
        ("/몬스터삭제", "몬스터 삭제"),
        ("/보스추가", "보스 추가"),
        ("/보스삭제", "보스 삭제"),
        ("/칭호추가", "칭호 추가"),
        ("/도전과제추가", "도전과제 추가"),
        ("/퀘스트추가", "일일 퀘스트 추가"),
        ("/장면변경", "현재 장면 변경"),
        ("/스토리선택지추가", "챕터 선택지 추가"),
    ],
    "브랜딩": [
        ("/브랜드확인", "현재 브랜딩 설정 확인"),
        ("/브랜드설정", "봇 이름/상태 저장"),
        ("/브랜드아이콘경로", "아이콘 파일 경로 저장"),
        ("/브랜드적용", "봇 이름/아이콘/상태 적용 시도"),
    ],
}

def ensure_data_files():
    DATA_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)
    for name, default in FILES.items():
        p = DATA_DIR / name
        if not p.exists():
            p.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")

def load_json(filename: str, default):
    p = DATA_DIR / filename
    if not p.exists():
        p.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        return json.loads(json.dumps(default))
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        p.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        return json.loads(json.dumps(default))

def save_json(filename: str, data):
    p = DATA_DIR / filename
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def today_str():
    return datetime.now(KST).strftime("%Y-%m-%d")

def make_bar(current: int, max_value: int, length: int = 12):
    max_value = max(1, max_value)
    current = max(0, min(current, max_value))
    filled = round((current / max_value) * length)
    return "█" * filled + "░" * (length - filled)

def ensure_user(uid: int, name: str = "Unknown") -> Dict[str, Any]:
    users = load_json("users.json", DEFAULT_USERS)
    suid = str(uid)
    if suid not in users:
        users[suid] = {
            "name": name,
            "xp": 0,
            "level": 1,
            "coins": 100,
            "warns": 0,
            "equipped_title": "",
            "owned_titles": [],
            "claimed_achievements": [],
            "inventory": {},
            "daily_last_claim": "",
            "daily_quest_date": "",
            "daily_quests": [],
            "stats": {"messages": 0, "kills": 0, "actions": 0, "boss_hits": 0, "boss_damage": 0},
            "rpg": {"joined": False, "hp": 100, "max_hp": 100, "str": 3, "agi": 3, "int": 3, "def": 0, "current_monster": "", "current_monster_hp": 0}
        }
    users[suid]["name"] = name
    save_json("users.json", users)
    return users[suid]

def get_users():
    return load_json("users.json", DEFAULT_USERS)

def apply_level_up(user: dict):
    changed = False
    while user["xp"] >= user["level"] * 100:
        user["xp"] -= user["level"] * 100
        user["level"] += 1
        user["coins"] += 30
        user["rpg"]["max_hp"] += 5
        user["rpg"]["hp"] = min(user["rpg"]["max_hp"], user["rpg"]["hp"] + 5)
        changed = True
    return changed

def assign_daily_quests(user: dict):
    quests = load_json("quests.json", DEFAULT_QUESTS)
    if user.get("daily_quest_date") == today_str():
        return
    templates = quests.get("templates", [])
    chosen = random.sample(templates, k=min(3, len(templates))) if templates else []
    user["daily_quest_date"] = today_str()
    user["daily_quests"] = []
    for q in chosen:
        user["daily_quests"].append({
            "code": q["code"], "name": q["name"], "type": q["type"], "target": q["target"],
            "progress": 0, "coin": q["coin"], "xp": q["xp"], "claimed": False
        })

def progress_user_stats(user: dict, stat_key: str, amount: int = 1):
    user["stats"][stat_key] = user["stats"].get(stat_key, 0) + amount
    for q in user.get("daily_quests", []):
        if q["type"] == stat_key and not q["claimed"] and q["progress"] < q["target"]:
            q["progress"] = min(q["target"], q["progress"] + amount)

def claim_daily_rewards(user: dict):
    claimed = []
    for q in user.get("daily_quests", []):
        if q["progress"] >= q["target"] and not q["claimed"]:
            q["claimed"] = True
            user["coins"] += q["coin"]
            user["xp"] += q["xp"]
            claimed.append(q["name"])
    if claimed:
        apply_level_up(user)
    return claimed

def check_unlocks(user: dict):
    titles = load_json("titles.json", DEFAULT_TITLES)
    achievements = load_json("achievements.json", DEFAULT_ACHIEVEMENTS)
    unlocked_titles = []
    unlocked_achievements = []
    for code, t in titles.items():
        if code in user["owned_titles"]:
            continue
        if user["stats"].get(t["condition_type"], 0) >= t["target"]:
            user["owned_titles"].append(code)
            unlocked_titles.append(t["name"])
    for code, a in achievements.items():
        if code in user["claimed_achievements"]:
            continue
        if user["stats"].get(a["condition_type"], 0) >= a["target"]:
            user["claimed_achievements"].append(code)
            user["coins"] += a.get("coin_reward", 0)
            user["xp"] += a.get("xp_reward", 0)
            unlocked_achievements.append(a["name"])
    if unlocked_achievements:
        apply_level_up(user)
    return unlocked_titles, unlocked_achievements

def item_apply(user: dict, item_code: str):
    rpg = load_json("rpg.json", DEFAULT_RPG)
    item = rpg["shop"].get(item_code)
    if not item:
        return "존재하지 않는 아이템입니다."
    eff = item["effect"]
    amt = item["amount"]
    if eff == "heal":
        if user["rpg"]["hp"] <= 0:
            return "전투불능 상태에서는 revive 계열을 사용하세요."
        old = user["rpg"]["hp"]
        user["rpg"]["hp"] = min(user["rpg"]["max_hp"], user["rpg"]["hp"] + amt)
        return f"HP {old} → {user['rpg']['hp']} 회복"
    if eff == "atk":
        user["rpg"]["str"] += amt
        return f"힘이 {amt} 증가했습니다."
    if eff == "agi":
        user["rpg"]["agi"] += amt
        return f"민첩이 {amt} 증가했습니다."
    if eff == "int":
        user["rpg"]["int"] += amt
        return f"지능이 {amt} 증가했습니다."
    if eff == "def":
        user["rpg"]["def"] += amt
        return f"방어력이 {amt} 증가했습니다."
    if eff == "revive":
        if user["rpg"]["hp"] > 0:
            return "전투불능 상태가 아니라 사용할 수 없습니다."
        user["rpg"]["hp"] = min(user["rpg"]["max_hp"], amt)
        return f"HP {user['rpg']['hp']}로 부활했습니다."
    return "아무 일도 일어나지 않았습니다."

def is_adminish(member: discord.Member, settings: dict) -> bool:
    roles = {r.name for r in member.roles}
    return member.guild_permissions.administrator or settings.get("gm_role_name", "GM") in roles or settings.get("admin_role_name", "관리자") in roles

def make_presence(branding: dict):
    activity_name = branding.get("status_text", "ROOM 09 가동 중")
    kind = branding.get("presence_type", "playing")
    if kind == "watching":
        return discord.Activity(type=discord.ActivityType.watching, name=activity_name)
    if kind == "listening":
        return discord.Activity(type=discord.ActivityType.listening, name=activity_name)
    return discord.Game(name=activity_name)

async def apply_branding_if_possible(bot):
    branding = load_json("branding.json", DEFAULT_BRANDING)
    await bot.change_presence(activity=make_presence(branding))
    if not branding.get("apply_on_startup", False):
        return
    name = branding.get("bot_display_name", "").strip()
    icon_path = branding.get("icon_path", "assets/icon.png")
    kwargs = {}
    if name:
        kwargs["username"] = name
    p = Path(icon_path)
    if p.exists():
        kwargs["avatar"] = p.read_bytes()
    if kwargs:
        await bot.user.edit(**kwargs)

def help_overview_text():
    lines = []
    for category, items in HELP_CATEGORIES.items():
        lines.append(f"**{category}** ({len(items)}개)")
        lines.append(" / ".join(cmd for cmd, _ in items))
        lines.append("")
    return "\n".join(lines).strip()
