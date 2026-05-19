-- Основные SQL-запросы для показа преподавателю

-- 1. Список студентов с группой и кафедрой
SELECT
    s.student_card,
    s.last_name || ' ' || s.first_name || COALESCE(' ' || s.middle_name, '') AS fio,
    g.code AS group_code,
    d.name AS department_name,
    s.status
FROM students s
JOIN student_groups g ON g.group_id = s.group_id
JOIN departments d ON d.department_id = g.department_id
ORDER BY g.code, s.last_name;

-- 2. Успеваемость студентов по дисциплинам
SELECT * FROM v_student_progress
ORDER BY group_code, student_name, course_title;

-- 3. Средний балл по группам и дисциплинам
SELECT * FROM v_group_average
ORDER BY group_code, course_title;

-- 4. Студенты с академическими задолженностями
SELECT * FROM v_student_debts
ORDER BY group_code, student_name;

-- 5. Полная ведомость посещаемости
SELECT * FROM v_attendance_report
ORDER BY lesson_date DESC, group_code, student_name, course_title;

-- 6. Количество пропусков по студентам
SELECT
    s.last_name || ' ' || s.first_name AS student_name,
    g.code AS group_code,
    COUNT(*) AS absence_count
FROM attendance atd
JOIN enrollments e ON e.enrollment_id = atd.enrollment_id
JOIN students s ON s.student_id = e.student_id
JOIN student_groups g ON g.group_id = s.group_id
WHERE atd.status IN ('отсутствовал', 'опоздал')
GROUP BY s.student_id, student_name, g.code
ORDER BY absence_count DESC;

-- 7. Полный журнал изменений, заполняется SQL-триггерами
-- В журнал попадают студенты, перемещения между группами, оценки, посещаемость,
-- группы, кафедры, преподаватели, дисциплины, назначения и записи на курсы.
SELECT * FROM audit_log
ORDER BY log_id DESC;
