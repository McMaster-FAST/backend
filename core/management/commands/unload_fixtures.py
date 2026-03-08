import json
import os
from django.conf import settings
from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Remove data loaded from initial fixtures by reading the fixture files directly"
    )

    def handle(self, *args, **options):
        # List the fixture files you want to read
        fixture_files = [
            "courses/fixtures/mock/data.json",
            "core/fixtures/mock/data.json",
        ]

        # Collect PKs grouped by model string
        # like this {'core.question': {1, 2, ...}, 'courses.course': {1, ...}}
        pks_by_model = {}

        self.stdout.write("Reading fixture files")

        for relative_path in fixture_files:
            file_path = settings.BASE_DIR / relative_path

            if not os.path.exists(file_path):
                self.stdout.write(
                    self.style.WARNING(f"File not found: {relative_path}")
                )
                continue

            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                for entry in data:
                    model_label = entry["model"]  # e.g., "core.question"
                    pk = entry["pk"]

                    if model_label not in pks_by_model:
                        pks_by_model[model_label] = set()
                    pks_by_model[model_label].add(pk)

            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR(f"Invalid JSON in {relative_path}"))
                continue

        # Define strict deletion order (Child -> Parent)
        deletion_order = [
            "core.questionoption",  # depends on Question
            "core.question",  # depends on UnitSubtopic
            "courses.studyaid",  # depends on AidType, UnitSubtopic
            "courses.aidtype",  # independent (mostly)
            "courses.unitsubtopic",  # depends on Unit
            "courses.unit",  # depends on Course
            "courses.course",  # independent
        ]

        total_deleted_count = 0

        for model_label in deletion_order:
            # Debug output to check for PKs
            # self.stdout.write(str(pks_by_model.get(model_label, set())))
            self.stdout.write(
                "Removing model:"
                + model_label
                + " with count "
                + str(len(pks_by_model.get(model_label)))
            )

            if model_label not in pks_by_model:
                continue

            pks_to_delete = list(pks_by_model[model_label])

            """
            Get the model class from the model label, then perform deletion on PKs found in the fixture files.
            """
            try:
                model_cls = apps.get_model(model_label)

                deleted = model_cls.objects.filter(pk__in=pks_to_delete).delete()

                # self.stdout.write(str(deleted))

                # deleted has type deleted: tuple[int, dict[str, int]]
                # so by getting deleted[0] we get the count of deleted records
                count = deleted[0]

                if count > 0:
                    self.stdout.write(f"Deleted {count} {model_cls.__name__}(s)")
                    total_deleted_count += count

            except LookupError:
                self.stdout.write(self.style.ERROR(f"Model not found: {model_label}"))
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error deleting {model_label}: {e}")
                )

        if total_deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully unloaded {total_deleted_count} fixture record(s)"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("No matching data found to unload."))
