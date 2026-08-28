import logging
import os
import urllib.parse
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
ADMIN_USERNAME = "@TGA_support"
# Nom d'utilisateur sans le "@", nécessaire pour construire les liens t.me
ADMIN_USERNAME_RAW = ADMIN_USERNAME.lstrip("@")

# Libellés du menu persistant en bas de l'écran
MENU_FOREX = "💱 Forex"
MENU_SYNTH = "📊 Indices Synthétiques"

PERSISTENT_MENU = ReplyKeyboardMarkup(
    [[KeyboardButton(MENU_FOREX), KeyboardButton(MENU_SYNTH)]],
    resize_keyboard=True,
)


def build_vip_contact_keyboard(broker: str, has_account: bool) -> InlineKeyboardMarkup:
    """Crée un bouton qui pré-remplit un message vers l'admin pour rejoindre le VIP.

    Le message pré-rempli précise le broker (Deriv/Weltrade) et si la
    personne a déjà un compte ou non, pour que l'admin sache directement.
    """
    statut = "j'ai déjà un compte" if has_account else "je n'ai pas de compte"
    message = f"Je veux rejoindre le VIP {broker} — {statut}"
    encoded_message = urllib.parse.quote(message)
    url = f"https://t.me/{ADMIN_USERNAME_RAW}?text={encoded_message}"
    keyboard = [[InlineKeyboardButton("✉️ Envoyer ma demande VIP", url=url)]]
    return InlineKeyboardMarkup(keyboard)


# ---- Message de bienvenue ----
# NOTE : tous les textes ci-dessous sont en HTML (parse_mode="HTML"), pas en
# Markdown. C'est plus robuste avec Telegram : les underscores, astérisques
# et autres caractères spéciaux dans les URLs ne cassent jamais le formatage.
# Balises utilisables : <b>gras</b>, <i>italique</i>, <a href="...">lien</a>
WELCOME_TEXT = (
    "👋 <b>Bienvenue !</b>\n\n"
    "Ravi de t'avoir parmi nous. Ce bot va t'aider à activer l'accès à mes "
    "<b>signaux de trading</b>.\n\n"
    "👉 Souhaites-tu trader sur le <b>Forex</b> ou les <b>Indices Synthétiques</b> ?"
)

# ---- Textes FOREX ----
FOREX_NO_ACCOUNT = (
    "🔵 <b>Forex — Création de compte PU Prime</b>\n\n"
    "Afin d'intégrer notre groupe VIP 100% gratuit Forex, tu dois d'abord :\n\n"
    "1️⃣ Créer un compte <b>PU Prime</b> avec notre lien (important) :\n"
    '👉 <a href="https://www.puprime.partners/forex-trading-account/?affid=29071347">Créer mon compte PU Prime</a>\n\n'
    "2️⃣ Faire un dépôt de <b>100$ minimum</b> (500$ conseillé)\n\n"
    "3️⃣ Envoyer la capture d'écran de ton compte contenant le <b>numéro ID</b>\n\n"
    f"Si tu es prêt, on procède à l'ouverture. Envoie ta capture directement à {ADMIN_USERNAME} 👍"
)

FOREX_HAS_ACCOUNT = (
    "🔵 <b>Forex — Taguer un compte PU Prime existant</b>\n\n"
    "<b>Option 1 — par email</b>\n"
    "Envoie ce message à <b>Info@puprime.com</b> et <b>erik.guilhem@puprime.com</b> :\n"
    '<i>"Je veux être tagué sous IB 29071347"</i>\n\n'
    "<b>Option 2 — manuellement dans ton compte</b>\n"
    "1️⃣ Va dans ton <b>Profil</b>\n"
    '2️⃣ Clique sur l\'onglet "Transfer IB/CPA"\n'
    "3️⃣ Sélectionne le type de partenariat : <b>IB</b>\n"
    '4️⃣ Dans "New CPA ID / IB Number" mets : <b>29071347</b>\n'
    '5️⃣ Dans "Reason for Transfer" écris : <b>Nouveau Partenaire</b>\n'
    "6️⃣ Clique sur <b>Submit</b>\n\n"
    f"Une fois fait, envoie-moi une confirmation à {ADMIN_USERNAME} pour que je valide ton accès ✅"
)

