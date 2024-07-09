from celery import shared_task
from scraper.public_registry.main import run_scraper
from .models import ScraperResult

@shared_task
def execute_scraper():
    results = run_scraper()
    for result in results:
        ScraperResult.objects.create(**result)
    return len(results)