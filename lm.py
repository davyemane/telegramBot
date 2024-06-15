import os
from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import requests
from flask import Flask, request
import logging

app = Flask(__name__)

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token du bot Telegram (remplacez par votre token)
TELEGRAM_TOKEN = "7237609520:AAHZ_0kFz1au-nTeCYZfnJspJ6lOAqpkoNI"

# URL de votre API déployée sur Render
API_URL = "https://lm1-paxp.onrender.com/dictionnaire/translate/"

# États pour le gestionnaire de conversation
CHOOSE_LANGUAGE, TRANSLATE_TEXT = range(2)

# Dictionnaire des langues disponibles
LANGUAGES = {
    'Anglais': 'en',
    'Français': 'fr',
    'Lingala': 'ln',
    'Haoussa': 'ha'
    # Ajoutez d'autres langues selon vos besoins
}

# Initialisation du bot Telegram
bot = Bot(token=TELEGRAM_TOKEN)
updater = Updater(bot=bot, use_context=True)

# Fonction pour annuler l'opération
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Opération annulée.')
    return ConversationHandler.END

# Fonction pour changer la langue cible
def change_language(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [[lang for lang in LANGUAGES.keys()]]
    update.message.reply_text(
        "Veuillez choisir la nouvelle langue cible :",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSE_LANGUAGE

# Fonction pour démarrer la conversation
def start(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [[lang for lang in LANGUAGES.keys()]]
    update.message.reply_text(
        "Bonjour je m'appelle LM ! Je suis une intelligence artificielle de traduction des langues maternelles africaines. "
        "Envoyez-moi votre texte et je le traduirai dans la langue choisie.\n\n"
        "Veuillez choisir la langue cible :",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSE_LANGUAGE

# Fonction pour choisir la langue cible
def choose_language(update: Update, context: CallbackContext) -> int:
    target_language = update.message.text
    if target_language in LANGUAGES:
        context.user_data['target_lang'] = LANGUAGES[target_language]
        update.message.reply_text(f'Langue choisie: {target_language}. Maintenant, envoyez-moi le texte que vous souhaitez traduire.')
        return TRANSLATE_TEXT
    else:
        update.message.reply_text('Langue non reconnue. Veuillez choisir une langue de la liste.')
        return CHOOSE_LANGUAGE

# Fonction pour traduire le texte
def translate_text(update: Update, context: CallbackContext) -> int:
    if 'target_lang' not in context.user_data:
        update.message.reply_text('Veuillez d\'abord choisir une langue en utilisant /start.')
        return CHOOSE_LANGUAGE

    message = update.message.text
    target_lang = context.user_data['target_lang']
    params = {
        'text': message,
        'source_lang': 'fr',  # Vous pouvez personnaliser cette valeur
        'target_lang': target_lang
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()  # Vérifie si la requête a réussi
        translated_text = response.json().get('translated_text', 'Désolé, la traduction a échoué.')
    except requests.RequestException as e:
        logger.error(f"Erreur de requête: {e}")
        translated_text = 'Désolé, une erreur est survenue lors de la traduction.'

    update.message.reply_text(translated_text)
    return TRANSLATE_TEXT

# Gestionnaire de conversation
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CHOOSE_LANGUAGE: [MessageHandler(Filters.text & ~Filters.command, choose_language)],
        TRANSLATE_TEXT: [MessageHandler(Filters.text & ~Filters.command, translate_text)],
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('change_language', change_language)]
)

# Configuration des gestionnaires de commandes et de messages
dispatcher = updater.dispatcher
dispatcher.add_handler(conv_handler)
dispatcher.add_handler(CommandHandler('change_language', change_language))

# Fonction pour recevoir les mises à jour de Telegram via webhook
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
