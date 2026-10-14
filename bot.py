import ast
import asyncio
import base64
import hashlib
import html
import ipaddress
import json
import os
import random
import re
import secrets
import socket
import string
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import time
import uuid
from datetime import date
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

import qrcode
import yt_dlp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
EULERSTREAM_API_KEY = os.getenv("EULERSTREAM_API_KEY", "").strip()
MAX_DOWNLOAD_BYTES = 45 * 1024 * 1024
ALLOWED_HOSTS = {"tiktok.com", "www.tiktok.com", "vm.tiktok.com", "vt.tiktok.com", "instagram.com", "www.instagram.com", "instagr.am", "www.instagr.am"}

BRAND = "NEXUS TOOLBOX"

MENU = [
    [InlineKeyboardButton("DOWNLOAD CENTER", callback_data="help_tt"), InlineKeyboardButton("GENERATORS", callback_data="help_gen")],
    [InlineKeyboardButton("DEVELOPER LAB", callback_data="help_dev"), InlineKeyboardButton("SYSTEM UTILITIES", callback_data="help_util")],
    [InlineKeyboardButton("ALL COMMANDS", callback_data="help_all"), InlineKeyboardButton("BOT STATUS", callback_data="help_status")],
]
BACK_MENU = [[InlineKeyboardButton("‹ MAIN MENU", callback_data="help_home"), InlineKeyboardButton("ALL COMMANDS", callback_data="help_all")]]

HOME_TEXT = """<b>ＮＥＸＵＳ  /  TOOLBOX</b>
<code>━━━━━━━━━━━━━━━━━━━━</code>
<b>YOUR ALL-IN-ONE TELEGRAM WORKSPACE</b>

Downloader media, generator, developer utilities, dan network tools dalam satu panel.

<code>MODULES     04</code>
<code>COMMANDS    30+</code>
<code>STATUS      ● ONLINE</code>
<code>━━━━━━━━━━━━━━━━━━━━</code>
<i>Pilih modul di bawah untuk membuka panel fitur.</i>"""

PAGES = {
    "help_tt": ("DOWNLOAD CENTER", """<b>01 / MEDIA DOWNLOADER</b>
<code>━━━━━━━━━━━━━━━━━━━━</code>

<b>TIKTOK</b>
<code>/tt URL</code> — unduh video TikTok
<code>/ttuser username</code> — cari profil publik TikTok

<b>INSTAGRAM</b>
<code>/ig URL</code> — unduh media publik

Kirim tautan TikTok atau Instagram langsung ke chat untuk memprosesnya otomatis.

<code>LIMIT   45 MB</code>
<code>MODE    PUBLIC MEDIA</code>"""),
    "help_gen": ("GENERATOR STUDIO", """<b>02 / GENERATOR STUDIO</b>
<code>━━━━━━━━━━━━━━━━━━━━</code>

<code>/password [panjang]</code> — password acak
<code>/uuid</code> — UUID v4
<code>/qr teks</code> — QR code PNG
<code>/color</code> — warna HEX
<code>/lorem [jumlah]</code> — teks dummy
<code>/pick a, b, c</code> — pilih acak
<code>/roll [sisi]</code> — dadu digital
<code>/coin</code> — lempar koin
<code>/quote</code> — kutipan acak"""),
    "help_dev": ("DEVELOPER LAB", """<b>03 / DEVELOPER LAB</b>
<code>━━━━━━━━━━━━━━━━━━━━</code>

<code>/hash teks</code> — SHA-256
<code>/base64 teks</code> / <code>/unbase64</code>
<code>/hex teks</code> / <code>/unhex</code>
<code>/rot13 teks</code> — ROT13
<code>/json {...}</code> — format JSON
<code>/slug teks</code> — URL slug
<code>/urlencode teks</code> / <code>/urldecode</code>
<code>/wordcount teks</code> — statistik teks
<code>/reverse teks</code> — balik teks
<code>/upper teks</code> / <code>/lower teks</code>
<code>/calc ekspresi</code> — kalkulator"""),
    "help_util": ("SYSTEM UTILITIES", """<b>04 / SYSTEM UTILITIES</b>
<code>━━━━━━━━━━━━━━━━━━━━</code>

<code>/dns domain.com</code> — DNS lookup
<code>/ipinfo 8.8.8.8</code> — klasifikasi IP
<code>/timestamp [unix]</code> — konversi waktu
<code>/age YYYY-MM-DD</code> — hitung umur

<code>/start</code> — buka dashboard
<code>/help</code> — daftar command"""),
    "help_all": ("COMMAND INDEX", """<b>COMMAND INDEX / 30+</b>
<code>━━━━━━━━━━━━━━━━━━━━</code>

<b>MEDIA & TIKTOK PROFILE</b>
<code>/tt</code> <code>/ig</code> <code>/ttuser</code>
<b>GENERATOR</b>
<code>/password</code> <code>/uuid</code> <code>/qr</code> <code>/color</code> <code>/lorem</code> <code>/pick</code> <code>/roll</code> <code>/coin</code> <code>/quote</code>
<b>DEVELOPER</b>
<code>/hash</code> <code>/base64</code> <code>/unbase64</code> <code>/hex</code> <code>/unhex</code> <code>/rot13</code> <code>/json</code> <code>/slug</code> <code>/urlencode</code> <code>/urldecode</code> <code>/wordcount</code> <code>/reverse</code> <code>/upper</code> <code>/lower</code> <code>/calc</code>
<b>UTILITIES</b>
<code>/dns</code> <code>/ipinfo</code> <code>/timestamp</code> <code>/age</code>"""),
    "help_status": ("SYSTEM STATUS", """<b>SYSTEM STATUS</b>
<code>━━━━━━━━━━━━━━━━━━━━</code>

<code>CORE       ONLINE</code>
<code>INTERFACE  INLINE MENU</code>
<code>DOWNLOAD   YT-DLP</code>
<code>GENERATORS READY</code>
<code>UTILITIES  READY</code>

<i>Status ini menunjukkan proses bot aktif, bukan hasil pemeriksaan semua layanan eksternal.</i>"""),
}
HELP = HOME_TEXT

