"""Comprehensive unit tests for the CSV Question Bank parser (DEC-006)."""
import pytest
from app.models.question import QuestionType
from app.services.csv_parser import (
    parse_and_validate_question_csv,
    MAX_FILE_SIZE_BYTES,
    MAX_QUESTIONS_PER_IMPORT,
)


def test_parse_valid_csv_standard_utf8():
    """Verify clean parsing of valid single, multi, and true/false questions."""
    csv_text = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"What is 2+2?",3,4,5,6,B,2.0,0.5\n'
        'multiple_choice,"Prime numbers under 10",2,3,4,5,"A, B, D",3.0,1.0\n'
        'true_false,"Earth orbits the Sun",True,False,,,A,1.0,0.0\n'
    )
    result = parse_and_validate_question_csv(csv_text)

    assert result.is_valid is True
    assert result.total_rows == 3
    assert result.valid_count == 3
    assert result.error_count == 0
    assert len(result.questions) == 3

    # Check question 1 (single choice)
    q1 = result.questions[0]
    assert q1.question_type == QuestionType.SINGLE_CHOICE
    assert q1.prompt == "What is 2+2?"
    assert q1.positive_marks == 2.0
    assert q1.negative_marks == 0.5
    assert len(q1.options) == 4
    assert [o.is_correct for o in q1.options] == [False, True, False, False]
    assert q1.options[1].option_text == "4"

    # Check question 2 (multiple choice)
    q2 = result.questions[1]
    assert q2.question_type == QuestionType.MULTIPLE_CHOICE
    assert len(q2.options) == 4
    assert [o.is_correct for o in q2.options] == [True, True, False, True]

    # Check question 3 (true/false)
    q3 = result.questions[2]
    assert q3.question_type == QuestionType.TRUE_FALSE
    assert len(q3.options) == 2
    assert q3.options[0].option_text == "True"
    assert q3.options[0].is_correct is True
    assert q3.options[1].option_text == "False"
    assert q3.options[1].is_correct is False


def test_parse_valid_csv_with_utf8_bom():
    """Verify that UTF-8 BOM (\\ufeff) is automatically stripped and does not corrupt headers."""
    bom_bytes = (
        b"\xef\xbb\xbfquestion_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        b'single_choice,"Capital of France?",Berlin,Paris,Madrid,Rome,B,1.0,0.0\n'
    )
    result = parse_and_validate_question_csv(bom_bytes)

    assert result.is_valid is True
    assert result.valid_count == 1
    assert result.questions[0].prompt == "Capital of France?"
    assert result.questions[0].options[1].option_text == "Paris"
    assert result.questions[0].options[1].is_correct is True


def test_missing_required_headers():
    """Verify rejection when required header columns are missing."""
    csv_text = "question_text,option_a,option_b,correct_answers\n"
    result = parse_and_validate_question_csv(csv_text)

    assert result.is_valid is False
    assert result.error_count > 0
    missing_cols = [e.column for e in result.errors]
    assert "question_type" in missing_cols
    assert "positive_marks" in missing_cols


def test_empty_csv_and_header_only_csv():
    """Verify rejection of empty or header-only CSVs."""
    empty_res = parse_and_validate_question_csv("")
    assert empty_res.is_valid is False
    assert "empty" in empty_res.errors[0].message.lower()

    header_only = "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
    hdr_res = parse_and_validate_question_csv(header_only)
    assert hdr_res.is_valid is False
    assert "no question data rows" in hdr_res.errors[0].message.lower()


def test_blank_prompt_rejection():
    """Verify that empty or whitespace prompts are rejected."""
    csv_text = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"   ",Opt1,Opt2,,,A,1.0,0.0\n'
    )
    result = parse_and_validate_question_csv(csv_text)

    assert result.is_valid is False
    assert any("prompt cannot be blank" in e.message.lower() for e in result.errors)


def test_invalid_question_type():
    """Verify rejection of unknown question types."""
    csv_text = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'essay,"Write an essay on AI",Opt1,Opt2,,,A,1.0,0.0\n'
    )
    result = parse_and_validate_question_csv(csv_text)

    assert result.is_valid is False
    assert any("invalid question type" in e.message.lower() for e in result.errors)


