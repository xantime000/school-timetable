import random
from sqlalchemy.orm import Session
from .models import SchoolClass, Subject, Room, Lesson, Teacher

# Правила: сколько уроков в неделю для каждого класса
SUBJECTS_BY_CLASS = {
    "10А": {
        "Алгебра": 4,
        "Геометрия": 4,
        "Физика": 2,
        "Информатика": 2,
        "Русский язык": 1,
        "Литература": 1,
        "Физкультура": 2,
        "Химия": 1
    },
}

# Сопоставление предмета и учителя
TEACHERS = {
    "Алгебра": "Иванов И.И. (алгебра)",
    "Геометрия": "Петрова А.В. (геометрия)",
    "Физика": "Сидорова Е.М. (физика)",
    "Информатика": "Фёдоров А.Б. (информатика)",
    "Русский язык": "Орлова Н.К. (русский язык)",
    "Литература": "Лебедев С.П. (литература)",
    "Физкультура": "Смирнова О.П. (физкультура)",
    "Химия": "Николаева Т.С. (химия)"
}

# Привязка предметов к кабинетам
SUBJECT_ROOMS = {
    "Алгебра": ["Кабинет 102 (алгебра)"],
    "Геометрия": ["Кабинет 103 (геометрия)"],
    "Физика": ["Кабинет 201 (физика)"],
    "Информатика": ["Кабинет 701 (информатика)"],
    "Русский язык": ["Кабинет 501 (русский язык)"],
    "Литература": ["Кабинет 502 (литература)"],
    "Физкультура": ["Спортзал №1", "Спортзал №2"],
    "Химия": ["Кабинет 202 (химия)"]
}

DAYS = list(range(5))  # Пн–Пт
SLOTS = list(range(1, 9))  # Уроки 1–8

def generate_random_schedule(db: Session):
    # Очистка старого расписания
    db.query(Lesson).delete()
    db.commit()

    # Загружаем данные из БД
    classes = db.query(SchoolClass).all()
    subjects = db.query(Subject).all()
    rooms = db.query(Room).all()
    teachers = db.query(Teacher).all()

    # Создаём словари: имя -> объект
    class_map = {f"{cls.number}{cls.letter}": cls for cls in classes}
    subject_map = {subj.name: subj for subj in subjects}
    room_map = {room.name: room for room in rooms}
    teacher_map = {t.name: t for t in teachers}

    # Структура для отслеживания занятых слотов
    schedule_grid = {}
    for day in DAYS:
        for slot in SLOTS:
            schedule_grid[(day, slot)] = {
                "classes": set(),
                "teachers": set(),
                "rooms": set()
            }

    # Для каждого класса генерируем расписание
    for class_name, subjects_config in SUBJECTS_BY_CLASS.items():
        if class_name not in class_map:
            print(f"⚠️ Класс {class_name} не найден в БД")
            continue

        cls = class_map[class_name]
        print(f"Генерация расписания для {class_name}...")

        # Собираем все уроки для расписания
        lessons_to_schedule = []
        for subject_name, hours in subjects_config.items():
            if subject_name not in subject_map:
                print(f"⚠️ Предмет {subject_name} не найден в БД")
                continue
            subject = subject_map[subject_name]
            teacher_name = TEACHERS.get(subject_name)
            if not teacher_name or teacher_name not in teacher_map:
                print(f"⚠️ Учитель для {subject_name} не найден: {teacher_name}")
                continue
            for _ in range(hours):
                lessons_to_schedule.append((subject, teacher_name))

        # Перемешиваем уроки
        random.shuffle(lessons_to_schedule)

        # Распределяем уроки по дням равномерно
        total_hours = sum(subjects_config.values())
        lessons_per_day = [total_hours // len(DAYS)] * len(DAYS)
        for i in range(total_hours % len(DAYS)):
            lessons_per_day[i] += 1

        # Размещаем уроки по порядку с начала слотов
        current_lesson = 0
        for day in DAYS:
            if current_lesson >= len(lessons_to_schedule):
                break
            lessons_for_day = lessons_to_schedule[current_lesson:current_lesson + lessons_per_day[day]]
            current_lesson += lessons_per_day[day]

            # Начинаем с 1-го слота
            slot = 1
            for subject, teacher_name in lessons_for_day:
                teacher = teacher_map[teacher_name]
                subject_obj = subject_map[subject.name]
                possible_rooms = [room_map[rn] for rn in SUBJECT_ROOMS.get(subject.name, []) if rn in room_map]

                if not possible_rooms:
                    print(f"❌ Нет подходящего кабинета для {subject.name}")
                    break

                room = random.choice(possible_rooms)
                while slot in SLOTS and (
                    cls.id in schedule_grid[(day, slot)]["classes"] or
                    teacher.id in schedule_grid[(day, slot)]["teachers"] or
                    room.id in schedule_grid[(day, slot)]["rooms"]
                ):
                    slot += 1
                if slot > SLOTS[-1]:
                    print(f"❌ Нет места для {subject.name} на день {day + 1}")
                    break

                lesson = Lesson(
                    class_id=cls.id,
                    subject_id=subject_obj.id,
                    teacher_id=teacher.id,
                    room_id=room.id,
                    day=day,
                    lesson_number=slot
                )
                db.add(lesson)
                schedule_grid[(day, slot)]["classes"].add(cls.id)
                schedule_grid[(day, slot)]["teachers"].add(teacher.id)
                schedule_grid[(day, slot)]["rooms"].add(room.id)
                print(f"✅ {subject.name} поставлен на {day + 1} день, {slot} урок в {room.name}")
                slot += 1

    db.commit()
    print("✅ Расписание сгенерировано!")