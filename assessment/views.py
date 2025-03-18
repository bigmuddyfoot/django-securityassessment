from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.db.models import Prefetch, Sum
import csv
import json

from .models import (
    Question, Category, Customer, Assessment,
    QuestionOption, UserAnswer
)


def home(request):
    return render(request, 'assessment/home.html')


# 🚀 Manage Question Order (Drag and Drop)
@login_required
def manage_question_order(request):
    categories = Category.objects.prefetch_related(
        Prefetch('question_set', queryset=Question.objects.order_by('order'))
    ).order_by('name')

    return render(request, 'assessment/manage_question_order.html', {'categories': categories})


# 🚀 API to Save Question Order
@require_POST
@login_required
def save_question_order(request):
    try:
        data = json.loads(request.body)

        for category_id, questions in data.items():
            for item in questions:
                question_id = item['id']
                new_order = item['order']
                Question.objects.filter(id=question_id, category_id=category_id).update(order=new_order)

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# 🚀 Start or Continue an Assessment
@login_required
def start_assessment(request):
    customers = Customer.objects.all()

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        customer = get_object_or_404(Customer, id=customer_id)

        assessment, created = Assessment.objects.get_or_create(
            customer=customer,
            employee=request.user,
            status='in_progress'
        )

        return redirect('assessment_questions', assessment_id=assessment.id)

    return render(request, 'assessment/start_assessment.html', {'customers': customers})


# 🚀 Display and Answer Questions
@login_required
def assessment_questions(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)

    selected_category_id = request.GET.get('category')
    previous_question_id = request.GET.get('previous')

    # Fetch previously answered questions
    answered_questions = UserAnswer.objects.filter(assessment=assessment).values_list('question_id', flat=True)

    # Get next unanswered question
    question_queryset = Question.objects.exclude(id__in=answered_questions).order_by('order')
    if selected_category_id:
        question_queryset = question_queryset.filter(category_id=selected_category_id)

    # Check if navigating back to a previous question
    question = get_object_or_404(Question, id=previous_question_id) if previous_question_id else question_queryset.first()

    if not question:
        return redirect('assessment_summary', assessment_id=assessment.id)

    # Fetch existing answer if available
    existing_answer = UserAnswer.objects.filter(assessment=assessment, question=question).first()

    if request.method == 'POST':
        answer_text = request.POST.get('answer_text', '')
        selected_option_id = request.POST.get('answer_option', None)
        note = request.POST.get('note', '')

        # Save or update the answer
        UserAnswer.objects.update_or_create(
            assessment=assessment,
            question=question,
            defaults={
                'answer_text': answer_text,
                'selected_option': QuestionOption.objects.filter(id=selected_option_id).first() if selected_option_id else None,
                'note': note
            }
        )
        return redirect('assessment_questions', assessment_id=assessment.id)

    # Pre-fill selected answer
    selected_answer = existing_answer.selected_option.id if existing_answer and existing_answer.selected_option else None

    context = {
        'assessment': assessment,
        'question': question,
        'categories': Category.objects.all().order_by('order'),
        'existing_answer': existing_answer,
        'selected_answer': selected_answer,
        'previous_question_id': previous_question_id if previous_question_id else None,
    }

    return render(request, 'assessment/assessment_questions.html', context)


# 🚀 Assessment Summary View
@login_required
def assessment_summary(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)

    categorized_answers = {}
    user_answers = UserAnswer.objects.filter(assessment=assessment).select_related('question', 'selected_option')

    for answer in user_answers:
        category = answer.question.category.name if answer.question.category else "Uncategorized"
        if category not in categorized_answers:
            categorized_answers[category] = []

        # Ensure selected dropdown options are displayed properly
        display_answer = (
            answer.answer_text if answer.answer_text else
            (answer.selected_option.text if answer.selected_option else "No answer provided")
        )

        categorized_answers[category].append({
            "question": answer.question.text,
            "answer": display_answer,
            "note": answer.note if answer.note else "",
        })

    # Calculate total score (ensure numerical sum works)
    total_score = (
        UserAnswer.objects.filter(assessment=assessment)
        .exclude(score__isnull=True)
        .aggregate(total=Sum('score'))['total']
    ) or "N/A"

    context = {
        "assessment": assessment,
        "categorized_answers": categorized_answers,
        "total_score": total_score,
    }
    return render(request, "assessment/assessment_summary.html", context)


# 🚀 Export Assessment Summary as CSV
@login_required
def export_assessment_summary(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Assessment_Summary_{assessment.customer.name}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Category", "Question", "Answer", "Notes"])

    user_answers = UserAnswer.objects.filter(assessment=assessment).select_related('question', 'selected_option')

    for answer in user_answers:
        category = answer.question.category.name if answer.question.category else "Uncategorized"
        display_answer = (
            answer.answer_text if answer.answer_text else
            (answer.selected_option.text if answer.selected_option else "No answer provided")
        )

        writer.writerow([category, answer.question.text, display_answer, answer.note if answer.note else ""])

    return response
