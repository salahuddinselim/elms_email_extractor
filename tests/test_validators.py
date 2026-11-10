from modules.validators import parse_course_ids_input, validate_course_id


def test_parse_course_ids_multiple_delimiters():
    parsed = parse_course_ids_input("7818, 7820\n7835  7835")
    assert parsed == ["7818", "7820", "7835"]


def test_validate_course_id():
    assert validate_course_id("7818")
    assert not validate_course_id("78A8")
    assert not validate_course_id("")

