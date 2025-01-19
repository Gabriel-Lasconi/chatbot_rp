# db.py

import json
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========================================================
# DATABASE MODELS
# ========================================================

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    current_stage = Column(String, default="Uncertain")
    stage_distribution = Column(String, default="{}")
    feedback = Column(String, default="")

    members = relationship("Member", back_populates="team")

    # ====================================================
    #   TEAM DATA HANDLING FUNCTIONS
    # ====================================================

    def load_team_distribution(self):
        """Loads the stage distribution from JSON to a dictionary."""
        try:
            dist = json.loads(self.stage_distribution)
            return dist if isinstance(dist, dict) else {}
        except:
            return {}

    def save_team_distribution(self, dist_dict):
        """Saves the stage distribution dictionary as a JSON string."""
        self.stage_distribution = json.dumps(dist_dict)

    def load_current_stage(self):
        """Returns the current stage of the team."""
        return self.current_stage or "Uncertain"

    def load_feedback(self):
        """Returns the feedback for the team."""
        return self.feedback or ""


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    team_id = Column(Integer, ForeignKey("teams.id"))
    team = relationship("Team", back_populates="members")

    current_stage = Column(String, default="Uncertain")
    accum_distribution = Column(String, default="{}")  # Tuckman stage distribution
    accum_emotions = Column(String, default="{}")      # Overall emotional distribution
    num_lines = Column(Integer, default=0)
    personal_feedback = Column(String, default="")      # Personal feedback for the member

    messages = relationship("Message", back_populates="member")

    # ====================================================
    #   MEMBER DATA HANDLING FUNCTIONS
    # ====================================================

    def load_accum_distrib(self):
        """Loads the accumulated Tuckman stage distribution from JSON to a dictionary."""
        try:
            dist = json.loads(self.accum_distribution)
            return dist if isinstance(dist, dict) else {}
        except:
            return {}

    def save_accum_distrib(self, dist_dict):
        """Saves the accumulated Tuckman stage distribution as a JSON string."""
        self.accum_distribution = json.dumps(dist_dict)

    def load_accum_emotions(self):
        """Loads the accumulated emotions from JSON to a dictionary."""
        try:
            dist = json.loads(self.accum_emotions)
            return dist if isinstance(dist, dict) else {}
        except:
            return {}

    def save_accum_emotions(self, dist_dict):
        """Saves the accumulated emotions as a JSON string."""
        self.accum_emotions = json.dumps(dist_dict)

    def load_personal_feedback(self):
        """Returns the personal feedback for the member."""
        return self.personal_feedback or ""

    def load_current_stage(self):
        """Returns the current stage of the member."""
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

    # ====================================================
    #   MESSAGE DATA HANDLING FUNCTIONS
    # ====================================================

    def load_top_emotion_distribution(self):
        """Loads the top emotion distribution from JSON to a dictionary."""
        try:
            dist = json.loads(self.top_emotion_distribution)
            return dist if isinstance(dist, dict) else {}
        except:
            return {}

    def save_top_emotion_distribution(self, dist_dict):
        """Saves the top emotion distribution as a JSON string."""
        self.top_emotion_distribution = json.dumps(dist_dict)


# ========================================================
# DATABASE INITIALIZATION FUNCTION
# ========================================================
def init_db():
    """
    Initializes the database by creating all tables.
    """
    Base.metadata.create_all(bind=engine)
