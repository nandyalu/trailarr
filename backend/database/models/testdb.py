# no cov
from contextlib import contextmanager
from datetime import datetime
import time
from typing import Optional


from sqlmodel import Field, Session, SQLModel, create_engine, select


def get_current_time():
    return datetime.now()


def get_current_year():
    return datetime.now().year


class HeroBase(SQLModel):
    name: str = Field()
    secret_name: str = Field()
    age: Optional[int] = None
    year: int = Field(default_factory=get_current_year)
    aid: int


class Hero(HeroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    added_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)


class HeroCreate(HeroBase):
    ext: str = Field(default="ext")
    pass


class HeroRead(HeroBase):
    id: int
    added_at: datetime
    updated_at: datetime


class HeroUpdate(SQLModel):
    name: Optional[str] = None
    secret_name: Optional[str] = None
    age: Optional[int] = None
    year: Optional[int] = None
    aid: Optional[int] = None


sqlite_file_name = "testdatabase.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


# C = TypeVar("C", bound=SQLModel)
# R = TypeVar("R", bound=SQLModel)
# U = TypeVar("U", bound=SQLModel)
# D = TypeVar("D", bound=SQLModel)


class DatabaseHandler2[D: Hero, C: HeroCreate, R: SQLModel, U: SQLModel]:

    __db_model: type[D]
    create_model: type[C]
    __read_model: type[R]
    update_model: type[U]

    def __init__(self, session: Session, db_model: type[D], read_model: type[R]):
        self.session = session
        self.__db_model = db_model
        self.__read_model = read_model
        if isinstance(db_model, Hero):
            assert isinstance(read_model, HeroRead)
            self.update_model = HeroUpdate

    def insert(self, item: C) -> R:
        db_media = self.__db_model.model_validate(item)
        self.session.add(db_media)
        self.session.commit()
        media_read = self.__read_model.model_validate(db_media)
        return media_read

    def delete(self, media_id: int):
        db_media = self.session.get(self.__db_model, media_id)
        if not db_media:
            # raise ValueError(f"Media with id {media_id} not found")
            return False
        self.session.delete(db_media)
        self.session.commit()
        return True

    def read(self, id: int) -> R | None:
        statement = select(self.__db_model).where(self.__db_model.id == id)
        result = self.session.exec(statement).one_or_none()
        if not result:
            return None
        media_read = self.__read_model.model_validate(result)
        return media_read

    def update(self, media_id: int, media_update: U) -> R:
        db_media = self.session.get(self.__db_model, media_id)
        if not db_media:
            raise ValueError(f"Media with id {media_id} not found")
        media_update_data = media_update.model_dump(exclude_unset=True)
        db_media.sqlmodel_update(media_update_data)
        self.session.commit()
        media_read = self.__read_model.model_validate(db_media)
        return media_read


class HeroDatabaseHandler(DatabaseHandler2[Hero, HeroCreate, HeroRead, HeroUpdate]):

    def __init__(self, session: Session):
        super().__init__(session, db_model=Hero, read_model=HeroRead)


def read_if_exists(session: Session, aid: int):
    statement = select(Hero).where(Hero.aid == aid)
    db_hero = session.exec(statement).one_or_none()
    return db_hero


def create_bulk(heroes: list[HeroCreate]):
    start = time.perf_counter()
    db_heroes: list[tuple[Hero, bool]] = []
    return_data: list[tuple[HeroRead, bool]] = []
    with get_session() as session:
        for hero in heroes:
            db_hero = read_if_exists(session, hero.aid)
            if db_hero:
                hero_update_data = hero.model_dump(exclude_unset=True)
                db_hero.sqlmodel_update(hero_update_data)
                created = False  # Hero was updated, not created
                if session.is_modified(db_hero):
                    db_hero.updated_at = datetime.now()
            else:
                db_hero = Hero.model_validate(hero)
                created = True  # Hero was created
                session.add(db_hero)
            db_heroes.append((db_hero, created))
        session.commit()
        for db_hero, created in db_heroes:
            hero_read = HeroRead.model_validate(db_hero)
            return_data.append((hero_read, created))
    end = time.perf_counter()
    print(f"Time taken BULK: {end - start:.4f} seconds")
    return return_data


def create_one(hero: HeroCreate):
    with get_session() as session:
        db_hero = read_if_exists(session, hero.aid)
        if db_hero:
            hero_update_data = hero.model_dump(exclude_unset=True)
            db_hero.sqlmodel_update(hero_update_data)
            _updated = True
        else:
            db_hero = Hero.model_validate(hero)
            _updated = False
        session.add(db_hero)
        session.commit()
        session.refresh(db_hero)
        hero_read = HeroRead.model_validate(db_hero)
        return hero_read, _updated


