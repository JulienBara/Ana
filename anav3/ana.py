# Library Imports
from collections import deque

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import logging

# Custom Imports
import database
from models import DeterminedWord, DeterminingState, DeterminingWord, Word, LogWord

CONST_NUMBER_WORDS_MARKOV_STATE = 8
version = '3.0'

lastWordsDictionnary = dict()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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
    chat_id = update.message.chat_id
    mot = update.message.text
    message = analyzeLastChatMessage(mot, chat_id)
    bot.sendMessage(chat_id, text=message)


# External Functions
def initAna():
    database.initDb()


def dropDb():
    database.dropDb()


def analyzeLastChatMessage(message: str, chat_id: str) -> str:
    logMessage(message, chat_id)
    lastWords = ifChatAlreadyExists(chat_id)
    learn(message, chat_id, lastWords)
    message = speakIfNeeded(lastWords)
    # logMessage(message, chat_id)
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


def speakIfNeeded(lastWords) -> str:
    if len(lastWords) == CONST_NUMBER_WORDS_MARKOV_STATE:
        message = "Reponse :"
        for i in range(0,10):
            words = database.findDeterminedWords(lastWords)
            if(len(words) > 0):
                message += words.index(0)
        return message
    else:
        return "" 
    


########################################


updater = Updater(key)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('startAna', start))
dispatcher.add_handler(CommandHandler('dropDb', reinitAna))
dispatcher.add_handler(MessageHandler([Filters.text], ana))

updater.start_polling()
updater.idle()