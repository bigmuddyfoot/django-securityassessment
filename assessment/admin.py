from django.contrib import admin
from django import forms
from tinymce.widgets import TinyMCE
from adminsortable2.admin import SortableAdminMixin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.template.response import TemplateResponse
import csv
import os

from .models import (
    Question, Category, Product, Customer, Assessment,
    QuestionOption, UserAnswer, StandardizedInput, HelpResource, CSVUploadPlaceholder
)

# ---------- EXISTING QUESTION ADMIN ---------- #

# Custom form for Question to use TinyMCE for explanation_text
class QuestionAdminForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'
        widgets = {
            'explanation_text': TinyMCE(attrs={'cols': 80, 'rows': 20}),
        }

@admin.register(Question)
class QuestionAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = QuestionAdminForm
    sortable_field_name = "order"
    list_display = ['text', 'display_category', 'question_type']
    list_filter = ['category', 'question_type']
    ordering = ('order',)
    search_fields = ['text']
    autocomplete_fields = ['video', 'audio', 'pdf', 'help_resources']

    def display_category(self, obj):
        return obj.category.name if obj.category else ""
    display_category.short_description = "Category"

    class Media:
        css = {
            'all': ('css/admin_custom.css',)
        }

# ---------- CSV UPLOAD ADMIN TIED TO PLACEHOLDER ---------- #

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='Select a CSV file to upload')

@admin.register(CSVUploadPlaceholder)
class CSVQuestionUploadAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-questions-csv/', self.admin_site.admin_view(self.upload_csv), name='question_csv_upload'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        return redirect('admin:question_csv_upload')

    def upload_csv(self, request):
        if request.method == "POST":
            form = CSVUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data['csv_file']
                fs = FileSystemStorage()
                filename = fs.save(csv_file.name, csv_file)
                file_path = fs.path(filename)

                imported, categories_created, inputs_created, errors = self.handle_csv_import(file_path)
                fs.delete(filename)

                msg = f"✅ {imported} Questions imported. ✅ {categories_created} Categories created. ✅ {inputs_created} Standardized Inputs created."
                if errors:
                    error_file_path = os.path.join(os.path.dirname(file_path), "import_errors.csv")
                    with open(error_file_path, "w", newline="", encoding="utf-8") as error_file:
                        writer = csv.writer(error_file)
                        writer.writerow(["Error Details"])
                        for error in errors:
                            writer.writerow([error])
                    msg += f" ❗ {len(errors)} Errors found. <a href='/media/import_errors.csv'>Download Error Log</a>"
                    messages.error(request, mark_safe(msg))
                else:
                    messages.success(request, mark_safe(msg))

                return redirect('admin:question_csv_upload')
        else:
            form = CSVUploadForm()

        context = dict(
            self.admin_site.each_context(request),
            form=form,
        )
        return TemplateResponse(request, "assessment/question_csv_upload.html", context)
    
    def handle_csv_import(self, file_path):
        imported = 0
        categories_created = 0
        inputs_created = 0
        errors = []

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            row_number = 1

            for row in reader:
                try:
                    required_fields = ['text', 'category', 'question_type', 'weight', 'neutral', 'is_count_question']
                    missing_fields = [field for field in required_fields if field not in row or not row[field].strip()]
                    if missing_fields:
                        raise ValueError(f"Row {row_number}: Missing fields: {', '.join(missing_fields)}")

                    category_name = row['category'].strip()
                    category, cat_created = Category.objects.get_or_create(name=category_name)
                    if cat_created:
                        categories_created += 1

                    input_list = [i.strip() for i in row.get('standardized_inputs', '').split(',') if i.strip()]
                    input_objs = []
                    for input_text in input_list:
                        input_obj, input_created = StandardizedInput.objects.get_or_create(text=input_text)
                        if input_created:
                            inputs_created += 1
                        input_objs.append(input_obj)

                    question = Question.objects.create(
                        category=category,
                        text=row['text'],
                        question_type=row['question_type'],
                        weight=int(row['weight']),
                        neutral=row['neutral'].strip().lower() == 'true',
                        is_count_question=row['is_count_question'].strip().lower() == 'true',
                        count_type=row['count_type'] if 'count_type' in row and row['count_type'] else None
                    )
                    question.standardized_inputs.set(input_objs)
                    imported += 1
                except Exception as e:
                    errors.append(f"Row {row_number}: {str(e)}")
                row_number += 1

        return imported, categories_created, inputs_created, errors

# ---------- OTHER EXISTING ADMINS ---------- #

@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'order', 'description')
    ordering = ('order',)

@admin.register(HelpResource)
class HelpResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'display_resource')

    def display_resource(self, obj):
        if obj.file:
            return format_html(f'<a href="{obj.file.url}" target="_blank">Uploaded File</a>')
        elif obj.is_youtube_link():
            return format_html(f'<a href="{obj.external_link}" target="_blank">YouTube Video</a>')
        elif obj.external_link:
            return format_html(f'<a href="{obj.external_link}" target="_blank">External Link</a>')
        return "No Resource"

    display_resource.short_description = "Resource Link"

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
