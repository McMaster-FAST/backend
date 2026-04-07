from django.conf import settings
from django.db import migrations


def create_missing_questionreport_tables(apps, schema_editor):
    existing_tables = set(schema_editor.connection.introspection.table_names())

    QuestionReport = apps.get_model("analytics", "QuestionReport")
    QuestionReportReason = apps.get_model("analytics", "QuestionReportReason")

    if QuestionReport._meta.db_table not in existing_tables:
        schema_editor.create_model(QuestionReport)
        existing_tables.add(QuestionReport._meta.db_table)

    if QuestionReportReason._meta.db_table not in existing_tables:
        schema_editor.create_model(QuestionReportReason)


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0006_merge_20260407_1154"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(
            code=create_missing_questionreport_tables,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
