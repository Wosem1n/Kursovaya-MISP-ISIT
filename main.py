from __future__ import annotations

import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

import db

STATUSES = ["учится", "академический отпуск", "отчислен", "выпускник"]
CONTROL_TYPES = ["экзамен", "зачёт", "курсовая работа", "дифференцированный зачёт"]
ASSESSMENT_TYPES = ["контрольная", "лабораторная", "зачёт", "экзамен", "курсовая", "итоговая"]
ATTENDANCE_STATUSES = ["присутствовал", "отсутствовал", "уважительная причина", "опоздал"]
EDUCATION_FORMS = ["очная", "заочная", "очно-заочная"]
ACTIVE_VALUES = ["да", "нет"]
COURSE_CREDITS = ["36", "72", "108", "144"]


class StudentCourseApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("ИС управления курсами и успеваемостью студентов")
        self.geometry("1280x780")
        self.minsize(1100, 680)

        db.ensure_database()

        self.group_map: dict[str, int] = {}
        self.department_map: dict[str, int] = {}
        self.teacher_map: dict[str, int] = {}
        self.course_map: dict[str, int] = {}
        self.assignment_map: dict[str, int] = {}
        self.enrollment_map: dict[str, int] = {}
        self.student_map: dict[str, int] = {}

        self.selected_student_id: int | None = None
        self.selected_course_id: int | None = None
        self.selected_teacher_id: int | None = None
        self.selected_group_id: int | None = None
        self.selected_department_id: int | None = None

        self._configure_style()
        self._build_layout()
        self.refresh_all()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TButton", padding=6)
        style.configure("TLabel", padding=2)
        style.configure("Treeview", rowheight=25)
        style.configure("Header.TLabel", font=("Arial", 14, "bold"))

    def _build_layout(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Система управления курсами и успеваемостью студентов", style="Header.TLabel").pack(side="left")
        ttk.Button(top, text="Обновить", command=self.refresh_all).pack(side="right", padx=4)
        ttk.Button(top, text="Пересоздать демо-БД", command=self.reset_database).pack(side="right", padx=4)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.students_tab = ttk.Frame(self.notebook, padding=8)
        self.groups_tab = ttk.Frame(self.notebook, padding=8)
        self.courses_tab = ttk.Frame(self.notebook, padding=8)
        self.departments_tab = ttk.Frame(self.notebook, padding=8)
        self.teachers_tab = ttk.Frame(self.notebook, padding=8)
        self.grades_tab = ttk.Frame(self.notebook, padding=8)
        self.reports_tab = ttk.Frame(self.notebook, padding=8)

        self.notebook.add(self.students_tab, text="Студенты")
        self.notebook.add(self.groups_tab, text="Группы")
        self.notebook.add(self.courses_tab, text="Курсы и назначения")
        self.notebook.add(self.departments_tab, text="Кафедры")
        self.notebook.add(self.teachers_tab, text="Преподаватели")
        self.notebook.add(self.grades_tab, text="Оценки и посещаемость")
        self.notebook.add(self.reports_tab, text="Отчёты")

        self._build_students_tab()
        self._build_groups_tab()
        self._build_courses_tab()
        self._build_departments_tab()
        self._build_teachers_tab()
        self._build_grades_tab()
        self._build_reports_tab()


    def _build_students_tab(self) -> None:
        form = ttk.LabelFrame(self.students_tab, text="Добавление / редактирование студента", padding=8)
        form.pack(fill="x")

        self.student_group_var = tk.StringVar()
        self.student_card_var = tk.StringVar()
        self.last_name_var = tk.StringVar()
        self.first_name_var = tk.StringVar()
        self.middle_name_var = tk.StringVar()
        self.birth_date_var = tk.StringVar(value="2004-01-01")
        self.student_email_var = tk.StringVar()
        self.student_phone_var = tk.StringVar()
        self.student_status_var = tk.StringVar(value="учится")

        self.student_group_combo = ttk.Combobox(form, textvariable=self.student_group_var, state="readonly", width=16)
        fields = [
            ("Группа", self.student_group_combo),
            ("№ зачётки", ttk.Entry(form, textvariable=self.student_card_var, width=14)),
            ("Фамилия", ttk.Entry(form, textvariable=self.last_name_var, width=16)),
            ("Имя", ttk.Entry(form, textvariable=self.first_name_var, width=16)),
            ("Отчество", ttk.Entry(form, textvariable=self.middle_name_var, width=16)),
            ("Дата рожд. YYYY-MM-DD", ttk.Entry(form, textvariable=self.birth_date_var, width=18)),
            ("Email", ttk.Entry(form, textvariable=self.student_email_var, width=22)),
            ("Телефон", ttk.Entry(form, textvariable=self.student_phone_var, width=16)),
            ("Статус", ttk.Combobox(form, textvariable=self.student_status_var, values=STATUSES, state="readonly", width=18)),
        ]
        for idx, (label, widget) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=idx, sticky="w", padx=3)
            widget.grid(row=1, column=idx, sticky="ew", padx=3, pady=3)

        actions = ttk.Frame(self.students_tab)
        actions.pack(fill="x", pady=(8, 4))
        ttk.Button(actions, text="Новый", command=self.clear_student_form).pack(side="left", padx=3)
        ttk.Button(actions, text="Добавить", command=self.add_student).pack(side="left", padx=3)
        ttk.Button(actions, text="Сохранить изменения", command=self.update_selected_student).pack(side="left", padx=3)
        ttk.Button(actions, text="Удалить выбранного", command=self.delete_selected_student).pack(side="left", padx=3)
        ttk.Button(actions, text="Статус: отчислен", command=lambda: self.change_selected_student_status("отчислен")).pack(side="left", padx=3)
        ttk.Button(actions, text="Статус: учится", command=lambda: self.change_selected_student_status("учится")).pack(side="left", padx=3)

        columns = ("student_id", "student_card", "fio", "birth_date", "group_code", "email", "phone", "status")
        self.students_tree = self._create_tree(self.students_tab, columns)
        self._set_tree_headings(
            self.students_tree,
            {
                "student_id": "ID",
                "student_card": "Зачётка",
                "fio": "ФИО",
                "birth_date": "Дата рождения",
                "group_code": "Группа",
                "email": "Email",
                "phone": "Телефон",
                "status": "Статус",
            },
        )
        self.students_tree.column("student_id", width=50, anchor="center")
        self.students_tree.column("student_card", width=90, anchor="center")
        self.students_tree.column("fio", width=230)
        self.students_tree.column("birth_date", width=110, anchor="center")
        self.students_tree.column("group_code", width=90, anchor="center")
        self.students_tree.column("email", width=180)
        self.students_tree.column("phone", width=140)
        self.students_tree.column("status", width=130, anchor="center")
        self.students_tree.bind("<<TreeviewSelect>>", self.on_student_select)


    def _build_groups_tab(self) -> None:
        form = ttk.LabelFrame(self.groups_tab, text="Добавление группы", padding=8)
        form.pack(fill="x")

        self.group_department_var = tk.StringVar()
        self.group_code_var = tk.StringVar()
        self.group_year_var = tk.StringVar(value="2026")
        self.group_form_var = tk.StringVar(value="очная")
        self.group_curator_var = tk.StringVar()

        self.group_department_combo = ttk.Combobox(form, textvariable=self.group_department_var, state="readonly", width=35)
        fields = [
            ("Кафедра", self.group_department_combo),
            ("Код группы", ttk.Entry(form, textvariable=self.group_code_var, width=14)),
            ("Год набора", ttk.Entry(form, textvariable=self.group_year_var, width=10)),
            ("Форма", ttk.Combobox(form, textvariable=self.group_form_var, values=EDUCATION_FORMS, state="readonly", width=16)),
            ("Куратор", ttk.Entry(form, textvariable=self.group_curator_var, width=28)),
        ]
        for idx, (label, widget) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=idx, sticky="w", padx=3)
            widget.grid(row=1, column=idx, sticky="ew", padx=3, pady=3)

        actions = ttk.Frame(self.groups_tab)
        actions.pack(fill="x", pady=(8, 4))
        ttk.Button(actions, text="Добавить группу", command=self.add_group).pack(side="left", padx=3)
        ttk.Button(actions, text="Удалить выбранную", command=self.delete_selected_group).pack(side="left", padx=3)

        columns = ("group_id", "code", "department_name", "admission_year", "education_form", "curator")
        self.groups_tree = self._create_tree(self.groups_tab, columns)
        self._set_tree_headings(
            self.groups_tree,
            {
                "group_id": "ID",
                "code": "Группа",
                "department_name": "Кафедра",
                "admission_year": "Год набора",
                "education_form": "Форма обучения",
                "curator": "Куратор",
            },
        )
        self.groups_tree.column("group_id", width=50, anchor="center")
        self.groups_tree.column("code", width=110, anchor="center")
        self.groups_tree.column("department_name", width=280)
        self.groups_tree.column("admission_year", width=100, anchor="center")
        self.groups_tree.column("education_form", width=130, anchor="center")
        self.groups_tree.column("curator", width=250)
        self.groups_tree.bind("<<TreeviewSelect>>", self.on_group_select)


    def _build_courses_tab(self) -> None:
        course_form = ttk.LabelFrame(self.courses_tab, text="Добавление / редактирование дисциплины", padding=8)
        course_form.pack(fill="x")

        self.course_department_var = tk.StringVar()
        self.course_code_var = tk.StringVar()
        self.course_title_var = tk.StringVar()
        self.credits_var = tk.StringVar(value="144")
        self.course_semester_var = tk.StringVar(value="1")
        self.control_type_var = tk.StringVar(value="экзамен")
        self.course_active_var = tk.StringVar(value="да")

        self.course_department_combo = ttk.Combobox(course_form, textvariable=self.course_department_var, state="readonly", width=30)
        widgets = [
            ("Кафедра", self.course_department_combo),
            ("Код", ttk.Entry(course_form, textvariable=self.course_code_var, width=12)),
            ("Название", ttk.Entry(course_form, textvariable=self.course_title_var, width=35)),
            ("Трудоёмкость", ttk.Combobox(course_form, textvariable=self.credits_var, values=COURSE_CREDITS, state="readonly", width=12)),
            ("Семестр", ttk.Entry(course_form, textvariable=self.course_semester_var, width=8)),
            ("Контроль", ttk.Combobox(course_form, textvariable=self.control_type_var, values=CONTROL_TYPES, state="readonly", width=24)),
            ("Активен", ttk.Combobox(course_form, textvariable=self.course_active_var, values=ACTIVE_VALUES, state="readonly", width=8)),
        ]
        for idx, (label, widget) in enumerate(widgets):
            ttk.Label(course_form, text=label).grid(row=0, column=idx, sticky="w", padx=3)
            widget.grid(row=1, column=idx, sticky="ew", padx=3, pady=3)

        course_actions = ttk.Frame(self.courses_tab)
        course_actions.pack(fill="x", pady=(8, 4))
        ttk.Button(course_actions, text="Новый", command=self.clear_course_form).pack(side="left", padx=3)
        ttk.Button(course_actions, text="Добавить курс", command=self.add_course).pack(side="left", padx=3)
        ttk.Button(course_actions, text="Сохранить изменения", command=self.update_selected_course).pack(side="left", padx=3)
        ttk.Button(course_actions, text="Удалить выбранный", command=self.delete_selected_course).pack(side="left", padx=3)

        columns = ("course_id", "code", "title", "department_name", "credits", "semester", "control_type", "is_active_text")
        self.courses_tree = self._create_tree(self.courses_tab, columns)
        self._set_tree_headings(
            self.courses_tree,
            {
                "course_id": "ID",
                "code": "Код",
                "title": "Дисциплина",
                "department_name": "Кафедра",
                "credits": "Трудоёмкость",
                "semester": "Семестр",
                "control_type": "Контроль",
                "is_active_text": "Активен",
            },
        )
        self.courses_tree.column("course_id", width=50, anchor="center")
        self.courses_tree.column("code", width=90, anchor="center")
        self.courses_tree.column("title", width=270)
        self.courses_tree.column("department_name", width=250)
        self.courses_tree.column("credits", width=60, anchor="center")
        self.courses_tree.column("semester", width=80, anchor="center")
        self.courses_tree.column("control_type", width=170, anchor="center")
        self.courses_tree.column("is_active_text", width=80, anchor="center")
        self.courses_tree.bind("<<TreeviewSelect>>", self.on_course_select)

        assignment_form = ttk.LabelFrame(self.courses_tab, text="Назначение дисциплины группе и преподавателю", padding=8)
        assignment_form.pack(fill="x", pady=(8, 4))

        self.assignment_course_var = tk.StringVar()
        self.assignment_teacher_var = tk.StringVar()
        self.assignment_group_var = tk.StringVar()
        self.academic_year_var = tk.StringVar(value="2025/2026")
        self.assignment_semester_var = tk.StringVar(value="1")

        self.assignment_course_combo = ttk.Combobox(assignment_form, textvariable=self.assignment_course_var, state="readonly", width=35)
        self.assignment_teacher_combo = ttk.Combobox(assignment_form, textvariable=self.assignment_teacher_var, state="readonly", width=34)
        self.assignment_group_combo = ttk.Combobox(assignment_form, textvariable=self.assignment_group_var, state="readonly", width=16)

        awidgets = [
            ("Дисциплина", self.assignment_course_combo),
            ("Преподаватель", self.assignment_teacher_combo),
            ("Группа", self.assignment_group_combo),
            ("Учебный год", ttk.Entry(assignment_form, textvariable=self.academic_year_var, width=12)),
            ("Семестр", ttk.Entry(assignment_form, textvariable=self.assignment_semester_var, width=8)),
        ]
        for idx, (label, widget) in enumerate(awidgets):
            ttk.Label(assignment_form, text=label).grid(row=0, column=idx, sticky="w", padx=3)
            widget.grid(row=1, column=idx, sticky="ew", padx=3, pady=3)
        ttk.Button(assignment_form, text="Назначить", command=self.add_assignment).grid(row=1, column=len(awidgets), padx=8)

        columns = ("course_code", "course_title", "group_code", "teacher_name", "academic_year", "semester")
        self.assignments_tree = self._create_tree(self.courses_tab, columns)
        self._set_tree_headings(
            self.assignments_tree,
            {
                "course_code": "Код",
                "course_title": "Дисциплина",
                "group_code": "Группа",
                "teacher_name": "Преподаватель",
                "academic_year": "Учебный год",
                "semester": "Семестр",
            },
        )
        self.assignments_tree.column("course_code", width=90, anchor="center")
        self.assignments_tree.column("course_title", width=300)
        self.assignments_tree.column("group_code", width=90, anchor="center")
        self.assignments_tree.column("teacher_name", width=220)
        self.assignments_tree.column("academic_year", width=110, anchor="center")
        self.assignments_tree.column("semester", width=80, anchor="center")


    def _build_departments_tab(self) -> None:
        form = ttk.LabelFrame(self.departments_tab, text="Добавление кафедры", padding=8)
        form.pack(fill="x")

        self.department_name_var = tk.StringVar()
        self.department_head_var = tk.StringVar()
        self.department_phone_var = tk.StringVar()
        self.department_email_var = tk.StringVar()

        fields = [
            ("Название", ttk.Entry(form, textvariable=self.department_name_var, width=36)),
            ("Заведующий", ttk.Entry(form, textvariable=self.department_head_var, width=28)),
            ("Телефон", ttk.Entry(form, textvariable=self.department_phone_var, width=18)),
            ("Email", ttk.Entry(form, textvariable=self.department_email_var, width=24)),
        ]
        for idx, (label, widget) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=idx, sticky="w", padx=3)
            widget.grid(row=1, column=idx, sticky="ew", padx=3, pady=3)

        actions = ttk.Frame(self.departments_tab)
        actions.pack(fill="x", pady=(8, 4))
        ttk.Button(actions, text="Добавить кафедру", command=self.add_department).pack(side="left", padx=3)
        ttk.Button(actions, text="Удалить выбранную", command=self.delete_selected_department).pack(side="left", padx=3)

        columns = ("department_id", "name", "head_name", "phone", "email")
        self.departments_tree = self._create_tree(self.departments_tab, columns)
        self._set_tree_headings(
            self.departments_tree,
            {
                "department_id": "ID",
                "name": "Кафедра",
                "head_name": "Заведующий",
                "phone": "Телефон",
                "email": "Email",
            },
        )
        self.departments_tree.column("department_id", width=50, anchor="center")
        self.departments_tree.column("name", width=330)
        self.departments_tree.column("head_name", width=240)
        self.departments_tree.column("phone", width=160)
        self.departments_tree.column("email", width=220)
        self.departments_tree.bind("<<TreeviewSelect>>", self.on_department_select)


    def _build_teachers_tab(self) -> None:
        form = ttk.LabelFrame(self.teachers_tab, text="Добавление / редактирование преподавателя", padding=8)
        form.pack(fill="x")

        self.teacher_department_var = tk.StringVar()
        self.teacher_last_name_var = tk.StringVar()
        self.teacher_first_name_var = tk.StringVar()
        self.teacher_middle_name_var = tk.StringVar()
        self.teacher_email_var = tk.StringVar()
        self.teacher_phone_var = tk.StringVar()
        self.teacher_position_var = tk.StringVar(value="преподаватель")

        self.teacher_department_combo = ttk.Combobox(form, textvariable=self.teacher_department_var, state="readonly", width=34)
        fields = [
            ("Кафедра", self.teacher_department_combo),
            ("Фамилия", ttk.Entry(form, textvariable=self.teacher_last_name_var, width=16)),
            ("Имя", ttk.Entry(form, textvariable=self.teacher_first_name_var, width=16)),
            ("Отчество", ttk.Entry(form, textvariable=self.teacher_middle_name_var, width=16)),
            ("Email", ttk.Entry(form, textvariable=self.teacher_email_var, width=24)),
            ("Телефон", ttk.Entry(form, textvariable=self.teacher_phone_var, width=18)),
            ("Должность", ttk.Entry(form, textvariable=self.teacher_position_var, width=22)),
        ]
        for idx, (label, widget) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=idx, sticky="w", padx=3)
            widget.grid(row=1, column=idx, sticky="ew", padx=3, pady=3)

        actions = ttk.Frame(self.teachers_tab)
        actions.pack(fill="x", pady=(8, 4))
        ttk.Button(actions, text="Новый", command=self.clear_teacher_form).pack(side="left", padx=3)
        ttk.Button(actions, text="Добавить", command=self.add_teacher).pack(side="left", padx=3)
        ttk.Button(actions, text="Сохранить изменения", command=self.update_selected_teacher).pack(side="left", padx=3)
        ttk.Button(actions, text="Удалить выбранного", command=self.delete_selected_teacher).pack(side="left", padx=3)

        columns = ("teacher_id", "fio", "department_name", "email", "phone", "position")
        self.teachers_tree = self._create_tree(self.teachers_tab, columns)
        self._set_tree_headings(
            self.teachers_tree,
            {
                "teacher_id": "ID",
                "fio": "ФИО",
                "department_name": "Кафедра",
                "email": "Email",
                "phone": "Телефон",
                "position": "Должность",
            },
        )
        self.teachers_tree.column("teacher_id", width=50, anchor="center")
        self.teachers_tree.column("fio", width=230)
        self.teachers_tree.column("department_name", width=280)
        self.teachers_tree.column("email", width=220)
        self.teachers_tree.column("phone", width=150)
        self.teachers_tree.column("position", width=180)
        self.teachers_tree.bind("<<TreeviewSelect>>", self.on_teacher_select)


    def _build_grades_tab(self) -> None:
        enroll_form = ttk.LabelFrame(self.grades_tab, text="Запись студента на назначенную дисциплину", padding=8)
        enroll_form.pack(fill="x")

        self.enroll_student_var = tk.StringVar()
        self.enroll_assignment_var = tk.StringVar()
        self.enroll_student_combo = ttk.Combobox(enroll_form, textvariable=self.enroll_student_var, state="readonly", width=34)
        self.enroll_assignment_combo = ttk.Combobox(enroll_form, textvariable=self.enroll_assignment_var, state="readonly", width=70)
        ttk.Label(enroll_form, text="Студент").grid(row=0, column=0, sticky="w", padx=3)
        ttk.Label(enroll_form, text="Дисциплина/группа/преподаватель").grid(row=0, column=1, sticky="w", padx=3)
        self.enroll_student_combo.grid(row=1, column=0, sticky="ew", padx=3, pady=3)
        self.enroll_assignment_combo.grid(row=1, column=1, sticky="ew", padx=3, pady=3)
        ttk.Button(enroll_form, text="Записать", command=self.enroll_student).grid(row=1, column=2, padx=8)

        grade_form = ttk.LabelFrame(self.grades_tab, text="Добавление / изменение оценки", padding=8)
        grade_form.pack(fill="x", pady=(8, 4))

        self.grade_enrollment_var = tk.StringVar()
        self.assessment_type_var = tk.StringVar(value="итоговая")
        self.grade_var = tk.StringVar(value="5")
        self.points_var = tk.StringVar(value="90")
        self.grade_comment_var = tk.StringVar()

        self.grade_enrollment_combo = ttk.Combobox(grade_form, textvariable=self.grade_enrollment_var, state="readonly", width=70)
        gwidgets = [
            ("Студент — дисциплина", self.grade_enrollment_combo),
            ("Тип", ttk.Combobox(grade_form, textvariable=self.assessment_type_var, values=ASSESSMENT_TYPES, state="readonly", width=16)),
            ("Оценка", ttk.Entry(grade_form, textvariable=self.grade_var, width=8)),
            ("Баллы", ttk.Entry(grade_form, textvariable=self.points_var, width=8)),
            ("Комментарий", ttk.Entry(grade_form, textvariable=self.grade_comment_var, width=32)),
        ]
        for idx, (label, widget) in enumerate(gwidgets):
            ttk.Label(grade_form, text=label).grid(row=0, column=idx, sticky="w", padx=3)
            widget.grid(row=1, column=idx, sticky="ew", padx=3, pady=3)
        ttk.Button(grade_form, text="Сохранить оценку", command=self.add_or_update_assessment).grid(row=1, column=len(gwidgets), padx=8)

        att_form = ttk.LabelFrame(self.grades_tab, text="Посещаемость", padding=8)
        att_form.pack(fill="x", pady=(8, 4))

        self.att_enrollment_var = tk.StringVar()
        self.att_date_var = tk.StringVar(value="2026-02-20")
        self.att_status_var = tk.StringVar(value="присутствовал")
        self.att_comment_var = tk.StringVar()
        self.att_enrollment_combo = ttk.Combobox(att_form, textvariable=self.att_enrollment_var, state="readonly", width=70)
        awidgets = [
            ("Студент — дисциплина", self.att_enrollment_combo),
            ("Дата YYYY-MM-DD", ttk.Entry(att_form, textvariable=self.att_date_var, width=14)),
            ("Статус", ttk.Combobox(att_form, textvariable=self.att_status_var, values=ATTENDANCE_STATUSES, state="readonly", width=22)),
            ("Комментарий", ttk.Entry(att_form, textvariable=self.att_comment_var, width=32)),
        ]
        for idx, (label, widget) in enumerate(awidgets):
            ttk.Label(att_form, text=label).grid(row=0, column=idx, sticky="w", padx=3)
            widget.grid(row=1, column=idx, sticky="ew", padx=3, pady=3)
        ttk.Button(att_form, text="Сохранить посещаемость", command=self.add_attendance).grid(row=1, column=len(awidgets), padx=8)

        grades_table = ttk.LabelFrame(self.grades_tab, text="Текущие оценки", padding=4)
        grades_table.pack(fill="both", expand=True, pady=(8, 4))

        columns = ("student_name", "group_code", "course_title", "assessment_type", "grade", "points", "assessed_at")
        self.grades_tree = self._create_tree(grades_table, columns)
        self._set_tree_headings(
            self.grades_tree,
            {
                "student_name": "Студент",
                "group_code": "Группа",
                "course_title": "Дисциплина",
                "assessment_type": "Тип",
                "grade": "Оценка",
                "points": "Баллы",
                "assessed_at": "Дата GMT+5",
            },
        )
        self.grades_tree.column("student_name", width=220)
        self.grades_tree.column("group_code", width=80, anchor="center")
        self.grades_tree.column("course_title", width=300)
        self.grades_tree.column("assessment_type", width=120, anchor="center")
        self.grades_tree.column("grade", width=80, anchor="center")
        self.grades_tree.column("points", width=80, anchor="center")
        self.grades_tree.column("assessed_at", width=160, anchor="center")

        attendance_table = ttk.LabelFrame(self.grades_tab, text="Текущая посещаемость", padding=4)
        attendance_table.pack(fill="both", expand=True, pady=(4, 0))

        att_columns = ("attendance_id", "lesson_date", "student_name", "group_code", "course_title", "status", "comment")
        self.attendance_tree = self._create_tree(attendance_table, att_columns)
        self._set_tree_headings(
            self.attendance_tree,
            {
                "attendance_id": "ID",
                "lesson_date": "Дата",
                "student_name": "Студент",
                "group_code": "Группа",
                "course_title": "Дисциплина",
                "status": "Статус",
                "comment": "Комментарий",
            },
        )
        self.attendance_tree.column("attendance_id", width=50, anchor="center")
        self.attendance_tree.column("lesson_date", width=100, anchor="center")
        self.attendance_tree.column("student_name", width=220)
        self.attendance_tree.column("group_code", width=80, anchor="center")
        self.attendance_tree.column("course_title", width=300)
        self.attendance_tree.column("status", width=160, anchor="center")
        self.attendance_tree.column("comment", width=260)


    def _build_reports_tab(self) -> None:
        toolbar = ttk.Frame(self.reports_tab)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="Успеваемость", command=self.show_progress_report).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Средний балл по группам", command=self.show_group_average_report).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Задолженности", command=self.show_debts_report).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Посещаемость", command=self.show_attendance_report).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Журнал всех изменений", command=self.show_audit_report).pack(side="left", padx=3)

        self.report_tree_frame = ttk.Frame(self.reports_tab)
        self.report_tree_frame.pack(fill="both", expand=True)
        self.report_tree: ttk.Treeview | None = None


    def _create_tree(self, parent: tk.Widget, columns: tuple[str, ...]) -> ttk.Treeview:
        wrapper = ttk.Frame(parent)
        wrapper.pack(fill="both", expand=True)
        tree = ttk.Treeview(wrapper, columns=columns, show="headings")
        y_scroll = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        x_scroll = ttk.Scrollbar(wrapper, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        wrapper.rowconfigure(0, weight=1)
        wrapper.columnconfigure(0, weight=1)
        return tree

    @staticmethod
    def _set_tree_headings(tree: ttk.Treeview, headings: dict[str, str]) -> None:
        for key, title in headings.items():
            tree.heading(key, text=title)

    @staticmethod
    def _clear_tree(tree: ttk.Treeview) -> None:
        tree.delete(*tree.get_children())

    @staticmethod
    def _select_first(variable: tk.StringVar, values: list[str]) -> None:
        if values:
            if variable.get() not in values:
                variable.set(values[0])
        else:
            variable.set("")

    @staticmethod
    def _selected_id(tree: ttk.Treeview, warning_text: str) -> int | None:
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Нет выбора", warning_text)
            return None
        return int(tree.item(selected[0], "values")[0])

    @staticmethod
    def _selected_id_silent(tree: ttk.Treeview) -> int | None:
        selected = tree.selection()
        if not selected:
            return None
        return int(tree.item(selected[0], "values")[0])

    @staticmethod
    def _find_key_by_id(mapping: dict[str, int], target_id: int) -> str:
        for text, value in mapping.items():
            if value == target_id:
                return text
        return ""

    @staticmethod
    def _handle_error(action: str, exc: Exception) -> None:
        messagebox.showerror("Ошибка", f"Не удалось {action}:\n{exc}")

    def refresh_all(self) -> None:
        self.load_combo_data()
        self.load_students()
        self.load_groups()
        self.load_departments()
        self.load_teachers()
        self.load_courses()
        self.load_assignments()
        self.load_grades()
        self.load_attendance()
        self.show_progress_report()

    def load_combo_data(self) -> None:
        groups = db.get_groups()
        self.group_map = {row["code"]: row["group_id"] for row in groups}
        group_values = list(self.group_map.keys())

        departments = db.get_departments()
        self.department_map = {row["name"]: row["department_id"] for row in departments}
        department_values = list(self.department_map.keys())

        teachers = db.get_teachers()
        self.teacher_map = {row["teacher_name"]: row["teacher_id"] for row in teachers}
        teacher_values = list(self.teacher_map.keys())

        courses = db.get_courses()
        self.course_map = {f'{row["code"]} — {row["title"]}': row["course_id"] for row in courses}
        course_values = list(self.course_map.keys())

        assignments = db.get_assignments()
        self.assignment_map = {row["assignment_name"]: row["assignment_id"] for row in assignments}
        assignment_values = list(self.assignment_map.keys())

        students = db.fetch_all(
            """
            SELECT student_id,
                   last_name || ' ' || first_name || ' (' || student_card || ')' AS student_name
            FROM students
            ORDER BY last_name, first_name;
            """
        )
        self.student_map = {row["student_name"]: row["student_id"] for row in students}
        student_values = list(self.student_map.keys())

        enrollments = db.get_enrollments_for_combo()
        self.enrollment_map = {row["enrollment_name"]: row["enrollment_id"] for row in enrollments}
        enrollment_values = list(self.enrollment_map.keys())

        for combo in [self.student_group_combo, self.assignment_group_combo]:
            combo.configure(values=group_values)
        for combo in [self.course_department_combo, self.group_department_combo, self.teacher_department_combo]:
            combo.configure(values=department_values)
        self.assignment_teacher_combo.configure(values=teacher_values)
        self.assignment_course_combo.configure(values=course_values)
        self.enroll_student_combo.configure(values=student_values)
        self.enroll_assignment_combo.configure(values=assignment_values)
        self.grade_enrollment_combo.configure(values=enrollment_values)
        self.att_enrollment_combo.configure(values=enrollment_values)

        self._select_first(self.student_group_var, group_values)
        self._select_first(self.assignment_group_var, group_values)
        self._select_first(self.course_department_var, department_values)
        self._select_first(self.group_department_var, department_values)
        self._select_first(self.teacher_department_var, department_values)
        self._select_first(self.assignment_teacher_var, teacher_values)
        self._select_first(self.assignment_course_var, course_values)
        self._select_first(self.enroll_student_var, student_values)
        self._select_first(self.enroll_assignment_var, assignment_values)
        self._select_first(self.grade_enrollment_var, enrollment_values)
        self._select_first(self.att_enrollment_var, enrollment_values)


    def load_students(self) -> None:
        self._clear_tree(self.students_tree)
        for row in db.get_students():
            fio = f'{row["last_name"]} {row["first_name"]} {row["middle_name"]}'.strip()
            self.students_tree.insert(
                "",
                "end",
                values=(
                    row["student_id"],
                    row["student_card"],
                    fio,
                    row["birth_date"],
                    row["group_code"],
                    row["email"],
                    row["phone"],
                    row["status"],
                ),
            )

    def load_groups(self) -> None:
        self._clear_tree(self.groups_tree)
        for row in db.get_groups_full():
            self.groups_tree.insert("", "end", values=tuple(row[col] for col in self.groups_tree["columns"]))

    def load_departments(self) -> None:
        self._clear_tree(self.departments_tree)
        for row in db.get_departments_full():
            self.departments_tree.insert("", "end", values=tuple(row[col] for col in self.departments_tree["columns"]))

    def load_teachers(self) -> None:
        self._clear_tree(self.teachers_tree)
        for row in db.get_teachers_full():
            fio = f'{row["last_name"]} {row["first_name"]} {row["middle_name"]}'.strip()
            self.teachers_tree.insert(
                "",
                "end",
                values=(row["teacher_id"], fio, row["department_name"], row["email"], row["phone"], row["position"]),
            )

    def load_courses(self) -> None:
        self._clear_tree(self.courses_tree)
        for row in db.get_courses_full():
            self.courses_tree.insert("", "end", values=tuple(row[col] for col in self.courses_tree["columns"]))

    def load_assignments(self) -> None:
        self._clear_tree(self.assignments_tree)
        rows = db.fetch_all(
            """
            SELECT c.code AS course_code,
                   c.title AS course_title,
                   g.code AS group_code,
                   t.last_name || ' ' || t.first_name AS teacher_name,
                   ca.academic_year,
                   ca.semester
            FROM course_assignments ca
            JOIN courses c ON c.course_id = ca.course_id
            JOIN student_groups g ON g.group_id = ca.group_id
            JOIN teachers t ON t.teacher_id = ca.teacher_id
            ORDER BY c.title, g.code;
            """
        )
        for row in rows:
            self.assignments_tree.insert("", "end", values=tuple(row[col] for col in self.assignments_tree["columns"]))

    def load_grades(self) -> None:
        self._clear_tree(self.grades_tree)
        rows = db.fetch_all(
            """
            SELECT student_name, group_code, course_title, assessment_type, grade, points, assessed_at
            FROM v_student_progress
            WHERE assessment_type IS NOT NULL
            ORDER BY group_code, student_name, course_title;
            """
        )
        for row in rows:
            self.grades_tree.insert("", "end", values=tuple(row[col] for col in self.grades_tree["columns"]))

    def load_attendance(self) -> None:
        self._clear_tree(self.attendance_tree)
        for row in db.get_attendance_records():
            self.attendance_tree.insert("", "end", values=tuple(row[col] for col in self.attendance_tree["columns"]))


    def on_student_select(self, _event: tk.Event | None = None) -> None:
        student_id = self._selected_id_silent(self.students_tree)
        if student_id is None:
            return
        row = db.get_student(student_id)
        if row is None:
            return
        self.selected_student_id = student_id
        self.student_group_var.set(self._find_key_by_id(self.group_map, row["group_id"]))
        self.student_card_var.set(row["student_card"])
        self.last_name_var.set(row["last_name"])
        self.first_name_var.set(row["first_name"])
        self.middle_name_var.set(row["middle_name"])
        self.birth_date_var.set(row["birth_date"])
        self.student_email_var.set(row["email"])
        self.student_phone_var.set(row["phone"])
        self.student_status_var.set(row["status"])

    def on_group_select(self, _event: tk.Event | None = None) -> None:
        group_id = self._selected_id_silent(self.groups_tree)
        if group_id is not None:
            self.selected_group_id = group_id

    def on_department_select(self, _event: tk.Event | None = None) -> None:
        department_id = self._selected_id_silent(self.departments_tree)
        if department_id is not None:
            self.selected_department_id = department_id

    def on_teacher_select(self, _event: tk.Event | None = None) -> None:
        teacher_id = self._selected_id_silent(self.teachers_tree)
        if teacher_id is None:
            return
        row = db.get_teacher(teacher_id)
        if row is None:
            return
        self.selected_teacher_id = teacher_id
        self.teacher_department_var.set(self._find_key_by_id(self.department_map, row["department_id"]))
        self.teacher_last_name_var.set(row["last_name"])
        self.teacher_first_name_var.set(row["first_name"])
        self.teacher_middle_name_var.set(row["middle_name"])
        self.teacher_email_var.set(row["email"])
        self.teacher_phone_var.set(row["phone"])
        self.teacher_position_var.set(row["position"])

    def on_course_select(self, _event: tk.Event | None = None) -> None:
        course_id = self._selected_id_silent(self.courses_tree)
        if course_id is None:
            return
        row = db.get_course(course_id)
        if row is None:
            return
        self.selected_course_id = course_id
        self.course_department_var.set(self._find_key_by_id(self.department_map, row["department_id"]))
        self.course_code_var.set(row["code"])
        self.course_title_var.set(row["title"])
        self.credits_var.set(str(row["credits"]))
        self.course_semester_var.set(str(row["semester"]))
        self.control_type_var.set(row["control_type"])
        self.course_active_var.set("да" if row["is_active"] == 1 else "нет")


    def clear_student_form(self) -> None:
        self.selected_student_id = None
        self.student_card_var.set("")
        self.last_name_var.set("")
        self.first_name_var.set("")
        self.middle_name_var.set("")
        self.birth_date_var.set("2004-01-01")
        self.student_email_var.set("")
        self.student_phone_var.set("")
        self.student_status_var.set("учится")
        if self.students_tree.selection():
            self.students_tree.selection_remove(*self.students_tree.selection())

    def clear_course_form(self) -> None:
        self.selected_course_id = None
        self.course_code_var.set("")
        self.course_title_var.set("")
        self.credits_var.set("144")
        self.course_semester_var.set("1")
        self.control_type_var.set("экзамен")
        self.course_active_var.set("да")
        if self.courses_tree.selection():
            self.courses_tree.selection_remove(*self.courses_tree.selection())

    def clear_teacher_form(self) -> None:
        self.selected_teacher_id = None
        self.teacher_last_name_var.set("")
        self.teacher_first_name_var.set("")
        self.teacher_middle_name_var.set("")
        self.teacher_email_var.set("")
        self.teacher_phone_var.set("")
        self.teacher_position_var.set("преподаватель")
        if self.teachers_tree.selection():
            self.teachers_tree.selection_remove(*self.teachers_tree.selection())


    def _read_student_form(self) -> tuple[int, str, str, str, str, str, str, str, str]:
        group_id = self.group_map[self.student_group_var.get()]
        student_card = self.student_card_var.get().strip()
        last_name = self.last_name_var.get().strip()
        first_name = self.first_name_var.get().strip()
        middle_name = self.middle_name_var.get().strip()
        birth_date = self.birth_date_var.get().strip()
        email = self.student_email_var.get().strip()
        phone = self.student_phone_var.get().strip()
        status = self.student_status_var.get()
        if not all([student_card, last_name, first_name, birth_date]):
            raise ValueError("Заполните зачётку, фамилию, имя и дату рождения.")
        return group_id, student_card, last_name, first_name, middle_name, birth_date, email, phone, status

    def add_student(self) -> None:
        try:
            db.add_student(*self._read_student_form())
            self.clear_student_form()
            self.refresh_all()
            messagebox.showinfo("Готово", "Студент добавлен.")
        except (sqlite3.IntegrityError, ValueError, KeyError) as exc:
            self._handle_error("добавить студента", exc)

    def update_selected_student(self) -> None:
        if self.selected_student_id is None:
            messagebox.showwarning("Нет выбора", "Выберите студента в таблице.")
            return
        try:
            db.update_student(self.selected_student_id, *self._read_student_form())
            self.refresh_all()
            messagebox.showinfo("Готово", "Данные студента обновлены.")
        except (sqlite3.IntegrityError, ValueError, KeyError) as exc:
            self._handle_error("обновить данные студента", exc)

    def delete_selected_student(self) -> None:
        student_id = self.selected_student_id or self._selected_id(self.students_tree, "Выберите студента в таблице.")
        if student_id is None:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранного студента? Связанные записи об оценках и посещаемости тоже будут удалены."):
            return
        try:
            db.delete_student(student_id)
            self.clear_student_form()
            self.refresh_all()
            messagebox.showinfo("Готово", "Студент удалён.")
        except sqlite3.IntegrityError as exc:
            self._handle_error("удалить студента", exc)

    def change_selected_student_status(self, status: str) -> None:
        student_id = self.selected_student_id or self._selected_id(self.students_tree, "Выберите студента в таблице.")
        if student_id is None:
            return
        db.update_student_status(student_id, status)
        self.refresh_all()


    def add_group(self) -> None:
        try:
            department_id = self.department_map[self.group_department_var.get()]
            code = self.group_code_var.get().strip()
            admission_year = int(self.group_year_var.get())
            education_form = self.group_form_var.get()
            curator = self.group_curator_var.get().strip()
            if not code:
                raise ValueError("Заполните код группы.")
            db.add_group(department_id, code, admission_year, education_form, curator)
            self.group_code_var.set("")
            self.group_curator_var.set("")
            self.refresh_all()
            messagebox.showinfo("Готово", "Группа добавлена.")
        except (sqlite3.IntegrityError, ValueError, KeyError) as exc:
            self._handle_error("добавить группу", exc)

    def delete_selected_group(self) -> None:
        group_id = self.selected_group_id or self._selected_id(self.groups_tree, "Выберите группу в таблице.")
        if group_id is None:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранную группу? Если в группе есть студенты или назначения, БД не даст удалить запись."):
            return
        try:
            db.delete_group(group_id)
            self.selected_group_id = None
            self.refresh_all()
            messagebox.showinfo("Готово", "Группа удалена.")
        except sqlite3.IntegrityError as exc:
            self._handle_error("удалить группу", exc)


    def add_department(self) -> None:
        try:
            name = self.department_name_var.get().strip()
            head = self.department_head_var.get().strip()
            phone = self.department_phone_var.get().strip()
            email = self.department_email_var.get().strip()
            if not name or not head:
                raise ValueError("Заполните название кафедры и заведующего.")
            db.add_department(name, head, phone, email)
            self.department_name_var.set("")
            self.department_head_var.set("")
            self.department_phone_var.set("")
            self.department_email_var.set("")
            self.refresh_all()
            messagebox.showinfo("Готово", "Кафедра добавлена.")
        except (sqlite3.IntegrityError, ValueError) as exc:
            self._handle_error("добавить кафедру", exc)

    def delete_selected_department(self) -> None:
        department_id = self.selected_department_id or self._selected_id(self.departments_tree, "Выберите кафедру в таблице.")
        if department_id is None:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранную кафедру? Если к ней привязаны группы, курсы или преподаватели, БД не даст удалить запись."):
            return
        try:
            db.delete_department(department_id)
            self.selected_department_id = None
            self.refresh_all()
            messagebox.showinfo("Готово", "Кафедра удалена.")
        except sqlite3.IntegrityError as exc:
            self._handle_error("удалить кафедру", exc)


    def _read_teacher_form(self) -> tuple[int, str, str, str, str, str, str]:
        department_id = self.department_map[self.teacher_department_var.get()]
        last_name = self.teacher_last_name_var.get().strip()
        first_name = self.teacher_first_name_var.get().strip()
        middle_name = self.teacher_middle_name_var.get().strip()
        email = self.teacher_email_var.get().strip()
        phone = self.teacher_phone_var.get().strip()
        position = self.teacher_position_var.get().strip()
        if not all([last_name, first_name, email, position]):
            raise ValueError("Заполните фамилию, имя, email и должность.")
        return department_id, last_name, first_name, middle_name, email, phone, position

    def add_teacher(self) -> None:
        try:
            db.add_teacher(*self._read_teacher_form())
            self.clear_teacher_form()
            self.refresh_all()
            messagebox.showinfo("Готово", "Преподаватель добавлен.")
        except (sqlite3.IntegrityError, ValueError, KeyError) as exc:
            self._handle_error("добавить преподавателя", exc)

    def update_selected_teacher(self) -> None:
        if self.selected_teacher_id is None:
            messagebox.showwarning("Нет выбора", "Выберите преподавателя в таблице.")
            return
        try:
            db.update_teacher(self.selected_teacher_id, *self._read_teacher_form())
            self.refresh_all()
            messagebox.showinfo("Готово", "Данные преподавателя обновлены.")
        except (sqlite3.IntegrityError, ValueError, KeyError) as exc:
            self._handle_error("обновить данные преподавателя", exc)

    def delete_selected_teacher(self) -> None:
        teacher_id = self.selected_teacher_id or self._selected_id(self.teachers_tree, "Выберите преподавателя в таблице.")
        if teacher_id is None:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранного преподавателя? Если у него есть назначения дисциплин, БД не даст удалить запись."):
            return
        try:
            db.delete_teacher(teacher_id)
            self.clear_teacher_form()
            self.refresh_all()
            messagebox.showinfo("Готово", "Преподаватель удалён.")
        except sqlite3.IntegrityError as exc:
            self._handle_error("удалить преподавателя", exc)


    def _read_course_form(self) -> tuple[int, str, str, int, int, str, int]:
        department_id = self.department_map[self.course_department_var.get()]
        code = self.course_code_var.get().strip()
        title = self.course_title_var.get().strip()
        credits = int(self.credits_var.get())
        semester = int(self.course_semester_var.get())
        control_type = self.control_type_var.get()
        is_active = 1 if self.course_active_var.get() == "да" else 0
        if not code or not title:
            raise ValueError("Заполните код и название дисциплины.")
        if credits not in (36, 72, 108, 144):
            raise ValueError("Трудоёмкость должна быть 36, 72, 108 или 144.")
        return department_id, code, title, credits, semester, control_type, is_active

    def add_course(self) -> None:
        try:
            db.add_course(*self._read_course_form())
            self.clear_course_form()
            self.refresh_all()
            messagebox.showinfo("Готово", "Дисциплина добавлена.")
        except (sqlite3.IntegrityError, ValueError, KeyError) as exc:
            self._handle_error("добавить дисциплину", exc)

    def update_selected_course(self) -> None:
        if self.selected_course_id is None:
            messagebox.showwarning("Нет выбора", "Выберите курс в таблице.")
            return
        try:
            db.update_course(self.selected_course_id, *self._read_course_form())
            self.refresh_all()
            messagebox.showinfo("Готово", "Данные дисциплины обновлены.")
        except (sqlite3.IntegrityError, ValueError, KeyError) as exc:
            self._handle_error("обновить дисциплину", exc)

    def delete_selected_course(self) -> None:
        course_id = self.selected_course_id or self._selected_id(self.courses_tree, "Выберите курс в таблице.")
        if course_id is None:
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранный курс? Если курс назначен группам, БД не даст удалить запись."):
            return
        try:
            db.delete_course(course_id)
            self.clear_course_form()
            self.refresh_all()
            messagebox.showinfo("Готово", "Дисциплина удалена.")
        except sqlite3.IntegrityError as exc:
            self._handle_error("удалить дисциплину", exc)


    def reset_database(self) -> None:
        if not messagebox.askyesno("Подтверждение", "Пересоздать базу данных и вернуть демонстрационные данные?"):
            return
        db.initialize_database(with_demo_data=True, reset=True)
        self.selected_student_id = None
        self.selected_course_id = None
        self.selected_teacher_id = None
        self.selected_group_id = None
        self.selected_department_id = None
        self.refresh_all()
        messagebox.showinfo("Готово", "База данных пересоздана.")

    def add_assignment(self) -> None:
        try:
            course_id = self.course_map[self.assignment_course_var.get()]
            teacher_id = self.teacher_map[self.assignment_teacher_var.get()]
            group_id = self.group_map[self.assignment_group_var.get()]
            academic_year = self.academic_year_var.get().strip()
            semester = int(self.assignment_semester_var.get())
            if not academic_year:
                raise ValueError("Заполните учебный год.")
            db.add_course_assignment(course_id, teacher_id, group_id, academic_year, semester)
            self.refresh_all()
            messagebox.showinfo("Готово", "Назначение создано.")
        except (sqlite3.IntegrityError, ValueError, KeyError) as exc:
            self._handle_error("создать назначение", exc)

    def enroll_student(self) -> None:
        try:
            student_id = self.student_map[self.enroll_student_var.get()]
            assignment_id = self.assignment_map[self.enroll_assignment_var.get()]
            db.enroll_student(student_id, assignment_id)
            self.refresh_all()
            messagebox.showinfo("Готово", "Студент записан на дисциплину.")
        except (sqlite3.IntegrityError, ValueError, KeyError) as exc:
            self._handle_error("записать студента", exc)

    def add_or_update_assessment(self) -> None:
        try:
            enrollment_id = self.enrollment_map[self.grade_enrollment_var.get()]
            grade = int(self.grade_var.get())
            points = int(self.points_var.get())
            if grade < 2 or grade > 5:
                raise ValueError("Оценка должна быть от 2 до 5.")
            if points < 0 or points > 100:
                raise ValueError("Баллы должны быть от 0 до 100.")
            db.add_or_update_assessment(enrollment_id, self.assessment_type_var.get(), grade, points, self.grade_comment_var.get().strip())
            self.refresh_all()
            messagebox.showinfo("Готово", "Оценка сохранена. Запись также появилась в журнале триггеров.")
        except (sqlite3.IntegrityError, ValueError, KeyError) as exc:
            self._handle_error("сохранить оценку", exc)

    def add_attendance(self) -> None:
        try:
            enrollment_id = self.enrollment_map[self.att_enrollment_var.get()]
            lesson_date = self.att_date_var.get().strip()
            if not lesson_date:
                raise ValueError("Укажите дату занятия.")
            db.add_attendance(enrollment_id, lesson_date, self.att_status_var.get(), self.att_comment_var.get().strip())
            self.refresh_all()
            messagebox.showinfo("Готово", "Посещаемость сохранена. Запись также появилась в журнале триггеров.")
        except (sqlite3.IntegrityError, ValueError, KeyError) as exc:
            self._handle_error("сохранить посещаемость", exc)


    def _render_report(self, rows: list[sqlite3.Row], title_map: dict[str, str] | None = None) -> None:
        for widget in self.report_tree_frame.winfo_children():
            widget.destroy()
        if not rows:
            ttk.Label(self.report_tree_frame, text="Нет данных для отображения.").pack(anchor="w")
            self.report_tree = None
            return

        columns = tuple(rows[0].keys())
        self.report_tree = self._create_tree(self.report_tree_frame, columns)
        for col in columns:
            self.report_tree.heading(col, text=title_map.get(col, col) if title_map else col)
            self.report_tree.column(col, width=max(100, min(260, len(col) * 14)))
        for row in rows:
            self.report_tree.insert("", "end", values=tuple(row[col] for col in columns))

    def show_progress_report(self) -> None:
        rows = db.report_student_progress()
        self._render_report(
            rows,
            {
                "student_id": "ID студента",
                "student_card": "Зачётка",
                "student_name": "Студент",
                "group_code": "Группа",
                "course_code": "Код",
                "course_title": "Дисциплина",
                "teacher_name": "Преподаватель",
                "academic_year": "Год",
                "semester": "Семестр",
                "enrollment_status": "Статус",
                "assessment_type": "Тип оценки",
                "grade": "Оценка",
                "points": "Баллы",
                "assessed_at": "Дата оценки",
            },
        )

    def show_group_average_report(self) -> None:
        self._render_report(db.report_group_average())

    def show_debts_report(self) -> None:
        self._render_report(db.report_debts())

    def show_attendance_report(self) -> None:
        self._render_report(
            db.report_attendance(),
            {
                "attendance_id": "ID",
                "lesson_date": "Дата занятия",
                "student_name": "Студент",
                "group_code": "Группа",
                "course_title": "Дисциплина",
                "teacher_name": "Преподаватель",
                "academic_year": "Учебный год",
                "semester": "Семестр",
                "status": "Статус",
                "comment": "Комментарий",
            },
        )

    def show_audit_report(self) -> None:
        self._render_report(
            db.report_audit_log(),
            {
                "log_id": "№",
                "created_at": "Дата и время GMT+5",
                "table_name": "Таблица",
                "action_name": "Действие",
                "row_id": "ID записи",
                "description": "Описание изменения",
            },
        )


def main() -> None:
    app = StudentCourseApp()
    app.mainloop()


if __name__ == "__main__":
    main()
