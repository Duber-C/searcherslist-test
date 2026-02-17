from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
def get_questions_list(request):
    """
    Get the list of active questions for the questionnaire
    """
    try:
        from ..models import Question

        questions = Question.objects.filter(is_active=True).order_by('order')

        questions_data = []
        for question in questions:
            question_data = {
                'id': question.id,
                'text': question.text,
                'type': question.question_type,
                'required': question.required,
                'placeholder': question.placeholder or '',
                'order': question.order
            }

            if question.options:
                question_data['options'] = question.options

            questions_data.append(question_data)

        return Response({
            'status': 'success',
            'questions': questions_data,
            'total_questions': len(questions_data)
        })

    except Exception as e:
        print(f"ERROR: Failed to fetch questions: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to fetch questions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def test_questionnaire_answers(request):
    """
    Test endpoint to receive questionnaire answers in JSON format
    """
    try:
        answers = request.data.get('answers', {})

        if not answers:
            return Response({
                'status': 'error',
                'message': 'No answers provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        print(f"DEBUG: Received questionnaire answers: {answers}")

        if not isinstance(answers, dict):
            return Response({
                'status': 'error',
                'message': 'Answers must be provided as a JSON object'
            }, status=status.HTTP_400_BAD_REQUEST)

        from ..models import Question
        valid_question_ids = set(Question.objects.filter(is_active=True).values_list('id', flat=True))

        answered_questions = []
        unknown_questions = []

        for question_id in answers.keys():
            if question_id in valid_question_ids:
                answered_questions.append(question_id)
            else:
                unknown_questions.append(question_id)

        response_data = {
            'status': 'success',
            'message': 'Questionnaire answers received successfully',
            'answers_received': answers,
            'summary': {
                'total_answers': len(answers),
                'valid_questions_answered': len(answered_questions),
                'unknown_questions': unknown_questions if unknown_questions else None
            }
        }

        return Response(response_data)

    except Exception as e:
        print(f"ERROR: Failed to process questionnaire answers: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to process questionnaire answers: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
