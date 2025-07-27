# fast_api/main.py
from fastapi import FastAPI, Request, Form, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, joinedload
from .models import Base, SchoolClass, Subject, Room, Lesson, Teacher
from .genetic import generate_random_schedule
from datetime import date, timedelta

DATABASE_URL = "postgresql://postgres:ADx809Klm0p@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(debug=True)
templates = Jinja2Templates(directory="fast_api/templates")


def create_initial_data(db: Session):
    if db.query(SchoolClass).first() is not None:
        return  # Уже есть данные — не добавляем

    # 1. Классы: 1А, 1Б, ..., 11В
    for number in range(1, 12):
        for letter in ["А", "Б", "В"]:
            db.add(SchoolClass(number=number, letter=letter))
    db.commit()

    # 2. Учителя — расширенный список
    teachers = [
        Teacher(name="Иванов И.И. (алгебра)"),
        Teacher(name="Петрова А.В. (геометрия)"),
        Teacher(name="Сидорова Е.М. (физика)"),
        Teacher(name="Козлов Д.Н. (история)"),
        Teacher(name="Морозова Л.К. (биология)"),
        Teacher(name="Орлова Н.К. (русский язык)"),
        Teacher(name="Васильева Е.М. (английский)"),
        Teacher(name="Лебедев С.П. (литература)"),
        Teacher(name="Николаева Т.С. (химия)"),
        Teacher(name="Фёдоров А.Б. (информатика)"),
        Teacher(name="Смирнова О.П. (физкультура)"),
        Teacher(name="Кузнецова Р.И. (музыка)"),
        Teacher(name="Григорьев Д.М. (ОБЖ)"),
        Teacher(name="Борисова Л.А. (география)"),
        Teacher(name="Тихонов К.Е. (черчение)"),
        Teacher(name="Романова Ю.С. (обществознание)")
    ]
    for t in teachers:
        db.add(t)
    db.commit()

    # Запоминаем ID учителей по имени
    teacher_map = {t.name: t.id for t in db.query(Teacher).all()}

    # 3. Кабинеты — больше и понятнее
    rooms = [
        Room(name="Кабинет 101 (математика)"),
        Room(name="Кабинет 102 (алгебра)"),
        Room(name="Кабинет 103 (геометрия)"),
        Room(name="Кабинет 201 (физика)"),
        Room(name="Кабинет 202 (химия)"),
        Room(name="Кабинет 301 (биология)"),
        Room(name="Кабинет 302 (география)"),
        Room(name="Кабинет 401 (история)"),
        Room(name="Кабинет 402 (обществознание)"),
        Room(name="Кабинет 501 (русский язык)"),
        Room(name="Кабинет 502 (литература)"),
        Room(name="Кабинет 601 (английский)"),
        Room(name="Кабинет 602 (немецкий)"),
        Room(name="Кабинет 701 (информатика)"),
        Room(name="Кабинет 702 (черчение)"),
        Room(name="Кабинет 801 (музыка)"),
        Room(name="Кабинет 802 (ОБЖ)"),
        Room(name="Спортзал №1"),
        Room(name="Спортзал №2"),
        Room(name="Актовый зал"),
        Room(name="Библиотека"),
        Room(name="Столовая")
    ]
    for r in rooms:
        db.add(r)
    db.commit()

    # Запоминаем ID кабинетов
    room_map = {r.name: r.id for r in db.query(Room).all()}

    # 4. Предметы — с привязкой к учителям и часам в неделю
    subjects = [
        # Алгебра и геометрия — отдельно
        Subject(name="Алгебра", teacher_id=teacher_map["Иванов И.И. (алгебра)"], hours_per_week=4),
        Subject(name="Геометрия", teacher_id=teacher_map["Петрова А.В. (геометрия)"], hours_per_week=2),

        # Основные предметы
        Subject(name="Русский язык", teacher_id=teacher_map["Орлова Н.К. (русский язык)"], hours_per_week=5),
        Subject(name="Литература", teacher_id=teacher_map["Лебедев С.П. (литература)"], hours_per_week=3),
        Subject(name="Физика", teacher_id=teacher_map["Сидорова Е.М. (физика)"], hours_per_week=3),
        Subject(name="Химия", teacher_id=teacher_map["Николаева Т.С. (химия)"], hours_per_week=2),
        Subject(name="Биология", teacher_id=teacher_map["Морозова Л.К. (биология)"], hours_per_week=2),
        Subject(name="История", teacher_id=teacher_map["Козлов Д.Н. (история)"], hours_per_week=2),
        Subject(name="Обществознание", teacher_id=teacher_map["Романова Ю.С. (обществознание)"], hours_per_week=2),
        Subject(name="География", teacher_id=teacher_map["Борисова Л.А. (география)"], hours_per_week=2),
        Subject(name="Информатика", teacher_id=teacher_map["Фёдоров А.Б. (информатика)"], hours_per_week=2),
        Subject(name="Английский", teacher_id=teacher_map["Васильева Е.М. (английский)"], hours_per_week=3),
        Subject(name="Физкультура", teacher_id=teacher_map["Смирнова О.П. (физкультура)"], hours_per_week=2),
        Subject(name="Музыка", teacher_id=teacher_map["Кузнецова Р.И. (музыка)"], hours_per_week=1),
        Subject(name="ОБЖ", teacher_id=teacher_map["Григорьев Д.М. (ОБЖ)"], hours_per_week=1),
        Subject(name="Черчение", teacher_id=teacher_map["Тихонов К.Е. (черчение)"], hours_per_week=1),
    ]
    for s in subjects:
        db.add(s)
    db.commit()

    # Дополнительно: можно добавить "Окружающий мир" для 1–4 классов
    subjects_primary = [
        Subject(name="Окружающий мир", teacher_id=teacher_map["Орлова Н.К. (русский язык)"], hours_per_week=3),
        Subject(name="Трудовое воспитание", teacher_id=teacher_map["Смирнова О.П. (физкультура)"], hours_per_week=1),
        Subject(name="ИЗО", teacher_id=teacher_map["Кузнецова Р.И. (музыка)"], hours_per_week=1)
    ]
    for s in subjects_primary:
        db.add(s)
    db.commit()

    print("✅ Расширенные начальные данные добавлены в БД.")


