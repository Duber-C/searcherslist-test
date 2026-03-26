"""Update text-based questions with subtitle, placeholder and examples from wireframe."""
from django.db import migrations


def update_text_questions(apps, schema_editor):
    Question = apps.get_model('users', 'Question')

    updates = {
        'q1': {
            'text': 'Business Type / Industry',
            'question_type': 'text',
            'placeholder': 'e.g., SaaS, E-commerce, Manufacturing, Professional Services, Healthcare, B2B Services',
            'extra': {
                'subtitle': "Specify the type of business or industry you're targeting. Be as specific or broad as you'd like.",
                'examples': ['SaaS','E-commerce','Professional Services','Manufacturing','Healthcare','Construction','Retail','Food & Beverage'],
                'note': "You can list multiple industries separated by commas if you're open to various business types"
            }
        },
        'q2': {
            'text': 'Where are you looking to buy?',
            'question_type': 'text',
            'placeholder': 'Type to search states...',
            'extra': {
                'subtitle': 'Select states or choose Nationwide/Remote-First',
                'examples': ['Great Lakes area','Southern California','South Florida','Chicago','Remote','Pacific Northwest','New England']
            }
        },
        'q4': {
            'text': 'Key Requirements',
            'question_type': 'textarea',
            'placeholder': 'Example: Looking for a business with recurring revenue, strong customer retention (>85%), established systems and processes, and growth potential. Must have a solid management team in place or be owner-independent. Prefer businesses with proven track record of profitability and clear growth opportunities...',
            'extra': {
                'subtitle': 'Describe your must-have requirements, deal-breakers, and key criteria for your ideal acquisition. Be specific about what matters most to you.',
                'examples': ['Revenue model preferences','Customer concentration limits','Operational maturity','Profitability track record']
            }
        },
        'q12': {
            'text': 'Additional Criteria & Notes',
            'question_type': 'textarea',
            'placeholder': "Example: Prefer businesses with strong online presence and digital marketing capabilities. Looking for opportunities where I can leverage my background in operations and process improvement. Interested in businesses with environmental or social impact. Open to seller financing for the right opportunity...",
            'extra': {
                'subtitle': "Any other important criteria, preferences, or notes that would help sellers understand what you're looking for?",
                'examples': ['Your relevant experience or expertise','Specific industry knowledge','Values or mission alignment','Deal structure preferences','Timeline expectations','Partnership or add-on opportunities']
            }
        }
    }

    for qid, data in updates.items():
        try:
            Question.objects.filter(id=qid).update(
                text=data['text'],
                question_type=data['question_type'],
                placeholder=data.get('placeholder', ''),
                extra=data.get('extra', {}),
            )
        except Exception:
            # create if missing
            Question.objects.update_or_create(id=qid, defaults={
                'text': data['text'],
                'question_type': data['question_type'],
                'placeholder': data.get('placeholder', ''),
                'options': data.get('options', []),
                'extra': data.get('extra', {}),
                'order': int(qid.replace('q','')),
                'is_active': True,
            })


def revert_text_questions(apps, schema_editor):
    # No-op revert: leave existing entries as-is
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0028_create_default_questions'),
    ]

    operations = [
        migrations.RunPython(update_text_questions, reverse_code=revert_text_questions),
    ]
