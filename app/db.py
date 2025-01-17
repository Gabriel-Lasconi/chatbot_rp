# db.py

import json
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

DATABASE_URL = "sqlite:///./teams.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    current_stage = Column(String, default="Uncertain")
    stage_distribution = Column(String, default="{}")
    feedback = Column(String, default="")  # Team feedback column

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

    def load_current_stage(self):
        """Load the current stage for the team."""
        return self.current_stage or "Uncertain"

    def load_feedback(self):
        """Load feedback for the team."""
        return self.feedback or ""


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    team_id = Column(Integer, ForeignKey("teams.id"))
    team = relationship("Team", back_populates="members")

    current_stage = Column(String, default="Uncertain")
    accum_distribution = Column(String, default="{}")  # Tuckman stage distribution
    accum_emotions = Column(String, default="{}")  # Overall emotional distribution
    num_lines = Column(Integer, default=0)
    personal_feedback = Column(String, default="")  # Personal feedback for the member

    messages = relationship("Message", back_populates="member")

    def load_accum_distrib(self):
        """Parse accum_distribution (Tuckman) as dict."""
        try:
            dist = json.loads(self.accum_distribution)
            return dist if isinstance(dist, dict) else {}
        except:
            return {}

    def save_accum_distrib(self, dist_dict):
        """Save Tuckman distribution to accum_distribution as JSON."""
        self.accum_distribution = json.dumps(dist_dict)

    def load_accum_emotions(self):
        """Parse accum_emotions (JSON) as dict."""
        try:
            dist = json.loads(self.accum_emotions)
            return dist if isinstance(dist, dict) else {}
        except:
            return {}

    def save_accum_emotions(self, dist_dict):
        """Save accumulative emotions as JSON."""
        self.accum_emotions = json.dumps(dist_dict)

    def load_personal_feedback(self):
        """Load personal feedback for the member."""
        return self.personal_feedback or ""

    def load_current_stage(self):
        """Load the current stage for the member."""
        return self.current_stage or "Uncertain"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    role = Column(String)
    text = Column(String)
    detected_emotion = Column(String, nullable=True)
    stage_at_time = Column(String, nullable=True)

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
