from django.urls import path
from .views import (AuditLogView, DeviceCollection, GDPRDeleteView, GDPRExportView, LoginView,
                    LogoutView, ObservationCollection, PatientAnalysisView, PatientCollection,
                    PatientDetail, PatientObservationCollection, PseudonymizedExportView,
                    UserDetailView, UserManagementView)

urlpatterns = [
    path('auth/token/', LoginView.as_view(), name='token-login'),
    path('auth/logout/', LogoutView.as_view(), name='token-logout'),
    path('patients/', PatientCollection.as_view(), name='patient-list'),
    path('patients/<str:patient_id>/', PatientDetail.as_view(), name='patient-detail'),
    path('patients/<str:patient_id>/observations/', PatientObservationCollection.as_view(), name='patient-observations'),
    path('patients/<str:patient_id>/analysis/', PatientAnalysisView.as_view(), name='patient-analysis'),
    path('patients/<str:patient_id>/gdpr-export/', GDPRExportView.as_view(), name='gdpr-export'),
    path('patients/<str:patient_id>/gdpr-delete/', GDPRDeleteView.as_view(), name='gdpr-delete'),
    path('observations/', ObservationCollection.as_view(), name='observation-list'),
    path('devices/', DeviceCollection.as_view(), name='device-list'),
    path('exports/pseudonymized/', PseudonymizedExportView.as_view(), name='pseudonymized-export'),
    path('users/', UserManagementView.as_view(), name='user-list'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('audit/', AuditLogView.as_view(), name='audit-log'),
]
