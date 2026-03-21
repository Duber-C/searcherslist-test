"""Add subtitle field to Question model

Revision ID: 0032_add_question_subtitle
Revises: 0031_populate_examples_from_extra
Create Date: 2026-02-19 00:00:00.000000
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0031_populate_examples_from_extra'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='subtitle',
            field=models.TextField(blank=True, help_text='Short subtitle or description for the question'),
        ),
    ]
