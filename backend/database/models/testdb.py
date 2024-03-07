# no cov
from contextlib import contextmanager
from datetime import datetime
from typing import Optional


from sqlmodel import Field, Session, SQLModel, create_engine


def get_current_time():
    return datetime.now()


def get_current_year():
    return datetime.now().year


class HeroBase(SQLModel):
    name: str = Field()
    secret_name: str = Field()
    age: Optional[int] = None
    year: int = Field(default_factory=get_current_year)


class Hero(HeroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    added_at: datetime = Field(default_factory=get_current_time)


class HeroCreate(HeroBase):
    ext: str = Field(default="ext")
    pass


class HeroRead(HeroBase):
    id: int
    added_at: datetime


sqlite_file_name = "testdatabase.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def create_heroes(session=get_session):
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    hero_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
    hero_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)
    # hero_31 = Hero(id=3, name="Rusty", secret_name="Tommy", age=50)

    print("Before interacting with the database")
    print("Hero 1:", hero_1)
    print("Hero 2:", hero_2)
    print("Hero 3:", hero_3)

    with get_session() as session:
        session.add(hero_1)
        session.add(hero_2)
        session.commit()

        session.add(hero_3)
        session.commit()

    # with Session(engine) as session:
    #     session.add(hero_1)
    #     session.add(hero_2)
    #     # session.add(hero_3)
    #     # db_hero = Hero.model_validate(hero_3)

    #     print("After adding to the session")
    #     print("Hero 1:", hero_1)
    #     print("Hero 2:", hero_2)
    #     print("Hero 3:", hero_3)

    #     session.commit()

    #     print("After committing the session")
    #     print(">>>without reading from the database")
    #     print(f">>>Model dump of hero_31: {hero_31.model_dump()}")
    #     session.bulk_update_mappings(Hero, [hero_31.model_dump(exclude_unset=True)])
    #     session.commit()
    #     print(">>>After bulk insert")
    # print("Read from database")
    # res = session.get(Hero, hero_31.id)
    # if res:
    #     print("Hero 31:", res)
    #     res.name = hero_31.name
    #     res.secret_name = hero_31.secret_name
    #     res.age = hero_31.age
    #     session.add(res)
    #     session.commit()
    #     print("After committing the session")
    #     session.refresh(res)
    #     print("Hero 3:", res)
    # else:
    #     print("Hero 31 not found")

    # print("Hero 1:", hero_1)
    # print("Hero 2:", hero_2)
    # print("Hero 3:", hero_3)

    # print("After committing the session, show IDs")
    # print("Hero 1 ID:", hero_1.id)
    # print("Hero 2 ID:", hero_2.id)
    # print("Hero 3 ID:", hero_3.id)

    # print("After committing the session, show names")
    # print("Hero 1 name:", hero_1.name)
    # print("Hero 2 name:", hero_2.name)
    # print("Hero 3 name:", hero_3.name)

    # session.refresh(hero_1)
    # session.refresh(hero_2)
    # session.refresh(hero_3)

    # print("After refreshing the heroes")
    # print("Hero 1:", hero_1)
    # print("Hero 2:", hero_2)
    # print("Hero 3:", hero_3)

    print("After the session closes")
    print("Hero 1:", hero_1)
    print("Hero 2:", hero_2)
    print("Hero 3:", hero_3)
    # print("Hero 31:", hero_31)


def main():
    create_db_and_tables()
    create_heroes()


if __name__ == "__main__":
    main()
