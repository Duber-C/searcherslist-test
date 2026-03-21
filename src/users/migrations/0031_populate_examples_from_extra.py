"""Populate the new `examples` field from `extra['examples']` when present."""
from django.db import migrations


def forwards(apps, schema_editor):
    Question = apps.get_model('users', 'Question')
    for q in Question.objects.all():
        try:
            extra = q.extra or {}
            examples = extra.get('examples')
            if examples:
                q.examples = examples
                q.save(update_fields=['examples'])
        except Exception:
            continue


def reverse(apps, schema_editor):
    # leave examples intact on reverse
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0030_question_examples'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse),
    ]
