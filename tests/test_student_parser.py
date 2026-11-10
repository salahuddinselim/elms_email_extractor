from modules.student_parser import parse_student_id


def test_parse_fall_student_id():
    parsed, err = parse_student_id("0112230512")
    assert err is None
    assert parsed is not None
    assert parsed.department_code == "011"
    assert parsed.admission_year == 2022
    assert parsed.trimester == "Fall"
    assert parsed.trimester_code == 3
    assert parsed.serial_number == "0512"


def test_parse_trimester_variants():
    p1, e1 = parse_student_id("0112210123")
    p2, e2 = parse_student_id("0112220345")
    p3, e3 = parse_student_id("0112230512")

    assert not e1 and p1.trimester == "Spring"
    assert not e2 and p2.trimester == "Summer"
    assert not e3 and p3.trimester == "Fall"


def test_invalid_student_id():
    parsed, err = parse_student_id("ABC")
    assert parsed is None
    assert err is not None

