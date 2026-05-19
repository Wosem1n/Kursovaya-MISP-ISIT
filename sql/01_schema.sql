PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    head_name TEXT NOT NULL,
    phone TEXT,
    email TEXT UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now', '+5 hours'))
);

CREATE TABLE IF NOT EXISTS student_groups (
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    code TEXT NOT NULL UNIQUE,
    admission_year INTEGER NOT NULL CHECK (admission_year BETWEEN 2000 AND 2100),
    education_form TEXT NOT NULL DEFAULT 'очная' CHECK (education_form IN ('очная', 'заочная', 'очно-заочная')),
    curator TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', '+5 hours')),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    student_card TEXT NOT NULL UNIQUE,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    birth_date TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'учится' CHECK (status IN ('учится', 'академический отпуск', 'отчислен', 'выпускник')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', '+5 hours')),
    FOREIGN KEY (group_id) REFERENCES student_groups(group_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS teachers (
    teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    last_name TEXT NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    position TEXT NOT NULL DEFAULT 'преподаватель',
    created_at TEXT NOT NULL DEFAULT (datetime('now', '+5 hours')),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL DEFAULT 108 CHECK (credits IN (36, 72, 108, 144)),
    semester INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 12),
    control_type TEXT NOT NULL DEFAULT 'экзамен' CHECK (control_type IN ('экзамен', 'зачёт', 'курсовая работа', 'дифференцированный зачёт')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now', '+5 hours')),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS course_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 12),
    created_at TEXT NOT NULL DEFAULT (datetime('now', '+5 hours')),
    UNIQUE (course_id, teacher_id, group_id, academic_year, semester),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (group_id) REFERENCES student_groups(group_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    assignment_id INTEGER NOT NULL,
    enrolled_at TEXT NOT NULL DEFAULT (datetime('now', '+5 hours')),
    status TEXT NOT NULL DEFAULT 'изучает' CHECK (status IN ('изучает', 'завершил', 'пересдача', 'отчислен')),
    UNIQUE (student_id, assignment_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (assignment_id) REFERENCES course_assignments(assignment_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    assessment_type TEXT NOT NULL DEFAULT 'итоговая' CHECK (assessment_type IN ('контрольная', 'лабораторная', 'зачёт', 'экзамен', 'курсовая', 'итоговая')),
    grade INTEGER NOT NULL CHECK (grade BETWEEN 2 AND 5),
    points INTEGER NOT NULL DEFAULT 0 CHECK (points BETWEEN 0 AND 100),
    assessed_at TEXT NOT NULL DEFAULT (datetime('now', '+5 hours')),
    comment TEXT,
    UNIQUE (enrollment_id, assessment_type),
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    lesson_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'присутствовал' CHECK (status IN ('присутствовал', 'отсутствовал', 'уважительная причина', 'опоздал')),
    comment TEXT,
    UNIQUE (enrollment_id, lesson_date),
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    action_name TEXT NOT NULL,
    row_id INTEGER,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', '+5 hours'))
);

CREATE INDEX IF NOT EXISTS idx_students_group_id ON students(group_id);
CREATE INDEX IF NOT EXISTS idx_teachers_department_id ON teachers(department_id);
CREATE INDEX IF NOT EXISTS idx_courses_department_id ON courses(department_id);
CREATE INDEX IF NOT EXISTS idx_assignments_course_teacher_group ON course_assignments(course_id, teacher_id, group_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student_assignment ON enrollments(student_id, assignment_id);
CREATE INDEX IF NOT EXISTS idx_assessments_enrollment_id ON assessments(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_attendance_enrollment_date ON attendance(enrollment_id, lesson_date);

CREATE VIEW IF NOT EXISTS v_student_progress AS
SELECT
    s.student_id,
    s.student_card,
    s.last_name || ' ' || s.first_name || COALESCE(' ' || s.middle_name, '') AS student_name,
    g.code AS group_code,
    c.code AS course_code,
    c.title AS course_title,
    t.last_name || ' ' || t.first_name AS teacher_name,
    ca.academic_year,
    ca.semester,
    e.status AS enrollment_status,
    a.assessment_type,
    a.grade,
    a.points,
    a.assessed_at
FROM students s
JOIN student_groups g ON g.group_id = s.group_id
JOIN enrollments e ON e.student_id = s.student_id
JOIN course_assignments ca ON ca.assignment_id = e.assignment_id
JOIN courses c ON c.course_id = ca.course_id
JOIN teachers t ON t.teacher_id = ca.teacher_id
LEFT JOIN assessments a ON a.enrollment_id = e.enrollment_id;

CREATE VIEW IF NOT EXISTS v_group_average AS
SELECT
    g.group_id,
    g.code AS group_code,
    c.title AS course_title,
    ca.academic_year,
    ca.semester,
    ROUND(AVG(a.grade), 2) AS average_grade,
    COUNT(a.assessment_id) AS grades_count
FROM student_groups g
JOIN course_assignments ca ON ca.group_id = g.group_id
JOIN courses c ON c.course_id = ca.course_id
JOIN enrollments e ON e.assignment_id = ca.assignment_id
LEFT JOIN assessments a ON a.enrollment_id = e.enrollment_id
GROUP BY g.group_id, g.code, c.title, ca.academic_year, ca.semester;

CREATE VIEW IF NOT EXISTS v_student_debts AS
SELECT
    s.student_id,
    s.last_name || ' ' || s.first_name AS student_name,
    g.code AS group_code,
    c.title AS course_title,
    ca.academic_year,
    ca.semester,
    COALESCE(a.grade, 0) AS grade,
    CASE
        WHEN a.assessment_id IS NULL THEN 'нет итоговой оценки'
        WHEN a.grade < 3 THEN 'неудовлетворительная оценка'
        ELSE 'нет задолженности'
    END AS debt_reason
FROM students s
JOIN student_groups g ON g.group_id = s.group_id
JOIN enrollments e ON e.student_id = s.student_id
JOIN course_assignments ca ON ca.assignment_id = e.assignment_id
JOIN courses c ON c.course_id = ca.course_id
LEFT JOIN assessments a ON a.enrollment_id = e.enrollment_id AND a.assessment_type = 'итоговая'
WHERE a.assessment_id IS NULL OR a.grade < 3;


CREATE VIEW IF NOT EXISTS v_attendance_report AS
SELECT
    atd.attendance_id,
    atd.lesson_date,
    s.last_name || ' ' || s.first_name || COALESCE(' ' || s.middle_name, '') AS student_name,
    g.code AS group_code,
    c.title AS course_title,
    t.last_name || ' ' || t.first_name AS teacher_name,
    ca.academic_year,
    ca.semester,
    atd.status,
    COALESCE(atd.comment, '') AS comment
FROM attendance atd
JOIN enrollments e ON e.enrollment_id = atd.enrollment_id
JOIN students s ON s.student_id = e.student_id
JOIN student_groups g ON g.group_id = s.group_id
JOIN course_assignments ca ON ca.assignment_id = e.assignment_id
JOIN courses c ON c.course_id = ca.course_id
JOIN teachers t ON t.teacher_id = ca.teacher_id;

-- Перед созданием триггеров удаляем старые версии, чтобы при запуске приложения
-- структура журнала обновлялась даже у уже существующей базы данных.
DROP TRIGGER IF EXISTS trg_departments_insert_log;
DROP TRIGGER IF EXISTS trg_departments_update_log;
DROP TRIGGER IF EXISTS trg_departments_delete_log;
DROP TRIGGER IF EXISTS trg_groups_insert_log;
DROP TRIGGER IF EXISTS trg_groups_update_log;
DROP TRIGGER IF EXISTS trg_groups_delete_log;
DROP TRIGGER IF EXISTS trg_students_insert_log;
DROP TRIGGER IF EXISTS trg_students_update_log;
DROP TRIGGER IF EXISTS trg_students_delete_log;
DROP TRIGGER IF EXISTS trg_teachers_insert_log;
DROP TRIGGER IF EXISTS trg_teachers_update_log;
DROP TRIGGER IF EXISTS trg_teachers_delete_log;
DROP TRIGGER IF EXISTS trg_courses_insert_log;
DROP TRIGGER IF EXISTS trg_courses_update_log;
DROP TRIGGER IF EXISTS trg_courses_delete_log;
DROP TRIGGER IF EXISTS trg_assignments_insert_log;
DROP TRIGGER IF EXISTS trg_assignments_update_log;
DROP TRIGGER IF EXISTS trg_assignments_delete_log;
DROP TRIGGER IF EXISTS trg_enrollments_insert_log;
DROP TRIGGER IF EXISTS trg_enrollments_update_log;
DROP TRIGGER IF EXISTS trg_enrollments_delete_log;
DROP TRIGGER IF EXISTS trg_assessments_insert_log;
DROP TRIGGER IF EXISTS trg_assessments_update_log;
DROP TRIGGER IF EXISTS trg_assessments_delete_log;
DROP TRIGGER IF EXISTS trg_attendance_insert_log;
DROP TRIGGER IF EXISTS trg_attendance_update_log;
DROP TRIGGER IF EXISTS trg_attendance_delete_log;

-- Кафедры
CREATE TRIGGER trg_departments_insert_log
AFTER INSERT ON departments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('departments', 'INSERT', NEW.department_id,
           'Добавлена кафедра: ' || NEW.name || ', заведующий: ' || NEW.head_name);
END;

CREATE TRIGGER trg_departments_update_log
AFTER UPDATE ON departments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('departments', 'UPDATE', NEW.department_id,
           'Изменена кафедра: ' || OLD.name || ' -> ' || NEW.name ||
           '; заведующий: ' || OLD.head_name || ' -> ' || NEW.head_name);
END;

CREATE TRIGGER trg_departments_delete_log
AFTER DELETE ON departments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('departments', 'DELETE', OLD.department_id,
           'Удалена кафедра: ' || OLD.name || ', заведующий: ' || OLD.head_name);
END;

-- Группы
CREATE TRIGGER trg_groups_insert_log
AFTER INSERT ON student_groups
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('student_groups', 'INSERT', NEW.group_id,
           'Добавлена группа: ' || NEW.code || ', кафедра: ' ||
           COALESCE((SELECT name FROM departments WHERE department_id = NEW.department_id), 'не указана'));
END;

CREATE TRIGGER trg_groups_update_log
AFTER UPDATE ON student_groups
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('student_groups', 'UPDATE', NEW.group_id,
           'Изменена группа: ' || OLD.code || ' -> ' || NEW.code ||
           '; кафедра: ' || COALESCE((SELECT name FROM departments WHERE department_id = OLD.department_id), 'не указана') ||
           ' -> ' || COALESCE((SELECT name FROM departments WHERE department_id = NEW.department_id), 'не указана'));
END;

CREATE TRIGGER trg_groups_delete_log
AFTER DELETE ON student_groups
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('student_groups', 'DELETE', OLD.group_id,
           'Удалена группа: ' || OLD.code);
END;

-- Студенты, включая перемещение между группами
CREATE TRIGGER trg_students_insert_log
AFTER INSERT ON students
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('students', 'INSERT', NEW.student_id,
           'Добавлен студент: ' || NEW.last_name || ' ' || NEW.first_name ||
           COALESCE(' ' || NEW.middle_name, '') || ', группа: ' ||
           COALESCE((SELECT code FROM student_groups WHERE group_id = NEW.group_id), 'не указана') ||
           ', зачётка: ' || NEW.student_card);
END;

CREATE TRIGGER trg_students_update_log
AFTER UPDATE ON students
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES(
        'students',
        CASE WHEN OLD.group_id <> NEW.group_id THEN 'MOVE' ELSE 'UPDATE' END,
        NEW.student_id,
        CASE
            WHEN OLD.group_id <> NEW.group_id THEN
                'Студент ' || NEW.last_name || ' ' || NEW.first_name ||
                COALESCE(' ' || NEW.middle_name, '') || ' перемещён из группы ' ||
                COALESCE((SELECT code FROM student_groups WHERE group_id = OLD.group_id), 'не указана') ||
                ' в группу ' ||
                COALESCE((SELECT code FROM student_groups WHERE group_id = NEW.group_id), 'не указана')
            ELSE
                'Изменены данные студента: ' || OLD.last_name || ' ' || OLD.first_name ||
                COALESCE(' ' || OLD.middle_name, '') || ' -> ' ||
                NEW.last_name || ' ' || NEW.first_name || COALESCE(' ' || NEW.middle_name, '') ||
                '; зачётка: ' || OLD.student_card || ' -> ' || NEW.student_card
        END ||
        CASE
            WHEN COALESCE(OLD.status, '') <> COALESCE(NEW.status, '')
            THEN '; статус: ' || OLD.status || ' -> ' || NEW.status
            ELSE ''
        END
    );
END;

CREATE TRIGGER trg_students_delete_log
AFTER DELETE ON students
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('students', 'DELETE', OLD.student_id,
           'Удалён студент: ' || OLD.last_name || ' ' || OLD.first_name ||
           COALESCE(' ' || OLD.middle_name, '') || ', группа: ' ||
           COALESCE((SELECT code FROM student_groups WHERE group_id = OLD.group_id), 'не указана') ||
           ', зачётка: ' || OLD.student_card);
END;

-- Преподаватели
CREATE TRIGGER trg_teachers_insert_log
AFTER INSERT ON teachers
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('teachers', 'INSERT', NEW.teacher_id,
           'Добавлен преподаватель: ' || NEW.last_name || ' ' || NEW.first_name ||
           COALESCE(' ' || NEW.middle_name, '') || ', кафедра: ' ||
           COALESCE((SELECT name FROM departments WHERE department_id = NEW.department_id), 'не указана'));
END;

CREATE TRIGGER trg_teachers_update_log
AFTER UPDATE ON teachers
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('teachers', 'UPDATE', NEW.teacher_id,
           'Изменён преподаватель: ' || OLD.last_name || ' ' || OLD.first_name ||
           COALESCE(' ' || OLD.middle_name, '') || ' -> ' ||
           NEW.last_name || ' ' || NEW.first_name || COALESCE(' ' || NEW.middle_name, '') ||
           '; должность: ' || OLD.position || ' -> ' || NEW.position ||
           '; кафедра: ' || COALESCE((SELECT name FROM departments WHERE department_id = OLD.department_id), 'не указана') ||
           ' -> ' || COALESCE((SELECT name FROM departments WHERE department_id = NEW.department_id), 'не указана'));
END;

CREATE TRIGGER trg_teachers_delete_log
AFTER DELETE ON teachers
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('teachers', 'DELETE', OLD.teacher_id,
           'Удалён преподаватель: ' || OLD.last_name || ' ' || OLD.first_name ||
           COALESCE(' ' || OLD.middle_name, ''));
END;

-- Курсы / дисциплины
CREATE TRIGGER trg_courses_insert_log
AFTER INSERT ON courses
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('courses', 'INSERT', NEW.course_id,
           'Добавлена дисциплина: ' || NEW.code || ' — ' || NEW.title ||
           ', кафедра: ' || COALESCE((SELECT name FROM departments WHERE department_id = NEW.department_id), 'не указана'));
END;

CREATE TRIGGER trg_courses_update_log
AFTER UPDATE ON courses
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('courses', 'UPDATE', NEW.course_id,
           'Изменена дисциплина: ' || OLD.code || ' — ' || OLD.title ||
           ' -> ' || NEW.code || ' — ' || NEW.title ||
           '; семестр: ' || OLD.semester || ' -> ' || NEW.semester ||
           '; форма контроля: ' || OLD.control_type || ' -> ' || NEW.control_type);
END;

CREATE TRIGGER trg_courses_delete_log
AFTER DELETE ON courses
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('courses', 'DELETE', OLD.course_id,
           'Удалена дисциплина: ' || OLD.code || ' — ' || OLD.title);
END;

-- Назначения дисциплин группам и преподавателям
CREATE TRIGGER trg_assignments_insert_log
AFTER INSERT ON course_assignments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('course_assignments', 'INSERT', NEW.assignment_id,
           'Добавлено назначение: дисциплина=' ||
           COALESCE((SELECT title FROM courses WHERE course_id = NEW.course_id), 'не указана') ||
           ', преподаватель=' || COALESCE((SELECT last_name || ' ' || first_name FROM teachers WHERE teacher_id = NEW.teacher_id), 'не указан') ||
           ', группа=' || COALESCE((SELECT code FROM student_groups WHERE group_id = NEW.group_id), 'не указана') ||
           ', год=' || NEW.academic_year || ', семестр=' || NEW.semester);
END;

CREATE TRIGGER trg_assignments_update_log
AFTER UPDATE ON course_assignments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('course_assignments', 'UPDATE', NEW.assignment_id,
           'Изменено назначение дисциплины: assignment_id=' || NEW.assignment_id);
END;

CREATE TRIGGER trg_assignments_delete_log
AFTER DELETE ON course_assignments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('course_assignments', 'DELETE', OLD.assignment_id,
           'Удалено назначение дисциплины: assignment_id=' || OLD.assignment_id);
END;

-- Запись студентов на дисциплины
CREATE TRIGGER trg_enrollments_insert_log
AFTER INSERT ON enrollments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('enrollments', 'INSERT', NEW.enrollment_id,
           'Студент записан на дисциплину: ' ||
           COALESCE((SELECT s.last_name || ' ' || s.first_name FROM students s WHERE s.student_id = NEW.student_id), 'не указан') ||
           ', assignment_id=' || NEW.assignment_id || ', статус=' || NEW.status);
END;

CREATE TRIGGER trg_enrollments_update_log
AFTER UPDATE ON enrollments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('enrollments', 'UPDATE', NEW.enrollment_id,
           'Изменена запись на дисциплину: enrollment_id=' || NEW.enrollment_id ||
           '; статус: ' || OLD.status || ' -> ' || NEW.status);
END;

CREATE TRIGGER trg_enrollments_delete_log
AFTER DELETE ON enrollments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('enrollments', 'DELETE', OLD.enrollment_id,
           'Удалена запись студента на дисциплину: enrollment_id=' || OLD.enrollment_id);
END;

-- Оценки
CREATE TRIGGER trg_assessments_insert_log
AFTER INSERT ON assessments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('assessments', 'INSERT', NEW.assessment_id,
           'Добавлена оценка: тип=' || NEW.assessment_type ||
           ', оценка=' || NEW.grade || ', баллы=' || NEW.points ||
           ', enrollment_id=' || NEW.enrollment_id);
END;

CREATE TRIGGER trg_assessments_update_log
AFTER UPDATE ON assessments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('assessments', 'UPDATE', NEW.assessment_id,
           'Изменена оценка: тип=' || NEW.assessment_type ||
           ', оценка ' || OLD.grade || ' -> ' || NEW.grade ||
           ', баллы ' || OLD.points || ' -> ' || NEW.points ||
           ', enrollment_id=' || NEW.enrollment_id);
END;

CREATE TRIGGER trg_assessments_delete_log
AFTER DELETE ON assessments
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('assessments', 'DELETE', OLD.assessment_id,
           'Удалена оценка: тип=' || OLD.assessment_type ||
           ', оценка=' || OLD.grade || ', баллы=' || OLD.points ||
           ', enrollment_id=' || OLD.enrollment_id);
END;

-- Посещаемость
CREATE TRIGGER trg_attendance_insert_log
AFTER INSERT ON attendance
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('attendance', 'INSERT', NEW.attendance_id,
           'Добавлена посещаемость: enrollment_id=' || NEW.enrollment_id ||
           ', дата=' || NEW.lesson_date || ', статус=' || NEW.status);
END;

CREATE TRIGGER trg_attendance_update_log
AFTER UPDATE ON attendance
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('attendance', 'UPDATE', NEW.attendance_id,
           'Изменена посещаемость: enrollment_id=' || NEW.enrollment_id ||
           ', дата=' || NEW.lesson_date ||
           ', статус ' || OLD.status || ' -> ' || NEW.status);
END;

CREATE TRIGGER trg_attendance_delete_log
AFTER DELETE ON attendance
BEGIN
    INSERT INTO audit_log(table_name, action_name, row_id, description)
    VALUES('attendance', 'DELETE', OLD.attendance_id,
           'Удалена посещаемость: enrollment_id=' || OLD.enrollment_id ||
           ', дата=' || OLD.lesson_date || ', статус=' || OLD.status);
END;
