from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('list/', views.filter_loans, name='get_simplified_loans_list'),
    path('list/<int:loan_id>/download/', views.download_loan_schedule, name='download_loan_schedule'),
    
]
