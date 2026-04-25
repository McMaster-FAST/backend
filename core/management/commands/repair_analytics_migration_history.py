from django.core.management.base import BaseCommand
from django.db import connection


TARGET_APP = 'analytics'
TARGET_MIGRATION = '0006_repair_missing_questionreport_tables'
DEPENDENT_MIGRATION = '0007_alter_questionattempt_user_and_more'


class Command(BaseCommand):
    help = (
        'Repair analytics migration history when 0007 is applied before 0006. '
        'Safe to run multiple times.'
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without modifying migration history.',
        )

    def handle(self, *args, **options) -> None:
        dry_run: bool = options['dry_run']

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM django_migrations
                WHERE app = %s AND name = %s
                LIMIT 1
                """,
                [TARGET_APP, DEPENDENT_MIGRATION],
            )
            has_dependent = cursor.fetchone() is not None

            cursor.execute(
                """
                SELECT 1
                FROM django_migrations
                WHERE app = %s AND name = %s
                LIMIT 1
                """,
                [TARGET_APP, TARGET_MIGRATION],
            )
            has_target = cursor.fetchone() is not None

            if has_target:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'No fix needed: {TARGET_APP}.{TARGET_MIGRATION} is already recorded.'
                    )
                )
                return

            if not has_dependent:
                self.stdout.write(
                    self.style.WARNING(
                        'No fix applied: dependent migration '
                        f'{TARGET_APP}.{DEPENDENT_MIGRATION} is not recorded.'
                    )
                )
                return

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        'Dry run: would insert missing migration history row for '
                        f'{TARGET_APP}.{TARGET_MIGRATION}.'
                    )
                )
                return

            cursor.execute(
                """
                INSERT INTO django_migrations(app, name, applied)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                """,
                [TARGET_APP, TARGET_MIGRATION],
            )

        self.stdout.write(
            self.style.SUCCESS(
                'Inserted missing migration history row for '
                f'{TARGET_APP}.{TARGET_MIGRATION}. '
                'You can now run `python manage.py migrate` safely.'
            )
        )
