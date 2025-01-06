# db.py
import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

DATABASE_URL = "sqlite:///./chatbot.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    current_stage = Column(String, default="Uncertain")
    stage_confidence = Column(Float, default=0.0)

    # New columns to store multi-message distribution
    accum_distribution = Column(String, default="{}")
    num_lines = Column(Integer, default=0)

    messages = relationship("Message", back_populates="team")

    def load_accum_distrib(self):
        """
        Parse the accum_distribution column (JSON string) into a Python dict.
        If empty or invalid, return a dict of stage->0.0
        """
        try:
            dist = json.loads(self.accum_distribution)
            if isinstance(dist, dict):
                return dist
            else:
                return {}
        except Exception:
            return {}

    def save_accum_distrib(self, dist_dict):
        """
        Convert the stage distribution Python dict to JSON, store in DB column.
        """
        self.accum_distribution = json.dumps(dist_dict)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    role = Column(String)  # "user" or "assistant"
    text = Column(String)
    detected_emotion = Column(String, nullable=True)
    stage_at_time = Column(String, nullable=True)

    team = relationship("Team", back_populates="messages")


def init_db():
    Base.metadata.create_all(bind=engine)


