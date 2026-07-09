import discord
from discord import app_commands
import io
from datetime import datetime, timedelta, timezone
from PIL import Image
import imagehash

import os
from config import TOKEN, SCAM_IMAGES_DIR, DELETED_IMAGES_DIR, SIMILARITY_THRESHOLD, GUILD_CONFIG_FILE
from scam_detector import ScamDetector
from guild_config import GuildConfig

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.guilds = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
detector = ScamDetector(SCAM_IMAGES_DIR, SIMILARITY_THRESHOLD)
gconf = GuildConfig(GUILD_CONFIG_FILE)
stored_hashes: set = set()

PUNISHMENT_CHOICES = [
    app_commands.Choice(name="Delete", value="delete"),
    app_commands.Choice(name="Mute + Delete", value="mute_delete"),
    app_commands.Choice(name="Kick + Delete", value="kick_delete"),
    app_commands.Choice(name="Ban + Delete", value="ban_delete"),
]


@bot.event
async def on_ready():
    os.makedirs(DELETED_IMAGES_DIR, exist_ok=True)
    for fname in os.listdir(DELETED_IMAGES_DIR):
        ext = os.path.splitext(fname)[1].lower()
        if ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}:
            path = os.path.join(DELETED_IMAGES_DIR, fname)
            try:
                with Image.open(path) as img:
                    stored_hashes.add(imagehash.phash(img))
            except Exception:
                pass
    print(f"Loaded {len(stored_hashes)} already-stored deleted images")
    await tree.sync()
    print(f"Logged in as {bot.user} ({len(detector.refs)} scam signatures)")


@bot.event
async def on_guild_join(guild: discord.Guild):
    target = None
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
            target = entry.user
    except Exception:
        pass
    if target is None or target.bot:
        target = guild.owner

    if target:
        try:
            await target.send(
                f"Hey! Thanks for adding **AntiScam** to **{guild.name}**.\n\n"
                f"To start using the bot, run `/setup` in your server to configure:\n"
                f"- **Log channel** – where scam alerts get posted\n"
                f"- **Punishment** – Delete / Mute+Delete / Kick+Delete / Ban+Delete"
            )
        except Exception:
            pass


@tree.command(name="setup", description="Configure AntiScam for this server")
@app_commands.describe(
    log_channel="Channel where scam-detection proofs are sent",
    punishment="Action to take when a scam image is found",
)
@app_commands.choices(punishment=PUNISHMENT_CHOICES)
async def setup(interaction: discord.Interaction, log_channel: discord.TextChannel, punishment: app_commands.Choice[str]):
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    gconf.set(guild_id, "log_channel_id", log_channel.id)
    gconf.set(guild_id, "punishment", punishment.value)

    await interaction.response.send_message(
        f"AntiScam configured!\n"
        f"**Log channel:** {log_channel.mention}\n"
        f"**Punishment:** {punishment.name}",
        ephemeral=False,
    )


PUNISHMENT_DM = {
    "delete": "Your message containing a scam image was deleted in **{guild}**. Please do not share scam content.",
    "mute_delete": "You have been muted for 1 hour in **{guild}** and your scam message was deleted. Please do not share scam content.",
    "kick_delete": "You have been kicked from **{guild}** for sharing scam images. Please do not share scam content.",
    "ban_delete": "You have been banned from **{guild}** for sharing scam images. Please do not share scam content.",
}


async def apply_punishment(member: discord.Member | None, guild_name: str, punishment: str):
    if member:
        try:
            await member.send(PUNISHMENT_DM[punishment].format(guild=guild_name))
        except Exception:
            pass

    match punishment:
        case "mute_delete":
            if member:
                try:
                    await member.timeout(timedelta(hours=1), reason="AntiScam: scam image")
                except Exception:
                    pass
        case "kick_delete":
            if member:
                try:
                    await member.kick(reason="AntiScam: scam image")
                except Exception:
                    pass
        case "ban_delete":
            if member:
                try:
                    await member.ban(reason="AntiScam: scam image", delete_message_days=0)
                except Exception:
                    pass


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return
    if not message.attachments:
        return

    cfg = gconf.get(message.guild.id)
    if not gconf.is_setup(message.guild.id):
        return

    image_attachments = [a for a in message.attachments if a.content_type and a.content_type.startswith("image/")]
    if not image_attachments:
        return

    proof_ch = bot.get_channel(cfg["log_channel_id"])
    if not proof_ch:
        print(f"WARNING: log channel {cfg['log_channel_id']} not found for guild {message.guild.id}")
        return

    scam_info = []
    for attachment in image_attachments:
        try:
            data = await attachment.read()
            with Image.open(io.BytesIO(data)) as img:
                is_scam, matched_name = detector.is_scam(img)
            if is_scam:
                scam_info.append({
                    "filename": attachment.filename,
                    "matched": matched_name,
                    "data": data,
                    "url": attachment.url,
                })
                print(f"SCAM in {message.guild.name}: {attachment.filename} matched {matched_name}")
        except Exception as e:
            print(f"Error processing {attachment.filename}: {e}")

    if not scam_info:
        return

    delete_time = datetime.now(timezone.utc)
    try:
        await message.delete()
    except Exception as e:
        print(f"Failed to delete message: {e}")

    member = message.guild.get_member(message.author.id)
    if member is None:
        try:
            member = await message.guild.fetch_member(message.author.id)
        except Exception:
            member = None
    await apply_punishment(member, message.guild.name, cfg["punishment"])

    for si in scam_info:
        with Image.open(io.BytesIO(si["data"])) as img:
            ph = imagehash.phash(img)
        if ph not in stored_hashes:
            stored_hashes.add(ph)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            base = os.path.splitext(si["matched"])[0]
            ext = os.path.splitext(si["filename"])[1] or ".jpg"
            save_path = os.path.join(DELETED_IMAGES_DIR, f"{ts}_{base}{ext}")
            with open(save_path, "wb") as f:
                f.write(si["data"])
            print(f"  Saved deleted image: {save_path}")

    embed = discord.Embed(
        title="🚨 Scam Image Detected",
        color=0xFF0000,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="User", value=message.author.mention, inline=True)
    embed.add_field(name="User ID", value=message.author.id, inline=True)
    embed.add_field(name="Channel", value=message.channel.mention, inline=True)
    embed.add_field(
        name="Time Sent",
        value=f"<t:{int(message.created_at.timestamp())}:F>",
        inline=True,
    )
    embed.add_field(
        name="Time Deleted",
        value=f"<t:{int(delete_time.timestamp())}:F>",
        inline=True,
    )
    embed.add_field(name="Punishment", value=cfg["punishment"].replace("_", " + ").title(), inline=True)
    if message.content:
        embed.add_field(name="Message Content", value=message.content[:1000], inline=False)

    files = []
    for i, si in enumerate(scam_info):
        embed.add_field(
            name=f"Image {i+1}: {si['filename']}",
            value=f"Matched reference: `{si['matched']}`",
            inline=False,
        )
        files.append(discord.File(io.BytesIO(si["data"]), filename=si["filename"]))

    await proof_ch.send(embed=embed, files=files)


if __name__ == "__main__":
    bot.run(TOKEN)
