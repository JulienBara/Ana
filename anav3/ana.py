# Library Imports
from collections import deque

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import logging
import random

# Custom Imports
import database
from models import DeterminedWord, DeterminingState, DeterminingWord, Word, LogWord

global CONST_NUMBER_WORDS_MARKOV_STATE
CONST_NUMBER_WORDS_MARKOV_STATE = database.getMaxMarkovDegree()
CONST_NUMBER_SILENT_MESSAGES = 10
version = '3.0'
global mute
mute = True
global silentMessages
silentMessages = 0

lastWordsDictionnary = dict()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


# Read key
key = open('key').read().splitlines()[0]


# Basic commands 
def start(bot, update):
    chat_id = update.message.chat_id
    initAna()
    message = 'Bonjour, je suis Ana'
    bot.sendMessage(chat_id, text=message)


def reinitAna(bot, update):
    chat_id = update.message.chat_id
    dropDb()
    initAna()
    message = 'Db dropped'
    bot.sendMessage(chat_id, text=message)


def ana(bot, update):
    global mute
    global silentMessages

    chat_id = update.message.chat_id
    mot = update.message.text
    silentMessages -= 1

    message = analyzeLastChatMessage(mot, chat_id)

    if mute == False and silentMessages < 0:
        silentMessages = CONST_NUMBER_SILENT_MESSAGES
        bot.sendMessage(chat_id, text=message)


def domute(bot, update):
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


def changeMarkovDegree(bot, update, args):
    global CONST_NUMBER_WORDS_MARKOV_STATE

    chat_id = update.message.chat_id
    new_degree = int(args[0])

    CONST_NUMBER_WORDS_MARKOV_STATE = new_degree
    maxConst = database.getMaxMarkovDegree()
    if new_degree > maxConst:
        database.clearDeterminedWord()
        database.clearDeterminingWord()
        database.clearDeterminingState()
        chargeLogs()
        database.setMaxMarkovDegree(CONST_NUMBER_WORDS_MARKOV_STATE)

    message = "Markov Degree Changed"
    bot.sendMessage(chat_id, text=message)


# External Functions
def initAna():
    database.initDb()


def dropDb():
    database.dropDb()


def analyzeLastChatMessage(message: str, chat_id: str) -> str:
    global mute
    global silentMessages

    message += " EOM"
    logMessage(message, chat_id)
    lastWords = ifChatAlreadyExists(chat_id)
    learn(message, chat_id, lastWords)
    if mute == False and silentMessages < 0:
        message = speakIfNeeded(lastWords)
        if message != ' ':
            logMessage(message, chat_id)
            return message


# Internal Functions
def logMessage(message: str, chat_id: str):
    words = message.split()
    for word in words:
        loggedWord = LogWord(int(chat_id), word)
        database.saveLogWord(loggedWord)


def ifChatAlreadyExists(chat_id: str) -> deque:
    if lastWordsDictionnary.get(chat_id) == None:
        lastWordsDictionnary[chat_id] = deque([])
    return lastWordsDictionnary.get(chat_id)


def insertNewLastWordInList(word: str, lastWords: deque):
    lastWords.append(word)
    if len(lastWords) > CONST_NUMBER_WORDS_MARKOV_STATE:
        lastWords.popleft()


def learn(message, chat_id, lastWords):
    words = message.split()
    for word in words:
        learnAState(word, lastWords)
        insertNewLastWordInList(word, lastWords)


def learnAState(word, lastWords):
    if len(lastWords) == CONST_NUMBER_WORDS_MARKOV_STATE:
        determiningStateId = database.findDeterminingStateId(lastWords)
        database.addDeterminedWord(word, determiningStateId)    


def getBestWeightedRandomMessage(listWeightedMessages) -> str:
    weightSum = 0
    for(i, weightedMessage) in enumerate(listWeightedMessages):
        weightSum += weightedMessage[1]
    rand = random.uniform(0, weightSum)
    weightSum = 0
    for(i, weightedMessage) in enumerate(listWeightedMessages):
        weightSum += weightedMessage[1]
        if weightSum >= rand:
            return weightedMessage[0]


def speakIfNeeded(lastWords) -> str:
    if len(lastWords) == CONST_NUMBER_WORDS_MARKOV_STATE:
        message = " "
        i = 0
        while True:
            words = database.findDeterminedWords(lastWords)
            word = ""
            if len(words) > 0:
                word = getBestWeightedRandomMessage(words)
                insertNewLastWordInList(word, lastWords)                       
            if word == 'EOM':
                break
            message = message + " " + word
            if len(words) == 0: #i > 10 or 
                break
            i = i + 1
        return message
    else:
        return ""

def chargeLogs():
    logwords = database.getLogWords()

    for logword in logwords:
        lastWords = ifChatAlreadyExists(logword.chatId)
        learn(logword.label, logword.chatId, lastWords)



    


########################################


updater = Updater(key)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('startAna', start))
dispatcher.add_handler(CommandHandler('dropDb', reinitAna))
dispatcher.add_handler(CommandHandler('mute', domute))
dispatcher.add_handler(CommandHandler('unmute', unmute))
dispatcher.add_handler(CommandHandler('changeMarkov', changeMarkovDegree, pass_args=True))
dispatcher.add_handler(MessageHandler(Filters.text, ana))

updater.start_polling()
updater.idle()