import asyncio

import json

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CacheMode,
)

from playwright.async_api import async_playwright

from loguru import logger

from src.med_llm_offline import utils
from src.med_llm_offline.domain import Document, DocumentMetadata


class Crawl4AIMedicineCrawler:
    """
    A crawler for dvago.pk to scrape medicine product details.
    This crawler uses Crawl4AI for web crawling and Playwright for scraping product details.
    It is designed to handle multiple pages of product listings and extract relevant information
    such as specifications, usage, precautions, and warnings from each product page.
    """
    def __init__(
            self, 
            max_concurrent_requests: int,
            base_url: str
    ) -> None:
        """Initialize the crawler with the maximum number of concurrent requests and base URL."""
        self.max_concurrent_requests = max_concurrent_requests
        self.base_url = base_url

    def __call__(self) -> list[dict]:
        """Run the crawler and return the scraped data."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.__crawl())
        else:
            return loop.run_until_complete(self.__crawl())
        
    async def check_no_results(
        self, 
        crawler: AsyncWebCrawler, 
        url: str, 
        session_id: str) -> bool:
        """Check if the page has no results."""
        result = await crawler.arun(
            url=url,
            crawler=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                session_id=session_id,
            ),
        )

        if result.success:
            if "Page Not Found" in result.cleaned_html:
                logger.warning(f"No results found for {url}")
                return True
        else:
            logger.error(f"Failed to fetch {url}: {result.error_message}")
        
        return False

    def extract_product_links(self, soup: BeautifulSoup) -> list[str]:
        """Extract product links from the soup object."""
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(self.base_url, href)
            parsed_result = urlparse(full_url)

            if parsed_result.path.startswith("/p/") and "/cat/" not in parsed_result.path:
                clean_url = parsed_result.scheme + "://" + parsed_result.netloc + parsed_result.path
                links.append(clean_url)

        return list(set(links))

    async def scrape_with_playwright(self, url: str) -> dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, timeout=20000)
                await page.wait_for_selector('h2', timeout=10000)

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                def extract_section(title):
                    h2 = soup.find('h2', string=lambda t: t and title.lower() in t.lower())
                    if h2:
                        content = []
                        for sibling in h2.find_next_siblings():
                            if sibling.name == 'h2':
                                break
                            content.append(sibling.get_text(" ", strip=True))
                        return "\n".join(content).strip()
                    return ""

                name_tag = soup.find('h1')
                name = name_tag.get_text(strip=True) if name_tag else "Unknown"

                logger.info(f"Extracted data for {url}")

                doc_id = utils.generate_random_hex(length=32)
                return Document(
                    id=doc_id,
                    metadata=DocumentMetadata(
                        id=doc_id,
                        url=url,
                        name=name,
                        properties={
                            "specification": extract_section("Specification"),
                            "usage_and_safety": extract_section("Usage and Safety"),
                            "precautions": extract_section("Precautions"),
                            "warnings": extract_section("Warnings"),
                            "additional_information": extract_section("Additional Information"),
                        },
                    ),
                )
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                return {}
            finally:
                await browser.close()


    async def __crawl(self) -> list[dict]:
        browser_congig = utils.get_browser_config()
        session_id = "dvgao_crawler_session"
        page_number = 1
        all_medicines = []

        async with AsyncWebCrawler(config=browser_congig) as crawler:
            while True:
                url = f"{self.base_url}/cat/medicine?page={page_number}"
                logger.info(f"Fetching page {page_number} from {url}")

                no_results = await self.check_no_results(crawler, url, session_id)
                if no_results:
                    logger.info("No more results found, stopping the crawl.")
                    break

                res = await crawler.arun(url=url)
                soup = BeautifulSoup(res.html, "html.parser")
                links = self.extract_product_links(soup)
                if not links:
                    logger.info("No product links found, stopping the crawl.")
                    break
                
                logger.info(f"Found {len(links)} product links on page {page_number}")
                for link in links:
                    medicine = await self.scrape_with_playwright(link)
                    all_medicines.append(medicine)

                await asyncio.sleep(2)
                page_number += 1

        logger.info(f"Crawled {len(all_medicines)} medicines.")
        return all_medicines
    