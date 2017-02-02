# --------------------------
#  Imports
# --------------------------

# Library imports
from collections import deque
import logging
import random
from telegram import ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Custom imports
import database


# --------------------------
#  Inits
# --------------------------

# Declare consts
CONST_NUMBER_SILENT_MESSAGES = 10

# Declare globals and init
global CONST_NUMBER_WORDS_MARKOV_STATE
CONST_NUMBER_WORDS_MARKOV_STATE = database.get_max_markov_degree()

global mute
mute = True

global silentMessages
silentMessages = 0

lastWordsDictionnary = dict()

key = open('keys/key').read().splitlines()[0]


# Set logging level
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


# --------------------------
#  Basic commands
# --------------------------

def start(bot, update):
    chat_id = update.message.chat_id
    init_ana()
    message = 'Bonjour, je suis Ana'
    bot.sendMessage(chat_id, text=message)


def reinit_ana(bot, update):
    chat_id = update.message.chat_id
    drop_db()
    init_ana()
    message = 'Db dropped'
    bot.sendMessage(chat_id, text=message)


def ana(bot, update):
    global mute
    global silentMessages

    chat_id = update.message.chat_id
    mot = update.message.text
    if update.message.reply_to_message is not None:
        if update.message.reply_to_message.from_user.name == '@An4bot':
            silentMessages = 0
    silentMessages -= 1

    message = analyze_last_chat_message(mot, chat_id, bot)

    if mute is False and silentMessages < 0:
        silentMessages = CONST_NUMBER_SILENT_MESSAGES
        # bot.sendMessage(chat_id, text=message)
        update.message.reply_text(message)


def do_mute(bot, update):
    chat_id = update.message.chat_id
    global mute
    mute = True
    message = "Ana muted"
    bot.sendMessage(chat_id, text=message)


def unmute(bot, update):
    chat_id = update.message.chat_id
    global mute
    mute = False
    message = "Ana unmuted"
    bot.sendMessage(chat_id, text=message)


def change_markov_degree(bot, update, args):
    global CONST_NUMBER_WORDS_MARKOV_STATE

    chat_id = update.message.chat_id
    new_degree = int(args[0])

    CONST_NUMBER_WORDS_MARKOV_STATE = new_degree
    max_const = database.get_max_markov_degree()
    if new_degree > max_const:
        database.clear_determined_word()
        database.clear_determining_word()
        database.clear_determining_state()
        charge_logs()
        database.set_max_markov_degree(CONST_NUMBER_WORDS_MARKOV_STATE)

    message = "Markov Degree Changed"
    bot.sendMessage(chat_id, text=message)


# --------------------------
#  External Functions
# --------------------------

def init_ana():
    database.init_db()


def drop_db():
    database.drop_db()


def analyze_last_chat_message(message: str, chat_id: str, bot) -> str:
    global mute
    global silentMessages

    message += " EOM"
    log_message(message, chat_id)
    last_words = if_chat_already_exists(chat_id)
    learn(message, chat_id, last_words)
    if mute is False and silentMessages < 0:
        bot.sendChatAction(chat_id=chat_id, action=ChatAction.TYPING)
        message = speak_if_needed(last_words)
        if message != ' ':
            log_message(message, chat_id)
            return message


# --------------------------
#  Internal Functions
# --------------------------

def log_message(message: str, chat_id: str):
    words = message.split()
    for word in words:
        database.save_log_word(int(chat_id), word)


def if_chat_already_exists(chat_id: str) -> deque:
    if lastWordsDictionnary.get(chat_id) is None:
        lastWordsDictionnary[chat_id] = deque([])
    return lastWordsDictionnary.get(chat_id)


def insert_new_last_word_in_list(word: str, lastWords: deque):
    lastWords.append(word)
    if len(lastWords) > CONST_NUMBER_WORDS_MARKOV_STATE:
        lastWords.popleft()


def learn(message, chat_id, lastWords):
    words = message.split()
    for word in words:
        learn_a_state(word, lastWords)
        insert_new_last_word_in_list(word, lastWords)


def learn_a_state(word, lastWords):
    if len(lastWords) == CONST_NUMBER_WORDS_MARKOV_STATE:
        determiningStateId = database.find_determining_state_id(lastWords)
        database.add_determined_word(word, determiningStateId)


def get_best_weighted_random_message(listWeightedMessages) -> str:
    weight_sum = 0
    for (i, weightedMessage) in enumerate(listWeightedMessages):
        weight_sum += weightedMessage[1]
    rand = random.uniform(0, weight_sum)
    weight_sum = 0
    for (i, weightedMessage) in enumerate(listWeightedMessages):
        weight_sum += weightedMessage[1]
        if weight_sum >= rand:
            return weightedMessage[0]


def speak_if_needed(lastWords) -> str:
    if len(lastWords) == CONST_NUMBER_WORDS_MARKOV_STATE:
        message = " "
        i = 0
        while True:
            words = database.find_determined_words(lastWords)
            word = ""
            if len(words) > 0:
                word = get_best_weighted_random_message(words)
                insert_new_last_word_in_list(word, lastWords)
            if word == 'EOM':
                break
            message = message + " " + word
            if len(words) == 0:  # i > 10 or
                break
            i += 1
        return message
    else:
        return ""


def charge_logs():
    log_words = database.get_log_words()

    for log_word in log_words:
        last_words = if_chat_already_exists(log_word.chatId)
        learn(log_word.label, log_word.chatId, last_words)


# --------------------------
#  Set up process
# --------------------------

updater = Updater(key)
dispatcher = updater.dispatcher

# dispatcher.add_handler(CommandHandler('startAna', start))
# dispatcher.add_handler(CommandHandler('drop_db', reinit_ana))
dispatcher.add_handler(CommandHandler('mute', do_mute))
dispatcher.add_handler(CommandHandler('unmute', unmute))
# dispatcher.add_handler(CommandHandler('changeMarkov', change_markov_degree, pass_args=True))
dispatcher.add_handler(MessageHandler(Filters.text, ana))

updater.start_polling()
updater.idle()