# ---- Textes SYNTHETIQUES - DERIV ----
DERIV_LINK = "https://partners.deriv.com/rx?sidc=3E33DCA0-53E8-4291-A650-73A152DF6BB1&utm_campaign=dynamicworks&utm_medium=affiliate&utm_source=CU27273"

DERIV_NO_ACCOUNT = (
    "🟢 <b>Indices Synthétiques — Deriv — Création de compte</b>\n\n"
    "Pour intégrer notre groupe VIP Indices Synthétiques (Deriv), tu dois :\n\n"
    "1️⃣ Créer un compte <b>Deriv</b> avec notre lien (important) :\n"
    f'👉 <a href="{DERIV_LINK}">Créer mon compte Deriv</a>\n\n'
    "2️⃣ Faire un dépôt de <b>30$ minimum</b> (250$ conseillé)\n\n"
    f"3️⃣ Envoie-moi ton <b>email</b> de compte en message privé sur Telegram ({ADMIN_USERNAME}) pour vérification\n\n"
    "Une fois vérifié, tu seras ajouté au groupe VIP ✅"
)

DERIV_HAS_ACCOUNT = (
    "🟢 <b>Indices Synthétiques — Deriv — Taguer un compte existant</b>\n\n"
    "Si tu as déjà un compte de trading chez Deriv :\n\n"
    "1️⃣ Écris au <b>live chat / support Deriv</b>\n"
    "2️⃣ Dis que tu veux taguer ton compte sous le partenaire <b>FOGANG</b>\n"
    "3️⃣ Si un lien est demandé, envoie celui-ci :\n"
    f'👉 <a href="{DERIV_LINK}">Lien partenaire Deriv</a>\n\n'
    f"Une fois fait, envoie-moi une confirmation à {ADMIN_USERNAME} et je t'ajoute au groupe de "
    "signaux — c'est là-bas qu'on discutera aussi du copy trading 📈"
)

# ---- Textes SYNTHETIQUES - WELTRADE ----
WELTRADE_LINK = "https://www.weltrade.com/?r1=ipartner&r2=68084&ibrefid=97343a9a-942c-4671-849a-95b05db4bb27"

WELTRADE_NO_ACCOUNT = (
    "🟡 <b>Indices Synthétiques — Weltrade — Création de compte</b>\n\n"
    "Pour intégrer le VIP Signaux Weltrade, il te suffit de :\n\n"
    "1️⃣ Créer ton compte <b>Weltrade</b> via notre lien (important) :\n"
    f'👉 <a href="{WELTRADE_LINK}">Créer mon compte Weltrade</a>\n\n'
    "2️⃣ Faire un dépôt de <b>40$ minimum</b> (250$ recommandé)\n\n"
    f"Une fois ton compte créé et le dépôt effectué, envoie-moi la confirmation en message "
    f"privé sur Telegram ({ADMIN_USERNAME}) pour être ajouté au groupe ✅"
)

