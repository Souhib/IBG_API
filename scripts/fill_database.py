import random
from datetime import timedelta

from faker import Faker
from sqlmodel import SQLModel, create_engine, Session

from ibg.models.undercover import Word, TermPair
from ibg.models.game import GameType
from ibg.models.models import Game, User

DATABASE_URL = "sqlite:///database.db"

engine = create_engine(DATABASE_URL)

fake = Faker()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


sample_words = [
    {
        "id": fake.uuid4(),
        "word": "Hajj",
        "category": "Pillars of Islam",
        "short_description": "Pilgrimage to Mecca.",
        "long_description": "Hajj is the fifth pillar of Islam, requiring Muslims who are physically and financially able to undertake a pilgrimage to Mecca at least once in their lifetime.",
    },
    {
        "id": fake.uuid4(),
        "word": "Umrah",
        "category": "Islamic Rituals",
        "short_description": "Minor pilgrimage to Mecca.",
        "long_description": "Umrah, the minor pilgrimage to Mecca, can be undertaken at any time of the year, unlike Hajj, which has specific dates according to the Islamic lunar calendar.",
    },
    {
        "id": fake.uuid4(),
        "word": "Salah",
        "category": "Pillars of Islam",
        "short_description": "Islamic ritual prayer.",
        "long_description": "Salah is the second pillar of Islam, consisting of five daily prayers that are obligatory for all adult Muslims.",
    },
    {
        "id": fake.uuid4(),
        "word": "Sawm",
        "category": "Pillars of Islam",
        "short_description": "Fasting during Ramadan.",
        "long_description": "Sawm, or fasting, is the fourth pillar of Islam, observed during the month of Ramadan, where Muslims fast from dawn until sunset.",
    },
    {
        "id": fake.uuid4(),
        "word": "Zakat",
        "category": "Pillars of Islam",
        "short_description": "Compulsory charity.",
        "long_description": "Zakat is the third pillar of Islam, requiring Muslims to give a fixed portion of their wealth to the needy.",
    },
    {
        "id": fake.uuid4(),
        "word": "Sadaqah",
        "category": "Islamic Charitable Practices",
        "short_description": "Voluntary charity.",
        "long_description": "Sadaqah refers to voluntary charitable acts performed by Muslims, extending beyond monetary donations to include acts of kindness and generosity.",
    },
    {
        "id": fake.uuid4(),
        "word": "Shahada",
        "category": "Pillars of Islam",
        "short_description": "Islamic declaration of faith.",
        "long_description": "The Shahada is the first pillar of Islam, expressing the declaration of faith in the oneness of Allah and the prophethood of Muhammad.",
    },
    {
        "id": fake.uuid4(),
        "word": "Tawhid",
        "category": "Islamic Beliefs",
        "short_description": "Oneness of God in Islam.",
        "long_description": "Tawhid is the principle of monotheism in Islam, affirming the oneness and absolute sovereignty of God as the central tenet of the Islamic faith.",
    },
    {
        "id": fake.uuid4(),
        "word": "Jihad",
        "category": "Islamic Concepts",
        "short_description": "Struggle or effort in the way of God.",
        "long_description": "Jihad represents a broad Islamic concept that encompasses struggle against evil inclinations, effort in the way of God, and in some contexts, warfare in defense of the Islamic community.",
    },
    {
        "id": fake.uuid4(),
        "word": "Hijrah",
        "category": "Islamic History",
        "short_description": "Prophet Muhammad's migration to Medina.",
        "long_description": "The Hijrah refers to the migration of the Prophet Muhammad and his followers from Mecca to Medina in 622 CE, marking the beginning of the Islamic calendar.",
    },
]

sample_pairs = [
    {
        "word1_id": sample_words[0]["id"],
        "word2_id": sample_words[1]["id"],
        "category": "Pilgrimages",
        "short_description": "Hajj and Umrah",
        "long_description": "Both Hajj and Umrah are Islamic pilgrimages to Mecca, but Hajj is mandatory and performed on specific dates, while Umrah is voluntary and can be performed any time.",
    },
    {
        "word1_id": sample_words[2]["id"],
        "word2_id": sample_words[3]["id"],
        "category": "Pillars of Islam",
        "short_description": "Salah and Sawm",
        "long_description": "Salah and Sawm are both pillars of Islam, emphasizing the spiritual practices of prayer and fasting, respectively.",
    },
    {
        "word1_id": sample_words[4]["id"],
        "word2_id": sample_words[5]["id"],
        "category": "Charitable Practices",
        "short_description": "Zakat and Sadaqah",
        "long_description": "Zakat and Sadaqah represent forms of charity in Islam, with Zakat being compulsory and Sadaqah being voluntary.",
    },
    {
        "word1_id": sample_words[6]["id"],
        "word2_id": sample_words[7]["id"],
        "category": "Fundamental Beliefs",
        "short_description": "Shahada and Tawhid",
        "long_description": "Shahada, the declaration of faith, and Tawhid, the oneness of God, are central to Islamic belief, emphasizing monotheism and the acceptance of Muhammad as God's prophet.",
    },
    {
        "word1_id": sample_words[8]["id"],
        "word2_id": sample_words[9]["id"],
        "category": "Islamic Concepts and History",
        "short_description": "Jihad and Hijrah",
        "long_description": "Jihad, denoting struggle in the way of God, and Hijrah, the migration to Medina, are significant in Islamic teachings and history, symbolizing spiritual and physical journeys for faith.",
    },
]


def generate_fake_users(num_users: int) -> list[User]:
    users = [
        User(
            username=fake.user_name(),
            email_address=fake.email(),
            country=fake.country(),
            password=fake.password(),
        )
        for _ in range(num_users)
    ]
    return users


def generate_sample_games(users: list[User], num_games: int) -> list[Game]:
    return [
        Game(
            user_id=(random.choice(users)).id,
            start_time=(start_time := fake.past_datetime(start_date="-30d")),
            end_time=(
                start_time + timedelta(minutes=random.randint(1, 15))
                if random.choice([True, False])
                else None
            ),
            number_of_players=random.randint(1, 8),
            type=random.choice(list(GameType)),
        )
        for _ in range(num_games)
    ]


def insert_sample_data() -> None:
    users = generate_fake_users(15)
    with Session(engine) as session:
        for user in users:
            session.add(user)

        session.commit()

        for word_data in sample_words:
            word = Word(**word_data)
            session.add(word)
        session.commit()

        for pair_data in sample_pairs:
            term_pair = TermPair(**pair_data)
            session.add(term_pair)
        session.commit()

        games = generate_sample_games(users, 10)  # Generate 10 sample games
        for game in games:
            session.add(game)
        session.commit()


if __name__ == "__main__":
    create_db_and_tables()
    insert_sample_data()
    print("Database populated with sample data.")
