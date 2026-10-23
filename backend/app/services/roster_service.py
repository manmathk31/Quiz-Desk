"""Student Roster business service: Identity matching, preview, and transactional import (DEC-007, Phase 5)."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.roster import QuizAssignment
from app.models.user import User, StudentProfile, UserRole
from app.models.quiz import Quiz
from app.models.audit import AuditEvent
from app.services.roster_parser import ParsedRosterRow


@dataclass
class EvaluatedRosterRow:
    """Evaluated student roster candidate row with identity matching and assignment status."""
    row_number: int
    prn: str
    name: str
    email: str
    division: str
    assignment_status: str  # "new", "already_assigned", "conflict"
    match_status: str       # "matched", "unregistered", "pending_profile", "conflict"
    matched_user_id: Optional[uuid.UUID]
    conflict_reason: Optional[str] = None
    existing_assignment_id: Optional[uuid.UUID] = None
    is_currently_active: Optional[bool] = None


@dataclass
class RosterEvaluationResult:
    """Consolidated dry-run preview evaluation result."""
    total_rows: int
    new_assignments_count: int
    already_assigned_count: int
    conflicts_count: int
    matched_count: int
    unregistered_count: int
    pending_profile_count: int
    can_confirm: bool
    items: List[EvaluatedRosterRow]


def evaluate_roster_candidates(
    db: Session,
    quiz_id: uuid.UUID,
    parsed_rows: List[ParsedRosterRow],
) -> RosterEvaluationResult:
    """
    Perform a bounded bulk evaluation of candidate student rows against the database.
    Does not mutate database state.
    Evaluates:
    1. Existing assignments for the target quiz.
    2. Student account identity matching (verified email + PRN alignment).
    3. Duplicate identities and conflicts.
    """
    if not parsed_rows:
        return RosterEvaluationResult(
            total_rows=0,
            new_assignments_count=0,
            already_assigned_count=0,
            conflicts_count=0,
            matched_count=0,
            unregistered_count=0,
            pending_profile_count=0,
            can_confirm=False,
            items=[],
        )

    # 1. Fetch existing quiz assignments
    existing_stmt = select(QuizAssignment).where(QuizAssignment.quiz_id == quiz_id)
    existing_assignments = db.scalars(existing_stmt).all()

    existing_by_prn: Dict[str, QuizAssignment] = {
        a.student_prn.upper(): a for a in existing_assignments
    }
    existing_by_email: Dict[str, QuizAssignment] = {
        a.student_email.lower(): a for a in existing_assignments
    }

    # 2. Bounded bulk query for matching accounts
    candidate_emails = [r.email.lower() for r in parsed_rows]
    candidate_prns = [r.prn.upper() for r in parsed_rows]

    user_stmt = (
        select(User, StudentProfile)
        .outerjoin(StudentProfile, User.id == StudentProfile.user_id)
        .where(
            or_(
                User.email.in_(candidate_emails),
                StudentProfile.prn.in_(candidate_prns),
            )
        )
    )
    user_records = db.execute(user_stmt).all()

    # Index users by email and PRN
    users_by_email: Dict[str, Tuple[User, Optional[StudentProfile]]] = {}
    users_by_prn: Dict[str, Tuple[User, StudentProfile]] = {}

    for user, profile in user_records:
        users_by_email[user.email.lower()] = (user, profile)
        if profile and profile.prn:
            users_by_prn[profile.prn.upper()] = (user, profile)

    evaluated_items: List[EvaluatedRosterRow] = []
    new_count = 0
    already_count = 0
    conflicts_count = 0
    matched_count = 0
    unregistered_count = 0
    pending_profile_count = 0

    for r in parsed_rows:
        norm_prn = r.prn.upper()
        norm_email = r.email.lower()

        matched_user_id: Optional[uuid.UUID] = None
        match_status = "unregistered"
        assignment_status = "new"
        conflict_reasons: List[str] = []

        # Step A: Evaluate Account Identity Matching
        user_by_email_entry = users_by_email.get(norm_email)
        user_by_prn_entry = users_by_prn.get(norm_prn)

        if user_by_email_entry:
            u_email, p_email = user_by_email_entry
            if u_email.role != UserRole.STUDENT:
                match_status = "conflict"
                conflict_reasons.append(
                    f"Account with email '{r.email}' has role '{u_email.role.value}' and cannot be assigned as a student."
                )
            elif p_email and p_email.prn:
                if p_email.prn.upper() == norm_prn:
                    match_status = "matched"
                    matched_user_id = u_email.id
                    matched_count += 1
                else:
                    match_status = "conflict"
                    conflict_reasons.append(
                        f"Identity conflict: User account '{r.email}' is registered with PRN '{p_email.prn}', which does not match roster PRN '{r.prn}'."
                    )
            else:
                # Student account exists but lacks student profile / PRN
                if user_by_prn_entry and user_by_prn_entry[0].id != u_email.id:
                    match_status = "conflict"
                    conflict_reasons.append(
                        f"Identity conflict: PRN '{r.prn}' is registered to account '{user_by_prn_entry[0].email}', not '{r.email}'."
                    )
                else:
                    match_status = "pending_profile"
                    pending_profile_count += 1
        elif user_by_prn_entry:
            # PRN belongs to an account with a different email
            u_prn, _ = user_by_prn_entry
            match_status = "conflict"
            conflict_reasons.append(
                f"Identity conflict: PRN '{r.prn}' belongs to existing account '{u_prn.email}', but roster specifies email '{r.email}'."
            )
        else:
            match_status = "unregistered"
            unregistered_count += 1

        # Step B: Evaluate Existing Assignment Status for this Quiz
        assigned_by_prn = existing_by_prn.get(norm_prn)
        assigned_by_email = existing_by_email.get(norm_email)

        existing_id: Optional[uuid.UUID] = None
        is_active_val: Optional[bool] = None

        if assigned_by_prn and assigned_by_email:
            if assigned_by_prn.id == assigned_by_email.id:
                assignment_status = "already_assigned"
                existing_id = assigned_by_prn.id
                is_currently_active = assigned_by_prn.is_active
                already_count += 1
            else:
                assignment_status = "conflict"
                conflict_reasons.append(
                    f"Roster conflict: PRN '{r.prn}' and email '{r.email}' belong to different existing assignments in this assessment."
                )
        elif assigned_by_prn:
            assignment_status = "conflict"
            conflict_reasons.append(
                f"PRN '{r.prn}' is already assigned to email '{assigned_by_prn.student_email}' for this quiz."
            )
        elif assigned_by_email:
            assignment_status = "conflict"
            conflict_reasons.append(
                f"Email '{r.email}' is already assigned with PRN '{assigned_by_email.student_prn}' for this quiz."
            )
        else:
            assignment_status = "new"
            new_count += 1

        if conflict_reasons:
            conflicts_count += 1

        evaluated_items.append(
            EvaluatedRosterRow(
                row_number=r.row_number,
                prn=r.prn,
                name=r.name,
                email=r.email,
                division=r.division,
                assignment_status=assignment_status,
                match_status=match_status,
                matched_user_id=matched_user_id,
                conflict_reason="; ".join(conflict_reasons) if conflict_reasons else None,
                existing_assignment_id=existing_id,
                is_currently_active=is_active_val,
            )
        )

    return RosterEvaluationResult(
        total_rows=len(parsed_rows),
        new_assignments_count=new_count,
        already_assigned_count=already_count,
        conflicts_count=conflicts_count,
        matched_count=matched_count,
        unregistered_count=unregistered_count,
        pending_profile_count=pending_profile_count,
        can_confirm=(conflicts_count == 0),
        items=evaluated_items,
    )


def commit_roster_import(
    db: Session,
    quiz: Quiz,
    current_user_id: uuid.UUID,
    parsed_rows: List[ParsedRosterRow],
) -> dict:
    """
    Transactionally commit an imported roster to the database.
    Idempotent and atomic:
    - Re-evaluates DB state inside transaction.
    - If any unresolved conflicts exist, raises HTTP 422 and rolls back.
    - Adds new valid assignments.
    - Updates name/division/matched_student_id on existing assignments without deleting them.
    - Records tamper-evident AuditEvent.
    """
    eval_result = evaluate_roster_candidates(db, quiz.id, parsed_rows)

    if not eval_result.can_confirm:
        conflict_messages = [
            f"Row {item.row_number} ({item.prn}): {item.conflict_reason}"
            for item in eval_result.items
            if item.conflict_reason
        ]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": f"Roster import rejected due to {eval_result.conflicts_count} conflict(s). Resolve conflicts and re-upload.",
                "conflicts": conflict_messages[:20],
            },
        )

    imported_new_count = 0
    updated_existing_count = 0

    for item in eval_result.items:
        if item.assignment_status == "new":
            assignment = QuizAssignment(
                quiz_id=quiz.id,
                student_prn=item.prn,
                student_email=item.email,
                student_name=item.name,
                division=item.division,
                assigned_student_id=item.matched_user_id,
                is_active=True,
            )
            db.add(assignment)
            imported_new_count += 1
        elif item.assignment_status == "already_assigned" and item.existing_assignment_id:
            existing = db.get(QuizAssignment, item.existing_assignment_id)
            if existing:
                existing.student_name = item.name
                existing.division = item.division
                if item.matched_user_id and not existing.assigned_student_id:
                    existing.assigned_student_id = item.matched_user_id
                updated_existing_count += 1

    # Record tamper-evident AuditEvent
    audit = AuditEvent(
        user_id=current_user_id,
        action="roster_imported",
        entity_type="quiz",
        entity_id=str(quiz.id),
        details={
            "total_rows": eval_result.total_rows,
            "new_assignments": imported_new_count,
            "updated_existing": updated_existing_count,
            "matched_accounts": eval_result.matched_count,
            "unregistered_students": eval_result.unregistered_count,
        },
    )
    db.add(audit)
    db.commit()

    return {
        "imported_count": imported_new_count,
        "already_assigned_count": updated_existing_count,
        "matched_accounts_count": eval_result.matched_count,
        "unregistered_count": eval_result.unregistered_count,
    }
