import asyncio
import logging
import sys
import signal
import psutil
from typing import List
from .search_scraper import SearchScraper
from .registrant_scraper import RegistrantInfoScraper, RegistrantInfo
from .rate_limiter import RateLimiter
import json
from dataclasses import asdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global flag to signal all tasks to stop
stop_flag = asyncio.Event()

def signal_handler(signum, frame):
    logger.info("Interrupt received, stopping scraper...")
    stop_flag.set()

async def registrant_worker(queue: asyncio.Queue, results: List[RegistrantInfo], 
                            rate_limiter: RateLimiter, worker_id: int):
    scraper = RegistrantInfoScraper()
    try:
        while True:
            try:
                user_id = await asyncio.wait_for(queue.get(), timeout=1.0)
                if user_id is None:
                    logger.info(f"Worker {worker_id}: Received stop signal")
                    break
                
                await rate_limiter.acquire()
                try:
                    info = await scraper.scrape(user_id)
                    results.append(info)
                    logger.info(f"Worker {worker_id}: Scraped info for URL: {info.url}")
                except Exception as e:
                    logger.error(f"Worker {worker_id}: Error scraping user_id {user_id}: {str(e)}")
                finally:
                    queue.task_done()
            except asyncio.TimeoutError:
                if stop_flag.is_set() and queue.empty():
                    logger.info(f"Worker {worker_id}: No more items and stop flag is set")
                    break
    finally:
        await scraper.close()
        logger.info(f"Worker {worker_id}: Shutting down")

async def main():
    queue = asyncio.Queue()
    search_scraper = SearchScraper(queue, stop_flag)

    try:
        rate_limiter = RateLimiter(rate=2, per=1.0, burst=1)

        logger.info("Starting search scraper...")
        search_task = asyncio.create_task(search_scraper.scrape())

        registrant_infos = []

        num_workers = 5
        worker_tasks = []
        for i in range(num_workers):
            task = asyncio.create_task(registrant_worker(queue, registrant_infos, rate_limiter, i))
            worker_tasks.append(task)

        # Wait for search task to complete
        await search_task
        logger.info("Search task completed")

        # Wait for all items in the queue to be processed
        logger.info("Waiting for all items in the queue to be processed...")
        await queue.join()

        # Signal all workers to exit
        logger.info("Signaling workers to exit...")
        for _ in range(num_workers):
            await queue.put(None)

        # Wait for all worker tasks to complete
        logger.info("Waiting for all worker tasks to complete...")
        await asyncio.gather(*worker_tasks, return_exceptions=True)

        logger.info(f"Scraping completed. Scraped info for {len(registrant_infos)} registrants")
        save_results(registrant_infos)
        
        return registrant_infos
    finally:
        await search_scraper.close()

def save_results(registrant_infos: List[RegistrantInfo]):
    filename = 'registrant_results.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump([asdict(info) for info in registrant_infos], f, ensure_ascii=False, indent=4)
    logger.info(f"Results saved to {filename}")

async def run_scraper():
    results = []
    try:
        results = await main()  # Assuming main() returns the scraped results
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, stopping scraper...")
    finally:
        logger.info("Shutting down...")
        cleanup_chrome_processes()
    return results


def cleanup_chrome_processes():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'chrome.exe':
            try:
                proc.terminate()
            except psutil.NoSuchProcess:
                pass


def run_scraper_sync():
    if sys.platform == 'win32':
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    else:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler, sig, None)
    
    asyncio.run(run_scraper())

if __name__ == "__main__":
    run_scraper_sync()