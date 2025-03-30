from django.db import models
from django.contrib.auth.models import User

# Choices for count types
COUNT_TYPE_CHOICES = [
    ('pc', 'PC (Workstations & Laptops)'),
    ('server', 'Servers'),
    ('employee', 'Employees'),
    ('sites', 'Sites / Branches / Locations'),
    ('switches', 'Network Switches'),
    ('phones', 'Phones'),
    ('tablets', 'Tablets (iPad, Android)'),
    ('vpn', 'VPN Users'),
]

#  Standardized Answer Options (Global Text Options)
class StandardizedInput(models.Model):
    text = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.text


#  Help Resources (Video, PDF, Audio, Links)
class HelpResource(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='help_resources/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True, help_text="Enter a YouTube video URL if applicable")
    type = models.CharField(
        max_length=50,
        choices=[
            ('video', 'Video'),
            ('audio', 'Audio'),
            ('pdf', 'PDF'),
            ('link', 'External Link'),
        ]
    )

    def is_youtube_link(self):
        return self.external_link and ('youtube.com' in self.external_link or 'youtu.be' in self.external_link)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField("something", default=0)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    item_number = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    unit_type = models.CharField(max_length=100, help_text='e.g., per device, per user, per site')
    quantity_source_count_type = models.CharField(
        max_length=100,
        choices=COUNT_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text='Count type to pull quantity from (e.g., pc, server)'
    )

    def __str__(self):
        return f"{self.name} ({self.item_number})"


class Customer(models.Model):
    name = models.CharField(max_length=255)
    contact_email = models.EmailField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Assessment(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='assessments')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessments')
    date_started = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')

    def __str__(self):
        return f"Assessment #{self.id} - {self.customer.name} ({self.status})"

    @property
    def total_score(self):
        return sum(answer.score or 0 for answer in self.answers.all())


class Question(models.Model):
    QUESTION_TYPE_CHOICES = (
        ('yes_no', 'Yes/No/Other'),
        ('multiple_choice', 'Multiple Choice'),
        ('input', 'Input'),
    )

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    explanation_text = models.TextField(blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPE_CHOICES)
    weight = models.IntegerField(default=1, help_text='Weight of this question in scoring')
    neutral = models.BooleanField(default=False, help_text='If true, does not affect score')
    is_count_question = models.BooleanField(default=False, help_text='Marks if this is a global count question')
    count_type = models.CharField(
        max_length=100,
        choices=COUNT_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text='Type of count this question gathers'
    )
    recommended_product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    help_resources = models.ManyToManyField(HelpResource, blank=True, help_text='Optional help resources for users')
    video = models.ForeignKey(
        HelpResource,
        limit_choices_to={'type': 'video'},
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='video_questions'
    )
    audio = models.ForeignKey(
        HelpResource,
        limit_choices_to={'type': 'audio'},
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audio_questions'
    )
    pdf = models.ForeignKey(
        HelpResource,
        limit_choices_to={'type': 'pdf'},
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pdf_questions'
    )
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.text[:80]

    class Meta:
        ordering = ['order']


class QuestionInputOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='input_options')
    standardized_input = models.ForeignKey(StandardizedInput, on_delete=models.CASCADE)
    score_value = models.IntegerField(default=0)
    is_preferred = models.BooleanField(default=False)

    class Meta:
        unique_together = ('question', 'standardized_input')

    def __str__(self):
        return f"{self.question.text[:30]} → {self.standardized_input.text}"


class UserAnswer(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True, null=True)
    selected_option = models.ForeignKey(StandardizedInput, on_delete=models.SET_NULL, blank=True, null=True)
    score = models.IntegerField(blank=True, null=True)
    flag_required = models.BooleanField(default=False)
    date_answered = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True, help_text='Optional note for explanation or context')

    def __str__(self):
        return f"Answer to {self.question.text[:50]} (Assessment #{self.assessment.id})"


class CSVUploadPlaceholder(models.Model):
    class Meta:
        verbose_name = "Upload Questions CSV"
        verbose_name_plural = "Upload Questions CSV"
        managed = False

    def __str__(self):
        return "Upload Questions CSV"
