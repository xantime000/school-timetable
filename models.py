# fast_api/models.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass


class SchoolClass(Base):
    __tablename__ = 'classes'
    id = Column(Integer, primary_key=True)
    number = Column(Integer)
    letter = Column(String(1))
    lessons = relationship("Lesson", back_populates="school_class")


class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    teacher_id = Column(Integer, ForeignKey('teachers.id'))
    hours_per_week = Column(Integer, default=3)
    teacher = relationship("Teacher", back_populates="subjects")
    lessons = relationship("Lesson", back_populates="subject")


class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    lessons = relationship("Lesson", back_populates="room")


class Teacher(Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    subjects = relationship("Subject", back_populates="teacher")
    lessons = relationship("Lesson", back_populates="teacher")


class Lesson(Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    day = Column(Integer)  # Было: day_of_week → теперь day
    lesson_number = Column(Integer)
    class_id = Column(Integer, ForeignKey('classes.id'))
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))

    school_class = relationship("SchoolClass", back_populates="lessons")
    subject = relationship("Subject", back_populates="lessons")
    teacher = relationship("Teacher", back_populates="lessons")
    room = relationship("Room", back_populates="lessons")