def get_heroes(n: int, start=0):
    heroes: list[HeroCreate] = []
    for i in range(start, start + n):
        hero = HeroCreate(name=f"Hero {i}", secret_name=f"Secret {i}_{start}", aid=i)
        heroes.append(hero)
    return heroes


def create_heroes():
    n = 5
    heroes = get_heroes(n)
    heroes.extend(get_heroes(n, 1000))
    with get_session() as session:
        db_handler = HeroDatabaseHandler(session)
        db_handler.__read_model
        for hero in heroes:
            print(db_handler.insert(hero))
        for i in range(1, 10):
            print(db_handler.read(i))
        for i in range(1, 10):
            update = HeroUpdate(
                name=f"Hero {i}_Updated", secret_name=f"Secret {i}_Updated"
            )
            print(db_handler.update(i, update))
        for i in range(1, 10):
            print(db_handler.delete(i))

    # create_bulk(heroes)
    # db_heroes = create_bulk(heroes)
    # print(db_heroes)
    # start_n = 100 + n
    # heroes2 = get_heroes(n, start_n)
    # heroes2.extend(get_heroes(n, start_n))
    # start = time.perf_counter()
    # for hero in heroes2:
    #     create_one(hero)
    #     # db_hero, updated = create_one(hero)
    #     # print(db_hero)
    #     # print(f"Updated? {updated}")
    # end = time.perf_counter()
    # print(f"Time taken Singles: {end - start:.4f} seconds")
    # hero = HeroCreate(name="Hero 1", secret_name="Secret 1", aid=1)
    # db_hero, updated = create_one(hero)
    # print(db_hero)
    # print(f"Updated? {updated}")
    # for hero in heroes:
    #     create_one(hero)


# def create_heroes(session=get_session):
#     hero_1 = HeroCreate(name="Deadpond", secret_name="Dive Wilson")
#     hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
#     hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)
#     # hero_31 = Hero(id=3, name="Rusty", secret_name="Tommy", age=50)

#     print("Before interacting with the database")
#     print("Hero 1:", hero_1)
#     print("Hero 2:", hero_2)
#     print("Hero 3:", hero_3)

#     with get_session() as session:
#         session.add(hero_1)
#         session.add(hero_2)
#         session.commit()

#         session.add(hero_3)
#         session.commit()

#     # with Session(engine) as session:
#     #     session.add(hero_1)
#     #     session.add(hero_2)
#     #     # session.add(hero_3)
#     #     # db_hero = Hero.model_validate(hero_3)

#     #     print("After adding to the session")
#     #     print("Hero 1:", hero_1)
#     #     print("Hero 2:", hero_2)
#     #     print("Hero 3:", hero_3)

#     #     session.commit()

#     #     print("After committing the session")
#     #     print(">>>without reading from the database")
#     #     print(f">>>Model dump of hero_31: {hero_31.model_dump()}")
#     #     session.bulk_update_mappings(Hero, [hero_31.model_dump(exclude_unset=True)])
#     #     session.commit()
#     #     print(">>>After bulk insert")
#     # print("Read from database")
#     # res = session.get(Hero, hero_31.id)
#     # if res:
#     #     print("Hero 31:", res)
#     #     res.name = hero_31.name
#     #     res.secret_name = hero_31.secret_name
#     #     res.age = hero_31.age
#     #     session.add(res)
#     #     session.commit()
#     #     print("After committing the session")
#     #     session.refresh(res)
#     #     print("Hero 3:", res)
#     # else:
#     #     print("Hero 31 not found")

#     # print("Hero 1:", hero_1)
#     # print("Hero 2:", hero_2)
#     # print("Hero 3:", hero_3)

#     # print("After committing the session, show IDs")
#     # print("Hero 1 ID:", hero_1.id)
#     # print("Hero 2 ID:", hero_2.id)
#     # print("Hero 3 ID:", hero_3.id)

#     # print("After committing the session, show names")
#     # print("Hero 1 name:", hero_1.name)
#     # print("Hero 2 name:", hero_2.name)
#     # print("Hero 3 name:", hero_3.name)

#     # session.refresh(hero_1)
#     # session.refresh(hero_2)
#     # session.refresh(hero_3)

#     # print("After refreshing the heroes")
#     # print("Hero 1:", hero_1)
#     # print("Hero 2:", hero_2)
#     # print("Hero 3:", hero_3)

#     print("After the session closes")
#     print("Hero 1:", hero_1)
#     print("Hero 2:", hero_2)
#     print("Hero 3:", hero_3)
#     # print("Hero 31:", hero_31)


def main():
    create_db_and_tables()
    create_heroes()


if __name__ == "__main__":
    main()
