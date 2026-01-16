"""
Management command to remove only the data loaded from fixtures.
This command deletes only the specific records that were loaded as fixtures.
Safe to run multiple times - only deletes the specific records if they exist.
"""
from django.core.management.base import BaseCommand
from core.models import Question, QuestionOption
from courses.models import Course, Unit, UnitSubtopic, AidType, StudyAid

class Command(BaseCommand):
    help = "Remove data loaded from initial fixtures"

    def handle(self, *args, **options):
        # Primary keys from core/fixtures/mock/data.json
        question_pks = list(range(1, 12))  # PKs 1-11
        question_option_pks = list(range(1, 45))  # PKs 1-44 (4 for each question)

        # Primary keys from courses/fixtures/mock/data.json
        course_pk = [1, 2]
        unit_pk = list(range(1, 18))
        unit_subtopic_pk = list(range(1, 29))
        aid_type_pk = [1]
        study_aid_pk = [1]

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
            
        # StudyAids (depends on AidType and UnitSubtopic)
        deleted = StudyAid.objects.filter(pk__in=study_aid_pk).delete()
        deleted_count += deleted[0]
        if deleted[0] > 0:
            self.stdout.write(f"  ✓ Deleted {deleted[0]} StudyAid(s)")
            
        # AidTypes (no dependencies)
        deleted = AidType.objects.filter(pk__in=aid_type_pk).delete()
        deleted_count += deleted[0]
        if deleted[0] > 0:
            self.stdout.write(f"  ✓ Deleted {deleted[0]} AidType(s)")

        # UnitSubtopic (depends on Unit)
        deleted = UnitSubtopic.objects.filter(pk__in=unit_subtopic_pk).delete()
        deleted_count += deleted[0]
        if deleted[0] > 0:
            self.stdout.write(f"  ✓ Deleted {deleted[0]} UnitSubtopic(s)")

        # Unit (depends on Course)
        deleted = Unit.objects.filter(pk__in=unit_pk).delete()
        deleted_count += deleted[0]
        if deleted[0] > 0:
            self.stdout.write(f"  ✓ Deleted {deleted[0]} Unit(s)")

        # Course (no dependencies)
        deleted = Course.objects.filter(pk__in=course_pk).delete()
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