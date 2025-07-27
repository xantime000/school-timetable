import random
from sqlalchemy.orm import Session
from .models import SchoolClass, Subject, Room, Lesson, Teacher


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
    "11А":{
        "Алгебра": 4,
        "Геометрия": 4
    }
}

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

DAYS = list(range(5))       # Пн–Пт
SLOTS = list(range(1, 9))   # Уроки 1–8


def generate_random_schedule(db: Session):
    db.query(Lesson).delete()
    db.commit()

    classes = db.query(SchoolClass).all()
    subjects = db.query(Subject).all()
    rooms = db.query(Room).all()
    teachers = db.query(Teacher).all()

    class_map = {f"{cls.number}{cls.letter}": cls for cls in classes}
    subject_map = {s.name: s for s in subjects}
    teacher_map = {t.name: t for t in teachers}
    room_map = {r.name: r for r in rooms}

    # Сетка занятости: (day, slot) -> списки занятых id
    busy_slots = {(day, slot): {"classes": set(), "teachers": set(), "rooms": set()}
                  for day in DAYS for slot in SLOTS}

    # Оптимизация: создаем список классов и перемешиваем его
    class_names = list(SUBJECTS_BY_CLASS.keys())
    random.shuffle(class_names)

    for class_name in class_names:
        if class_name not in class_map:
            print(f"⚠️ Класс {class_name} не найден")
            continue
        school_class = class_map[class_name]
        subj_dict = SUBJECTS_BY_CLASS[class_name]

        # Равномерное распределение уроков по дням недели
        lessons_by_day = {day: [] for day in DAYS}
        total_lessons = sum(subj_dict.values())
        lessons_per_day = total_lessons // len(DAYS)
        extra_lessons = total_lessons % len(DAYS)

        # Распределяем уроки по дням
        day_index = 0
        for subj_name, count in subj_dict.items():
            subj = subject_map.get(subj_name)
            teacher = teacher_map.get(TEACHERS.get(subj_name))
            rooms_list = [room_map[r] for r in SUBJECT_ROOMS.get(subj_name, []) if r in room_map]

            if not subj or not teacher or not rooms_list:
                print(f"⚠️ Пропущен {subj_name}: нет предмета/учителя/кабинета")
                continue

            # Распределяем уроки предмета по дням
            for _ in range(count):
                target_day = DAYS[day_index]
                lessons_by_day[target_day].append((subj, teacher, random.choice(rooms_list)))
                day_index = (day_index + 1) % len(DAYS)

        # Оптимизация: группируем уроки в непрерывные блоки
        for day in DAYS:
            daily_lessons = lessons_by_day[day]
            if not daily_lessons:
                continue

            # Сортируем уроки по сложности размещения
            daily_lessons.sort(key=lambda x: len(SUBJECT_ROOMS.get(x[0].name, [])))

            # Пытаемся разместить уроки непрерывным блоком
            target_slots = list(range(1, len(daily_lessons) + 1))
            random.shuffle(target_slots)  # Начинаем со случайной позиции

            for lesson_data in daily_lessons:
                subj, teacher, room = lesson_data
                placed = False

                # Пробуем слоты в порядке близости к началу блока
                for slot in sorted(target_slots, key=lambda s: abs(s - target_slots[0])):
                    slot_key = (day, slot)

                    # Проверяем доступность
                    if (school_class.id in busy_slots[slot_key]["classes"] or
                            teacher.id in busy_slots[slot_key]["teachers"] or
                            room.id in busy_slots[slot_key]["rooms"]):
                        continue

                    # Нашли свободный слот - размещаем урок
                    db.add(Lesson(
                        class_id=school_class.id,
                        subject_id=subj.id,
                        teacher_id=teacher.id,
                        room_id=room.id,
                        day=day,
                        lesson_number=slot
                    ))

                    # Обновляем информацию о занятости
                    busy_slots[slot_key]["classes"].add(school_class.id)
                    busy_slots[slot_key]["teachers"].add(teacher.id)
                    busy_slots[slot_key]["rooms"].add(room.id)

                    # Убираем использованный слот из целевых
                    if slot in target_slots:
                        target_slots.remove(slot)

                    placed = True
                    break

                if not placed:
                    # Если не удалось разместить в целевом блоке, ищем любой свободный слот
                    for slot in SLOTS:
                        slot_key = (day, slot)
                        if (school_class.id in busy_slots[slot_key]["classes"] or
                                teacher.id in busy_slots[slot_key]["teachers"] or
                                room.id in busy_slots[slot_key]["rooms"]):
                            continue

                        db.add(Lesson(
                            class_id=school_class.id,
                            subject_id=subj.id,
                            teacher_id=teacher.id,
                            room_id=room.id,
                            day=day,
                            lesson_number=slot
                        ))

                        busy_slots[slot_key]["classes"].add(school_class.id)
                        busy_slots[slot_key]["teachers"].add(teacher.id)
                        busy_slots[slot_key]["rooms"].add(room.id)
                        placed = True
                        break

                    if not placed:
                        print(f"❌ Не удалось поставить {subj.name} для {class_name} в день {day}")

    db.commit()
    print("✅ Генерация завершена. Минимизированы окна в расписании.")