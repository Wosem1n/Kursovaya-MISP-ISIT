from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "students_courses.db"
SQL_DIR = BASE_DIR / "sql"
GMT_PLUS_5_SQL = "datetime(\'now\', \'+5 hours\')"


def get_connection() -> sqlite3.Connection:
    """Возвращает соединение с SQLite и включает поддержку внешних ключей."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def run_script(conn: sqlite3.Connection, script_name: str) -> None:
    script_path = SQL_DIR / script_name
    sql = script_path.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


def initialize_database(with_demo_data: bool = True, reset: bool = False) -> None:
    """Создаёт базу данных и при необходимости заполняет её демонстрационными данными."""
    if reset and DB_PATH.exists():
        DB_PATH.unlink()

    with get_connection() as conn:
        run_script(conn, "01_schema.sql")
        if with_demo_data:
            run_script(conn, "02_seed.sql")
            # Демо-загрузка нужна только как стартовые данные.
            # Журнал должен показывать действия пользователя в приложении,
            # поэтому записи, созданные триггерами при INSERT из 02_seed.sql, очищаем.
            conn.execute("DELETE FROM audit_log;")
            conn.commit()


def fetch_all(query: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(query, tuple(params)).fetchall()


def fetch_one(query: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(query, tuple(params)).fetchone()


def execute(query: str, params: Iterable[Any] = ()) -> int:
    with get_connection() as conn:
        cur = conn.execute(query, tuple(params))
        conn.commit()
        return cur.lastrowid


def execute_many(query: str, rows: Iterable[Iterable[Any]]) -> None:
    with get_connection() as conn:
        conn.executemany(query, rows)
        conn.commit()


def table_exists(table_name: str) -> bool:
    row = fetch_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?;",
        (table_name,),
    )
    return row is not None


def ensure_database() -> None:
    """Проверяет наличие БД и применяет актуальную SQL-схему.

    Если база уже существует, демонстрационные данные повторно не вставляются,
    но 01_schema.sql всё равно выполняется. Это нужно, чтобы новые triggers/views
    применялись после обновления файлов проекта без ручного удаления БД.
    """
    if not DB_PATH.exists() or not table_exists("students"):
        initialize_database(with_demo_data=True, reset=False)
        return

    with get_connection() as conn:
        run_script(conn, "01_schema.sql")


# ---------- Справочники для выпадающих списков ----------


def get_groups() -> list[sqlite3.Row]:
    return fetch_all("SELECT group_id, code FROM student_groups ORDER BY code;")


def get_departments() -> list[sqlite3.Row]:
    return fetch_all("SELECT department_id, name FROM departments ORDER BY name;")


def get_teachers() -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT teacher_id,
               last_name || ' ' || first_name || COALESCE(' ' || middle_name, '') || ' (' || email || ')' AS teacher_name
        FROM teachers
        ORDER BY last_name, first_name;
        """
    )


def get_courses() -> list[sqlite3.Row]:
    return fetch_all("SELECT course_id, code, title FROM courses ORDER BY title;")


def get_assignments() -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT
            ca.assignment_id,
            c.title || ' / ' || g.code || ' / ' || t.last_name || ' ' || t.first_name AS assignment_name
        FROM course_assignments ca
        JOIN courses c ON c.course_id = ca.course_id
        JOIN student_groups g ON g.group_id = ca.group_id
        JOIN teachers t ON t.teacher_id = ca.teacher_id
        ORDER BY c.title, g.code;
        """
    )


# ---------- Студенты ----------


def get_students() -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT
            s.student_id,
            s.student_card,
            s.last_name,
            s.first_name,
            COALESCE(s.middle_name, '') AS middle_name,
            s.birth_date,
            COALESCE(s.email, '') AS email,
            COALESCE(s.phone, '') AS phone,
            s.status,
            g.code AS group_code
        FROM students s
        JOIN student_groups g ON g.group_id = s.group_id
        ORDER BY g.code, s.last_name, s.first_name;
        """
    )


def get_student(student_id: int) -> sqlite3.Row | None:
    return fetch_one(
        """
        SELECT student_id, group_id, student_card, last_name, first_name,
               COALESCE(middle_name, '') AS middle_name,
               birth_date,
               COALESCE(email, '') AS email,
               COALESCE(phone, '') AS phone,
               status
        FROM students
        WHERE student_id = ?;
        """,
        (student_id,),
    )


def add_student(
    group_id: int,
    student_card: str,
    last_name: str,
    first_name: str,
    middle_name: str,
    birth_date: str,
    email: str,
    phone: str,
    status: str,
) -> int:
    return execute(
        """
        INSERT INTO students(group_id, student_card, last_name, first_name, middle_name, birth_date, email, phone, status)
        VALUES (?, ?, ?, ?, NULLIF(?, ''), ?, NULLIF(?, ''), NULLIF(?, ''), ?);
        """,
        (group_id, student_card, last_name, first_name, middle_name, birth_date, email, phone, status),
    )


