"""
PostgreSQL database verification & validation (V&V §3.1).

Maps to the project V&V document:
- 3.1.1 Unit and integration (migrations, CRUD, cascades, transactions, concurrency)
- 3.1.2 Performance thresholds (single write, concurrent writes, read queries, connection stress)
- Validation: ORM vs raw SQL aggregates (proxy for frontend/API vs database)

Notes:
- Default pytest settings use in-memory SQLite (MacFAST.settings_test); migration and ORM
  behaviour are the same SQL semantics Django guarantees. Load/latency acceptance on
  PostgreSQL should be confirmed with Locust (see loadtests/submit_answer_locustfile.py).
- Pilot usage stability (real students) is assessed operationally during the pilot, not
  automated here.
"""

from __future__ import annotations

import time

import pytest
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor

from analytics.models import CourseXP, QuestionAttempt
from core.models import Question, QuestionOption
from core.queries.question_queries import add_response
from courses.models import Course, Enrolment, Unit, UnitSubtopic
from sso_auth.models import MacFastUser


# ---------------------------------------------------------------------------
# 3.1.1 Migrations
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMigrationsApplyCleanly:
    """V&V: migrations apply cleanly (no pending plan when DB is up to date)."""

    def test_no_pending_migrations_when_fully_migrated(self) -> None:
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        plan = executor.migration_plan(targets)
        assert plan == [], (
            "Expected empty migration plan when test database is fully migrated; "
            f"pending operations: {plan!r}"
        )

    def test_migrate_command_idempotent(self) -> None:
        """Applying migrate again should succeed with no errors (fresh vs drift)."""
        call_command("migrate", verbosity=0, interactive=False)


# ---------------------------------------------------------------------------
# 3.1.1 CRUD — Users, Questions, Question Attempts, Enrolments
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCoreModelCrud:
    """V&V: CRUD for core models used throughout the app."""

    def test_user_crud(self) -> None:
        u = MacFastUser.objects.create_user(username="vv_user_crud", password="x")
        assert MacFastUser.objects.filter(pk=u.pk).exists()
        u.first_name = "VV"
        u.save()
        assert MacFastUser.objects.get(pk=u.pk).first_name == "VV"
        u.delete()
        assert not MacFastUser.objects.filter(pk=u.pk).exists()

    def test_question_and_options_crud(
        self,
        course: Course,
        unit: Unit,
        subtopic: UnitSubtopic,
    ) -> None:
        q = Question.objects.create(
            subtopic=subtopic,
            serial_number="VV-Q-CRUD-1",
            content="CRUD question",
        )
        opt = QuestionOption.objects.create(
            question=q,
            content="A",
            is_answer=True,
        )
        assert Question.objects.get(pk=q.pk).serial_number == "VV-Q-CRUD-1"
        opt.content = "A-updated"
        opt.save()
        assert QuestionOption.objects.get(pk=opt.pk).content == "A-updated"
        q.delete()
        assert not QuestionOption.objects.filter(pk=opt.pk).exists()

    def test_question_attempt_crud(
        self,
        user: MacFastUser,
        question: Question,
        correct_option: QuestionOption,
        testing_parameters,  # noqa: ANN001
    ) -> None:
        add_response(user, question, correct_option, time_spent=1.0)
        att = QuestionAttempt.objects.get(user=user, question=question)
        assert att.answered_correctly is True
        att.time_spent = 2.0
        att.save()
        assert QuestionAttempt.objects.get(pk=att.pk).time_spent == 2.0
        att.delete()
        assert not QuestionAttempt.objects.filter(pk=att.pk).exists()

    def test_enrolment_crud(self, user: MacFastUser, course: Course) -> None:
        e = Enrolment.objects.create(user=user, course=course, is_instructor=False)
        assert Enrolment.objects.get(pk=e.pk).course_id == course.id
        e.is_ta = True
        e.save()
        assert Enrolment.objects.get(pk=e.pk).is_ta is True
        e.delete()
        assert not Enrolment.objects.filter(pk=e.pk).exists()


