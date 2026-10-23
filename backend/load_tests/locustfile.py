"""Locust Load Testing Task Definition for Quizdesk (Phase 9).

Usage:
    locust -f backend/load_tests/locustfile.py --host=http://localhost:8000
"""
from datetime import datetime, timezone
import random
import uuid
from locust import HttpUser, task, between, tag


class StudentAssessmentUser(HttpUser):
    """Simulates an authenticated student undertaking a scheduled examination."""
    wait_time = between(1, 3)

    def on_start(self):
        """Prepare student headers with JWT token."""
        # Note: in real runs, tokens are populated from a pre-generated pool or login endpoint
        self.student_token = getattr(self.environment, "student_token", None)
        self.quiz_id = getattr(self.environment, "target_quiz_id", None)
        self.attempt_id = None
        self.question_ids = []

    @task(3)
    def start_or_resume_attempt(self):
        """Student starts or resumes an assessment attempt."""
        if not self.quiz_id or not self.student_token or self.attempt_id:
            return

        headers = {"Authorization": f"Bearer {self.student_token}"}
        with self.client.post(
            f"/api/v1/student/quizzes/{self.quiz_id}/attempts",
            headers=headers,
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201):
                self.attempt_id = resp.json().get("attempt_id")
                resp.success()
            else:
                resp.failure(f"Attempt start failed with HTTP {resp.status_code}")

    @task(10)
    def autosave_answer(self):
        """Student autosaves an answer to a question."""
        if not self.attempt_id or not self.student_token:
            return

        # Dummy question save
        q_id = str(uuid.uuid4())
        payload = {
            "selected_option_ids": [str(uuid.uuid4())],
            "client_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        headers = {"Authorization": f"Bearer {self.student_token}"}
        self.client.put(
            f"/api/v1/student/attempts/{self.attempt_id}/answers/{q_id}",
            json=payload,
            headers=headers,
        )

    @task(2)
    def report_telemetry(self):
        """Student reports window blur or tab switch telemetry."""
        if not self.attempt_id or not self.student_token:
            return

        payload = {
            "event_type": "tab_switch",
            "client_event_id": str(uuid.uuid4()),
            "client_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        headers = {"Authorization": f"Bearer {self.student_token}"}
        self.client.post(
            f"/api/v1/student/attempts/{self.attempt_id}/telemetry",
            json=payload,
            headers=headers,
        )


class TeacherMonitorUser(HttpUser):
    """Simulates an instructor monitoring quiz progress and querying results."""
    wait_time = between(5, 10)

    @task(2)
    def query_results_summary(self):
        """Teacher queries the real-time assessment KPI summary."""
        quiz_id = getattr(self.environment, "target_quiz_id", None)
        teacher_token = getattr(self.environment, "teacher_token", None)
        if not quiz_id or not teacher_token:
            return

        headers = {"Authorization": f"Bearer {teacher_token}"}
        self.client.get(f"/api/v1/quizzes/{quiz_id}/results/summary", headers=headers)
