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
    if db_session.query(Word).filter_by(label = label).count() == 0:
        newWord = Word(label = label)
        db_session.add(newWord)
        db_session.commit()
    return db_session.query(Word).filter_by(label = label).first().wordId


def findDeterminingState(lastWords):
    from models import DeterminingWord, DeterminingState
    query = select([determiningState]).join(Word)
    n = len(lastWords)
    for (i,word) in enumerate(lastWords):
        query = query.where(and_(label = word, order = n - i - 1))
    result = db_session.execute(query)

    if result is not None:
        determiningState = DeterminingState()
        db_session.add(determiningState)
        db_session.commit()
        for (i,word) in enumerate(lastWords):
            determiningWord = DeterminingWord(word, determiningState.determiningStateId, n - i - 1)
            db_session.add(determiningWord)
            db_session.commit()
        return determiningState.determiningStateId

    return result.determiningStateId


    
def saveLogWord(logWord):
    db_session.add(logWord)
    db_session.commit()
