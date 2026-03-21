"""Create default questionnaire questions used by the frontend.

This data migration creates or updates a fixed set of questions so the
frontend can render components based on `question_type` and `component`.
"""
from django.db import migrations


def create_questions(apps, schema_editor):
    Question = apps.get_model('users', 'Question')

    questions = [
        {
            'id': 'q1',
            'text': 'Describe the acquisition target in one sentence',
            'question_type': 'text',
            'required': True,
            'placeholder': 'E.g. profitable SaaS business in healthcare',
            'order': 1,
            'is_active': True,
            'extra': {'examples': ['SaaS business', 'Healthcare', 'EBITDA > $1M']},
            'component': '',
            'validation': {}
        },
        {
            'id': 'q2',
            'text': 'What is the ideal company size (revenue or employees)?',
            'question_type': 'text',
            'required': True,
            'placeholder': 'E.g. $5M-$20M ARR or 20-100 employees',
            'order': 2,
            'is_active': True,
            'extra': {},
            'component': '',
            'validation': {}
        },
        {
            'id': 'q3',
            'text': 'Upload or paste any target-company profile or notes (custom)',
            'question_type': 'custom',
            'required': False,
            'placeholder': '',
            'order': 3,
            'is_active': True,
            'extra': {'accepts': ['text', 'file'], 'max_files': 3},
            'component': 'TargetProfileUploader',
            'validation': {}
        },
        {
            'id': 'q4',
            'text': 'Which industries are you most interested in?',
            'question_type': 'text',
            'required': True,
            'placeholder': 'E.g. Healthcare, Fintech',
            'order': 4,
            'is_active': True,
            'extra': {},
            'component': '',
            'validation': {}
        },
        {
            'id': 'q5',
            'text': 'What deal structures are acceptable? (select all that apply)',
            'question_type': 'checkbox_group',
            'required': False,
            'placeholder': '',
            'order': 5,
            'is_active': True,
            'options': ['Asset sale', 'Stock sale', 'Seller financing', 'Earnout'],
            'extra': {},
            'component': '',
            'validation': {}
        },
        {
            'id': 'q6',
            'text': 'Do you require current management to stay?',
            'question_type': 'radio',
            'required': False,
            'placeholder': '',
            'order': 6,
            'is_active': True,
            'options': ['Yes, fully', 'Yes, transition period', 'No, not necessary'],
            'extra': {},
            'component': '',
            'validation': {}
        },
        {
            'id': 'q7',
            'text': 'Preferred geography for acquisitions?',
            'question_type': 'radio',
            'required': False,
            'placeholder': '',
            'order': 7,
            'is_active': True,
            'options': ['North America', 'Europe', 'Global', 'Specific countries only'],
            'extra': {},
            'component': '',
            'validation': {}
        },
        {
            'id': 'q8',
            'text': 'What is your approximate target EBITDA or margin expectations?',
            'question_type': 'radio',
            'required': False,
            'placeholder': '',
            'order': 8,
            'is_active': True,
            'options': ['<10%', '10-20%', '20-30%', '30%+'],
            'extra': {},
            'component': '',
            'validation': {}
        },
        {
            'id': 'q9',
            'text': 'Which of these buyer constraints apply? (select all that apply)',
            'question_type': 'checkbox_group',
            'required': False,
            'placeholder': '',
            'order': 9,
            'is_active': True,
            'options': ['No foreign ownership', 'No debt', 'No legal encumbrances', 'Must have existing recurring revenue'],
            'extra': {},
            'component': '',
            'validation': {}
        },
        {
            'id': 'q10',
            'text': 'Timing for closing a deal?',
            'question_type': 'radio',
            'required': False,
            'placeholder': '',
            'order': 10,
            'is_active': True,
            'options': ['Immediately', '3-6 months', '6-12 months', 'No rush'],
            'extra': {},
            'component': '',
            'validation': {}
        },
        {
            'id': 'q11',
            'text': 'Do you require any specific certifications or accreditations?',
            'question_type': 'checkbox_group',
            'required': False,
            'placeholder': '',
            'order': 11,
            'is_active': True,
            'options': ['ISO', 'HIPAA', 'SOC2', 'None'],
            'extra': {},
            'component': '',
            'validation': {}
        },
        {
            'id': 'q12',
            'text': 'Any additional notes or preferences?',
            'question_type': 'text',
            'required': True,
            'placeholder': 'Provide any other details that help define your target',
            'order': 12,
            'is_active': True,
            'extra': {},
            'component': '',
            'validation': {}
        },
    ]

    for q in questions:
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
            }
        )


def remove_questions(apps, schema_editor):
    Question = apps.get_model('users', 'Question')
    ids = [f'q{i}' for i in range(1, 13)]
    Question.objects.filter(id__in=ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0027_question_component_question_extra_and_more'),
    ]

    operations = [
        migrations.RunPython(create_questions, reverse_code=remove_questions),
    ]
