from django.urls import path
from . import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),  
    path('start/', views.start_assessment, name='start_assessment'),
    path('questions/<int:assessment_id>/<int:category_id>/', views.assessment_questions, name='assessment_questions'),

    path('manage-question-order/', views.manage_question_order, name='manage_question_order'),
    path('save-question-order/', views.save_question_order, name='save_question_order'),
    path('summary/<int:assessment_id>/', views.assessment_summary, name='assessment_summary'),
    path('', views.home, name='home'),
]
