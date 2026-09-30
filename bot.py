import logging
import os
import urllib.parse

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

# ============================================================
# CONFIGURATION - Modifie uniquement cette section si besoin
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8573272152:AAE1Cql3gE8IWCwckmWNXnANToHn-HfHEw4")
ADMIN_USERNAME = "@TGA_support"
ADMIN_USERNAME_RAW = ADMIN_USERNAME.lstrip("@")

# Libellés du menu persistant en bas de l'écran
MENU_FOREX = "💱 Forex"
MENU_SYNTH = "📊 Indices Synthétiques"

PERSISTENT_MENU = ReplyKeyboardMarkup(
    [[KeyboardButton(MENU_SYNTH), KeyboardButton(MENU_FOREX)]],
    resize_keyboard=True,
)

WELCOME_TEXT = (
    "👋 <b>Bienvenue !</b>\n\n"
    "Ravi de t'avoir parmi nous. Ce bot va t'aider à activer l'accès à mes "
    "<b>signaux de trading</b>.\n\n"
    "👉 Souhaites-tu trader sur le <b>Forex</b> ou les <b>Indices Synthétiques</b> ?"
)


def build_vip_contact_url(marche: str, has_account: bool) -> str:
    """Construit l'URL Telegram qui pré-remplit un message vers l'admin.

    Le message pré-rempli précise le marché/broker (Forex/Deriv/Weltrade) et
    si la personne a déjà un compte ou non, pour que l'admin sache directement
    comment continuer la conversation manuellement.
    """
    statut = "j'ai déjà un compte" if has_account else "je n'ai pas de compte"
    message = f"Je veux rejoindre le VIP {marche} — {statut}"
    encoded_message = urllib.parse.quote(message)
    return f"https://t.me/{ADMIN_USERNAME_RAW}?text={encoded_message}"


def build_vip_contact_keyboard(marche: str, has_account: bool) -> InlineKeyboardMarkup:
    """Crée un bouton qui pré-remplit un message vers l'admin pour rejoindre le VIP."""
    url = build_vip_contact_url(marche, has_account)
    keyboard = [[InlineKeyboardButton("✉️ Envoyer ma demande VIP", url=url)]]
    return InlineKeyboardMarkup(keyboard)


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
    """Envoie un message en HTML, avec repli automatique en texte brut en cas
    d'échec de formatage, pour qu'un message ne reste jamais silencieusement
    bloqué."""
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
        [InlineKeyboardButton("📊 Indices Synthétiques", callback_data="market_synth")],
        [InlineKeyboardButton("💱 Forex", callback_data="market_forex")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        WELCOME_TEXT, parse_mode="HTML", reply_markup=reply_markup
    )
    await update.message.reply_text(
        "Tu peux aussi utiliser les boutons ci-dessous à tout moment 👇",
        reply_markup=PERSISTENT_MENU,
    )


async def ask_market_choice(context, chat_id):
    keyboard = [
        [InlineKeyboardButton("📊 Indices Synthétiques", callback_data="market_synth")],
        [InlineKeyboardButton("💱 Forex", callback_data="market_forex")],
    ]
    await safe_send_message(
        context,
        chat_id,
        "👉 Souhaites-tu trader sur le <b>Forex</b> ou les <b>Indices Synthétiques</b> ?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def persistent_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gère les clics sur le menu persistant en bas de l'écran (Forex / Synthétiques)."""
    text = update.message.text
    chat_id = update.message.chat_id

    if text == MENU_FOREX:
        await send_account_question(context, chat_id, "forex")
    elif text == MENU_SYNTH:
        await ask_broker_choice(context, chat_id)


async def ask_broker_choice(context, chat_id):
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


async def send_account_question(context, chat_id, marche_key):
    """Affiche la question 'as-tu déjà un compte ?' pour le marché donné.

    marche_key est une clé technique interne (forex / deriv / weltrade),
    utilisée pour construire les callback_data suivants.
    """
    labels = {"forex": "Forex", "deriv": "Deriv", "weltrade": "Weltrade"}
    label = labels[marche_key]

    # Boutons URL directs : ouvrent tout de suite Telegram vers l'admin avec
    # le message pré-rempli, sans étape intermédiaire dans le bot.
    url_has = build_vip_contact_url(label, has_account=True)
    url_no = build_vip_contact_url(label, has_account=False)
    keyboard = [
        [InlineKeyboardButton("✅ J'ai déjà un compte", url=url_has)],
        [InlineKeyboardButton("🆕 Je n'ai pas de compte", url=url_no)],
    ]
    await safe_send_message(
        context,
        chat_id,
        f"As-tu déjà un compte de trading pour <b>{label}</b> ?\n\n"
        f"Clique sur l'option qui te correspond pour envoyer ta demande directement à "
        f"{ADMIN_USERNAME} et continuer avec lui 👇",
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
        await send_account_question(context, chat_id, "forex")

    elif data == "market_synth":
        await ask_broker_choice(context, chat_id)

    # --- Choix du broker (synthétiques) ---
    elif data == "broker_deriv":
        await send_account_question(context, chat_id, "deriv")

    elif data == "broker_weltrade":
        await send_account_question(context, chat_id, "weltrade")

    # NOTE : les boutons "J'ai déjà un compte" / "Je n'ai pas de compte" sont
    # maintenant des boutons URL directs (voir send_account_question) qui
    # ouvrent Telegram vers l'admin sans repasser par ce handler.


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
