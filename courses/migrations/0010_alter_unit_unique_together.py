from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0007_alter_questionattempt_user_and_more'),
        ('core', '0017_add_last_seen_at_index'),
        ('courses', '0009_alter_questionuploadfailures_public_id_and_more'),
        ('sso_auth', '0003_macfastuser_active_subtopic'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='unit',
            unique_together={('course', 'number')},
        ),
    ]
