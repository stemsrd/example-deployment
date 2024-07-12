from django.urls import path
from .views import ScrapeView, TaskStatusView, ResultsView

urlpatterns = [
    path('scrape/', ScrapeView.as_view(), name='scrape'),
    path('task-status/<str:task_id>/', TaskStatusView.as_view(), name='task_status'),
    path('results/', ResultsView.as_view(), name='results'),
]