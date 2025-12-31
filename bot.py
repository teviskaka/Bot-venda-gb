import discord
from discord.ext import commands
import json
import os
import sys

# ================== CONFIG ==================
GUILD_ID = 1361129837238157472  # <<< ID DO SEU SERVIDOR AQUI
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ ERRO: Variável DISCORD_TOKEN não definida")
    sys.exit(1)

DB_FILE = "database.json"

# ================== DATABASE ==================
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "config": {
                "pix": "Não configurado",
                "cargo_owner": None,
                "cat_suporte": None
            },
            "produtos": {}
        }
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

db = load_db()

# ================== PACOTES ==================
PACOTES_SALAS = {
    "50": {"label": "10 Salas 💎", "preco": "R$ 3,00", "mensagem": "Crie Sala Automaticamente!"},
    "100": {"label": "30 Salas 💎", "preco": "R$ 6,00", "mensagem": "Crie Sala Automaticamente!"},
    "300": {"label": "50 Salas 💎", "preco": "R$ 10,00", "mensagem": "Crie Sala Automaticamente!"},
    "500": {"label": "100 Salas 💎", "preco": "R$ 18,00", "mensagem": "Crie Sala Automaticamente!"},
    "1000": {"label": "300 Salas 💎", "preco": "R$ 60,00", "mensagem": "Crie Sala Automaticamente!"}
}

# ================== ADMIN VIEW ==================
class AdminActions(discord.ui.View):
    def __init__(self, cliente_id):
        super().__init__(timeout=None)
        self.cliente_id = cliente_id

    @discord.ui.button(label="Aprovar Pagamento", style=discord.ButtonStyle.success, emoji="✅")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if db["config"]["cargo_owner"] not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

        membro = interaction.guild.get_member(self.cliente_id)
        if membro:
            await interaction.channel.send(f"✅ Pagamento aprovado! {membro.mention}")
        await interaction.response.send_message("Confirmado!", ephemeral=True)

    @discord.ui.button(label="Fechar Carrinho", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if db["config"]["cargo_owner"] not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
        await interaction.channel.delete()

# ================== PRODUUP VIEW ==================
class ProduUpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        options = [
            discord.SelectOption(
                label=f"{v['label']} - {v['preco']}",
                description=v["mensagem"],
                value=k
            ) for k, v in PACOTES_SALAS.items()
        ]

        select = discord.ui.Select(
            placeholder="📦 Escolha seu pacote",
            options=options
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        escolha = interaction.data["values"][0]
        data = PACOTES_SALAS[escolha]
        cfg = db["config"]

        guild = interaction.guild
        categoria = guild.get_channel(cfg["cat_suporte"])

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            guild.get_role(cfg["cargo_owner"]): discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(
            name=f"🆙-{interaction.user.name}",
            category=categoria,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="💳 Pagamento PIX",
            description=(
                f"Produto: **{data['label']}**\n"
                f"Valor: **{data['preco']}**\n\n"
                f"Pix: `{cfg['pix']}`\n\n"
                "📢 Envie o comprovante abaixo"
            ),
            color=discord.Color.blue()
        )

        await canal.send(
            content=interaction.user.mention,
            embed=embed,
            view=AdminActions(interaction.user.id)
        )

        await interaction.response.send_message(
            f"✅ Carrinho criado: {canal.mention}",
            ephemeral=True
        )

# ================== BOT ==================
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.clear_commands(guild=guild)
        await self.tree.sync(guild=guild)
        print("✅ Slash commands sincronizados na guild")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"🤖 Online como {bot.user}")

# ================== COMMANDS ==================
@bot.tree.command(name="setup", description="Configura o sistema")
async def setup(
    interaction: discord.Interaction,
    pix: str,
    cargo_admin: discord.Role,
    categoria: discord.CategoryChannel
):
    db["config"]["pix"] = pix
    db["config"]["cargo_owner"] = cargo_admin.id
    db["config"]["cat_suporte"] = categoria.id
    save_db(db)
    await interaction.response.send_message("✅ Configurado com sucesso!", ephemeral=True)

@bot.tree.command(name="produup", description="Abrir menu de pacotes")
async def produup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🚀 SALAS AUTOMÁTICAS - GB STORE",
        description="Escolha um pacote abaixo para continuar.",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed, view=ProduUpView())

bot.run(TOKEN)
