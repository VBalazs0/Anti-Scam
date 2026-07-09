# AntiScam — Discord Scam Image Detection Bot

Automatically detects and removes scam images in Discord servers using perceptual image hashing.

## Features

- **Multi-algorithm image matching** — phash, dhash, ahash, whash, colorhash (including blur/mirror variants)
- **Configurable punishments** — Delete, Mute+Delete, Kick+Delete, Ban+Delete
- **Per-server setup** — each guild configures its own log channel and punishment via `/setup`
- **Evidence logging** — deleted scam images are saved locally and proof is posted to the log channel
- **Blur-tolerant** — Gaussian blur + mirror transforms help catch variants of known scam images

## Requirements

- Python 3.10+
- A [Discord bot application](https://discord.com/developers/applications) with:
  - `bot` + `applications.commands` scopes enabled
  - Privileged Gateway Intents: **Message Content Intent** enabled

## Try the hosted bot

[Invite AntiScam to your server](https://discord.com/api/oauth2/authorize?client_id=1524791325847851119&permissions=1099511753734&scope=bot+applications.commands) — no hosting required, just authorize and run `/setup`.

## Installation

### Windows

```
install.bat
```

### Linux / macOS

```bash
chmod +x install.sh
./install.sh
```

### Manual

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Configuration

Edit `.env` and set your bot token:

```
TOKEN=your_discord_bot_token_here
```

Other optional settings (defaults shown):

| Variable | Default | Description |
|---|---|---|
| `SCAM_IMAGES_DIR` | `img` | Folder with reference scam images |
| `DELETED_IMAGES_DIR` | `deleted` | Folder to store deleted scam evidence |
| `SIMILARITY_THRESHOLD` | `16` | Lower = stricter matching (0-64) |
| `GUILD_CONFIG_FILE` | `guild_config.json` | Per-guild settings file |

## Adding Scam Images

Place reference scam images (`.jpg`, `.png`, `.webp`, etc.) in the `img/` folder. The bot computes multiple perceptual hashes for each image at startup and compares incoming images against them.

## Usage

1. Invite the bot to your server with `bot` + `applications.commands` scopes.
2. Run `/setup` to configure the log channel and punishment action.
3. The bot will automatically scan image attachments and take action when a match is found.

## Commands

| Command | Description |
|---|---|
| `/setup` | Configure log channel and punishment for the server |
