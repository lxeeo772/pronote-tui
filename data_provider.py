from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Protocol

@dataclass
class StudentProfile:
    name: str = "Élève Inconnu"
    class_name: str = "Classe"
    school_name: str = "Établissement"
    period_name: str = "Trimestre 1"
    is_demo: bool = True

@dataclass
class GradeItem:
    id: str
    subject: str
    value: float          # e.g. 15.5
    out_of: float = 20.0  # e.g. 20.0
    default_out_of: float = 20.0
    coeff: float = 1.0
    class_avg: Optional[float] = None
    min_grade: Optional[float] = None
    max_grade: Optional[float] = None
    date: Optional[date] = None
    title: str = "Devoir"
    is_significant: bool = True

@dataclass
class SubjectAverage:
    subject: str
    student_avg: Optional[float]
    class_avg: Optional[float]
    min_avg: Optional[float]
    max_avg: Optional[float]
    coeff: float = 1.0
    grades: List[GradeItem] = field(default_factory=list)

@dataclass
class OverallAverage:
    student_avg: Optional[float] = 0.0
    class_avg: Optional[float] = 0.0
    min_avg: Optional[float] = 0.0
    max_avg: Optional[float] = 0.0

@dataclass
class LessonItem:
    id: str
    subject: str
    teacher: str
    room: str
    start_time: str      # "08:15"
    end_time: str        # "09:10"
    date: date
    is_cancelled: bool = False
    status: Optional[str] = None # e.g. "Prof. absent", "Salle modifiée"
    is_modified: bool = False

@dataclass
class HomeworkItem:
    id: str
    subject: str
    due_date: date
    description: str
    done: bool = False
    files: List[str] = field(default_factory=list)
    given_date: Optional[date] = None

@dataclass
class AbsenceItem:
    id: str
    date_str: str
    duration: str
    reason: str
    justified: bool = False

@dataclass
class PunishmentItem:
    id: str
    date_str: str
    reason: str
    giver: str
    punishment_type: str
    duration: str

class DataProvider(Protocol):
    def get_profile(self) -> StudentProfile:
        ...
    def get_grades_and_averages(self) -> tuple[List[SubjectAverage], OverallAverage]:
        ...
    def get_timetable(self, target_date: date) -> List[LessonItem]:
        ...
    def get_homework(self) -> List[HomeworkItem]:
        ...
    def set_homework_done(self, homework_id: str, done: bool) -> bool:
        ...
    def get_vie_scolaire(self) -> tuple[List[AbsenceItem], List[PunishmentItem]]:
        ...
