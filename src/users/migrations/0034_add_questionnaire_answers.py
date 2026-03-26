from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0033_populate_question_subtitle_from_extra'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='questionnaire_answers',
            field=models.JSONField(blank=True, default=dict, help_text='Structured questionnaire answers (may include option titles and subtitles)'),
        ),
    ]