# ---------------------------------------------------------------------------
# 3.1.1 Cascade deletion
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCascadeDeletion:
    """V&V: deleting a parent removes dependent rows (options, attempts)."""

    def test_deleting_question_removes_options_and_attempts(
        self,
        user: MacFastUser,
        course: Course,
        unit: Unit,
        subtopic: UnitSubtopic,
        testing_parameters,  # noqa: ANN001
    ) -> None:
        q = Question.objects.create(
            subtopic=subtopic,
            serial_number="VV-CASCADE-1",
            content="Cascade",
        )
        opt = QuestionOption.objects.create(
            question=q,
            content="opt",
            is_answer=True,
        )
        add_response(user, q, opt, time_spent=1.0)
        assert QuestionOption.objects.filter(question=q).exists()
        assert QuestionAttempt.objects.filter(question=q).exists()

        q.delete()

        assert not QuestionOption.objects.filter(pk=opt.pk).exists()
        assert not QuestionAttempt.objects.filter(question_id=q.id).exists()


# ---------------------------------------------------------------------------
# 3.1.1 Failed transactions rollback
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTransactionRollback:
    """V&V: failed transactions do not leave partial writes."""

    def test_integrity_error_in_atomic_rolls_back_enrolment(
        self,
        user: MacFastUser,
        course: Course,
    ) -> None:
        Enrolment.objects.filter(user=user, course=course).delete()

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Enrolment.objects.create(user=user, course=course)
                Enrolment.objects.create(user=user, course=course)

        assert Enrolment.objects.filter(user=user, course=course).count() == 0


# ---------------------------------------------------------------------------
# 3.1.1 Concurrent writes — uniqueness and consistency
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestConcurrentWrites:
    """
    V&V: no duplicate or inconsistent rows under contention.

    True parallel writers are exercised with Locust against PostgreSQL; in-memory
    SQLite used by settings_test.py serializes and can raise ``database is locked``,
    so we assert database-level uniqueness and bulk correctness without threads.
    """

    def test_enrolment_unique_constraint_prevents_duplicate_row(
        self,
        course: Course,
    ) -> None:
        user = MacFastUser.objects.create_user(
            username="vv_unique_enrol",
            password="x",
        )
        Enrolment.objects.filter(user=user, course=course).delete()
        Enrolment.objects.create(user=user, course=course)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Enrolment.objects.create(user=user, course=course)
        assert Enrolment.objects.filter(user=user, course=course).count() == 1

    def test_many_question_attempt_inserts_all_distinct_rows_persist(
        self,
        unit: Unit,
        testing_parameters,  # noqa: ANN001
    ) -> None:
        """Many submissions for distinct (user, question) pairs — all rows persisted."""
        subtopic = UnitSubtopic.objects.create(unit=unit, name="VV Bulk Subtopic")
        n = 32
        questions: list[Question] = []
        for i in range(n):
            u = MacFastUser.objects.create_user(
                username=f"vv_bulk_{i}",
                password="x",
            )
            q = Question.objects.create(
                subtopic=subtopic,
                serial_number=f"VV-BULK-{i}",
                content="Bulk",
            )
            opt = QuestionOption.objects.create(
                question=q,
                content="ok",
                is_answer=True,
            )
            questions.append(q)
            add_response(u, q, opt, time_spent=0.5)

        assert QuestionAttempt.objects.filter(
            question_id__in=[q.id for q in questions]
        ).count() == n


# ---------------------------------------------------------------------------
# 3.1.2 Performance — latencies (regression; production: Postgres + Locust)
# ---------------------------------------------------------------------------


