import logging
import os
from pathlib import Path

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Dossier où se trouve ce script, pour retrouver les images jointes
BASE_DIR = Path(__file__).resolve().parent
PUPRIME_TRANSFER_IMAGES = [
    BASE_DIR / "puprime_step1_profil.jpg",
    BASE_DIR / "puprime_step2_profile_menu.jpg",
    BASE_DIR / "puprime_step3_transfer_ib.jpg",
]

# ============================================================
# CONFIGURATION - Modifie uniquement cette section si besoin
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8573272152:AAE1Cql3gE8IWCwckmWNXnANToHn-HfHEw4")
ADMIN_USERNAME = "@TradingGoldAcademy13"

# Libellés du menu persistant en bas de l'écran
MENU_FOREX = "💱 Forex"
MENU_SYNTH = "📊 Indices Synthétiques"

PERSISTENT_MENU = ReplyKeyboardMarkup(
    [[KeyboardButton(MENU_FOREX), KeyboardButton(MENU_SYNTH)]],
    resize_keyboard=True,
)

# Nom d'utilisateur sans le "@", nécessaire pour construire les liens t.me
ADMIN_USERNAME_RAW = ADMIN_USERNAME.lstrip("@")


def build_vip_contact_keyboard(broker: str, has_account: bool) -> InlineKeyboardMarkup:
    """Crée un bouton qui pré-remplit un message vers l'admin pour rejoindre le VIP.

    Le message pré-rempli précise le broker (Deriv/Weltrade) et si la
    personne a déjà un compte ou non, pour que l'admin sache directement.
    """
    statut = "j'ai déjà un compte" if has_account else "je n'ai pas de compte"
    message = f"Je veux rejoindre le VIP {broker} — {statut}"
    import urllib.parse

    encoded_message = urllib.parse.quote(message)
    url = f"https://t.me/{ADMIN_USERNAME_RAW}?text={encoded_message}"
    keyboard = [[InlineKeyboardButton("✉️ Envoyer ma demande VIP", url=url)]]
    return InlineKeyboardMarkup(keyboard)

# ---- Message de bienvenue ----
WELCOME_TEXT = (
    "👋 *Bienvenue !*\n\n"
    "Ravi de t'avoir parmi nous. Ce bot va t'aider à activer l'accès à mes "
    "*signaux de trading*.\n\n"
    "👉 Souhaites-tu trader sur le *Forex* ou les *Indices Synthétiques* ?"
)

# ---- Textes FOREX ----
FOREX_NO_ACCOUNT = (
    "🔵 *Forex — Création de compte PU Prime*\n\n"
    "Afin d'intégrer notre groupe VIP 100% gratuit Forex, tu dois d'abord :\n\n"
    "1️⃣ Créer un compte *PU Prime* avec notre lien (important) :\n"
    "👉 https://www.puprime.partners/forex-trading-account/?affid=29071347\n\n"
    "2️⃣ Faire un dépôt de *100$ minimum* (500$ conseillé)\n\n"
    "3️⃣ Envoyer la capture d'écran de ton compte contenant le *numéro ID*\n\n"
    f"Si tu es prêt, on procède à l'ouverture. Envoie ta capture directement à {ADMIN_USERNAME} 👍"
)

FOREX_HAS_ACCOUNT = (
    "🔵 *Forex — Taguer un compte PU Prime existant*\n\n"
    "*Option 1 — par email*\n"
    "Envoie ce message à *Info@puprime.com* et *erik.guilhem@puprime.com* :\n"
    "_\"Je veux être tagué sous IB 29071347\"_\n\n"
    "*Option 2 — manuellement dans ton compte*\n"
    "1️⃣ Va dans ton *Profil*\n"
    "2️⃣ Clique sur l'onglet *\"Transfer IB/CPA\"*\n"
    "3️⃣ Sélectionne le type de partenariat : *IB*\n"
    "4️⃣ Dans \"New CPA ID / IB Number\" mets : *29071347*\n"
    "5️⃣ Dans \"Reason for Transfer\" écris : *Nouveau Partenaire*\n"
    "6️⃣ Clique sur *Submit*\n\n"
    f"Une fois fait, envoie-moi une confirmation à {ADMIN_USERNAME} pour que je valide ton accès ✅"
)

