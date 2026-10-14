# NEXUS TOOLBOX

Telegram bot dengan downloader TikTok/Instagram, generator, developer utilities, dan system utilities.

## Instalasi

```bash
python -m pip install -r requirements.txt
```

Set token dari `@BotFather` sebagai environment variable. Untuk fitur `/ttuser`, tambahkan juga `EULERSTREAM_API_KEY` dari dashboard Euler Stream: https://www.eulerstream.com/register. Fitur profil menggunakan API Euler Stream dan memerlukan API key.

Environment variables:

Linux/macOS:

```bash
export TELEGRAM_BOT_TOKEN="TOKEN_BOT_KAMU"
python bot.py
```

Windows PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN="TOKEN_BOT_KAMU"
python bot.py
```

## Downloader

- `/tt URL` untuk TikTok
- `/ttuser username` untuk mencari data profil TikTok publik (nama, username, user ID, region registrasi, followers/following, likes, video, bio jika tersedia). Memerlukan `EULERSTREAM_API_KEY`.
- `/ig URL` untuk Instagram
- Bisa juga kirim URL langsung ke chat.
- Caption keluaran menyertakan nama akun/uploader, judul, dan deskripsi/caption yang diekspos oleh extractor. Jika teks melebihi batas caption Telegram, sisanya dikirim sebagai pesan lanjutan.
- Batas ukuran file 45 MiB.

Metadata yang tersedia bergantung pada halaman dan versi `yt-dlp`; beberapa post mungkin tidak mengekspos nama akun atau caption lengkap. Konten privat/login-gated tidak dijamin bisa diunduh.

## Deploy ke Railway

1. Upload seluruh isi project ke repository GitHub.
2. Di Railway, pilih **New Project → Deploy from GitHub repo**, lalu pilih repository ini.
3. Buka **Variables** pada service dan tambahkan `TELEGRAM_BOT_TOKEN` dengan token dari `@BotFather`.
4. Pastikan start command adalah `python bot.py` (sudah diatur di `railway.json`), lalu deploy/redeploy.
5. Buka **Deployments → View Logs**. Jika log menampilkan `toolbox bot berjalan`, proses bot sudah mulai berjalan.

Bot ini menggunakan Telegram long polling, jadi tidak memerlukan domain publik atau webhook. Jalankan hanya satu replica/service untuk token bot yang sama agar tidak terjadi konflik polling.
