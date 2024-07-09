from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .tasks import execute_scraper
from .models import ScraperResult
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q

class ScrapeView(APIView):
    def post(self, request):
        task = execute_scraper.delay()
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)

class TaskStatusView(APIView):
    def get(self, request, task_id):
        task = execute_scraper.AsyncResult(task_id)
        return Response({"status": task.status, "result": task.result})

class ResultsView(APIView):
    def get(self, request):
        query = request.GET.get('query', '')
        page = request.GET.get('page', 1)
        per_page = request.GET.get('per_page', 10)

        results = ScraperResult.objects.filter(
            Q(name__icontains=query) | 
            Q(userid__icontains=query) |
            Q(registration_number__icontains=query)
        )

        paginator = Paginator(results, per_page)
        page_obj = paginator.get_page(page)

        return JsonResponse({
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'results': list(page_obj.object_list.values()),
        })