# ---- Textes SYNTHETIQUES - DERIV ----
DERIV_NO_ACCOUNT = (
    "🟢 *Indices Synthétiques — Deriv — Création de compte*\n\n"
    "Pour intégrer notre groupe VIP Indices Synthétiques (Deriv), tu dois :\n\n"
    "1️⃣ Créer un compte *Deriv* avec notre lien (important) :\n"
    "👉 https://partners.deriv.com/rx?sidc=3E33DCA0-53E8-4291-A650-73A152DF6BB1&utm_campaign=dynamicworks&utm_medium=affiliate&utm_source=CU27273\n\n"
    "2️⃣ Faire un dépôt de *30$ minimum* (250$ conseillé)\n\n"
    f"3️⃣ Envoie-moi ton *email* de compte en message privé sur Telegram ({ADMIN_USERNAME}) pour vérification\n\n"
    "Une fois vérifié, tu seras ajouté au groupe VIP ✅"
)

DERIV_HAS_ACCOUNT = (
    "🟢 *Indices Synthétiques — Deriv — Taguer un compte existant*\n\n"
    "Si tu as déjà un compte de trading chez Deriv :\n\n"
    "1️⃣ Écris au *live chat / support Deriv*\n"
    "2️⃣ Dis que tu veux taguer ton compte sous le partenaire *FOGANG*\n"
    "3️⃣ Si un lien est demandé, envoie celui-ci :\n"
    "👉 https://partners.deriv.com/rx?sidc=3E33DCA0-53E8-4291-A650-73A152DF6BB1&utm_campaign=dynamicworks&utm_medium=affiliate&utm_source=CU27273\n\n"
    f"Une fois fait, envoie-moi une confirmation à {ADMIN_USERNAME} et je t'ajoute au groupe de "
    "signaux — c'est là-bas qu'on discutera aussi du copy trading 📈"
)

# ---- Textes SYNTHETIQUES - WELTRADE ----
WELTRADE_NO_ACCOUNT = (
    "🟡 *Indices Synthétiques — Weltrade — Création de compte*\n\n"
    "Pour intégrer le VIP Signaux Weltrade, il te suffit de :\n\n"
    "1️⃣ Créer ton compte *Weltrade* via notre lien (important) :\n"
    "👉 https://www.weltrade.com/?r1=ipartner&r2=68084&ibrefid=97343a9a-942c-4671-849a-95b05db4bb27\n\n"
    "2️⃣ Faire un dépôt de *40$ minimum* (250$ recommandé)\n\n"
    f"Une fois ton compte créé et le dépôt effectué, envoie-moi la confirmation en message "
    f"privé sur Telegram ({ADMIN_USERNAME}) pour être ajouté au groupe ✅"
)

