from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from core.views import HealthView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/health/', HealthView.as_view(), name='health'),
    path('api/', include('core.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='spa'),
]
