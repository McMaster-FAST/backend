# Merge migration: parallel branches from 0007 (CourseResumeState vs adaptive-test metrics).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_courseresumestate"),
        (
            "core",
            "0012_rename_adaptivetestquestionmetrics_adaptivetestquestionmetric_and_more",
        ),
    ]

    operations = []
