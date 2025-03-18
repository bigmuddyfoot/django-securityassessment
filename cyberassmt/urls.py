from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import necessary views from assessment
from assessment.views import (
    assessment_summary,
    assessment_questions,
    start_assessment,
    export_assessment_summary  # ✅ FIX: Import this view
)

urlpatterns = [
    path('summary/<int:assessment_id>/', assessment_summary, name='assessment_summary'),
    path('questions/<int:assessment_id>/', assessment_questions, name='assessment_questions'),
    path('start/', start_assessment, name='start_assessment'),
    path('summary/<int:assessment_id>/export/', export_assessment_summary, name='export_assessment_summary'),  # ✅ Fix: Now properly imported
    
    # Admin and authentication
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),

    # Include assessment app URLs
    path('assessment/', include('assessment.urls')),
    path('', include('assessment.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
