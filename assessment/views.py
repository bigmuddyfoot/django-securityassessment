from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Prefetch
from .models import (
    Question, Category, Product, Customer, Assessment,
    QuestionOption, UserAnswer, StandardizedInput, HelpResource
)
import json

def home(request):
    return render(request, 'assessment/home.html')



#  View to Manage Question Order (Drag and Drop)
@login_required  # You can also use @staff_member_required for admin-only
def manage_question_order(request):
    categories = Category.objects.prefetch_related(
        Prefetch('question_set', queryset=Question.objects.order_by('order'))
    ).order_by('name')  # Adjust to 'order' if you want category ordering too

    return render(request, 'assessment/manage_question_order.html', {'categories': categories})


#  API to Save Question Order
@require_POST
@login_required  # You can also use @staff_member_required for admin-only
def save_question_order(request):
    data = json.loads(request.body)

    for category_id, questions in data.items():
        for item in questions:
            question_id = item['id']
            new_order = item['order']
            Question.objects.filter(id=question_id, category_id=category_id).update(order=new_order)

    return JsonResponse({'status': 'success'})


#  View to Start or Continue an Assessment
@login_required
def start_assessment(request):
    customers = Customer.objects.all()

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        customer = get_object_or_404(Customer, id=customer_id)

        # Check if an in-progress assessment already exists for this customer and employee
        assessment, created = Assessment.objects.get_or_create(
            customer=customer,
            employee=request.user,
            status='in_progress'
        )

        # Redirect to the question flow for this assessment
        return redirect('assessment_questions', assessment_id=assessment.id)

    return render(request, 'assessment/start_assessment.html', {'customers': customers})


#  View to Show and Answer Questions with Navigation and Category Filtering
@login_required
def assessment_questions(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)

    # Handle navigation via query parameters
    selected_category_id = request.GET.get('category')
    previous_question_id = request.GET.get('previous')

    # Questions already answered in this assessment
    answered_questions = UserAnswer.objects.filter(assessment=assessment).values_list('question_id', flat=True)

    # Questions to filter (by category if selected)
    question_queryset = Question.objects.exclude(id__in=answered_questions).order_by('order')
    if selected_category_id:
        question_queryset = question_queryset.filter(category_id=selected_category_id)

    # If going back to a previous question (for viewing/editing)
    if previous_question_id:
        question = get_object_or_404(Question, id=previous_question_id)
    else:
        question = question_queryset.first()

    #  Redirect to summary if no more questions are available
    if not question:
        return redirect('assessment_summary', assessment_id=assessment.id)

    # Form submission to save current answer
    if request.method == 'POST' and question:
        answer_text = request.POST.get('answer_text', '')
        selected_option_id = request.POST.get('answer_option', None)
        note = request.POST.get('note', '')

        # Avoid duplicate answer saves
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

    # All questions for total count/progress
    total_questions = Question.objects.count()
    answered_count = UserAnswer.objects.filter(assessment=assessment).count()
    current_question_number = min(answered_count + 1, total_questions)  # ✅ Avoid over-counting

    # All categories for left sidebar
    categories = Category.objects.all()

    # Fetch previous question id if available for back button
    previous_answers = UserAnswer.objects.filter(assessment=assessment).order_by('-id')
    previous_question = previous_answers.first().question if previous_answers.exists() else None

    context = {
        'assessment': assessment,
        'question': question,
        'categories': categories,
        'current_question_number': current_question_number,
        'total_questions': total_questions,
        'previous_question_id': previous_question.id if previous_question else None
    }

    return render(request, 'assessment/assessment_questions.html', context)


#  View to Show Assessment Summary when Complete
@login_required
def assessment_summary(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)
    # Gather data to show in the summary, e.g. user answers, scores, etc.
    user_answers = UserAnswer.objects.filter(assessment=assessment)
    # You might also calculate total scores, percentage correct, etc.

    return render(request, 'assessment/assessment_summary.html', {
        'assessment': assessment,
        'user_answers': user_answers,
        # Add any other summary data here
    })
