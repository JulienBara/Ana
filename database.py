from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

# from models import DeterminedWord, DeterminingState, DeterminingWord, Word, LogWord

engine = create_engine('sqlite:///./teste.db', echo=True)
# engine = create_engine('sqlite:///./teste.db', echo=False)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def initDb():
    from models import DeterminedWord, DeterminingState, DeterminingWord, Word, LogWord
    # Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def dropDb():
    from models import DeterminedWord, DeterminingState, DeterminingWord, Word, LogWord
    Base.metadata.drop_all(bind=engine)


def clearDeterminedWord():
    from models import DeterminedWord
    DeterminedWord.__table__.drop(engine)
    DeterminedWord.__table__.create(engine)


def clearDeterminingWord():
    from models import DeterminingWord
    DeterminingWord.__table__.drop(engine)
    DeterminingWord.__table__.create(engine)

def clearDeterminingState():
    from models import DeterminingState
    DeterminingState.__table__.drop(engine)
    DeterminingState.__table__.create(engine)


def get_word_id_by_label(label: str) -> int:
    from models import Word
    query = db_session.query(Word).filter_by(label=label)
    if query.count() == 0:
        new_word = Word(label=label)
        db_session.add(new_word)
        db_session.commit()
        return new_word.wordId
    word_id = query.first().wordId
    return word_id


def find_determining_state_id(last_words) -> int:
    from models import DeterminingWord, DeterminingState, Word

    # get Markov's order
    n = len(last_words)

    # forge query
    query = db_session.query(DeterminingState.determiningStateId)
    for (i, word) in enumerate(last_words):
        query = query.intersect(db_session
                                .query(DeterminingState)
                                .join(DeterminingWord)
                                .join(Word)
                                .filter(Word.label == word, DeterminingWord.order == n - i - 1)
                                .group_by(DeterminingState.determiningStateId))

    # if doesn't exist add
    if query.count() == 0:
        determining_state = DeterminingState()
        db_session.add(determining_state)
        for (i, word) in enumerate(last_words):
            determining_word = DeterminingWord(word, n - i - 1)
            determining_state.determiningWords.append(determining_word)
            db_session.add(determining_word)
        db_session.commit()
        determining_state_id = determining_state.determiningStateId
        return determining_state_id

    # else get the id
    determining_state_id = query.first().determiningStateId
    return determining_state_id

    
def save_log_word(chat_id: int, word_label: str):
    from models import LogWord

    logged_word = LogWord(int(chat_id), word_label)
    db_session.add(logged_word)
    db_session.commit()


def get_log_words():
    from models import LogWord, Word

    log_words = db_session\
        .query(LogWord)\
        .join(Word)\
        .add_columns(LogWord.chatId, Word.label)

    ss = []

    for (i, log_word) in enumerate(log_words):
        ss.append(log_word)

    return ss


def add_determined_word(word_label: str, determiningStateId: int):
    from models import DeterminedWord

    word_id = get_word_id_by_label(word_label)

    query = db_session\
        .query(DeterminedWord)\
        .filter_by(determiningStateId=determiningStateId)\
        .filter_by(wordId=word_id)\

    if query.count() == 0:
        determined_word = DeterminedWord(
            determiningStateId=determiningStateId,
            wordId=word_id,
            number=1,
            anger=0,
            disgust=0,
            fear=0,
            joy=0,
            sadness=0)
        db_session.add(determined_word)
        db_session.commit()

    else:
        determined_word = query.first()
        determined_word.number += 1
        db_session.commit()


def find_determined_words(lastWords):
    from models import DeterminedWord, Word, DeterminingState

    determining_state_id = find_determining_state_id(lastWords)

    query = db_session\
        .query(DeterminedWord)\
        .join(Word)\
        .join(DeterminingState)\
        .add_columns(Word.label, DeterminedWord.number)\
        .filter_by(determiningStateId=determining_state_id)

    pairs = []
    if query.count() > 0:
        for word in list(query.all()):
            pairs.append((word.label, word.number))

    return pairs

def getMaxMarkovDegree():
    from models import MaxMarkovDegree
    query = db_session.query(MaxMarkovDegree)
    degree = query.first().maxMarkovDegree
    return degree

def setMaxMarkovDegree(newMaxMarkovDegree):
    from models import MaxMarkovDegree
    query = db_session.query(MaxMarkovDegree).first()
    query.maxMarkovDegree = newMaxMarkovDegree
    db_session.commit()


