from __future__ import annotations

import db


def main() -> None:
    db.initialize_database(with_demo_data=True, reset=True)
    print(f"База данных создана: {db.DB_PATH}")

    print(f"Количество кафедр: {len(db.get_departments_full())}")
    print(f"Количество групп: {len(db.get_groups_full())}")
    print(f"Количество преподавателей: {len(db.get_teachers_full())}")
    print(f"Количество курсов: {len(db.get_courses_full())}")
    print(f"Количество студентов: {len(db.get_students())}")
    print("Трудоёмкость курсов:", [dict(row) for row in db.fetch_all("SELECT code, credits FROM courses ORDER BY course_id")])
    print(f"Количество строк посещаемости: {len(db.get_attendance_records())}")

    # Проверка CRUD для новых возможностей интерфейса.
    department_id = db.add_department("Тестовая кафедра", "Тестов Тест Тестович", "", "test-dept@example.edu")
    group_id = db.add_group(department_id, "ТЕСТ-26", 2026, "очная", "")
    group_id_2 = db.add_group(department_id, "ТЕСТ-27", 2027, "очная", "")
    teacher_id = db.add_teacher(department_id, "Тестов", "Иван", "", "test-teacher@example.edu", "", "преподаватель")
    course_id = db.add_course(department_id, "TEST-101", "Тестовая дисциплина", 72, 1, "экзамен")
    student_id = db.add_student(group_id, "ST-TEST", "Тестов", "Пётр", "", "2004-01-01", "test-student@example.edu", "", "учится")

    db.update_student(student_id, group_id, "ST-TEST-2", "Тестов", "Пётр", "Петрович", "2004-01-02", "test-student2@example.edu", "+7-900-000-00-00", "учится")
    # Отдельно проверяем перемещение студента между группами.
    db.update_student(student_id, group_id_2, "ST-TEST-2", "Тестов", "Пётр", "Петрович", "2004-01-02", "test-student2@example.edu", "+7-900-000-00-00", "учится")
    db.update_teacher(teacher_id, department_id, "Тестова", "Ирина", "", "test-teacher2@example.edu", "", "доцент")
    db.update_course(course_id, department_id, "TEST-102", "Тестовая дисциплина 2", 108, 2, "зачёт", 1)

    # Проверяем, что триггеры также пишут изменения оценок и посещаемости.
    db.add_or_update_assessment(1, "итоговая", 4, 85, "Проверка изменения оценки")
    db.add_attendance(1, "2026-03-01", "опоздал", "Проверка журнала")

    db.delete_student(student_id)
    db.delete_course(course_id)
    db.delete_teacher(teacher_id)
    db.delete_group(group_id)
    db.delete_group(group_id_2)
    db.delete_department(department_id)
    print("CRUD-проверка: добавление, редактирование, перемещение и удаление работают.")

    progress = db.report_student_progress()
    print(f"Количество отчётных строк успеваемости: {len(progress)}")

    print("\nСредний балл по группам:")
    for row in db.report_group_average():
        print(dict(row))

    print("\nЗадолженности:")
    for row in db.report_debts():
        print(dict(row))

    print("\nПосещаемость:")
    for row in db.report_attendance():
        print(dict(row))

    audit_rows = db.report_audit_log()
    print(f"\nКоличество записей в полном журнале изменений: {len(audit_rows)}")
    print("Последние записи журнала:")
    for row in audit_rows[:10]:
        print(dict(row))


if __name__ == "__main__":
    main()