def test_missing_or_duplicate_options():
    """Verify option count requirements and duplicate detection."""
    # Missing option B
    csv_missing_opt = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"Question 1",OptA,,,,A,1.0,0.0\n'
    )
    res1 = parse_and_validate_question_csv(csv_missing_opt)
    assert res1.is_valid is False
    assert any("option b cannot be empty" in e.message.lower() for e in res1.errors)

    # Option D provided without Option C
    csv_gap_opt = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"Question 2",OptA,OptB,,OptD,A,1.0,0.0\n'
    )
    res2 = parse_and_validate_question_csv(csv_gap_opt)
    assert res2.is_valid is False
    assert any("option c cannot be empty when option d is provided" in e.message.lower() for e in res2.errors)

    # Duplicate options
    csv_dup = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"Question 3",Identical,Identical,,,A,1.0,0.0\n'
    )
    res3 = parse_and_validate_question_csv(csv_dup)
    assert res3.is_valid is False
    assert any("duplicate option text" in e.message.lower() for e in res3.errors)


def test_single_choice_answer_key_validation():
    """Single choice must reference exactly 1 valid, non-empty option."""
    # Multiple answers given to single choice
    csv_multi_on_single = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"Single choice question",OptA,OptB,OptC,,"A,B",1.0,0.0\n'
    )
    res1 = parse_and_validate_question_csv(csv_multi_on_single)
    assert res1.is_valid is False
    assert any("single-choice question cannot have multiple correct answers" in e.message.lower() for e in res1.errors)

    # Reference to empty option D
    csv_empty_ref = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"Single choice question",OptA,OptB,,,D,1.0,0.0\n'
    )
    res2 = parse_and_validate_question_csv(csv_empty_ref)
    assert res2.is_valid is False
    assert any("references option(s) ['d'] which are empty" in e.message.lower() for e in res2.errors)

    # Invalid letter reference 'Z'
    csv_invalid_ref = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"Single choice question",OptA,OptB,,,Z,1.0,0.0\n'
    )
    res3 = parse_and_validate_question_csv(csv_invalid_ref)
    assert res3.is_valid is False
    assert any("invalid option reference(s) ['z']" in e.message.lower() for e in res3.errors)


def test_true_false_validation():
    """True/False must forbid options C/D and accept standard True/False answer keys."""
    # Option C supplied on True/False
    csv_tf_extra = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'true_false,"TF question",True,False,ExtraOpt,,A,1.0,0.0\n'
    )
    res1 = parse_and_validate_question_csv(csv_tf_extra)
    assert res1.is_valid is False
    assert any("true/false questions must not define option_c" in e.message.lower() for e in res1.errors)

    # Defaults to True and False when left blank
    csv_tf_defaults = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'true_false,"Gravity pulls downwards",,,,,TRUE,2.0,0.0\n'
    )
    res2 = parse_and_validate_question_csv(csv_tf_defaults)
    assert res2.is_valid is True
    assert res2.questions[0].options[0].option_text == "True"
    assert res2.questions[0].options[0].is_correct is True
    assert res2.questions[0].options[1].option_text == "False"
    assert res2.questions[0].options[1].is_correct is False


def test_marks_validation():
    """Positive marks must be > 0 and negative marks must be >= 0."""
    csv_marks = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"Zero positive mark",OptA,OptB,,,A,0.0,0.0\n'
        'single_choice,"Negative negative mark",OptA,OptB,,,A,1.0,-0.5\n'
        'single_choice,"String mark",OptA,OptB,,,A,abc,0.0\n'
    )
    res = parse_and_validate_question_csv(csv_marks)
    assert res.is_valid is False
    assert any("strictly greater than 0" in e.message.lower() for e in res.errors)
    assert any("cannot be less than 0" in e.message.lower() for e in res.errors)
    assert any("invalid number format" in e.message.lower() for e in res.errors)


def test_row_limit_enforcement():
    """Verify that row count is capped at MAX_QUESTIONS_PER_IMPORT."""
    lines = ["question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks"]
    for i in range(MAX_QUESTIONS_PER_IMPORT + 5):
        lines.append(f'single_choice,"Question {i}",OptA,OptB,,,A,1.0,0.0')

    csv_text = "\n".join(lines)
    res = parse_and_validate_question_csv(csv_text)
    assert res.is_valid is False
    assert any("exceeded maximum row limit" in e.message.lower() for e in res.errors)


