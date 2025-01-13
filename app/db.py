# db.py

import json
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# CHANGED DB NAME:
DATABASE_URL = "sqlite:///./teams.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    current_stage = Column(String, default="Uncertain")

    # The JSON column storing the entire team distribution
    stage_distribution = Column(String, default="{}")

    members = relationship("Member", back_populates="team")

    def load_team_distribution(self):
        """
        Returns the stage_distribution (JSON) from this Team as a Python dict.
        If the column is invalid JSON or empty, returns an empty dict.
        """
        import json
        try:
            dist = json.loads(self.stage_distribution)
            return dist if isinstance(dist, dict) else {}
        except Exception:
            return {}

    def save_team_distribution(self, dist_dict):
        """
        Takes a dict like {"Forming": 0.1, "Storming": 0.2, ...} and
        serializes it into stage_distribution (JSON) in the DB.
        """
        import json
        self.stage_distribution = json.dumps(dist_dict)


class Member(Base):
    """
    Each Member belongs to one Team. Each Member has their own stage and accum_distribution,
    just like Team originally did.
    """
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    current_stage = Column(String, default="Uncertain")
    stage_confidence = Column(Float, default=0.0)

    accum_distribution = Column(String, default="{}")
    num_lines = Column(Integer, default=0)

    # RELATIONSHIPS
    team = relationship("Team", back_populates="members")
    messages = relationship("Message", back_populates="member")

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
    member_id = Column(Integer, ForeignKey("members.id"))
    role = Column(String)  # "user" or "assistant"
    text = Column(String)
    detected_emotion = Column(String, nullable=True)
    stage_at_time = Column(String, nullable=True)

    # NEW COLUMN: JSON string to store top-5 emotion distribution
    top_emotion_distribution = Column(String, default="{}")  # CHANGED / ADDED

    # RELATIONSHIPS
    member = relationship("Member", back_populates="messages")

    def load_top_emotion_distribution(self):
        try:
            dist = json.loads(self.top_emotion_distribution)
            if isinstance(dist, dict):
                return dist
            else:
                return {}
        except Exception:
            return {}

    def save_top_emotion_distribution(self, dist_dict):
        self.top_emotion_distribution = json.dumps(dist_dict)

def init_db():
    Base.metadata.create_all(bind=engine)
