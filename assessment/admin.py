from django.contrib import admin
from django import forms
from tinymce.widgets import TinyMCE
from adminsortable2.admin import SortableAdminMixin

from .models import (
    Question, Category, Product, Customer, Assessment,
    QuestionOption, UserAnswer, StandardizedInput, HelpResource
)

# Custom form for Question to use TinyMCE for explanation_text
class QuestionAdminForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'
        widgets = {
            'explanation_text': TinyMCE(attrs={'cols': 80, 'rows': 20}),
        }

# Category Admin with Drag-and-Drop sorting
@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'order', 'description')
    ordering = ('order',)


# Question Admin with TinyMCE and Drag-and-Drop sorting
@admin.register(Question)
class QuestionAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = QuestionAdminForm
    list_display = ['text', 'category', 'question_type', 'order']
    list_filter = ['category', 'question_type']
    ordering = ('category', 'order')
    search_fields = ['text']
    autocomplete_fields = ['video', 'audio', 'pdf', 'help_resources']


@admin.register(HelpResource)
class HelpResourceAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_number', 'unit_type', 'quantity_source_count_type')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email')


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('customer', 'employee', 'status', 'date_started', 'date_completed')


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'score_value', 'flag_required')


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'question', 'answer_text', 'selected_option', 'score', 'flag_required', 'date_answered')


@admin.register(StandardizedInput)
class StandardizedInputAdmin(admin.ModelAdmin):
    list_display = ('text', 'description')
