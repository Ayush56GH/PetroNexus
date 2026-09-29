import math
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

# Setup DB Engine
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# If SQLite is used, register a custom Haversine distance function for spatial offset radius search
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        def haversine_distance(lat1, lon1, lat2, lon2):
            if None in (lat1, lon1, lat2, lon2):
                return 999999.0
            r = 6371.0 # Earth radius in km
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)
            a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
            c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
            return r * c
        
        dbapi_connection.create_function("haversine_distance", 4, haversine_distance)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
