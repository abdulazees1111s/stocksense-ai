from sqlalchemy.orm import Session

from app.core.symbols import SUPPORTED_COMPANIES
from app.db.session import Base, engine
from app.models.entities import Company


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def seed_companies(db: Session) -> None:
    for seed in SUPPORTED_COMPANIES:
        company = db.query(Company).filter(Company.symbol == seed.symbol).one_or_none()
        if company:
            company.display_symbol = seed.display_symbol
            company.name = seed.name
            company.sector = seed.sector
            company.exchange = seed.exchange
        else:
            db.add(
                Company(
                    symbol=seed.symbol,
                    display_symbol=seed.display_symbol,
                    name=seed.name,
                    sector=seed.sector,
                    exchange=seed.exchange,
                )
            )
    db.commit()