WELTRADE_HAS_ACCOUNT = (
    "🟡 <b>Indices Synthétiques — Weltrade — Taguer un compte existant</b>\n\n"
    "Si tu as déjà un compte chez Weltrade :\n\n"
    "1️⃣ Écris au <b>support Weltrade</b>\n"
    "2️⃣ Dis que tu veux être tagué sous <b>FOGANG</b>\n"
    "3️⃣ Envoie ce lien s'ils le demandent :\n"
    f'👉 <a href="{WELTRADE_LINK}">Lien partenaire Weltrade</a>\n\n'
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


async def safe_send_message(context, chat_id, text, reply_markup=None):
    """Envoie un message en HTML, avec repli automatique en texte brut
    si le formatage est mal formé. Cela évite qu'un message reste
    silencieusement bloqué."""
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Échec envoi HTML (%s), repli en texte brut", exc)
        await context.bot.send_message(
            chat_id=chat_id, text=text, reply_markup=reply_markup
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Affiche le message de bienvenue et le choix Forex / Synthétiques."""
    keyboard = [
        [InlineKeyboardButton("💱 Forex", callback_data="market_forex")],
        [InlineKeyboardButton("📊 Indices Synthétiques", callback_data="market_synth")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        WELCOME_TEXT, parse_mode="HTML", reply_markup=reply_markup
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
        await safe_send_message(
            context,
            chat_id,
            "💱 <b>Forex sélectionné</b>\n\nAs-tu déjà un compte de trading chez PU Prime ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif text == MENU_SYNTH:
        keyboard = [
            [InlineKeyboardButton("Deriv", callback_data="broker_deriv")],
            [InlineKeyboardButton("Weltrade", callback_data="broker_weltrade")],
        ]
        await safe_send_message(
            context,
            chat_id,
            "📊 <b>Indices Synthétiques sélectionnés</b>\n\nQuel broker veux-tu utiliser ?",
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
        await safe_send_message(
            context,
            chat_id,
            "💱 <b>Forex sélectionné</b>\n\nAs-tu déjà un compte de trading chez PU Prime ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "market_synth":
        keyboard = [
            [InlineKeyboardButton("Deriv", callback_data="broker_deriv")],
            [InlineKeyboardButton("Weltrade", callback_data="broker_weltrade")],
        ]
        await safe_send_message(
            context,
            chat_id,
            "📊 <b>Indices Synthétiques sélectionnés</b>\n\nQuel broker veux-tu utiliser ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # --- Choix du broker (synthétiques) ---
    elif data == "broker_deriv":
        keyboard = [
            [InlineKeyboardButton("✅ J'ai déjà un compte", callback_data="deriv_has")],
            [InlineKeyboardButton("🆕 Je n'ai pas de compte", callback_data="deriv_no")],
        ]
        await safe_send_message(
            context,
            chat_id,
            "🟢 <b>Deriv sélectionné</b>\n\nAs-tu déjà un compte de trading chez Deriv ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "broker_weltrade":
        keyboard = [
            [InlineKeyboardButton("✅ J'ai déjà un compte", callback_data="weltrade_has")],
            [InlineKeyboardButton("🆕 Je n'ai pas de compte", callback_data="weltrade_no")],
        ]
        await safe_send_message(
            context,
            chat_id,
            "🟡 <b>Weltrade sélectionné</b>\n\nAs-tu déjà un compte de trading chez Weltrade ?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # --- Réponses finales (les 6 procédures) ---
    elif data == "forex_has":
        # Envoie d'abord les captures d'écran de la procédure, dans l'ordre, puis le texte
        for image_path in PUPRIME_TRANSFER_IMAGES:
            if image_path.exists():
                with open(image_path, "rb") as photo:
                    await context.bot.send_photo(chat_id=chat_id, photo=photo)
        await safe_send_message(context, chat_id, FOREX_HAS_ACCOUNT)
    elif data == "forex_no":
        await safe_send_message(context, chat_id, FOREX_NO_ACCOUNT)
    elif data == "deriv_has":
        await safe_send_message(
            context,
            chat_id,
            DERIV_HAS_ACCOUNT,
            reply_markup=build_vip_contact_keyboard("Deriv", has_account=True),
        )
    elif data == "deriv_no":
        await safe_send_message(
            context,
            chat_id,
            DERIV_NO_ACCOUNT,
            reply_markup=build_vip_contact_keyboard("Deriv", has_account=False),
        )
    elif data == "weltrade_has":
        await safe_send_message(
            context,
            chat_id,
            WELTRADE_HAS_ACCOUNT,
            reply_markup=build_vip_contact_keyboard("Weltrade", has_account=True),
        )
    elif data == "weltrade_no":
        await safe_send_message(
            context,
            chat_id,
            WELTRADE_NO_ACCOUNT,
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
