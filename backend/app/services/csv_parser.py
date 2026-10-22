"""CSV parsing and validation engine for Question Bank imports (DEC-006)."""
from dataclasses import dataclass, field
import csv
import io
import re
from typing import List, Optional, Set, Tuple

from app.models.question import QuestionType

# Bounded import limits
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2MB
MAX_QUESTIONS_PER_IMPORT = 200

REQUIRED_CSV_HEADERS = [
    "question_type",
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_answers",
    "positive_marks",
    "negative_marks",
]


@dataclass
class ParsedOption:
    """Option candidate extracted from CSV."""
    option_text: str
    order_index: int
    is_correct: bool


@dataclass
class ParsedQuestion:
    """Question candidate extracted and validated from CSV row."""
    row_number: int
    question_type: QuestionType
    prompt: str
    positive_marks: float
    negative_marks: float
    options: List[ParsedOption]


@dataclass
class CSVRowError:
    """Actionable validation error with row and column location."""
    row_number: int
    column: Optional[str]
    message: str


@dataclass
class CSVValidationResult:
    """Overall result of parsing and validating an uploaded CSV file."""
    is_valid: bool
    total_rows: int
    valid_count: int
    error_count: int
    questions: List[ParsedQuestion] = field(default_factory=list)
    errors: List[CSVRowError] = field(default_factory=list)


def normalize_header(header: str) -> str:
    """Clean and normalize CSV header string."""
    return header.strip().lower().replace(" ", "_")


