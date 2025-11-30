"""
Management command to load initial fixtures if the database is empty.

This command checks if key tables (Course, Question) are empty and loads
fixtures if needed. Safe to run multiple times - only loads if database is empty.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from courses.models import Course
from core.models import Question


class Command(BaseCommand):
    help = "Load initial fixtures if database is empty (for development)"

    def handle(self, *args, **options):
        # Check if database is empty by checking key models
        is_empty = self._is_database_empty()
        
        if not is_empty:
            self.stdout.write(
                self.style.WARNING(
                    'Database already contains data. Skipping fixture loading.\n'
                )
            )
            return
        
        try:
            self.stdout.write('Loading initial fixtures...')
            
            # Load courses first (questions depend on subtopics)
            self.stdout.write('  → Loading courses fixtures...')
            call_command('loaddata', 'courses/fixtures/initial_courses.json', verbosity=0)
            self.stdout.write(self.style.SUCCESS('    ✓ Courses loaded'))
            
            # Then load questions
            self.stdout.write('  → Loading questions fixtures...')
            call_command('loaddata', 'core/fixtures/initial_questions.json', verbosity=0)
            self.stdout.write(self.style.SUCCESS('    ✓ Questions loaded'))
            
            self.stdout.write(
                self.style.SUCCESS('\n✓ Initial fixtures loaded successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ Error loading fixtures: {str(e)}')
            )
            raise

    def _is_database_empty(self):
        """
        Check if the database is empty by checking if key models have any records.
        Returns True if database appears empty, False otherwise.
        """
        try:
            # Check if key models have any data
            # This will raise an exception if tables don't exist (migrations not run)
            has_courses = Course.objects.exists()
            has_questions = Question.objects.exists()
            
            # Database is empty if neither courses nor questions exist
            return not (has_courses or has_questions)
        except Exception:
            # If we can't check (tables don't exist, connection issues, etc.),
            # assume empty - migrations might not have run yet
            return True

