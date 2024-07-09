# api_project/api/tasks.py

from celery import shared_task
from scraper.public_registry.main import run_scraper
from .models import ScraperResult
import asyncio

@shared_task
def execute_scraper():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(run_scraper())
    loop.close()

    for result in results:
        data = result.__dict__
        # Remove any keys that aren't in the ScraperResult model
        model_fields = [f.name for f in ScraperResult._meta.get_fields()]
        filtered_data = {k: v for k, v in data.items() if k in model_fields}
        ScraperResult.objects.create(**filtered_data)
    
    return len(results)