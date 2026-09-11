from app.database import SessionLocal, init_database
from app.services.seed import seed_defaults


def main() -> None:
    init_database()
    with SessionLocal() as db:
        seed_defaults(db)
    print("Database initialized and defaults seeded.")


if __name__ == "__main__":
    main()
