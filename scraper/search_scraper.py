import asyncio
import logging
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class SearchScraper:
    URL = "https://members.collegeofopticians.ca/coo/Public%20Register/Member-Search.aspx"
    
    def __init__(self, queue: asyncio.Queue, stop_flag: asyncio.Event):
        self.driver = self._setup_driver()
        self.queue = queue
        self.stop_flag = stop_flag

    @staticmethod
    def _setup_driver():
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument('--log-level=3')  # Only show fatal errors
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    async def scrape(self):
        try:
            logger.info("Navigating to search page...")
            await self._navigate_to_search_page()
            logger.info("Applying search filter...")
            await self._apply_search_filter()
            logger.info("Performing search...")
            await self._perform_search()
            logger.info("Setting page size...")
            await self._set_page_size(50)  # Set to 50 items per page
            logger.info("Getting total pages...")
            total_pages = await self._get_total_pages()
            logger.info(f"Total pages: {total_pages}")
            
            for page in range(1, total_pages + 1):
                if self.stop_flag.is_set():
                    logger.info("Stop flag set, interrupting search scraper...")
                    break
                logger.info(f"Scraping page {page} of {total_pages}")
                user_ids = await self._parse_results(self.driver.page_source)
                for user_id in user_ids:
                    await self.queue.put(user_id)
                
                if page < total_pages:
                    logger.info("Moving to next page...")
                    await self._go_to_next_page()
            
            logger.info("Search scraping completed.")
        except Exception as e:
            logger.exception(f"An error occurred during scraping: {str(e)}")
        finally:
            logger.info("Closing browser...")
            await self.close()

    async def _navigate_to_search_page(self):
        self.driver.get(self.URL)

    async def _apply_search_filter(self):
        try:
            # Wait for the dropdown to be present
            dropdown_locator = (By.ID, "ctl01_TemplateBody_WebPartManager1_gwpciNewQueryMenuCommon_ciNewQueryMenuCommon_ResultsGrid_Sheet0_Input7_DropDown1")
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located(dropdown_locator))
            
            # Select the dropdown
            service_area_dropdown = Select(self.driver.find_element(*dropdown_locator))
            
            # Select the desired value
            service_area_dropdown.select_by_value("ARTIFICIAL")
            logger.info("Applied 'ARTIFICIAL' filter to the search.")
        except Exception as e:
            logger.error(f"Error applying search filter: {str(e)}")
            raise

    async def _set_page_size(self, size: int = 50):
        try:
            logger.info(f"Setting page size to {size}...")
            
            # Find and click the page size dropdown to open it
            dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "ctl01_TemplateBody_WebPartManager1_gwpciNewQueryMenuCommon_ciNewQueryMenuCommon_ResultsGrid_Grid1_ctl00_ctl03_ctl01_PageSizeComboBox_Input"))
            )
            self.driver.execute_script("arguments[0].click();", dropdown)

            # Wait for the dropdown options to be visible
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, f"//ul[@id='ctl01_TemplateBody_WebPartManager1_gwpciNewQueryMenuCommon_ciNewQueryMenuCommon_ResultsGrid_Grid1_ctl00_ctl03_ctl01_PageSizeComboBox_listbox']/li[text()='{size}']"))
            )

            # Find and click the option for the specified number of items per page
            page_size_option = self.driver.find_element(By.XPATH, f"//ul[@id='ctl01_TemplateBody_WebPartManager1_gwpciNewQueryMenuCommon_ciNewQueryMenuCommon_ResultsGrid_Grid1_ctl00_ctl03_ctl01_PageSizeComboBox_listbox']/li[text()='{size}']")
            self.driver.execute_script("arguments[0].click();", page_size_option)

            # Wait for the page to reload with the new page size
            await asyncio.sleep(20)  # Adjust the sleep time as needed
            logger.info(f"Page size set to {size}")
        except Exception as e:
            logger.error(f"Error setting page size: {str(e)}")
            raise

    async def _perform_search(self):
        try:
            search_button = WebDriverWait(self.driver, 40).until(
                EC.element_to_be_clickable((By.ID, "ctl01_TemplateBody_WebPartManager1_gwpciNewQueryMenuCommon_ciNewQueryMenuCommon_ResultsGrid_Sheet0_SubmitButton"))
            )
            search_button.click()
            WebDriverWait(self.driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            raise

    async def _get_total_pages(self) -> int:
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            pagination_info = soup.select_one(".rgWrap.rgInfoPart")
            if pagination_info:
                return int(pagination_info.find_all("strong")[-1].text)
            return 1
        except Exception as e:
            logger.error(f"Error getting total pages: {str(e)}")
            return 1

    async def _parse_results(self, html: str) -> List[str]:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            user_ids = []
            for row in soup.select("table tbody tr"):
                user_id_cell = row.find("td", {"style": "display:none;"})
                if user_id_cell:
                    user_ids.append(user_id_cell.text.strip())
            return user_ids
        except Exception as e:
            logger.error(f"Error parsing search results: {str(e)}")
            return []

    async def _go_to_next_page(self):
        try:
            next_button = self.driver.find_elements(By.CLASS_NAME, "rgPageNext")
            if next_button:
                self.driver.execute_script("arguments[0].click();", next_button[0])
                time.sleep(20)  # Wait for next page to load
            else:
                logger.info("No next page button found.")
        except Exception as e:
            logger.error(f"Error going to next page: {str(e)}")

    async def close(self):
        try:
            self.driver.quit()
        except Exception as e:
            logger.error(f"Error closing WebDriver: {str(e)}")