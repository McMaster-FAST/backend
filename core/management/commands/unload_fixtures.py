"""
Management command to remove only the data loaded from initial fixtures.

This command deletes only the specific records that were loaded from initial_courses.json and
initial_questions.json, preserving any other data that may have been added.
"""
from django.core.management.base import BaseCommand
from core.models import Question, QuestionOption, QuestionGroup
from courses.models import Course, Unit, UnitSubtopic

class Command(BaseCommand):
    help = "Remove data loaded from initial fixtures"

    def handle(self, *args, **options):
        # Primary keys from initial_questions.json
        question_pks = [1, 2, 3]
        question_option_pks = list(range(1, 13))  # PKs 1-12
        question_group_pk = 1

        # Primary keys from initial_courses.json
        course_pk = 1
        unit_pk = 1
        unit_subtopic_pk = 1

        deleted_count = 0

        # Delete in reverse dependency order
        # QuestionOptions (depend on Questions)
        deleted = QuestionOption.objects.filter(pk__in=question_option_pks).delete()
        deleted_count += deleted[0]
        if deleted[0] > 0:
            self.stdout.write(f"  ✓ Deleted {deleted[0]} QuestionOption(s)")

        # Questions (depend on UnitSubtopic)
        deleted = Question.objects.filter(pk__in=question_pks).delete()
        deleted_count += deleted[0]
        if deleted[0] > 0:
            self.stdout.write(f"  ✓ Deleted {deleted[0]} Question(s)")

        # QuestionGroup (ManyToMany with Questions, but we delete the group itself)
        deleted = QuestionGroup.objects.filter(pk=question_group_pk).delete()
        deleted_count += deleted[0]
        if deleted[0] > 0:
            self.stdout.write(f"  ✓ Deleted {deleted[0]} QuestionGroup(s)")

        # UnitSubtopic (depends on Unit)
        deleted = UnitSubtopic.objects.filter(pk=unit_subtopic_pk).delete()
        deleted_count += deleted[0]
        if deleted[0] > 0:
            self.stdout.write(f"  ✓ Deleted {deleted[0]} UnitSubtopic(s)")

        # Unit (depends on Course)
        deleted = Unit.objects.filter(pk=unit_pk).delete()
        deleted_count += deleted[0]
        if deleted[0] > 0:
            self.stdout.write(f"  ✓ Deleted {deleted[0]} Unit(s)")

        # Course
        deleted = Course.objects.filter(pk=course_pk).delete()
        deleted_count += deleted[0]
        if deleted[0] > 0:
            self.stdout.write(f"  ✓ Deleted {deleted[0]} Course(s)")

        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Successfully unloaded {deleted_count} fixture record(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('No fixture data found to unload')
            )