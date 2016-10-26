from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

# from models import DeterminedWord, DeterminingState, DeterminingWord, Word, LogWord

engine = create_engine('sqlite:///./teste.db', echo=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def initDb():
    # # import all modules here that might define models so that
    # # they will be registered properly on the metadata.  Otherwise
    # # you will have to import them first before calling init_db()
    from models import DeterminedWord, DeterminingState, DeterminingWord, Word, LogWord
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # # Create the fixtures
    # engineering = Department(name='Engineering')
    # db_session.add(engineering)
    # hr = Department(name='Human Resources')
    # db_session.add(hr)

    # manager = Role(name='manager')
    # db_session.add(manager)
    # engineer = Role(name='engineer')
    # db_session.add(engineer)

    # peter = Employee(name='Peter', department=engineering, role=engineer)
    # db_session.add(peter)
    # roy = Employee(name='Roy', department=engineering, role=engineer)
    # db_session.add(roy)
    # tracy = Employee(name='Tracy', department=hr, role=manager)

    # # postgresql specific dialects tests
    # # tracy.articles = [1, 2, 3, 4]
    # # tracy.json_data = {"test_json": "test_json"}
    # # tracy.jsonb_data = {"test_jsonb": "test_jsonb"}
    # # tracy.hstore_data = {"test_hstore": "test_hstore"}

    # db_session.add(tracy)
    # db_session.commit()

def dropDb():
    from models import DeterminedWord, DeterminingState, DeterminingWord, Word, LogWord
    Base.metadata.drop_all(bind=engine)


def getWordIdByLabel(label: str) -> int:
    from models import Word
    query = db_session.query(Word).filter_by(label = label)
    if query.count() == 0:
        # to close query
        result = db_session.execute(query)

        newWord = Word(label = label)
        db_session.add(newWord)
        db_session.commit()
        return newWord.wordId
    wordId = query.first().wordId
    # to close query
    result = db_session.execute(query)
    return wordId

#TODO HERE. The query try to matc every words and every orders at the same time
def findDeterminingStateId(lastWords) -> int:
    from models import DeterminingWord, DeterminingState, Word
    query = db_session.query(DeterminingState.determiningStateId)
    for (i,word) in enumerate(lastWords):
        query = query.intersect(db_session.query(DeterminingState).join(DeterminingWord).join(Word).filter(Word.label == word, DeterminingWord.order == i).group_by(DeterminingState.determiningStateId))
        # queryTemp = db_session.query(DeterminingState).join(DeterminingWord).join(Word).filter(Word.label == word, DeterminingWord.order == i).group_by(DeterminingState.determiningStateId)
        # resultTemp = db_session.execute(queryTemp)
    
    if query.count() == 0:
        # to close query
        result = db_session.execute(query)

        determiningState = DeterminingState()
        db_session.add(determiningState)
        db_session.flush()
        db_session.commit()
        for (i,word) in enumerate(lastWords):
            determiningWord = DeterminingWord(word, determiningState.determiningStateId, i)
            db_session.add(determiningWord)
            db_session.flush()
            db_session.commit()
        return determiningState.determiningStateId

    number = query.first().determiningStateId
    # to close query
    result = db_session.execute(query)
    return number

    
def saveLogWord(logWord):
    db_session.add(logWord)
    db_session.commit()


def addDeterminedWord(word, determiningStateId):
    from models import DeterminingWord, DeterminedWord
    wordId = getWordIdByLabel(word)
    if db_session.query(DeterminedWord).filter_by(determiningStateId = determiningStateId).filter_by(wordId = wordId).count() == 0:
        determinedWord = DeterminedWord(determiningStateId = determiningStateId, wordId = wordId, number = 0, anger = 0, disgust = 0, fear = 0, joy = 0, sadness = 0)
        db_session.add(determinedWord)
        db_session.commit()
    else:
        determinedWord = db_session.query(DeterminedWord).filter_by(determiningStateId = determiningStateId).filter_by(wordId = wordId).first()
    determinedWord.number = determinedWord.number + 1
    db_session.commit()

def findDeterminedWords(lastWords):
    from models import DeterminedWord, Word, DeterminingState
    determiningStateId = findDeterminingStateId(lastWords)
    query = db_session.query(DeterminedWord).join(Word).join(DeterminingState).add_columns(Word.label, DeterminedWord.number).filter_by(determiningStateId = determiningStateId)
    pairs = []
    if query.count() > 0:
        for word in list(query.all()):
            pairs.append((word.label, word.number))
    # to close query
    result = db_session.execute(query)
    return pairs