@pytest.mark.performance
@pytest.mark.django_db
class TestDatabasePerformanceThresholds:
    """
    V&V §3.1.2: single write, concurrent writes, read queries.

    Thresholds are chosen so normal CI (SQLite) passes; PostgreSQL under load should
    meet the same or stricter budgets — validate with Locust when reporting results.
    """

    SINGLE_WRITE_MAX_S = 5.0
    CONCURRENT_EACH_MAX_S = 2.0
    QUERY_MAX_S = 1.0
    STRESS_ITERATIONS = 500

    def test_single_question_attempt_write_within_budget(
        self,
        user: MacFastUser,
        question: Question,
        correct_option: QuestionOption,
        testing_parameters,  # noqa: ANN001
    ) -> None:
        start = time.perf_counter()
        add_response(user, question, correct_option, time_spent=1.0)
        elapsed = time.perf_counter() - start
        assert elapsed <= self.SINGLE_WRITE_MAX_S, (
            f"Single attempt write took {elapsed:.3f}s (budget {self.SINGLE_WRITE_MAX_S}s)"
        )

    def test_many_writes_each_complete_within_budget(
        self,
        course: Course,
        unit: Unit,
        testing_parameters,  # noqa: ANN001
    ) -> None:
        """
        Per-submission latency for 100 back-to-back writes (same budget as V&V §3.1.2).

        Parallel contention is validated with Locust against PostgreSQL; SQLite test
        DB cannot run 100 parallel writers reliably.
        """
        subtopic = UnitSubtopic.objects.create(unit=unit, name="VV Perf Many Writes")
        n = 100
        timings: list[float] = []
        for i in range(n):
            u = MacFastUser.objects.create_user(
                username=f"vv_perf_many_{i}",
                password="x",
            )
            q = Question.objects.create(
                subtopic=subtopic,
                serial_number=f"VV-PERF-{i}",
                content="Perf",
            )
            opt = QuestionOption.objects.create(
                question=q,
                content="y",
                is_answer=True,
            )
            t0 = time.perf_counter()
            add_response(u, q, opt, time_spent=0.1)
            timings.append(time.perf_counter() - t0)

        assert max(timings) <= self.CONCURRENT_EACH_MAX_S, (
            f"Slowest write {max(timings):.3f}s "
            f"(budget {self.CONCURRENT_EACH_MAX_S}s per submission)"
        )

    def test_common_read_queries_within_budget(
        self,
        user: MacFastUser,
        question: Question,
        correct_option: QuestionOption,
        subtopic: UnitSubtopic,
        testing_parameters,  # noqa: ANN001
    ) -> None:
        add_response(user, question, correct_option, time_spent=1.0)

        start = time.perf_counter()
        list(
            Question.objects.filter(subtopic=subtopic).select_related("subtopic"),
        )
        t1 = time.perf_counter() - start

        start = time.perf_counter()
        list(
            QuestionAttempt.objects.filter(user=user).values(
                "answered_correctly",
                "skipped",
            ),
        )
        t2 = time.perf_counter() - start

        assert t1 <= self.QUERY_MAX_S and t2 <= self.QUERY_MAX_S, (
            f"Question fetch {t1:.3f}s, attempt analytics fetch {t2:.3f}s "
            f"(budget {self.QUERY_MAX_S}s each)"
        )

    def test_sustained_queries_no_connection_failure(self) -> None:
        """Proxy for connection stability under sustained ORM load (Locust covers full pool)."""
        for _ in range(self.STRESS_ITERATIONS):
            Question.objects.count()
            QuestionAttempt.objects.count()


# ---------------------------------------------------------------------------
# Validation — analytics vs raw SQL aggregates
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAnalyticsMatchRawAggregates:
    """V&V Validation: API/ORM-facing counts match raw SQL aggregates."""

    def test_attempt_counts_match_raw_sql(
        self,
        user: MacFastUser,
        question: Question,
        correct_option: QuestionOption,
        wrong_option: QuestionOption,
        testing_parameters,  # noqa: ANN001
    ) -> None:
        add_response(user, question, correct_option, time_spent=1.0)
        add_response(user, question, wrong_option, time_spent=1.0)

        orm_total = QuestionAttempt.objects.filter(user=user).count()
        orm_correct = QuestionAttempt.objects.filter(
            user=user,
            answered_correctly=True,
        ).count()

        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT COUNT(*) FROM analytics_questionattempt WHERE user_id = %s',
                [user.pk],
            )
            raw_total = cursor.fetchone()[0]
            cursor.execute(
                """
                SELECT COUNT(*) FROM analytics_questionattempt
                WHERE user_id = %s AND answered_correctly = 1
                """,
                [user.pk],
            )
            raw_correct = cursor.fetchone()[0]

        assert orm_total == raw_total
        assert orm_correct == raw_correct

    def test_course_xp_matches_stored_row(
        self,
        user: MacFastUser,
        question: Question,
        correct_option: QuestionOption,
        testing_parameters,  # noqa: ANN001
    ) -> None:
        """XP shown to clients comes from the same row raw SQL reads."""
        add_response(user, question, correct_option, time_spent=1.0)
        course = question.subtopic.unit.course

        xp = CourseXP.objects.get(user=user, course=course)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT total_xp FROM analytics_coursexp
                WHERE user_id = %s AND course_id = %s
                """,
                [user.pk, course.pk],
            )
            raw_xp = cursor.fetchone()[0]
        assert xp.total_xp == raw_xp