def update_student(
    student_id: int,
    group_id: int,
    student_card: str,
    last_name: str,
    first_name: str,
    middle_name: str,
    birth_date: str,
    email: str,
    phone: str,
    status: str,
) -> None:
    execute(
        """
        UPDATE students
        SET group_id = ?,
            student_card = ?,
            last_name = ?,
            first_name = ?,
            middle_name = NULLIF(?, ''),
            birth_date = ?,
            email = NULLIF(?, ''),
            phone = NULLIF(?, ''),
            status = ?
        WHERE student_id = ?;
        """,
        (group_id, student_card, last_name, first_name, middle_name, birth_date, email, phone, status, student_id),
    )


def update_student_status(student_id: int, status: str) -> None:
    execute("UPDATE students SET status = ? WHERE student_id = ?;", (status, student_id))


def delete_student(student_id: int) -> None:
    execute("DELETE FROM students WHERE student_id = ?;", (student_id,))


# ---------- Группы ----------


def get_groups_full() -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT g.group_id,
               g.code,
               d.name AS department_name,
               g.admission_year,
               g.education_form,
               COALESCE(g.curator, '') AS curator
        FROM student_groups g
        JOIN departments d ON d.department_id = g.department_id
        ORDER BY g.code;
        """
    )


def add_group(department_id: int, code: str, admission_year: int, education_form: str, curator: str) -> int:
    return execute(
        """
        INSERT INTO student_groups(department_id, code, admission_year, education_form, curator)
        VALUES (?, ?, ?, ?, NULLIF(?, ''));
        """,
        (department_id, code, admission_year, education_form, curator),
    )


def delete_group(group_id: int) -> None:
    execute("DELETE FROM student_groups WHERE group_id = ?;", (group_id,))


# ---------- Кафедры ----------


def get_departments_full() -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT department_id, name, head_name,
               COALESCE(phone, '') AS phone,
               COALESCE(email, '') AS email
        FROM departments
        ORDER BY name;
        """
    )


def add_department(name: str, head_name: str, phone: str, email: str) -> int:
    return execute(
        """
        INSERT INTO departments(name, head_name, phone, email)
        VALUES (?, ?, NULLIF(?, ''), NULLIF(?, ''));
        """,
        (name, head_name, phone, email),
    )


def delete_department(department_id: int) -> None:
    execute("DELETE FROM departments WHERE department_id = ?;", (department_id,))


# ---------- Преподаватели ----------


def get_teachers_full() -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT t.teacher_id,
               t.last_name,
               t.first_name,
               COALESCE(t.middle_name, '') AS middle_name,
               d.name AS department_name,
               t.email,
               COALESCE(t.phone, '') AS phone,
               t.position
        FROM teachers t
        JOIN departments d ON d.department_id = t.department_id
        ORDER BY t.last_name, t.first_name;
        """
    )


def get_teacher(teacher_id: int) -> sqlite3.Row | None:
    return fetch_one(
        """
        SELECT teacher_id, department_id, last_name, first_name,
               COALESCE(middle_name, '') AS middle_name,
               email,
               COALESCE(phone, '') AS phone,
               position
        FROM teachers
        WHERE teacher_id = ?;
        """,
        (teacher_id,),
    )


def add_teacher(
    department_id: int,
    last_name: str,
    first_name: str,
    middle_name: str,
    email: str,
    phone: str,
    position: str,
) -> int:
    return execute(
        """
        INSERT INTO teachers(department_id, last_name, first_name, middle_name, email, phone, position)
        VALUES (?, ?, ?, NULLIF(?, ''), ?, NULLIF(?, ''), ?);
        """,
        (department_id, last_name, first_name, middle_name, email, phone, position),
    )


def update_teacher(
    teacher_id: int,
    department_id: int,
    last_name: str,
    first_name: str,
    middle_name: str,
    email: str,
    phone: str,
    position: str,
) -> None:
    execute(
        """
        UPDATE teachers
        SET department_id = ?,
            last_name = ?,
            first_name = ?,
            middle_name = NULLIF(?, ''),
            email = ?,
            phone = NULLIF(?, ''),
            position = ?
        WHERE teacher_id = ?;
        """,
        (department_id, last_name, first_name, middle_name, email, phone, position, teacher_id),
    )


def delete_teacher(teacher_id: int) -> None:
    execute("DELETE FROM teachers WHERE teacher_id = ?;", (teacher_id,))


# ---------- Курсы ----------


def get_courses_full() -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT c.course_id,
               c.code,
               c.title,
               d.name AS department_name,
               c.credits,
               c.semester,
               c.control_type,
               CASE c.is_active WHEN 1 THEN 'да' ELSE 'нет' END AS is_active_text
        FROM courses c
        JOIN departments d ON d.department_id = c.department_id
        ORDER BY c.title;
        """
    )


