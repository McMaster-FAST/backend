from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0009_alter_questionuploadfailures_public_id_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='unit',
            unique_together={('course', 'number')},
        ),
    ]
