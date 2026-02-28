"""Script to create the skill_list table."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, Base
from models.skill_list import SkillList


def create_table():
    """Create the skill_list table."""
    print("Creating skill_list table...")
    Base.metadata.create_all(bind=engine, tables=[SkillList.__table__])
    print("skill_list table created successfully!")


if __name__ == "__main__":
    create_table()
