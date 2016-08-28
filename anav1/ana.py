#coding=utf-8

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from collections import deque
import sqlite3 as base
import logging

CONST_MAX_LEARN_MESSAGES_NUMBER = 8
CONST_MIN_ROBOT_MESSAGES_TO_ACCURACY_NUMBER = 2
version = '1.2'


lastMessages = deque([])

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Read key
key = open('./key').read().splitlines()[0]

# Basic commands 
def start(bot, update):
    chat_id = update.message.chat_id
    initAna()
    message = 'Bonjour, je suis Ana'
    bot.sendMessage(chat_id, text=message)


def ana(bot, update):
    chat_id = update.message.chat_id
    mot = update.message.text
    message = analyzeLastChatMessage(mot)
    bot.sendMessage(chat_id, text=message)

# Functions
def analyzeLastChatMessage(message: str) -> str:
    # connect to db
    con = base.connect('ana.db')
    cur = con.cursor()

    # stock last messages
    lastMessages.append(message)
    if(len(lastMessages)>CONST_MAX_LEARN_MESSAGES_NUMBER):
        lastMessages.popleft()

    # check if the message is a VictoryMessage
    cur.execute("SELECT VictoryMessageId, COUNT(VictoryMessageId) FROM VictoryMessages WHERE ? LIKE '%' || Label || '%'",  [str.lower(message)])
    result = cur.fetchone()
    if(result[1] > 0): # the message is a VictoryMessage
        cur.execute('INSERT INTO Messages (Label) VALUES (?)', [lastMessages[1]])
        con.commit()
        winningMessageId = cur.lastrowid
        for (i,lastMessage) in enumerate(lastMessages):
            if(i > len(lastMessages) - 3): # don't persist the two last messages : Winning Message and Victory Message
                break
            cur.execute('INSERT INTO Messages (Label) VALUES (?)', [lastMessage])
            con.commit()
            messageId = cur.lastrowid
            cur.execute('INSERT INTO Clues (PotentialTriggerMessageId, WinningMessageId, VictoryMessageId) VALUES (?,?,?)', [messageId, winningMessageId, result[0]])
            con.commit()

    # check if the message is a PotentialTriggerMessage
    cur.execute("SELECT WM.Label, COUNT(WM.Label) AS CountPotentialTriggerMessages FROM Clues C INNER JOIN Messages PTM ON C.PotentialTriggerMessageId = PTM.MessageId INNER JOIN Messages WM ON C.WinningMessageId = WM.MessageId WHERE PTM.Label=? GROUP BY WM.Label ORDER BY CountPotentialTriggerMessages DESC", [message])
    result = cur.fetchall()
    if(len(result) > 0 and result[0][1] >= CONST_MIN_ROBOT_MESSAGES_TO_ACCURACY_NUMBER):
        return result[0][0]

    return ""

def initAna():
    # init db
    con = base.connect('ana.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS Messages(MessageId INTEGER PRIMARY KEY, Label VARCHAR(200))")
    cur.execute("CREATE TABLE IF NOT EXISTS VictoryMessages(VictoryMessageId INTEGER PRIMARY KEY, Label VARCHAR(200))")
    cur.execute("CREATE TABLE IF NOT EXISTS Clues(ClueId INTEGER PRIMARY KEY, PotentialTriggerMessageId INT, WinningMessageId INT, VictoryMessageId INT, FOREIGN KEY (PotentialTriggerMessageId) REFERENCES Messages (MessageId), FOREIGN KEY (WinningMessageId) REFERENCES Messages (MessageId), FOREIGN KEY  (VictoryMessageId) REFERENCES VictoryMessages (VictoryMessageId))")
    con.commit()
    addAWinningMessage("gagné !")
    addAWinningMessage("haha")
    addAWinningMessage("race")
    addAWinningMessage("roti")
    addAWinningMessage("ui")
    addAWinningMessage("ana")


def addAWinningMessage(message: str):
    con = base.connect('ana.db')
    cur = con.cursor()
    cur.execute("SELECT COUNT(VictoryMessageId) FROM VictoryMessages WHERE Label=?", [str.lower(message)])
    if(cur.fetchone()[0] > 0):
        return
    cur.execute("INSERT INTO VictoryMessages (Label) VALUES (?)", [str.lower(message)])
    con.commit()


########################################

updater = Updater(key)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler('startAna', start))
dispatcher.add_handler(MessageHandler([Filters.text], ana))

updater.start_polling()
updater.idle()
