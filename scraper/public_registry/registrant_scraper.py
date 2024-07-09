import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from webdriver_manager.chrome import ChromeDriverManager
import logging

logger = logging.getLogger(__name__)

@dataclass
class RegistrantInfo:
    name: str
    userid: str
    url: str
    registration_number: Optional[str] = None
    registration_date: Optional[str] = None
    name_used_in_practice: Optional[str] = None
    registrant_type: Optional[str] = None
    languages_of_care: Optional[str] = None
    registration_status: Optional[str] = None
    areas_of_practice: Optional[str] = None
    registrant_history: List[Dict[str, str]] = field(default_factory=list)
    practice_locations: List[Dict[str, str]] = field(default_factory=list)
    professional_corporation: List[Dict[str, str]] = field(default_factory=list)

class RegistrantInfoScraper:
    BASE_URL = "https://members.collegeofopticians.ca/coo/Public%20Register/Reigstrant-Information.aspx"
    
    def __init__(self):
        self.driver = self._setup_driver()

    @staticmethod
    def _setup_driver():
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument('--log-level=3')  # Only show fatal errors
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    async def scrape(self, user_id: str) -> RegistrantInfo:
        url = f"{self.BASE_URL}?UserID={user_id}"
        try:
            self.driver.get(url)
            await asyncio.sleep(10)  # Wait for dynamic content to load
            
            html = self.driver.page_source
            return self._parse_registrant_info(html, user_id, url)
        except Exception as e:
            logger.error(f"Error scraping registrant info for URL {url}: {str(e)}")
            return RegistrantInfo(name=f"Error: {str(e)}", userid=user_id, url=url)

    def _parse_registrant_info(self, html: str, userid: str, url: str) -> RegistrantInfo:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            name = soup.find("h3").text.strip() if soup.find("h3") else "Unknown"
            info = RegistrantInfo(name=name, userid=userid, url=url)
            
            for p in soup.find_all("p"):
                strong_tag = p.find("strong")
                if strong_tag:
                    label = strong_tag.text.strip().rstrip(":")
                    value = strong_tag.next_sibling.strip() if strong_tag.next_sibling else None
                    
                    if label == "Registration Number":
                        info.registration_number = value
                    elif label == "Date of Registration":
                        info.registration_date = value
                    elif label == "Name used in practice":
                        info.name_used_in_practice = value
                    elif label == "Registrant Type":
                        info.registrant_type = value
                    elif label == "Languages":
                        info.languages_of_care = value
                    elif label == "Registration Status":
                        info.registration_status = value
                    elif label == "Areas of Practice":
                        info.areas_of_practice = value
            
            info.registrant_history = self._extract_table_data(soup, 'ctl01_TemplateBody_WebPartManager1_gwpciRegistrantHistoryIQA_ciRegistrantHistoryIQA_ResultsGrid_Grid1_ctl00')
            info.practice_locations = self._extract_table_data(soup, 'ctl01_TemplateBody_WebPartManager1_gwpciPracticeLocationsIQA_ciPracticeLocationsIQA_ResultsGrid_Grid1_ctl00')
            info.professional_corporation = self._extract_table_data(soup, 'ctl01_TemplateBody_WebPartManager1_gwpciProfessionalCorporationIQA_ciProfessionalCorporationIQA_ResultsGrid_Grid1_ctl00')
            
            return info
        except Exception as e:
            logger.error(f"Error parsing registrant info: {str(e)}")
            return RegistrantInfo(name=f"Error: {str(e)}", userid=userid, url=url)

    @staticmethod
    def _extract_table_data(soup: BeautifulSoup, table_id: str) -> List[Dict[str, str]]:
        try:
            table = soup.find('table', {'id': table_id})
            if not table:
                return []
            
            headers = [header.text.strip() for header in table.find_all('th')]
            rows = []
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if cells:
                    row_data = {headers[i] if headers else f'Column {i+1}': cell.text.strip() 
                                for i, cell in enumerate(cells)}
                    rows.append(row_data)
            return rows
        except Exception as e:
            logger.error(f"Error extracting table data: {str(e)}")
            return []

    async def close(self):
        try:
            self.driver.quit()
        except Exception as e:
            logger.error(f"Error closing WebDriver: {str(e)}")