def test_difficulty_parsing_and_defaults():
    """Verify difficulty level parsing, case insensitivity, and safe default."""
    from app.models.question import QuestionDifficulty

    csv_with_diff = (
        "question_type,difficulty,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,easy,"Easy Question",A,B,,,A,1.0,0.0\n'
        'single_choice,MEDIUM,"Medium Question",A,B,,,A,1.0,0.0\n'
        'single_choice,Hard,"Hard Question",A,B,,,A,1.0,0.0\n'
        'single_choice,,"Blank Difficulty Question",A,B,,,A,1.0,0.0\n'
    )
    res = parse_and_validate_question_csv(csv_with_diff)
    assert res.is_valid is True
    assert res.valid_count == 4
    assert res.questions[0].difficulty == QuestionDifficulty.EASY
    assert res.questions[1].difficulty == QuestionDifficulty.MEDIUM
    assert res.questions[2].difficulty == QuestionDifficulty.HARD
    assert res.questions[3].difficulty == QuestionDifficulty.MEDIUM

    # Backward compatibility: CSV without difficulty column defaults to medium
    csv_no_diff = (
        "question_type,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,"Legacy Question",A,B,,,A,1.0,0.0\n'
    )
    res_legacy = parse_and_validate_question_csv(csv_no_diff)
    assert res_legacy.is_valid is True
    assert res_legacy.questions[0].difficulty == QuestionDifficulty.MEDIUM


def test_invalid_difficulty_rejection():
    """Verify that unrecognized difficulty strings are rejected with row-level errors."""
    csv_invalid_diff = (
        "question_type,difficulty,question_text,option_a,option_b,option_c,option_d,correct_answers,positive_marks,negative_marks\n"
        'single_choice,extreme,"Extreme Question",A,B,,,A,1.0,0.0\n'
    )
    res = parse_and_validate_question_csv(csv_invalid_diff)
    assert res.is_valid is False
    assert any("invalid difficulty 'extreme'" in e.message.lower() for e in res.errors)
    assert any(e.column == "difficulty" for e in res.errors)


def test_parse_valid_xlsx_workbook():
    """Verify genuine Excel .xlsx parsing via openpyxl."""
    import io
    import openpyxl
    from app.models.question import QuestionDifficulty, QuestionType

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Questions"

    # Header row
    ws.append([
        "question_type",
        "difficulty",
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_answers",
        "positive_marks",
        "negative_marks",
    ])
    # Data row 1
    ws.append([
        "single_choice",
        "hard",
        "What is the binary representation of 10?",
        "1010",
        "1100",
        "1001",
        "1111",
        "A",
        2.5,
        0.5,
    ])
    # Data row 2 (True/False)
    ws.append([
        "true_false",
        "easy",
        "RAM is non-volatile memory.",
        "True",
        "False",
        "",
        "",
        "B",
        1.0,
        0.0,
    ])

    bio = io.BytesIO()
    wb.save(bio)
    xlsx_bytes = bio.getvalue()

    result = parse_and_validate_question_csv(xlsx_bytes, filename="questions.xlsx")
    assert result.is_valid is True
    assert result.total_rows == 2
    assert result.valid_count == 2
    assert result.error_count == 0

    q1 = result.questions[0]
    assert q1.question_type == QuestionType.SINGLE_CHOICE
    assert q1.difficulty == QuestionDifficulty.HARD
    assert q1.prompt == "What is the binary representation of 10?"
    assert q1.positive_marks == 2.5
    assert q1.negative_marks == 0.5
    assert len(q1.options) == 4
    assert q1.options[0].is_correct is True

    q2 = result.questions[1]
    assert q2.question_type == QuestionType.TRUE_FALSE
    assert q2.difficulty == QuestionDifficulty.EASY
    assert q2.prompt == "RAM is non-volatile memory."
    assert q2.options[1].is_correct is True


def test_corrupt_or_empty_xlsx_rejection():
    """Verify proper error reporting on corrupt or empty Excel files."""
    # File named .xlsx but contains arbitrary non-zip bytes
    corrupt_bytes = b"Not really an excel file content"
    res = parse_and_validate_question_csv(corrupt_bytes, filename="bad.xlsx")
    assert res.is_valid is False
    assert any("failed to read excel workbook" in e.message.lower() for e in res.errors)