QUOTES = [
    "Simplicity is the ultimate sophistication.",
    "First, solve the problem; then, write the code.",
    "Programs must be written for people to read.",
    "Make it work, make it right, make it fast.",
    "The best way to predict the future is to invent it.",
]
LOREM = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua".split()


def arg_text(update: Update) -> str:
    return update.message.text.partition(" ")[2].strip() if update.message and update.message.text else ""

async def reply(update: Update, text: str, **kwargs):
    if update.message:
        await update.message.reply_text(text, **kwargs)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update, HOME_TEXT, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(MENU))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply(update, PAGES["help_all"][1], parse_mode="HTML", reply_markup=InlineKeyboardMarkup(BACK_MENU))

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data
    if key == "help_home":
        text, keyboard, mode = HOME_TEXT, MENU, "HTML"
    else:
        _, text = PAGES.get(key, PAGES["help_all"])
        keyboard, mode = BACK_MENU, "HTML"
    try:
        await q.edit_message_text(text, parse_mode=mode, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    except Exception as exc:
        if "Message is not modified" not in str(exc):
            await q.message.reply_text(text, parse_mode=mode, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

async def download_media(update: Update, url: str, platform: str):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or host not in ALLOWED_HOSTS:
        await reply(update, "URL tidak valid atau domain tidak didukung.")
        return
    if platform == "tt" and "tiktok.com" not in host:
        await reply(update, "gunakan URL TikTok untuk perintah /tt.")
        return
    if platform == "ig" and not ("instagram.com" in host or "instagr.am" in host):
        await reply(update, "gunakan URL Instagram untuk perintah /ig.")
        return
    await update.effective_chat.send_action(ChatAction.UPLOAD_VIDEO)
    with tempfile.TemporaryDirectory(prefix="tgtool_") as tmp:
        opts = {
            "outtmpl": str(Path(tmp) / "media.%(ext)s"),
            "format": "best[filesize<45M][ext=mp4]/best[ext=mp4]/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 20,
            "max_filesize": MAX_DOWNLOAD_BYTES,
            "retries": 1,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                path = Path(ydl.prepare_filename(info))
                if not path.exists():
                    candidates = list(Path(tmp).glob("media.*"))
                    if not candidates:
                        raise RuntimeError("file hasil unduhan tidak ditemukan")
                    path = candidates[0]
                if path.stat().st_size > MAX_DOWNLOAD_BYTES:
                    await reply(update, "file melebihi batas 45 MB untuk bot ini.")
                    return
                username = (
                    info.get("uploader_id")
                    or info.get("channel_id")
                    or info.get("creator")
                    or info.get("uploader")
                    or info.get("channel")
                    or ""
                )
                username = str(username).strip()
                if username and not username.startswith("@") and re.fullmatch(r"[A-Za-z0-9._]+", username):
                    username = "@" + username

                title = str(info.get("title") or "Media")
                source_caption = str(info.get("description") or info.get("alt_title") or "").strip()
                lines = [f"{platform.upper()} DOWNLOAD"]
                if username:
                    lines.append(f"Akun: {username}")
                if title and title.lower() != source_caption.lower():
                    lines.append(f"Judul: {title}")
                if source_caption:
                    lines.extend(["", source_caption])
                full_caption = "\n".join(lines).strip()
                media_caption = full_caption[:1024]
                with path.open("rb") as media:
                    if path.suffix.lower() in {".mp4", ".mov", ".m4v", ".webm"}:
                        await update.message.reply_video(video=media, caption=media_caption)
                    else:
                        await update.message.reply_document(document=media, caption=media_caption)
                if len(full_caption) > 1024:
                    remainder = full_caption[1024:]
                    for offset in range(0, len(remainder), 4000):
                        await update.message.reply_text(remainder[offset:offset + 4000])
        except Exception as exc:
            await reply(update, f"gagal mengunduh media: {str(exc)[:250]}")

async def tt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = " ".join(context.args).strip()
    if not url: return await reply(update, "format: /tt https://www.tiktok.com/...")
    await download_media(update, url, "tt")

async def ttuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Look up a public TikTok profile through Euler Stream's API."""
    username = context.args[0].strip().lstrip("@") if context.args else ""
    if not username or not re.fullmatch(r"[A-Za-z0-9._]{1,24}", username):
        return await reply(update, "format: /ttuser username\ncontoh: /ttuser tiktok")
    if not EULERSTREAM_API_KEY:
        return await reply(
            update,
            "fitur TikTok User Finder perlu API key Euler Stream.\n"
            "1. daftar/login: https://www.eulerstream.com/register\n"
            "2. ambil API key dari dashboard\n"
            "3. tambahkan variable Railway: EULERSTREAM_API_KEY\n\n"
            "setelah itu jalankan /ttuser username lagi."
        )

    api_url = "https://api.eulerstream.com/tiktok/users/" + urllib.parse.quote(username, safe="") + "/detailed"
    req = urllib.request.Request(
        api_url,
        headers={"x-api-key": EULERSTREAM_API_KEY, "Accept": "application/json", "User-Agent": "NEXUS-TOOLBOX/1.0"},
        method="GET",
    )
    try:
        def fetch_profile():
            with urllib.request.urlopen(req, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        payload = await asyncio.to_thread(fetch_profile)
        user = payload.get("user") or (payload.get("data") or {}).get("user") or payload.get("data") or {}
        if not isinstance(user, dict) or not user:
            message = str(payload.get("message") or "profil tidak ditemukan atau tidak tersedia.")
            return await reply(update, f"pencarian gagal: {html.escape(message[:250])}")

        def field(*names):
            for name in names:
                value = user.get(name)
                if value not in (None, ""):
                    return value
            return None

        handle = str(field("unique_id", "uniqueId", "username") or username).lstrip("@")
        nickname = str(field("nickname", "display_name", "displayName") or handle)
        user_id = field("id", "uid", "user_id", "userId")
        region = field("region", "country", "country_code", "countryCode")
        followers = field("follower_count", "followerCount", "followers")
        following = field("following_count", "followingCount", "following")
        likes = field("heart_count", "heartCount", "total_favorited", "likes")
        videos = field("video_count", "videoCount")
        bio = field("signature", "bio", "description")
        verified = field("verified", "is_verified", "isVerified")
        avatar = field("avatar_larger", "avatarLarger", "avatar_url", "avatarUrl", "avatar_thumb", "avatarThumb")

        def pretty(value):
            if isinstance(value, (int, float)):
                return f"{value:,}".replace(",", ".")
            return str(value) if value is not None else "—"

        lines = ["<b>TIKTOK USER FINDER</b>", "━━━━━━━━━━━━━━━━━━", f"Nama: {html.escape(nickname)}", f"Username: @{html.escape(handle)}"]
        if user_id is not None: lines.append(f"User ID: <code>{html.escape(str(user_id))}</code>")
        if region is not None: lines.append(f"Region akun: {html.escape(str(region))}")
        lines.extend([f"Followers: {pretty(followers)}", f"Following: {pretty(following)}"])
        if likes is not None: lines.append(f"Total likes: {pretty(likes)}")
        if videos is not None: lines.append(f"Video: {pretty(videos)}")
        if verified is not None: lines.append(f"Verified: {'ya' if verified else 'tidak'}")
        if bio: lines.extend(["", f"Bio: {html.escape(str(bio)[:700])}"])
        lines.extend(["", "<i>Hanya data profil publik. Region adalah wilayah registrasi akun, bukan lokasi real-time.</i>"])
        result = "\n".join(lines)
        if isinstance(avatar, str) and avatar.startswith("https://"):
            try:
                await update.message.reply_photo(photo=avatar, caption=result, parse_mode="HTML")
                return
            except Exception:
                pass
        await reply(update, result, parse_mode="HTML", disable_web_page_preview=True)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            message = "API key Euler Stream tidak valid atau akses API tidak tersedia. Periksa EULERSTREAM_API_KEY dan kuota akun."
        elif exc.code == 404:
            message = "username tidak ditemukan atau profil tidak dapat diakses."
        elif exc.code == 429:
            message = "batas permintaan API tercapai. coba lagi nanti."
        else:
            message = f"API Euler Stream mengembalikan HTTP {exc.code}."
        await reply(update, message)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        await reply(update, f"gagal menghubungi Euler Stream: {str(exc)[:180]}")
    except Exception as exc:
        await reply(update, f"pencarian profil gagal: {str(exc)[:180]}")

async def ig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = " ".join(context.args).strip()
    if not url: return await reply(update, "format: /ig https://www.instagram.com/p/...")
    await download_media(update, url, "ig")

async def auto_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = re.search(r"https?://[^\s]+", text)
    if not match: return
    url = match.group(0).rstrip(".,!?)]}")
    host = (urlparse(url).hostname or "").lower()
    if host in ALLOWED_HOSTS:
        platform = "tt" if "tiktok.com" in host else "ig"
        await download_media(update, url, platform)

async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: length = int(context.args[0]) if context.args else 20
    except ValueError: return await reply(update, "format: /password [panjang 8-128]")
    if not 8 <= length <= 128: return await reply(update, "panjang harus 8-128 karakter.")
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    await reply(update, "`" + "".join(secrets.choice(alphabet) for _ in range(length)) + "`", parse_mode="Markdown")

async def qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = arg_text(update)
    if not value: return await reply(update, "format: /qr teks_atau_url")
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        qrcode.make(value).save(f.name)
        with open(f.name, "rb") as img: await update.message.reply_photo(img)

async def uuid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await reply(update, str(uuid.uuid4()))
async def color(update: Update, context: ContextTypes.DEFAULT_TYPE): await reply(update, "#" + secrets.token_hex(3).upper())
async def lorem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: n = int(context.args[0]) if context.args else 30
    except ValueError: n = 30
    n = max(1, min(n, 300))
    await reply(update, " ".join(random.choice(LOREM) for _ in range(n)))
async def pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = [x.strip() for x in arg_text(update).split(",") if x.strip()]
    if len(items) < 2: return await reply(update, "format: /pick merah, biru, hijau")
    await reply(update, "pilihan: " + random.choice(items))
async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: sides = int(context.args[0]) if context.args else 6
    except ValueError: sides = 6
    if not 2 <= sides <= 1_000_000: return await reply(update, "jumlah sisi harus 2-1000000.")
    await reply(update, f"hasil d{sides}: {secrets.randbelow(sides) + 1}")
async def coin(update: Update, context: ContextTypes.DEFAULT_TYPE): await reply(update, secrets.choice(["angka", "gambar"]))
async def quote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await reply(update, random.choice(QUOTES))
async def hash_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = arg_text(update)
    if not s: return await reply(update, "format: /hash teks")
    await reply(update, hashlib.sha256(s.encode()).hexdigest())
async def base64_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = arg_text(update)
    if not s: return await reply(update, "format: /base64 teks")
    await reply(update, base64.b64encode(s.encode()).decode())
async def unbase64_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: out = base64.b64decode(arg_text(update), validate=True).decode("utf-8")
    except Exception: return await reply(update, "base64 tidak valid atau bukan UTF-8.")
    await reply(update, out[:4000])
async def hex_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = arg_text(update)
    if not s: return await reply(update, "format: /hex teks")
    await reply(update, s.encode().hex())
async def unhex_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: out = bytes.fromhex(arg_text(update)).decode("utf-8")
    except Exception: return await reply(update, "hex tidak valid atau bukan UTF-8.")
    await reply(update, out[:4000])
async def rot13(update: Update, context: ContextTypes.DEFAULT_TYPE): await reply(update, arg_text(update).encode("rot13").decode() if arg_text(update) else "format: /rot13 teks")
async def json_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: out = json.dumps(json.loads(arg_text(update)), ensure_ascii=False, indent=2)
    except Exception as e: return await reply(update, f"JSON tidak valid: {str(e)[:150]}")
    await reply(update, out[:4000])
async def slug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = arg_text(update).lower().strip()
    await reply(update, re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "kosong")
async def urlencode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await reply(update, quote(arg_text(update), safe="") if arg_text(update) else "format: /urlencode teks")
async def urldecode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE): await reply(update, unquote(arg_text(update)) if arg_text(update) else "format: /urldecode teks")
async def wordcount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = arg_text(update)
    if not s: return await reply(update, "format: /wordcount teks")
    await reply(update, f"karakter: {len(s)}\nkarakter tanpa spasi: {len(re.sub(r'\\s', '', s))}\nkata: {len(s.split())}\nbaris: {len(s.splitlines())}")
async def reverse(update: Update, context: ContextTypes.DEFAULT_TYPE): await reply(update, arg_text(update)[::-1] if arg_text(update) else "format: /reverse teks")
async def upper(update: Update, context: ContextTypes.DEFAULT_TYPE): await reply(update, arg_text(update).upper()[:4000] if arg_text(update) else "format: /upper teks")
async def lower(update: Update, context: ContextTypes.DEFAULT_TYPE): await reply(update, arg_text(update).lower()[:4000] if arg_text(update) else "format: /lower teks")

ALLOWED_AST = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.USub, ast.UAdd, ast.Load)
def safe_calc(expr):
    tree = ast.parse(expr, mode="eval")
    if sum(1 for _ in ast.walk(tree)) > 50: raise ValueError("ekspresi terlalu kompleks")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST): raise ValueError("operator tidak didukung")
        if isinstance(node, ast.Constant) and (type(node.value) not in (int, float) or abs(node.value) > 10**100): raise ValueError("angka tidak valid")
        if isinstance(node, ast.Pow) and isinstance(node, ast.Constant) and abs(node.value) > 100: raise ValueError("pangkat terlalu besar")
    result = eval(compile(tree, "<calc>", "eval"), {"__builtins__": {}}, {})
    if isinstance(result, complex) or abs(result) > 10**100: raise ValueError("hasil di luar batas")
    return result
async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        expr = arg_text(update)
        if not expr or len(expr) > 200: raise ValueError("format: /calc (12 + 3) * 4")
        await reply(update, str(safe_calc(expr)))
    except Exception as e: await reply(update, f"kalkulasi gagal: {str(e)[:150]}")
async def dns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    host = context.args[0].strip() if context.args else ""
    if not host or len(host) > 253 or re.fullmatch(r"[A-Za-z0-9.-]+", host) is None: return await reply(update, "format: /dns example.com")
    try:
        records = sorted({item[4][0] for item in socket.getaddrinfo(host, None)})
        await reply(update, "\n".join(records[:30]))
    except Exception as e: await reply(update, f"lookup gagal: {str(e)[:150]}")
async def ipinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = context.args[0] if context.args else ""
    try:
        ip = ipaddress.ip_address(value)
        await reply(update, f"IP: {ip}\nversi: IPv{ip.version}\nglobal: {ip.is_global}\nprivate: {ip.is_private}\nloopback: {ip.is_loopback}\nmulticast: {ip.is_multicast}")
    except ValueError: await reply(update, "format: /ipinfo 8.8.8.8")
async def timestamp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = int(context.args[0]) if context.args else int(time.time())
        await reply(update, f"unix: {value}\nUTC: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(value))}")
    except (ValueError, OverflowError, OSError): await reply(update, "format: /timestamp [unix]")
async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        born = date.fromisoformat(context.args[0])
        today = date.today()
        if born > today: raise ValueError("tanggal di masa depan")
        years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        await reply(update, f"umur: {years} tahun")
    except Exception: await reply(update, "format: /age YYYY-MM-DD")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"handler error: {context.error!r}")


def main():
    if not TOKEN:
        raise SystemExit("set environment variable TELEGRAM_BOT_TOKEN terlebih dahulu")
    app = Application.builder().token(TOKEN).build()
    commands = {
        "start": start, "help": help_cmd, "tt": tt, "ig": ig, "ttuser": ttuser,
        "password": password, "qr": qr, "uuid": uuid_cmd, "color": color,
        "lorem": lorem, "pick": pick, "roll": roll, "coin": coin, "quote": quote_cmd,
        "hash": hash_cmd, "base64": base64_cmd, "unbase64": unbase64_cmd,
        "hex": hex_cmd, "unhex": unhex_cmd, "rot13": rot13, "json": json_cmd,
        "slug": slug, "urlencode": urlencode_cmd, "urldecode": urldecode_cmd,
        "wordcount": wordcount, "reverse": reverse, "upper": upper, "lower": lower,
        "calc": calc, "dns": dns, "ipinfo": ipinfo, "timestamp": timestamp, "age": age,
    }
    for name, handler in commands.items(): app.add_handler(CommandHandler(name, handler))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^help_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_download))
    app.add_error_handler(error_handler)
    print("toolbox bot berjalan")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
