"""Populate Question.subtitle from extra['subtitle'] when present

Revision ID: 0033_populate_question_subtitle_from_extra
Revises: 0032_add_question_subtitle
Create Date: 2026-02-19 00:00:00.000000
"""
from django.db import migrations


def copy_subtitle_from_extra(apps, schema_editor):
    Question = apps.get_model('users', 'Question')
    for q in Question.objects.all():
        try:
            extra = q.extra or {}
            subtitle = extra.get('subtitle')
            if subtitle:
                q.subtitle = subtitle
                q.save(update_fields=['subtitle'])
        except Exception:
            # Skip individual failures
            continue


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_add_question_subtitle'),
    ]

    operations = [
        migrations.RunPython(copy_subtitle_from_extra, reverse_code=migrations.RunPython.noop),
    ]
