import os
import discord
import logging
from discord.ext import commands

# ──────────────────────────────────────────
# LOGGING (ANTI ERROR DIAM-DIAM)
# ──────────────────────────────────────────
logging.basicConfig(level=logging.INFO)

# ──────────────────────────────────────────
# INTENTS (LEBIH AMAN)
# ──────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ──────────────────────────────────────────
# GLOBAL DATA
# ──────────────────────────────────────────
user_selections = {}
temp_voice_channels = set()

CREATE_CHANNEL_NAME = "➕ Buat Voice Channel"

# ──────────────────────────────────────────
# REGISTER SYSTEM
# ──────────────────────────────────────────

class RegisterModal(discord.ui.Modal, title="📋 Registrasi Member"):
    nama = discord.ui.TextInput(label="Nama", required=True)
    asal = discord.ui.TextInput(label="Asal", required=True)
    ign = discord.ui.TextInput(label="Nick In Game", required=True)
    rank = discord.ui.TextInput(label="Rank", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        data = user_selections.get(user_id, {})

        device = data.get("device", "📱Mobile")
        role_game = data.get("role", "⚡Rusher")

        # Set nickname
        try:
            await interaction.user.edit(nick=self.ign.value)
        except:
            pass

        # Add roles
        guild = interaction.guild
        for role_name in ["🤝New Member", device, role_game]:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await interaction.user.add_roles(role)

        # Kirim ke announcement
        channel = discord.utils.get(guild.text_channels, name="announcement")
        if channel:
            embed = discord.Embed(
                title="📢 MEMBER BARU MASUK!",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 Nama", value=self.nama.value)
            embed.add_field(name="🌍 Asal", value=self.asal.value)
            embed.add_field(name="🎮 IGN", value=self.ign.value)
            embed.add_field(name="🏆 Rank", value=self.rank.value)
            embed.add_field(name="📱 Device", value=device)
            embed.add_field(name="🎯 Role", value=role_game)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)

            await channel.send(embed=embed)

        user_selections.pop(user_id, None)

        await interaction.response.send_message(
            "✅ Registrasi berhasil! Welcome 🔥",
            ephemeral=True
        )


class SelectionView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        user_selections[user_id] = {}

    @discord.ui.select(
        placeholder="Pilih Device",
        options=[
            discord.SelectOption(label="📱Mobile"),
            discord.SelectOption(label="🖥PC"),
        ],
    )
    async def device(self, interaction, select):
        user_selections[interaction.user.id]["device"] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        placeholder="Pilih Role",
        options=[
            discord.SelectOption(label="⚡Rusher"),
            discord.SelectOption(label="🎯Sniper"),
            discord.SelectOption(label="🛡Support"),
        ],
    )
    async def role(self, interaction, select):
        user_selections[interaction.user.id]["role"] = select.values[0]
        await interaction.response.defer()

    @discord.ui.button(label="Isi Data", style=discord.ButtonStyle.green)
    async def isi(self, interaction, button):
        await interaction.response.send_modal(RegisterModal())


class RegisterPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="REGISTER", style=discord.ButtonStyle.primary, custom_id="register_btn")
    async def register(self, interaction, button):
        await interaction.response.send_message(
            "Pilih dulu device & role ya",
            view=SelectionView(interaction.user.id),
            ephemeral=True
        )


async def send_panel(channel):
    embed = discord.Embed(
        title="🔥 BLOOD STRIKE REGISTER",
        description="Klik tombol di bawah untuk daftar",
        color=discord.Color.red()
    )
    await channel.send(embed=embed, view=RegisterPanel())


@bot.command()
async def setup(ctx):
    await send_panel(ctx.channel)

# ──────────────────────────────────────────
# AUTO VOICE
# ──────────────────────────────────────────

@bot.event
async def on_voice_state_update(member, before, after):

    # Buat channel baru
    if after.channel and after.channel.name == CREATE_CHANNEL_NAME:
        category = after.channel.category

        vc = await member.guild.create_voice_channel(
            name=member.display_name,
            category=category
        )

        temp_voice_channels.add(vc.id)
        await member.move_to(vc)

    # Hapus kalau kosong
    if before.channel and before.channel.id in temp_voice_channels:
        if len(before.channel.members) == 0:
            await before.channel.delete()
            temp_voice_channels.remove(before.channel.id)

# ──────────────────────────────────────────
# READY
# ──────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

    bot.add_view(RegisterPanel())

    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name="register")
        if channel:
            await send_panel(channel)

# ──────────────────────────────────────────
# ERROR HANDLER
# ──────────────────────────────────────────

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Error di event: {event}")

# ──────────────────────────────────────────
# RUN
# ──────────────────────────────────────────

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise Exception("Token tidak ditemukan!")

bot.run(TOKEN)