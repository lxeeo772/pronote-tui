from datetime import date, timedelta
from typing import List, Tuple
from .data_provider import (
    DataProvider, StudentProfile, GradeItem, SubjectAverage,
    OverallAverage, LessonItem, HomeworkItem, AbsenceItem, PunishmentItem
)

class MockDataProvider(DataProvider):
    """Fournit des données de démonstration ultra-réalistes d'un lycéen français."""

    def __init__(self):
        self.profile = StudentProfile(
            name="Alexandre Martin",
            class_name="Tle Générale 2 (Spé Maths / NSI)",
            school_name="Lycée Victor Hugo - Paris",
            period_name="Trimestre 1",
            is_demo=True
        )

        today = date.today()
        # Initialize realistic subjects and grades
        self._subjects_averages: List[SubjectAverage] = [
            SubjectAverage(
                subject="Mathématiques (Spé)",
                student_avg=15.25,
                class_avg=12.40,
                min_avg=6.50,
                max_avg=19.50,
                coeff=16.0,
                grades=[
                    GradeItem("m1", "Mathématiques (Spé)", 16.5, 20.0, 20.0, 3.0, 12.1, 5.0, 19.5, today - timedelta(days=28), "DS 1 - Récurrence & Suites"),
                    GradeItem("m2", "Mathématiques (Spé)", 18.0, 20.0, 20.0, 1.0, 13.5, 7.0, 20.0, today - timedelta(days=20), "Interro Flash - Limites"),
                    GradeItem("m3", "Mathématiques (Spé)", 13.5, 20.0, 20.0, 4.0, 11.2, 4.5, 18.0, today - timedelta(days=10), "DS 2 - Continuité & Dérivation"),
                    GradeItem("m4", "Mathématiques (Spé)", 17.0, 20.0, 20.0, 1.0, 14.0, 8.0, 19.0, today - timedelta(days=3), "DM 1 - Étude de fonction exponentielle"),
                ]
            ),
            SubjectAverage(
                subject="Numérique & Sciences Info (Spé)",
                student_avg=17.80,
                class_avg=13.60,
                min_avg=8.00,
                max_avg=19.20,
                coeff=16.0,
                grades=[
                    GradeItem("n1", "Numérique & Sciences Info (Spé)", 19.0, 20.0, 20.0, 2.0, 14.5, 9.0, 20.0, today - timedelta(days=25), "Projet Python - Graphes et parcours BFS/DFS"),
                    GradeItem("n2", "Numérique & Sciences Info (Spé)", 16.5, 20.0, 20.0, 3.0, 12.8, 6.5, 18.5, today - timedelta(days=12), "DS 1 - Récursion et Programmation Dynamique"),
                    GradeItem("n3", "Numérique & Sciences Info (Spé)", 18.5, 20.0, 20.0, 1.0, 14.2, 8.0, 20.0, today - timedelta(days=4), "TP Noté - Base de données SQL"),
                ]
            ),
            SubjectAverage(
                subject="Philosophie",
                student_avg=12.50,
                class_avg=10.80,
                min_avg=5.50,
                max_avg=16.00,
                coeff=8.0,
                grades=[
                    GradeItem("p1", "Philosophie", 11.5, 20.0, 20.0, 4.0, 10.2, 4.0, 15.5, today - timedelta(days=22), "Dissertation - La vérité est-elle libératrice ?"),
                    GradeItem("p2", "Philosophie", 13.5, 20.0, 20.0, 3.0, 11.4, 6.0, 16.0, today - timedelta(days=7), "Explication de texte - Nietzsche, Gai Savoir"),
                ]
            ),
            SubjectAverage(
                subject="Histoire-Géographie",
                student_avg=14.75,
                class_avg=12.10,
                min_avg=7.00,
                max_avg=17.50,
                coeff=3.0,
                grades=[
                    GradeItem("h1", "Histoire-Géographie", 16.0, 20.0, 20.0, 1.0, 12.5, 8.0, 18.0, today - timedelta(days=30), "Croquis cartographique - Mers et océans"),
                    GradeItem("h2", "Histoire-Géographie", 14.0, 20.0, 20.0, 3.0, 11.8, 6.0, 17.0, today - timedelta(days=14), "Épreuve type Bac - L'impact de la crise de 1929"),
                ]
            ),
            SubjectAverage(
                subject="Anglais LVA",
                student_avg=16.20,
                class_avg=13.20,
                min_avg=8.50,
                max_avg=18.50,
                coeff=3.0,
                grades=[
                    GradeItem("a1", "Anglais LVA", 17.0, 20.0, 20.0, 2.0, 13.8, 9.0, 19.0, today - timedelta(days=21), "Oral Presentation - Dystopian Literatures"),
                    GradeItem("a2", "Anglais LVA", 15.5, 20.0, 20.0, 2.0, 12.6, 7.5, 18.0, today - timedelta(days=8), "Reading Comprehension - AI Ethics"),
                ]
            ),
            SubjectAverage(
                subject="Espagnol LVB",
                student_avg=13.80,
                class_avg=12.50,
                min_avg=7.00,
                max_avg=17.00,
                coeff=3.0,
                grades=[
                    GradeItem("e1", "Espagnol LVB", 13.0, 20.0, 20.0, 1.0, 11.5, 6.0, 17.0, today - timedelta(days=27), "Contrôle de vocabulaire - El medio ambiente"),
                    GradeItem("e2", "Espagnol LVB", 14.5, 20.0, 20.0, 2.0, 13.0, 8.0, 16.5, today - timedelta(days=11), "Compréhension orale - Podcasts RNE"),
                ]
            ),
            SubjectAverage(
                subject="Enseignement Scientifique",
                student_avg=15.00,
                class_avg=12.80,
                min_avg=7.50,
                max_avg=18.00,
                coeff=2.0,
                grades=[
                    GradeItem("s1", "Enseignement Scientifique", 17.0, 20.0, 20.0, 1.0, 13.5, 8.0, 18.5, today - timedelta(days=24), "QCM - Le rayonnement solaire"),
                    GradeItem("s2", "Enseignement Scientifique", 14.0, 20.0, 20.0, 2.0, 12.2, 7.0, 17.5, today - timedelta(days=9), "Devoir de synthèse - Datation de la Terre"),
                ]
            ),
            SubjectAverage(
                subject="EPS (Éducation Physique)",
                student_avg=15.50,
                class_avg=13.80,
                min_avg=9.00,
                max_avg=18.50,
                coeff=2.0,
                grades=[
                    GradeItem("ep1", "EPS", 15.5, 20.0, 20.0, 2.0, 13.8, 9.0, 18.5, today - timedelta(days=15), "Cycle Demi-Fond - Épreuve 3x500m"),
                ]
            ),
        ]

        # Overall average calculation
        total_pts = sum(s.student_avg * s.coeff for s in self._subjects_averages if s.student_avg is not None)
        total_coeff = sum(s.coeff for s in self._subjects_averages if s.student_avg is not None)
        class_pts = sum(s.class_avg * s.coeff for s in self._subjects_averages if s.class_avg is not None)
        
        student_gen = round(total_pts / total_coeff, 2) if total_coeff > 0 else 0.0
        class_gen = round(class_pts / total_coeff, 2) if total_coeff > 0 else 0.0

        self._overall_avg = OverallAverage(
            student_avg=student_gen,
            class_avg=class_gen,
            min_avg=7.80,
            max_avg=18.20
        )

        # Homework items
        self._homework: List[HomeworkItem] = [
            HomeworkItem(
                id="hw1",
                subject="Mathématiques (Spé)",
                due_date=today + timedelta(days=1),
                description="Exercices 42 et 45 page 184. Traiter le cas n=3 pour la récurrence forte.",
                done=False,
                given_date=today - timedelta(days=2)
            ),
            HomeworkItem(
                id="hw2",
                subject="Numérique & Sciences Info (Spé)",
                due_date=today + timedelta(days=2),
                description="Finaliser l'algorithme d'A* en Python et tester sur la grille fournie.",
                done=True,
                given_date=today - timedelta(days=4)
            ),
            HomeworkItem(
                id="hw3",
                subject="Philosophie",
                due_date=today + timedelta(days=3),
                description="Faire le plan détaillé de la dissertation : 'La technique nous rend-elle plus libres ?'. 3 parties exigées.",
                done=False,
                given_date=today - timedelta(days=1)
            ),
            HomeworkItem(
                id="hw4",
                subject="Histoire-Géographie",
                due_date=today + timedelta(days=4),
                description="Lire les documents pages 88-89 sur les câbles sous-marins et répondre aux 3 questions.",
                done=False,
                given_date=today - timedelta(days=3)
            ),
            HomeworkItem(
                id="hw5",
                subject="Anglais LVA",
                due_date=today + timedelta(days=5),
                description="Watch the TED talk on 'Algorithmic bias' and take notes for the debate next Monday.",
                done=False,
                given_date=today - timedelta(days=2)
            ),
        ]

        # Absences & Punishments
        self._absences: List[AbsenceItem] = [
            AbsenceItem("ab1", (today - timedelta(days=16)).strftime("%d/%m/%Y"), "Demi-journée (matin)", "Raison médicale (Certificat fourni)", justified=True),
            AbsenceItem("ab2", (today - timedelta(days=3)).strftime("%d/%m/%Y"), "Retard 15 min", "Perturbations RER B", justified=True),
        ]
        self._punishments: List[PunishmentItem] = [
            PunishmentItem("pu1", (today - timedelta(days=20)).strftime("%d/%m/%Y"), "Oubli répété du manuel", "M. Dupont (Philo)", "Devoir supplémentaire", "1 heure"),
        ]

    def get_profile(self) -> StudentProfile:
        return self.profile

    def get_grades_and_averages(self) -> Tuple[List[SubjectAverage], OverallAverage]:
        return self._subjects_averages, self._overall_avg

    def get_timetable(self, target_date: date) -> List[LessonItem]:
        # Generate timetable based on target_date's day of week (0=Monday, 6=Sunday)
        weekday = target_date.weekday()
        if weekday == 0: # Lundi
            return [
                LessonItem("l1", "Mathématiques (Spé)", "Mme. Valette", "Salle B204", "08:15", "10:10", target_date),
                LessonItem("l2", "Philosophie", "M. Dupont", "Salle A102", "10:25", "12:15", target_date),
                LessonItem("l3", "Histoire-Géographie", "Mme. Blanc", "Salle B108", "13:30", "14:25", target_date),
                LessonItem("l4", "Anglais LVA", "Mr. Smith", "Salle C301", "14:30", "16:20", target_date),
            ]
        elif weekday == 1: # Mardi
            return [
                LessonItem("l5", "Numérique & Sciences Info", "M. Chen", "Labo Info 2", "08:15", "10:10", target_date),
                LessonItem("l6", "Espagnol LVB", "Sra. Gomez", "Salle C205", "10:25", "11:20", target_date),
                LessonItem("l7", "Enseignement Scientifique", "M. Leroy", "Salle B304", "11:25", "12:20", target_date),
                LessonItem("l8", "EPS", "M. Traoré", "Gymnase Jaurès", "14:00", "16:00", target_date),
            ]
        elif weekday == 2: # Mercredi
            return [
                LessonItem("l9", "Mathématiques (Spé)", "Mme. Valette", "Salle B204", "08:15", "10:10", target_date),
                LessonItem("l10", "Histoire-Géographie", "Mme. Blanc", "Salle B108", "10:25", "12:15", target_date),
            ]
        elif weekday == 3: # Jeudi
            return [
                LessonItem("l11", "Numérique & Sciences Info", "M. Chen", "Labo Info 2", "08:15", "11:20", target_date),
                LessonItem("l12", "Philosophie", "M. Dupont", "Salle A102", "11:25", "12:20", target_date, is_cancelled=True, status="Professeur absent"),
                LessonItem("l13", "Anglais LVA", "Mr. Smith", "Salle C301", "13:30", "14:25", target_date),
                LessonItem("l14", "Espagnol LVB", "Sra. Gomez", "Salle C205", "14:30", "15:25", target_date),
                LessonItem("l15", "Accompagnement Personnalisé", "Mme. Valette", "Salle B204", "15:35", "16:30", target_date),
            ]
        elif weekday == 4: # Vendredi
            return [
                LessonItem("l16", "Mathématiques (Spé)", "Mme. Valette", "Salle B204", "08:15", "10:10", target_date),
                LessonItem("l17", "Numérique & Sciences Info", "M. Chen", "Labo Info 2", "10:25", "12:15", target_date),
                LessonItem("l18", "Enseignement Scientifique", "M. Leroy", "Salle B304", "13:30", "14:25", target_date),
                LessonItem("l19", "Devoir Surveillé (DS)", "Surveillant", "Amphithéâtre", "14:30", "17:30", target_date),
            ]
        else: # Samedi / Dimanche
            return []

    def get_homework(self) -> List[HomeworkItem]:
        return self._homework

    def set_homework_done(self, homework_id: str, done: bool) -> bool:
        for hw in self._homework:
            if hw.id == homework_id:
                hw.done = done
                return True
        return False

    def get_vie_scolaire(self) -> Tuple[List[AbsenceItem], List[PunishmentItem]]:
        return self._absences, self._punishments