def parse_and_validate_question_csv(
    file_content: bytes | str,
) -> CSVValidationResult:
    """
    Parse and validate a teacher's Question Bank CSV upload.

    Enforces:
    - Safe UTF-8 decoding with automatic BOM stripping (utf-8-sig).
    - File size limit (2MB) and row count limit (200 rows).
    - Required headers presence.
    - Type-specific option counts, correctness rules, and duplicate checks.
    - True/False option structure and answer key normalization.
    - Strict non-negative and positive mark validation.
    - Formula injection mitigation: text fields stored as plain strings.
    """
    errors: List[CSVRowError] = []
    questions: List[ParsedQuestion] = []

    # 1. File size check (if raw bytes provided)
    if isinstance(file_content, bytes):
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            return CSVValidationResult(
                is_valid=False,
                total_rows=0,
                valid_count=0,
                error_count=1,
                errors=[
                    CSVRowError(
                        row_number=0,
                        column="file",
                        message=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB",
                    )
                ],
            )
        try:
            # utf-8-sig automatically removes the UTF-8 Byte Order Mark (BOM) if present
            decoded_text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return CSVValidationResult(
                is_valid=False,
                total_rows=0,
                valid_count=0,
                error_count=1,
                errors=[
                    CSVRowError(
                        row_number=0,
                        column="file",
                        message="File is not valid UTF-8 text. Please save your file as UTF-8 CSV.",
                    )
                ],
            )
    else:
        decoded_text = file_content.lstrip("\ufeff")

    if not decoded_text.strip():
        return CSVValidationResult(
            is_valid=False,
            total_rows=0,
            valid_count=0,
            error_count=1,
            errors=[
                CSVRowError(
                    row_number=0,
                    column="file",
                    message="CSV file is empty.",
                )
            ],
        )

    # 2. Parse CSV rows
    stream = io.StringIO(decoded_text)
    reader = csv.reader(stream)

    try:
        raw_headers = next(reader, None)
    except Exception as e:
        return CSVValidationResult(
            is_valid=False,
            total_rows=0,
            valid_count=0,
            error_count=1,
            errors=[
                CSVRowError(
                    row_number=1,
                    column="header",
                    message=f"Failed to read CSV headers: {str(e)}",
                )
            ],
        )

    if not raw_headers:
        return CSVValidationResult(
            is_valid=False,
            total_rows=0,
            valid_count=0,
            error_count=1,
            errors=[
                CSVRowError(
                    row_number=1,
                    column="header",
                    message="CSV header row is missing or empty.",
                )
            ],
        )

    # Normalize headers
    normalized_headers = [normalize_header(h) for h in raw_headers]
    header_index = {h: i for i, h in enumerate(normalized_headers)}

    missing_headers = [
        req for req in REQUIRED_CSV_HEADERS if req not in header_index
    ]
    if missing_headers:
        return CSVValidationResult(
            is_valid=False,
            total_rows=0,
            valid_count=0,
            error_count=len(missing_headers),
            errors=[
                CSVRowError(
                    row_number=1,
                    column=h,
                    message=f"Missing required header column: '{h}'",
                )
                for h in missing_headers
            ],
        )

    # 3. Process data rows
    row_count = 0
    for row_idx, row in enumerate(reader, start=2):
        # Ignore completely empty lines at end or middle of CSV
        if not any(cell.strip() for cell in row):
            continue

        row_count += 1
        if row_count > MAX_QUESTIONS_PER_IMPORT:
            errors.append(
                CSVRowError(
                    row_number=row_idx,
                    column="file",
                    message=f"Exceeded maximum row limit of {MAX_QUESTIONS_PER_IMPORT} questions per import.",
                )
            )
            break

        def get_col(col_name: str) -> str:
            idx = header_index.get(col_name)
            if idx is not None and idx < len(row):
                return row[idx].strip()
            return ""

        row_errors: List[CSVRowError] = []

        raw_type = get_col("question_type").lower()
        prompt = get_col("question_text")
        opt_a = get_col("option_a")
        opt_b = get_col("option_b")
        opt_c = get_col("option_c")
        opt_d = get_col("option_d")
        correct_raw = get_col("correct_answers")
        pos_marks_raw = get_col("positive_marks")
        neg_marks_raw = get_col("negative_marks")

        # Validate question prompt
        if not prompt:
            row_errors.append(
                CSVRowError(
                    row_number=row_idx,
                    column="question_text",
                    message="Question text prompt cannot be blank.",
                )
            )

        # Validate question type
        question_type: Optional[QuestionType] = None
        if raw_type in ("single_choice", "single", "mcq"):
            question_type = QuestionType.SINGLE_CHOICE
        elif raw_type in ("multiple_choice", "multiple", "multi", "multi_mcq"):
            question_type = QuestionType.MULTIPLE_CHOICE
        elif raw_type in ("true_false", "tf", "boolean"):
            question_type = QuestionType.TRUE_FALSE
        else:
            row_errors.append(
                CSVRowError(
                    row_number=row_idx,
                    column="question_type",
                    message=f"Invalid question type '{raw_type}'. Supported: 'single_choice', 'multiple_choice', 'true_false'",
                )
            )

        # Validate marks
        positive_marks = 1.00
        if pos_marks_raw:
            try:
                positive_marks = float(pos_marks_raw)
                if positive_marks <= 0:
                    row_errors.append(
                        CSVRowError(
                            row_number=row_idx,
                            column="positive_marks",
                            message=f"Positive marks must be strictly greater than 0 (got {positive_marks}).",
                        )
                    )
            except ValueError:
                row_errors.append(
                    CSVRowError(
                        row_number=row_idx,
                        column="positive_marks",
                        message=f"Invalid number format for positive marks: '{pos_marks_raw}'",
                    )
                )

        negative_marks = 0.00
        if neg_marks_raw:
            try:
                negative_marks = float(neg_marks_raw)
                if negative_marks < 0:
                    row_errors.append(
                        CSVRowError(
                            row_number=row_idx,
                            column="negative_marks",
                            message=f"Negative marks cannot be less than 0 (got {negative_marks}).",
                        )
                    )
            except ValueError:
                row_errors.append(
                    CSVRowError(
                        row_number=row_idx,
                        column="negative_marks",
                        message=f"Invalid number format for negative marks: '{neg_marks_raw}'",
                    )
                )

        # Validate options and correct answers based on question type
        parsed_options: List[ParsedOption] = []

        if question_type == QuestionType.TRUE_FALSE:
            # Disallow option_c and option_d for True/False
            if opt_c or opt_d:
                row_errors.append(
                    CSVRowError(
                        row_number=row_idx,
                        column="option_c",
                        message="True/False questions must not define option_c or option_d.",
                    )
                )

            # Option A defaults to "True", Option B defaults to "False"
            tf_opt_a = opt_a if opt_a else "True"
            tf_opt_b = opt_b if opt_b else "False"

            # Parse correct answer for True/False
            # Acceptable representations: A, B, TRUE, FALSE, T, F
            norm_correct = correct_raw.upper().replace(" ", "")
            correct_choice: Optional[str] = None
            if norm_correct in ("A", "TRUE", "T"):
                correct_choice = "A"
            elif norm_correct in ("B", "FALSE", "F"):
                correct_choice = "B"
            else:
                row_errors.append(
                    CSVRowError(
                        row_number=row_idx,
                        column="correct_answers",
                        message=f"Invalid correct answer '{correct_raw}' for True/False. Expected 'A' (True) or 'B' (False).",
                    )
                )

            parsed_options = [
                ParsedOption(option_text=tf_opt_a, order_index=0, is_correct=(correct_choice == "A")),
                ParsedOption(option_text=tf_opt_b, order_index=1, is_correct=(correct_choice == "B")),
            ]

        elif question_type in (QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE):
            # Must have at least option_a and option_b
            if not opt_a:
                row_errors.append(
                    CSVRowError(
                        row_number=row_idx,
                        column="option_a",
                        message="Option A cannot be empty.",
                    )
                )
            if not opt_b:
                row_errors.append(
                    CSVRowError(
                        row_number=row_idx,
                        column="option_b",
                        message="Option B cannot be empty.",
                    )
                )

            # If option_d is provided but option_c is blank
            if opt_d and not opt_c:
                row_errors.append(
                    CSVRowError(
                        row_number=row_idx,
                        column="option_c",
                        message="Option C cannot be empty when Option D is provided.",
                    )
                )

            # Build available options list
            candidate_options: List[Tuple[str, str]] = []  # (letter, text)
            if opt_a:
                candidate_options.append(("A", opt_a))
            if opt_b:
                candidate_options.append(("B", opt_b))
            if opt_c:
                candidate_options.append(("C", opt_c))
            if opt_d:
                candidate_options.append(("D", opt_d))

            # Duplicate option texts check
            seen_texts: Set[str] = set()
            has_duplicates = False
            for letter, opt_text in candidate_options:
                normalized_text = opt_text.lower()
                if normalized_text in seen_texts:
                    has_duplicates = True
                    row_errors.append(
                        CSVRowError(
                            row_number=row_idx,
                            column=f"option_{letter.lower()}",
                            message=f"Duplicate option text '{opt_text}' found in row {row_idx}.",
                        )
                    )
                seen_texts.add(normalized_text)

            available_letters = {letter for letter, _ in candidate_options}

            # Parse correct answers key
            # Allow delimiter: comma, space, semicolon
            if not correct_raw:
                row_errors.append(
                    CSVRowError(
                        row_number=row_idx,
                        column="correct_answers",
                        message="Correct answers key cannot be blank.",
                    )
                )
                correct_letters: Set[str] = set()
            else:
                raw_tokens = re.split(r"[,\s;]+", correct_raw.upper().strip())
                correct_letters = {token.strip() for token in raw_tokens if token.strip()}

                # Check for invalid letters
                invalid_letters = correct_letters - {"A", "B", "C", "D"}
                if invalid_letters:
                    row_errors.append(
                        CSVRowError(
                            row_number=row_idx,
                            column="correct_answers",
                            message=f"Invalid option reference(s) {sorted(invalid_letters)} in correct_answers. Expected A, B, C, or D.",
                        )
                    )

                # Check for letters pointing to empty options
                empty_refs = correct_letters - available_letters
                valid_empty_refs = empty_refs.intersection({"A", "B", "C", "D"})
                if valid_empty_refs:
                    row_errors.append(
                        CSVRowError(
                            row_number=row_idx,
                            column="correct_answers",
                            message=f"Correct answer references option(s) {sorted(valid_empty_refs)} which are empty in this row.",
                        )
                    )

            if question_type == QuestionType.SINGLE_CHOICE:
                if len(correct_letters) > 1:
                    row_errors.append(
                        CSVRowError(
                            row_number=row_idx,
                            column="correct_answers",
                            message=f"Single-choice question cannot have multiple correct answers (found {sorted(correct_letters)}). Use 'multiple_choice' instead.",
                        )
                    )
                elif len(correct_letters) == 0:
                    if correct_raw:  # already handled if empty
                        row_errors.append(
                            CSVRowError(
                                row_number=row_idx,
                                column="correct_answers",
                                message="Must specify exactly one correct answer (e.g. 'A').",
                            )
                        )

            elif question_type == QuestionType.MULTIPLE_CHOICE:
                if len(correct_letters) == 0 and correct_raw:
                    row_errors.append(
                        CSVRowError(
                            row_number=row_idx,
                            column="correct_answers",
                            message="Multiple-choice question must specify at least one correct option (e.g. 'A,B').",
                        )
                    )

            # Build parsed options
            for idx, (letter, text) in enumerate(candidate_options):
                parsed_options.append(
                    ParsedOption(
                        option_text=text,
                        order_index=idx,
                        is_correct=(letter in correct_letters),
                    )
                )

        if row_errors:
            errors.extend(row_errors)
        elif question_type is not None:
            questions.append(
                ParsedQuestion(
                    row_number=row_idx,
                    question_type=question_type,
                    prompt=prompt,
                    positive_marks=positive_marks,
                    negative_marks=negative_marks,
                    options=parsed_options,
                )
            )

    if row_count == 0:
        errors.append(
            CSVRowError(
                row_number=1,
                column="file",
                message="CSV contains headers but no question data rows.",
            )
        )

    is_valid = len(errors) == 0 and len(questions) > 0

    return CSVValidationResult(
        is_valid=is_valid,
        total_rows=row_count,
        valid_count=len(questions),
        error_count=len(errors),
        questions=questions,
        errors=errors,
    )
