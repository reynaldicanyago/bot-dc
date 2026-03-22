import os
import discord
from discord.ext import commands
import logging

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

user_selections = {}
temp_voice_channels = set()

CREATE_CHANNEL_NAME = "➕ Buat Voice Channel"
VOICE_CATEGORY_NAME = "🎧 | VOICE"


# ──────────────────────────────────────────
# REGISTRATION SYSTEM
# ──────────────────────────────────────────


class RegisterModal(discord.ui.Modal, title="📋 Registrasi Member"):
    nama = discord.ui.TextInput(
        label="Nama",
        placeholder="Masukkan nama lengkap kamu",
        required=True,
        max_length=50,
    )
    asal = discord.ui.TextInput(
        label="Asal",
        placeholder="Masukkan kota / daerah asal kamu",
        required=True,
        max_length=50,
    )
    ign = discord.ui.TextInput(
        label="Nick In Game",
        placeholder="Masukkan nick in game kamu",
        required=True,
        max_length=50,
    )
    rank = discord.ui.TextInput(
        label="Rank",
        placeholder="Masukkan rank kamu saat ini",
        required=True,
        max_length=50,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # ✅ FIX

        try:
            user_id = interaction.user.id
            data = user_selections.get(user_id, {})
            device = data.get("device", "📱Mobile")
            role_game = data.get("role", "⚡Rusher")

            # Set nickname to IGN
            try:
                await interaction.user.edit(nick=self.ign.value)
            except discord.Forbidden:
                pass

            # Assign roles
            guild = interaction.guild
            for role_name in ["🤝New Member", device, role_game]:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    await interaction.user.add_roles(role)

            # Post to #announcement
            channel = next(
                (c for c in guild.text_channels if "announcement" in c.name.lower()),
                None
            )
            if channel:
                embed = discord.Embed(
                    title="📢 MEMBER BARU MASUK!", color=discord.Color.red()
                )
                embed.add_field(name="👤 Nama", value=self.nama.value, inline=True)
                embed.add_field(name="🌍 Asal", value=self.asal.value, inline=True)
                embed.add_field(name="🎮 Nick In Game", value=self.ign.value, inline=True)
                embed.add_field(name="🏆 Rank", value=self.rank.value, inline=True)
                embed.add_field(name="📱 Device", value=device, inline=True)
                embed.add_field(name="🎯 Role", value=role_game, inline=True)
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                embed.set_footer(text="Welcome TO Night Fury! 🔥")
                await channel.send(embed=embed)

            user_selections.pop(user_id, None)

            await interaction.followup.send(  # ✅ FIX
                "✅ **Registrasi berhasil!** Selamat bergabung di Night Fury! 🔥",
                ephemeral=True,
            )

        except Exception as e:
            print("ERROR:", e)
            await interaction.followup.send(
                "❌ Terjadi kesalahan saat registrasi. Silakan coba lagi.",
                ephemeral=True
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        try:
            await interaction.response.send_message(
                "❌ Terjadi kesalahan saat registrasi. Silakan coba lagi.",
                ephemeral=True
            )
        except:
            pass


class SelectionView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        user_selections[user_id] = {"device": "📱Mobile", "role": "⚡Rusher"}

    @discord.ui.select(
        placeholder="📱 Pilih Device kamu",
        options=[
            discord.SelectOption(label="📱Mobile", description="Bermain di HP"),
            discord.SelectOption(label="🖥PC", description="Bermain di PC / Emulator"),
        ],
    )
    async def select_device(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        user_selections.setdefault(interaction.user.id, {})["device"] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        placeholder="🎯 Pilih Role Gameplay",
        options=[
            discord.SelectOption(label="🎯Sniper", description="Jarak jauh, presisi tinggi"),
            discord.SelectOption(label="⚡Rusher", description="Agresif dan cepat"),
            discord.SelectOption(label="🛡Support", description="Mendukung tim"),
            discord.SelectOption(label="🧠Kang Deploy", description="Specialist deploy"),
            discord.SelectOption(label="👀Scout", description="Pengintai, informasi tim"),
        ],
    )
    async def select_role(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        user_selections.setdefault(interaction.user.id, {})["role"] = select.values[0]
        await interaction.response.defer()

    @discord.ui.button(label="📝 Isi Data Diri", style=discord.ButtonStyle.green, row=2)
    async def open_modal(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(RegisterModal())


class RegisterPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📋 REGISTER",
        style=discord.ButtonStyle.primary,
        custom_id="register_panel_button",
    )
    async def register(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        view = SelectionView(interaction.user.id)

        await interaction.response.defer(ephemeral=True)  # ✅ FIX
        await interaction.followup.send(
            "**Langkah 1:** Pilih device dan role kamu, lalu klik **Isi Data Diri** untuk melanjutkan.",
            view=view,
            ephemeral=True,
        )


async def send_register_panel(channel: discord.TextChannel):
    embed = discord.Embed(
        title="🔥 Night Fury — Registrasi Member",
        description=(
            "Selamat datang di **Night Fury Clan**!\n\n"
            "Klik tombol **REGISTER** di bawah untuk mendaftar sebagai member resmi.\n\n"
            "📋 **Data yang akan diisi:**\n"
            "┣ 👤 Nama\n"
            "┣ 🌍 Asal\n"
            "┣ 🎮 Nick In Game\n"
            "┣ 🏆 Rank\n"
            "┣ 📱 Device\n"
            "┗ 🎯 Role Gameplay"
        ),
        color=discord.Color.red(),
    )
    embed.set_footer(text="Night Fury Clan • Sistem Registrasi Modern")
    await channel.send(embed=embed, view=RegisterPanel())


@bot.command()
async def setup(ctx):
    await send_register_panel(ctx.channel)


# ──────────────────────────────────────────
# AUTO VOICE CHANNEL SYSTEM
# ──────────────────────────────────────────


@bot.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    if after.channel and after.channel.name == CREATE_CHANNEL_NAME:
        category = after.channel.category
        new_channel = await member.guild.create_voice_channel(
            name=f"{member.display_name}", category=category
        )
        temp_voice_channels.add(new_channel.id)
        await member.move_to(new_channel)

    if before.channel and before.channel.id in temp_voice_channels:
        if len(before.channel.members) == 0:
            await before.channel.delete()
            temp_voice_channels.discard(before.channel.id)


# ──────────────────────────────────────────
# STARTUP
# ──────────────────────────────────────────


@bot.event
async def on_ready():
    print(f"Bot aktif sebagai {bot.user}")

    bot.add_view(RegisterPanel())

    for guild in bot.guilds:
        register_channel = discord.utils.get(guild.text_channels, name="register")
        if register_channel:
            already_posted = False
            async for msg in register_channel.history(limit=20):
                if msg.author == bot.user and msg.embeds:
                    already_posted = True
                    break
            if not already_posted:
                await send_register_panel(register_channel)


@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Error di event: {event}")


token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN environment variable is not set.")

bot.run(token)
