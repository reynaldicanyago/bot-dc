import os
import discord
import logging
from discord.ext import commands

# LOG
logging.basicConfig(level=logging.INFO)

# INTENTS
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_selections = {}
temp_voice_channels = set()

CREATE_CHANNEL_NAME = "➕ Buat Voice Channel"

# ================= REGISTER =================

class RegisterModal(discord.ui.Modal, title="📋 Registrasi"):
    nama = discord.ui.TextInput(label="Nama")
    asal = discord.ui.TextInput(label="Asal")
    ign = discord.ui.TextInput(label="Nick In Game")
    rank = discord.ui.TextInput(label="Rank")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            data = user_selections.get(interaction.user.id, {})
            device = data.get("device", "📱Mobile")
            role_game = data.get("role", "⚡Rusher")

            guild = interaction.guild

            # set nickname
            try:
                await interaction.user.edit(nick=self.ign.value)
            except:
                pass

            # roles
            for role_name in ["🤝New Member", device, role_game]:
                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    await interaction.user.add_roles(role)

            # kirim ke announcement
            channel = discord.utils.get(guild.text_channels, name="announcement")
            if channel:
                embed = discord.Embed(
                    title="📢 MEMBER BARU!",
                    color=discord.Color.red()
                )
                embed.add_field(name="Nama", value=self.nama.value)
                embed.add_field(name="Asal", value=self.asal.value)
                embed.add_field(name="IGN", value=self.ign.value)
                embed.add_field(name="Rank", value=self.rank.value)
                embed.add_field(name="Device", value=device)
                embed.add_field(name="Role", value=role_game)

                await channel.send(embed=embed)

            await interaction.followup.send("✅ Registrasi berhasil!", ephemeral=True)

        except Exception as e:
            print("ERROR:", e)
            await interaction.followup.send("❌ Terjadi error!", ephemeral=True)


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
        await interaction.response.defer()
        user_selections[interaction.user.id]["device"] = select.values[0]

    @discord.ui.select(
        placeholder="Pilih Role",
        options=[
            discord.SelectOption(label="⚡Rusher"),
            discord.SelectOption(label="🎯Sniper"),
            discord.SelectOption(label="🛡Support"),
        ],
    )
    async def role(self, interaction, select):
        await interaction.response.defer()
        user_selections[interaction.user.id]["role"] = select.values[0]

    @discord.ui.button(label="Isi Data", style=discord.ButtonStyle.green)
    async def isi(self, interaction, button):
        await interaction.response.send_modal(RegisterModal())


class RegisterPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="REGISTER", style=discord.ButtonStyle.primary, custom_id="register_btn")
    async def register(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            "Pilih device & role dulu",
            view=SelectionView(interaction.user.id),
            ephemeral=True
        )


async def send_panel(channel):
    embed = discord.Embed(
        title="🔥 BLOOD STRIKE REGISTER",
        description="Klik tombol untuk daftar",
        color=discord.Color.red()
    )
    await channel.send(embed=embed, view=RegisterPanel())


@bot.command()
async def setup(ctx):
    await send_panel(ctx.channel)

# ================= VOICE =================

@bot.event
async def on_voice_state_update(member, before, after):

    if after.channel and after.channel.name == CREATE_CHANNEL_NAME:
        category = after.channel.category

        vc = await member.guild.create_voice_channel(
            name=member.display_name,
            category=category
        )

        temp_voice_channels.add(vc.id)
        await member.move_to(vc)

    if before.channel and before.channel.id in temp_voice_channels:
        if len(before.channel.members) == 0:
            await before.channel.delete()
            temp_voice_channels.remove(before.channel.id)

# ================= READY =================

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

    bot.add_view(RegisterPanel())

    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name="register")
        if channel:
            await send_panel(channel)

# ================= ERROR =================

@bot.event
async def on_error(event, *args, **kwargs):
    print("ERROR EVENT:", event)

# ================= RUN =================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise Exception("Token tidak ditemukan!")

bot.run(TOKEN)