# @app.on_event("startup")
# def on_startup():
#     Base.metadata.create_all(bind=engine)
#     db = SessionLocal()
#     try:
#         create_initial_data(db)
#     finally:
#         db.close()
@app.on_event("startup")
def on_startup():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        create_initial_data(db)
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def choose_class_number(request: Request, db: Session = Depends(get_db)):
    numbers = list(range(1, 12))
    return templates.TemplateResponse("choose_number.html", {"request": request, "numbers": numbers})


@app.get("/classes/{number}", response_class=HTMLResponse)
def choose_class_letter(request: Request, number: int, db: Session = Depends(get_db)):
    classes = db.query(SchoolClass).filter(SchoolClass.number == number).all()
    letters = [cls.letter for cls in classes]
    classes_dict = {cls.letter: cls.id for cls in classes}
    return templates.TemplateResponse("choose_letter.html", {
        "request": request,
        "number": number,
        "letters": letters,
        "classes_dict": classes_dict
    })


@app.get("/schedule", response_class=HTMLResponse)
def view_schedule(request: Request, class_id: int, week_offset: int = Query(0), db: Session = Depends(get_db)):
    school_class = db.query(SchoolClass).filter(SchoolClass.id == class_id).first()
    if not school_class:
        raise HTTPException(404, detail="Класс не найден")

    lessons = db.query(Lesson).filter(Lesson.class_id == class_id).options(
        joinedload(Lesson.subject).joinedload(Subject.teacher),
        joinedload(Lesson.room)
    ).all()

    lessons_by_day = {i: [""] * 8 for i in range(7)}
    for l in lessons:
        teacher_name = l.subject.teacher.name if l.subject and l.subject.teacher else "?"
        lessons_by_day[l.day][l.lesson_number - 1] = f"{l.subject.name} ({l.room.name}, {teacher_name})"

    today = date.today()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    days = [monday + timedelta(days=i) for i in range(7)]

    return templates.TemplateResponse("schedule.html", {
        "request": request,
        "class_id": class_id,
        "class_name": f"{school_class.number}{school_class.letter}",
        "days": days,
        "lessons_week": [lessons_by_day[i] for i in range(7)],
        "week_offset": week_offset
    })


@app.get("/add_lesson", response_class=HTMLResponse)
def form_add_lesson(request: Request, db: Session = Depends(get_db)):
    classes = db.query(SchoolClass).all()
    subjects = db.query(Subject).all()
    rooms = db.query(Room).all()
    teachers = db.query(Teacher).all()
    return templates.TemplateResponse("add_lesson.html", {
        "request": request,
        "classes": classes,
        "subjects": subjects,
        "rooms": rooms,
        "teachers": teachers
    })


@app.post("/add_lesson")
def add_lesson(
    class_id: int = Form(...),
    subject_id: int = Form(...),
    teacher_id: int = Form(...),
    room_id: int = Form(...),
    day: int = Form(...),
    lesson_number: int = Form(...),
    db: Session = Depends(get_db)
):
    if db.query(Lesson).filter_by(class_id=class_id, day=day, lesson_number=lesson_number).first():
        raise HTTPException(400, detail="У этого класса уже есть урок в это время.")
    if db.query(Lesson).filter_by(room_id=room_id, day=day, lesson_number=lesson_number).first():
        raise HTTPException(400, detail="Этот кабинет занят.")
    if db.query(Lesson).join(Subject).filter(
        Subject.teacher_id == teacher_id,
        Lesson.day == day,
        Lesson.lesson_number == lesson_number
    ).first():
        raise HTTPException(400, detail="Учитель занят.")

    lesson = Lesson(
        class_id=class_id,
        subject_id=subject_id,
        teacher_id=teacher_id,
        room_id=room_id,
        day=day,
        lesson_number=lesson_number
    )
    db.add(lesson)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/generate_schedule")
def generate_schedule(db: Session = Depends(get_db)):
    generate_random_schedule(db)
    return RedirectResponse(url="/", status_code=303)


@app.get("/delete_lesson", response_class=HTMLResponse)
def delete_lesson_form(request: Request, db: Session = Depends(get_db)):
    lessons = db.query(Lesson).options(
        joinedload(Lesson.school_class),
        joinedload(Lesson.subject),
        joinedload(Lesson.teacher),
        joinedload(Lesson.room)
    ).all()
    return templates.TemplateResponse("delete_lesson.html", {
        "request": request,
        "lessons": lessons
    })


@app.post("/delete_lesson")
def delete_lesson(lesson_id: int = Form(...), db: Session = Depends(get_db)):
    lesson = db.query(Lesson).filter_by(id=lesson_id).first()
    if lesson:
        db.delete(lesson)
        db.commit()
    return RedirectResponse(url="/", status_code=303)