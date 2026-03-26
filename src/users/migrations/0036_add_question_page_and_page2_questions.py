"""Add `page` field to Question and create two page-2 questions.

This migration adds a new `page` integer field to split questions across multiple
pages, sets existing questions to page 1 by default (handled by the field default),
and creates two new questions on page 2: value proposition and areas of expertise.
"""
from django.db import migrations, models


def create_page2_questions(apps, schema_editor):
    Question = apps.get_model('users', 'Question')

    page2 = [
        {
            'id': 'q13',
            'text': 'Your Value Proposition',
            'question_type': 'textarea',
            'required': False,
            'placeholder': 'Describe your unique value as a potential business owner...',
            'order': 13,
            'page': 2,
            'is_active': True,
            'extra': {'examples': ['People-first leader who can turn complexity into clarity']},
            'component': '',
            'validation': {}
        },
        {
            'id': 'q14',
            'text': 'Areas of Expertise',
            'question_type': 'textarea',
            'required': False,
            'placeholder': 'List your areas of expertise (one per line)',
            'order': 14,
            'page': 2,
            'is_active': True,
            'extra': {'examples': ['Operations Management', 'Financial Analysis', 'Team Building']},
            'component': '',
            'validation': {}
        }
    ]

    for q in page2:
        Question.objects.update_or_create(
            id=q['id'],
            defaults={
                'text': q['text'],
                'question_type': q.get('question_type', 'text'),
                'required': q.get('required', False),
                'placeholder': q.get('placeholder', ''),
                'options': q.get('options', []),
                'extra': q.get('extra', {}),
                'component': q.get('component', None),
                'validation': q.get('validation', {}),
                'order': q['order'],
                'is_active': q.get('is_active', True),
                'page': q.get('page', 1),
            }
        )


def remove_page2_questions(apps, schema_editor):
    Question = apps.get_model('users', 'Question')
    Question.objects.filter(id__in=['q13', 'q14']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0035_update_checkbox_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='page',
            field=models.PositiveIntegerField(default=1, help_text='Questionnaire page number (1,2,...)'),
        ),
        migrations.RunPython(create_page2_questions, reverse_code=remove_page2_questions),
    ]
