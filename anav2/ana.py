#coding=utf-8

from collections import deque
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import sqlite3 as base
import logging
import random

CONST_MAX_LEARN_MESSAGES_NUMBER = 8
CONST_MIN_ROBOT_MESSAGES_TO_ACCURACY_NUMBER = 1
version = '2.1'
mute = True

lastMessagesDictionnary = dict()
# lastMessages = deque([])

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Read key
key = open('key').read().splitlines()[0]
FATHER_ID = float(open('father').read().splitlines()[0])
print(FATHER_ID)

# Basic commands 
def start(bot, update):
    chat_id = update.message.chat_id
    initAna()
    message = 'Bonjour, je suis Ana'
    bot.sendMessage(chat_id, text=message)


def ana(bot, update):
    chat_id = update.message.chat_id
    mot = update.message.text
    message = analyzeLastChatMessage(mot, chat_id)
    bot.sendMessage(chat_id, text=message)


def updateAccuracyNumber(bot, update, args):
    chat_id = update.message.chat_id
    try:
        if update.message.chat_id == FATHER_ID:
            CONST_MIN_ROBOT_MESSAGES_TO_ACCURACY_NUMBER = float(args[0])
            message = "New accuracy number = " + str(CONST_MIN_ROBOT_MESSAGES_TO_ACCURACY_NUMBER)
        else:
            message = "You are not my father !"
    except (ValueError, IndexError):
        message = "Wrong syntax"
        pass  
    bot.sendMessage(chat_id, text=message)    

def mute(bot, update):
    chat_id = update.message.chat_id
    if update.message.chat_id == FATHER_ID:
        mute = True
        message = "Ana muted"
    else:
        message = "You are not my father !"
    bot.sendMessage(chat_id, text=message)

def unmute(bot, update):
    chat_id = update.message.chat_id
    if update.message.chat_id == FATHER_ID:
        mute = False
        message = "Ana unmuted"
    else:
        message = "You are not my father !"
    bot.sendMessage(chat_id, text=message)

# External Functions
def analyzeLastChatMessage(message: str, chat_id: str) -> str:
    # connect to db
    con = base.connect('ana.db')

    lastMessages = ifChatAlreadyExists(chat_id)
    insertNewLastMessageInList(message, lastMessages)
    learn(con, lastMessages)
    if mute:
        message = ""
    else:
        message = speakIfNeeded(con, lastMessages)
    return message


def initAna():
    # init db
    con = base.connect('ana.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS Messages(MessageId INTEGER PRIMARY KEY, Label VARCHAR(200))")
    cur.execute("CREATE TABLE IF NOT EXISTS Clues(ClueId INTEGER PRIMARY KEY, PotentialTriggerMessageId INT, WinningMessageId INT, Weight REAL, FOREIGN KEY (PotentialTriggerMessageId) REFERENCES Messages (MessageId), FOREIGN KEY (WinningMessageId) REFERENCES Messages (MessageId))")
    con.commit()


# Internal Functions
def insertNewLastMessageInList(message: str, lastMessages: deque):
    lastMessages.append(message)
    if len(lastMessages) > CONST_MAX_LEARN_MESSAGES_NUMBER:
        lastMessages.popleft()


def learn(con, lastMessages: deque):
    if len(lastMessages) < 2: # prevent from error
        return
    cur = con.cursor()
    winningMessageId = insertMessageInDb(con, lastMessages[len(lastMessages)-1])
    for (i, lastMessage) in enumerate(lastMessages):
        if i > len(lastMessages) - 2: # don't persist the last messages : Winning Message
            break
        messageId = insertMessageInDb(con, lastMessage)
        print(len(lastMessages)-i-1)
        print("TriggerMessage : " + lastMessage + ",WinningMessage : " + lastMessages[len(lastMessages)-1] + ", Weight : " + str(1/(len(lastMessages)-i-1)))
        cur.execute('INSERT INTO Clues (PotentialTriggerMessageId, WinningMessageId, Weight) VALUES (?,?,?)', [messageId, winningMessageId, 1/(len(lastMessages)-i-1)])
        con.commit()


def insertMessageInDb(con, message: str) -> int:
    cur = con.cursor()
    cur.execute('SELECT COUNT(MessageId), MessageId FROM Messages WHERE Label LIKE ?', [message])
    rep = cur.fetchone()
    numberOfThisMessageAlreadyInBase = rep[0]
    messageId = rep[1]
    if numberOfThisMessageAlreadyInBase == 0:
        cur.execute('INSERT INTO Messages (Label) VALUES (?)', [message])
        con.commit()
        messageId = cur.lastrowid
    return messageId


def speakIfNeeded(con, lastMessages: deque) -> str:
    cur = con.cursor()
    message = lastMessages[len(lastMessages)-1]
    cur.execute("SELECT WM.Label, SUM(C.Weight) AS SumPotentialTriggerMessagesWeight FROM Clues C INNER JOIN Messages PTM ON C.PotentialTriggerMessageId = PTM.MessageId INNER JOIN Messages WM ON C.WinningMessageId = WM.MessageId WHERE ( ? LIKE '%' || PTM.Label || '%' OR PTM.Label LIKE '%' || ? || '%' ) AND WM.Label LIKE '%__ __%' AND PTM.Label LIKE '%__ __%' GROUP BY C.WinningMessageId HAVING SumPotentialTriggerMessagesWeight > ? ORDER BY SumPotentialTriggerMessagesWeight DESC", [message, message, CONST_MIN_ROBOT_MESSAGES_TO_ACCURACY_NUMBER])
    result = cur.fetchall()
    if len(result) > 0 and result[0][1] >= CONST_MIN_ROBOT_MESSAGES_TO_ACCURACY_NUMBER:
        insertNewLastMessageInList(result[0][0], lastMessages)
        return getBestWeightedRandomMessage(result)
    return ""


def ifChatAlreadyExists(chat_id: str) -> deque:
    if(lastMessagesDictionnary.get(chat_id) == None):
        lastMessagesDictionnary[chat_id] = deque([])
    return lastMessagesDictionnary.get(chat_id)

def getBestWeightedRandomMessage(listWeightedMessages) -> str:
    weightSum = 0
    for(i, weightedMessage) in enumerate(listWeightedMessages):
        weightSum += weightedMessage[1]
    print
    rand = random.uniform(0, weightSum)
    weightSum = 0
    for(i, weightedMessage) in enumerate(listWeightedMessages):
        weightSum += weightedMessage[1]
        if weightSum >= rand:
            return weightedMessage[0]

########################################

updater = Updater(key)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('startAna', start))
dispatcher.add_handler(CommandHandler('updateAccuracyNumber', updateAccuracyNumber, pass_args=True))
dispatcher.add_handler(CommandHandler('mute', mute))
dispatcher.add_handler(CommandHandler('unmute', unmute))
dispatcher.add_handler(MessageHandler([Filters.text], ana))

updater.start_polling()
updater.idle()