def get_course(course_id: int) -> sqlite3.Row | None:
    return fetch_one(
        """
        SELECT course_id, department_id, code, title, credits, semester, control_type, is_active
        FROM courses
        WHERE course_id = ?;
        """,
        (course_id,),
    )


def add_course(
    department_id: int,
    code: str,
    title: str,
    credits: int,
    semester: int,
    control_type: str,
    is_active: int = 1,
) -> int:
    return execute(
        """
        INSERT INTO courses(department_id, code, title, credits, semester, control_type, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (department_id, code, title, credits, semester, control_type, is_active),
    )


def update_course(
    course_id: int,
    department_id: int,
    code: str,
    title: str,
    credits: int,
    semester: int,
    control_type: str,
    is_active: int,
) -> None:
    execute(
        """
        UPDATE courses
        SET department_id = ?,
            code = ?,
            title = ?,
            credits = ?,
            semester = ?,
            control_type = ?,
            is_active = ?
        WHERE course_id = ?;
        """,
        (department_id, code, title, credits, semester, control_type, is_active, course_id),
    )


def delete_course(course_id: int) -> None:
    execute("DELETE FROM courses WHERE course_id = ?;", (course_id,))


# ---------- Назначения, оценки, посещаемость ----------


def get_enrollments_for_combo() -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT
            e.enrollment_id,
            s.last_name || ' ' || s.first_name || ' — ' || c.title || ' (' || g.code || ')' AS enrollment_name
        FROM enrollments e
        JOIN students s ON s.student_id = e.student_id
        JOIN course_assignments ca ON ca.assignment_id = e.assignment_id
        JOIN courses c ON c.course_id = ca.course_id
        JOIN student_groups g ON g.group_id = s.group_id
        ORDER BY s.last_name, s.first_name, c.title;
        """
    )


def add_course_assignment(
    course_id: int,
    teacher_id: int,
    group_id: int,
    academic_year: str,
    semester: int,
) -> int:
    return execute(
        """
        INSERT INTO course_assignments(course_id, teacher_id, group_id, academic_year, semester)
        VALUES (?, ?, ?, ?, ?);
        """,
        (course_id, teacher_id, group_id, academic_year, semester),
    )


def enroll_student(student_id: int, assignment_id: int) -> int:
    return execute(
        "INSERT INTO enrollments(student_id, assignment_id, status) VALUES (?, ?, 'изучает');",
        (student_id, assignment_id),
    )


def add_or_update_assessment(
    enrollment_id: int,
    assessment_type: str,
    grade: int,
    points: int,
    comment: str,
) -> None:
    execute(
        """
        INSERT INTO assessments(enrollment_id, assessment_type, grade, points, comment)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(enrollment_id, assessment_type)
        DO UPDATE SET
            grade = excluded.grade,
            points = excluded.points,
            comment = excluded.comment,
            assessed_at = datetime('now', '+5 hours');
        """,
        (enrollment_id, assessment_type, grade, points, comment),
    )


def add_attendance(enrollment_id: int, lesson_date: str, status: str, comment: str) -> None:
    execute(
        """
        INSERT INTO attendance(enrollment_id, lesson_date, status, comment)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(enrollment_id, lesson_date)
        DO UPDATE SET status = excluded.status, comment = excluded.comment;
        """,
        (enrollment_id, lesson_date, status, comment),
    )


def get_attendance_records() -> list[sqlite3.Row]:
    return fetch_all(
        """
        SELECT
            attendance_id,
            lesson_date,
            student_name,
            group_code,
            course_title,
            teacher_name,
            academic_year,
            semester,
            status,
            comment
        FROM v_attendance_report
        ORDER BY lesson_date DESC, group_code, student_name, course_title;
        """
    )


def report_student_progress() -> list[sqlite3.Row]:
    return fetch_all("SELECT * FROM v_student_progress ORDER BY group_code, student_name, course_title;")


def report_group_average() -> list[sqlite3.Row]:
    return fetch_all("SELECT * FROM v_group_average ORDER BY group_code, course_title;")


def report_debts() -> list[sqlite3.Row]:
    return fetch_all("SELECT * FROM v_student_debts ORDER BY group_code, student_name;")


def report_attendance() -> list[sqlite3.Row]:
    return get_attendance_records()


def report_audit_log() -> list[sqlite3.Row]:
    """Возвращает полный журнал изменений, который заполняется SQL-триггерами."""
    return fetch_all(
        """
        SELECT
            log_id,
            created_at,
            table_name,
            action_name,
            row_id,
            description
        FROM audit_log
        ORDER BY log_id DESC;
        """
    )
