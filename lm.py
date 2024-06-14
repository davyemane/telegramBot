import os
from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import requests
from flask import Flask

app = Flask(__name__)

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
    # Ajoutez d'autres langues selon vos besoins
}

def start(update: Update, context: CallbackContext) -> None:
    reply_keyboard = [[lang for lang in LANGUAGES.keys()]]
    update.message.reply_text(
        "Bonjour je m'appelle LM ! Je suis une intelligence artificielle de traduction des langues maternelles africaines. "
        "Envoyez-moi votre texte et je le traduirai dans la langue choisie.\n\n"
        "Veuillez choisir la langue cible :",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return CHOOSE_LANGUAGE

def choose_language(update: Update, context: CallbackContext) -> None:
    target_language = update.message.text
    if target_language in LANGUAGES:
        context.user_data['target_lang'] = LANGUAGES[target_language]
        update.message.reply_text('Merci. Maintenant, envoyez-moi le texte que vous souhaitez traduire.')
        return TRANSLATE_TEXT
    else:
        update.message.reply_text('Langue non reconnue. Veuillez choisir une langue de la liste.')
        return CHOOSE_LANGUAGE

def translate_text(update: Update, context: CallbackContext) -> None:
    message = update.message.text
    target_lang = context.user_data['target_lang']
    params = {
        'text': message,
        'source_lang': 'fr',  # Vous pouvez personnaliser cette valeur
        'target_lang': target_lang
    }
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        translated_text = response.json().get('translated_text', 'Désolé, la traduction a échoué.')
    else:
        translated_text = 'Désolé, la traduction a échoué.'
    update.message.reply_text(translated_text)
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Opération annulée.')
    return ConversationHandler.END

def main() -> None:
    # Initialisation du bot Telegram
    bot = Bot(token=TELEGRAM_TOKEN)
    updater = Updater(bot=bot, use_context=True)

    # Gestionnaire de conversation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_LANGUAGE: [MessageHandler(Filters.text & ~Filters.command, choose_language)],
            TRANSLATE_TEXT: [MessageHandler(Filters.text & ~Filters.command, translate_text)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Configuration des gestionnaires de commandes et de messages
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conv_handler)

    # Démarrage du bot en mode non-bloquant
    updater.start_polling()
    updater.idle()

@app.route('/')
def index():
    return "Bot Telegram est en cours d'exécution."

if __name__ == '__main__':
    from threading import Thread
    # Lancer le bot Telegram dans un thread séparé
    Thread(target=main).start()
    # Lancer le serveur Flask
    app.run(host='0.0.0.0', port=5000)
