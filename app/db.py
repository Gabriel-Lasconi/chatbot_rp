# db.py

import json
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

DATABASE_URL = "sqlite:///./teams_extended.db"  # or your DB path
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"  # or your chosen name

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    current_stage = Column(String, default="Uncertain")
    stage_distribution = Column(String, default="{}")

    members = relationship("Member", back_populates="team")

    def load_team_distribution(self):
        """Load stage_distribution as a dict."""
        try:
            dist = json.loads(self.stage_distribution)
            return dist if isinstance(dist, dict) else {}
        except:
            return {}

    def save_team_distribution(self, dist_dict):
        """Save dict to stage_distribution as JSON."""
        self.stage_distribution = json.dumps(dist_dict)


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    team_id = Column(Integer, ForeignKey("teams.id"))
    team = relationship("Team", back_populates="members")

    current_stage = Column(String, default="Uncertain")
    accum_distribution = Column(String, default="{}")  # Tuckman stage distribution
    num_lines = Column(Integer, default=0)

    # NEW: store overall (accumulative) emotions distribution across messages
    accum_emotions = Column(String, default="{}")  # <--- ADDED

    messages = relationship("Message", back_populates="member")

    def load_accum_distrib(self):
        """Parse accum_distribution (Tuckman) as dict."""
        try:
            dist = json.loads(self.accum_distribution)
            return dist if isinstance(dist, dict) else {}
        except:
            return {}

    def save_accum_distrib(self, dist_dict):
        self.accum_distribution = json.dumps(dist_dict)

    # NEW EMOTIONS LOGIC
    def load_accum_emotions(self):
        """Parse accum_emotions (JSON) as dict of emotion->score."""
        try:
            dist = json.loads(self.accum_emotions)
            return dist if isinstance(dist, dict) else {}
        except:
            return {}

    def save_accum_emotions(self, dist_dict):
        """Save the accumulative emotions as JSON."""
        self.accum_emotions = json.dumps(dist_dict)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    role = Column(String)  # "User" or "Assistant"
    text = Column(String)
    detected_emotion = Column(String, nullable=True)
    stage_at_time = Column(String, nullable=True)

    # JSON string to store top-5 emotions distribution for this message
    top_emotion_distribution = Column(String, default="{}")

    member = relationship("Member", back_populates="messages")

    def load_top_emotion_distribution(self):
        """Load top_emotion_distribution as dict."""
        try:
            dist = json.loads(self.top_emotion_distribution)
            return dist if isinstance(dist, dict) else {}
        except:
            return {}

    def save_top_emotion_distribution(self, dist_dict):
        self.top_emotion_distribution = json.dumps(dist_dict)


def init_db():
    Base.metadata.create_all(bind=engine)
