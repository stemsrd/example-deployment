from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .tasks import execute_scraper
import asyncio

class ScrapeView(APIView):
    def post(self, request):
        try:
            asyncio.run(execute_scraper())
            return Response({"message": "Scraping completed successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)