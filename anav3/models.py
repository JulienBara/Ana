from sqlalchemy import Column, Integer, Unicode, UnicodeText, String, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, relationship

from database import Base
import database

class DeterminedWord(Base):
    __tablename__ = 'determinedWords'
    determinedWordId = Column(Integer, primary_key=True) #PK
    determiningStateId = Column(Integer, ForeignKey('determiningStates.determiningStateId')) #FK
    wordId = Column(Integer, ForeignKey('words.wordId')) #FK
    number = Column(Integer) 
    anger = Column(Float)
    digust = Column(Float)
    fear = Column(Float)
    joy = Column(Float)
    sadness = Column(Float)

    # # word = relationship("Word", back_populates="determinedWords")
    # # determiningState = relationship("DeterminingState", back_populates="determinedWords")

    def __init__(self, determiningStateId, word, number, anger, disgust, fear, joy, sadness):
        self.determiningStateId = determiningStateId
        self.wordId = database.getWordIdByLabel(word)
        self.number += number
        self.anger += anger
        self.disgust += disgust
        self.fear += fear
        self.joy = joy
        self.sadness = sadness


class DeterminingState(Base):
    __tablename__ = 'determiningStates'
    determiningStateId = Column(Integer, primary_key=True) #PK

    # determinedWords = relationship("DeterminedWord", order_by=DeterminedWord.determinedWordId, back_populates="determiningState")
    # determiningWords = relationship("DeterminingdWord", order_by=DeterminingWord.determiningdWordId, back_populates="word")

    # def __init__(self):


class DeterminingWord(Base):
    __tablename__ = 'determiningWords'
    determiningWordId = Column(Integer, primary_key=True) #PK
    wordId = Column(Integer, ForeignKey('words.wordId')) #FK
    determiningStateId = Column(Integer) #FK
    order = Column(Integer)

    # # word = relationship("Word", back_populates="determiningWords")
    #determiningState = relationship("DeterminingState", back_populates="determiningWord")

    def __init__(self, word, determiningStateId, order):
        self.wordId = database.getWordIdByLabel(word)
        self.determiningStateId = determiningStateId
        self.order = order


class Word(Base):
    __tablename__ = 'words'
    wordId = Column(Integer, primary_key=True) #PK
    label = Column(String) 

    # # determinedWords = relationship("DeterminedWord", order_by=DeterminedWord.determinedWordId, back_populates="word")
    # # determiningWords = relationship("DeterminingdWord", order_by=DeterminedWord.determiningdWordId, back_populates="word")

    def __init__(self, label):
        self.label = label
    

class LogWord(Base):
    __tablename__ = 'logWords'
    logWordId = Column(Integer, primary_key=True) #PK
    chatId = Column(Integer)
    wordId = Column(Integer) 

    def __init__(self, chatId, word):
        self.chatId = chatId
        self.wordId = database.getWordIdByLabel(word)
