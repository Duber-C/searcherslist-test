from django.core.management.base import BaseCommand
from users.models import Question


class Command(BaseCommand):
    help = 'Load questionnaire questions into the database'

    def handle(self, *args, **options):
        # Clear existing questions
        deleted_count, _ = Question.objects.all().delete()
        if deleted_count > 0:
            self.stdout.write(f'Deleted {deleted_count} existing questions')
        
        # Define the questions from the questionnaire-slider.tsx
        questions_data = [
            # Required questions
            {
                'id': 'target_business_types',
                'text': 'What type of business are you looking to acquire?',
                'question_type': 'text',
                'required': True,
                'placeholder': 'e.g., B2B service business, SaaS, manufacturing',
                'order': 1
            },
            {
                'id': 'target_geography',
                'text': 'What geographic area are you targeting?',
                'question_type': 'text',
                'required': True,
                'placeholder': 'e.g., Chicagoland area, California, Remote-friendly',
                'order': 2
            },
            {
                'id': 'size_metric',
                'text': 'What metric do you prefer for business size?',
                'question_type': 'select',
                'required': True,
                'options': ['SDE (Seller Discretionary Earnings)', 'EBITDA', 'Annual Profit', 'Annual Revenue'],
                'order': 3
            },
            {
                'id': 'size_range_min',
                'text': 'What is your minimum target size?',
                'question_type': 'text',
                'required': True,
                'placeholder': 'e.g., $500k, $1M, $2M',
                'order': 4
            },
            {
                'id': 'size_range_max',
                'text': 'What is your maximum target size?',
                'question_type': 'text',
                'required': True,
                'placeholder': 'e.g., $2M, $5M, $10M',
                'order': 5
            },
            {
                'id': 'other_search_notes',
                'text': 'Any other search criteria or constraints?',
                'question_type': 'textarea',
                'required': True,
                'placeholder': 'e.g., Must be profitable, growth opportunities, specific industries to avoid',
                'order': 6
            },
            
            # Optional questions
            {
                'id': 'industry_geo_experience',
                'text': 'Do you have experience in your target industry or geography?',
                'question_type': 'textarea',
                'required': False,
                'placeholder': 'Describe any relevant industry or geographic experience...',
                'order': 7
            },
            {
                'id': 'owned_or_sold_before',
                'text': 'Have you owned or sold a business before?',
                'question_type': 'textarea',
                'required': False,
                'placeholder': 'Share your business ownership experience...',
                'order': 8
            },
            {
                'id': 'three_five_words',
                'text': 'What 3-5 words describe you best?',
                'question_type': 'text',
                'required': False,
                'placeholder': 'e.g., Strategic, Analytical, Collaborative, Results-driven',
                'order': 9
            },
            {
                'id': 'enjoy_work_most',
                'text': 'What kind of work do you enjoy most?',
                'question_type': 'textarea',
                'required': False,
                'placeholder': 'Describe the type of work that energizes you...',
                'order': 10
            },
            {
                'id': 'pnl_experience',
                'text': 'Do you have P&L experience?',
                'question_type': 'textarea',
                'required': False,
                'placeholder': 'Describe your profit and loss management experience...',
                'order': 11
            },
            {
                'id': 'team_building_experience',
                'text': 'Do you have team building/leadership experience?',
                'question_type': 'textarea',
                'required': False,
                'placeholder': 'Share your leadership and team management experience...',
                'order': 12
            },
            {
                'id': 'why_search_fund',
                'text': 'Why did you choose the search fund route?',
                'question_type': 'textarea',
                'required': False,
                'placeholder': 'Explain your motivation for pursuing a search fund...',
                'order': 13
            },
            {
                'id': 'favorite_part_job',
                'text': 'What was your favorite part of your last job?',
                'question_type': 'textarea',
                'required': False,
                'placeholder': 'Describe what you enjoyed most in your previous role...',
                'order': 14
            },
            {
                'id': 'least_favorite_part_job',
                'text': 'What was your least favorite part of your last job?',
                'question_type': 'textarea',
                'required': False,
                'placeholder': 'Share what you liked least about your previous role...',
                'order': 15
            },
            {
                'id': 'challenges_opportunities',
                'text': 'What kind of challenges or opportunities excite you?',
                'question_type': 'textarea',
                'required': False,
                'placeholder': 'Describe the types of business challenges that motivate you...',
                'order': 16
            },
            {
                'id': 'biggest_professional_success',
                'text': 'What has been your biggest professional success so far?',
                'question_type': 'textarea',
                'required': False,
                'placeholder': 'Share a significant professional achievement...',
                'order': 17
            },
            {
                'id': 'value_add_as_owner',
                'text': 'How do you think you will add value as a business owner?',
                'question_type': 'textarea',
                'required': False,
                'placeholder': 'Highlight your strengths as a future business owner...',
                'order': 18
            }
        ]

        # Create questions one by one to handle any issues
        created_count = 0
        for question_data in questions_data:
            try:
                question = Question.objects.create(**question_data)
                created_count += 1
                self.stdout.write(f'Created: {question.id} - {question.text[:50]}...')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create question {question_data["id"]}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} questions!')
        )
        
        self.stdout.write(
            self.style.WARNING('You can now view and edit these questions in the Django Admin at /admin/users/question/')
        )