WELTRADE_HAS_ACCOUNT = (
    "🟡 *Indices Synthétiques — Weltrade — Taguer un compte existant*\n\n"
    "Si tu as déjà un compte chez Weltrade :\n\n"
    "1️⃣ Écris au *support Weltrade*\n"
    "2️⃣ Dis que tu veux être tagué sous *FOGANG*\n"
    "3️⃣ Envoie ce lien s'ils le demandent :\n"
    "👉 https://www.weltrade.com/?r1=ipartner&r2=68084&ibrefid=97343a9a-942c-4671-849a-95b05db4bb27\n\n"
    f"Une fois fait, envoie-moi une confirmation à {ADMIN_USERNAME} et je t'ajoute au groupe de signaux 📈"
)

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# HANDLERS
# ============================================================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Affiche le message de bienvenue et le choix Forex / Synthétiques."""
    keyboard = [
        [InlineKeyboardButton("💱 Forex", callback_data="market_forex")],
        [InlineKeyboardButton("📊 Indices Synthétiques", callback_data="market_synth")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        WELCOME_TEXT, parse_mode="Markdown", reply_markup=reply_markup
    )
    # Affiche aussi le menu persistant en bas de l'écran, pour permettre de
    # relancer le parcours sans avoir à remonter chercher /start.
    await update.message.reply_text(
        "Tu peux aussi utiliser les boutons ci-dessous à tout moment 👇",
        reply_markup=PERSISTENT_MENU,
    )


async def persistent_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les clics sur le menu persistant en bas de l'écran (Forex / Synthétiques)."""
    text = update.message.text
    chat_id = update.message.chat_id

    if text == MENU_FOREX:
        keyboard = [
            [InlineKeyboardButton("✅ J'ai déjà un compte", callback_data="forex_has")],
            [InlineKeyboardButton("🆕 Je n'ai pas de compte", callback_data="forex_no")],
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text="💱 *Forex sélectionné*\n\nAs-tu déjà un compte de trading chez PU Prime ?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif text == MENU_SYNTH:
        keyboard = [
            [InlineKeyboardButton("Deriv", callback_data="broker_deriv")],
            [InlineKeyboardButton("Weltrade", callback_data="broker_weltrade")],
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text="📊 *Indices Synthétiques sélectionnés*\n\nQuel broker veux-tu utiliser ?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère tous les clics sur les boutons inline du bot.

    Chaque étape envoie un NOUVEAU message (au lieu de modifier l'ancien),
    afin que l'historique complet du parcours reste visible pour l'utilisateur.
    """
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id

    # --- Choix du marché ---
    if data == "market_forex":
        keyboard = [
            [InlineKeyboardButton("✅ J'ai déjà un compte", callback_data="forex_has")],
            [InlineKeyboardButton("🆕 Je n'ai pas de compte", callback_data="forex_no")],
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text="💱 *Forex sélectionné*\n\nAs-tu déjà un compte de trading chez PU Prime ?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "market_synth":
        keyboard = [
            [InlineKeyboardButton("Deriv", callback_data="broker_deriv")],
            [InlineKeyboardButton("Weltrade", callback_data="broker_weltrade")],
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text="📊 *Indices Synthétiques sélectionnés*\n\nQuel broker veux-tu utiliser ?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # --- Choix du broker (synthétiques) ---
    elif data == "broker_deriv":
        keyboard = [
            [InlineKeyboardButton("✅ J'ai déjà un compte", callback_data="deriv_has")],
            [InlineKeyboardButton("🆕 Je n'ai pas de compte", callback_data="deriv_no")],
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text="🟢 *Deriv sélectionné*\n\nAs-tu déjà un compte de trading chez Deriv ?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "broker_weltrade":
        keyboard = [
            [InlineKeyboardButton("✅ J'ai déjà un compte", callback_data="weltrade_has")],
            [InlineKeyboardButton("🆕 Je n'ai pas de compte", callback_data="weltrade_no")],
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text="🟡 *Weltrade sélectionné*\n\nAs-tu déjà un compte de trading chez Weltrade ?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # --- Réponses finales (les 6 procédures) ---
    elif data == "forex_has":
        # Envoie d'abord les captures d'écran de la procédure, dans l'ordre, puis le texte
        for image_path in PUPRIME_TRANSFER_IMAGES:
            if image_path.exists():
                with open(image_path, "rb") as photo:
                    await context.bot.send_photo(chat_id=chat_id, photo=photo)
        await context.bot.send_message(
            chat_id=chat_id, text=FOREX_HAS_ACCOUNT, parse_mode="Markdown"
        )
    elif data == "forex_no":
        await context.bot.send_message(
            chat_id=chat_id, text=FOREX_NO_ACCOUNT, parse_mode="Markdown"
        )
    elif data == "deriv_has":
        await context.bot.send_message(
            chat_id=chat_id,
            text=DERIV_HAS_ACCOUNT,
            parse_mode="Markdown",
            reply_markup=build_vip_contact_keyboard("Deriv", has_account=True),
        )
    elif data == "deriv_no":
        await context.bot.send_message(
            chat_id=chat_id,
            text=DERIV_NO_ACCOUNT,
            parse_mode="Markdown",
            reply_markup=build_vip_contact_keyboard("Deriv", has_account=False),
        )
    elif data == "weltrade_has":
        await context.bot.send_message(
            chat_id=chat_id,
            text=WELTRADE_HAS_ACCOUNT,
            parse_mode="Markdown",
            reply_markup=build_vip_contact_keyboard("Weltrade", has_account=True),
        )
    elif data == "weltrade_no":
        await context.bot.send_message(
            chat_id=chat_id,
            text=WELTRADE_NO_ACCOUNT,
            parse_mode="Markdown",
            reply_markup=build_vip_contact_keyboard("Weltrade", has_account=False),
        )


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Commande /menu pour recommencer le parcours sans redémarrer le bot."""
    await start(update, context)


# ============================================================
# LANCEMENT DU BOT
# ============================================================


def main() -> None:
    # Compatibilité Python 3.12+/3.14 : s'assurer qu'une boucle asyncio
    # existe dans le thread principal avant que la librairie n'en cherche une.
    import asyncio

    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", restart))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(
        MessageHandler(
            filters.Text([MENU_FOREX, MENU_SYNTH]), persistent_menu_handler
        )
    )

    logger.info("Bot démarré, en écoute...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES, drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
