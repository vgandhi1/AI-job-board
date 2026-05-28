"""Playwright-backed scrapers for LinkedIn, Indeed, and Wellfound.

Ported from the legacy `job-board/job_scraper/app/scraper.py`. The contract is
unchanged: each scraper returns a list of `ScrapedJob` (which the ingestion
service then upserts into the unified `jobs` table).

Notes:
  - Site selectors can drift; failures are logged and skipped rather than
    raised so a partial scrape still returns useful data.
  - Be mindful of each site's Terms of Service and robots.txt.
"""
from __future__ import annotations

import logging
from typing import List, Optional
from urllib.parse import urljoin

from playwright.async_api import async_playwright

from app.schemas import ScrapedJob

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class JobScraper:
    """Base class. Subclasses override `scrape`."""

    source: str = "unknown"

    async def scrape(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        max_results: int = 10,
    ) -> List[ScrapedJob]:
        raise NotImplementedError

    @staticmethod
    def _extract_city(location_text: Optional[str]) -> Optional[str]:
        if not location_text:
            return None
        parts = location_text.split(",")
        return parts[0].strip() if parts else None


# ---------------------------------------------------------------------------
# LinkedIn
# ---------------------------------------------------------------------------


class LinkedInScraper(JobScraper):
    source = "linkedin"

    async def scrape(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        max_results: int = 10,
    ) -> List[ScrapedJob]:
        jobs: List[ScrapedJob] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            base_url = "https://www.linkedin.com/jobs/search"
            params = []
            if query:
                params.append(f"keywords={query.replace(' ', '%20')}")
            if location:
                params.append(f"location={location.replace(' ', '%20')}")
            url = f"{base_url}?{'&'.join(params)}" if params else base_url

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_selector(".jobs-search__results-list", timeout=10000)

                for _ in range(max_results // 25 + 1):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)

                job_cards = await page.query_selector_all(".jobs-search__results-list > li")

                for card in job_cards[:max_results]:
                    try:
                        title_elem = await card.query_selector("h3.base-search-card__title")
                        title = (await title_elem.inner_text()).strip() if title_elem else "N/A"

                        company_elem = await card.query_selector("h4.base-search-card__subtitle")
                        company = (await company_elem.inner_text()).strip() if company_elem else "N/A"

                        location_elem = await card.query_selector(".job-search-card__location")
                        location_text = await location_elem.inner_text() if location_elem else ""
                        city = self._extract_city(location_text)

                        link_elem = await card.query_selector("a.base-card__full-link")
                        job_url = await link_elem.get_attribute("href") if link_elem else None

                        if job_url and title != "N/A" and company != "N/A":
                            jobs.append(
                                ScrapedJob(
                                    title=title,
                                    company=company,
                                    city=city,
                                    url=job_url,
                                    description=None,
                                    source=self.source,
                                )
                            )
                    except Exception as e:
                        # Do not log raw page HTML or full exception bodies that could
                        # contain user PII; log only a short class+message.
                        logger.warning(
                            "Skipped LinkedIn card: %s", type(e).__name__
                        )
                        continue
            except Exception as e:
                logger.error("LinkedIn scrape failed: %s", type(e).__name__)
            finally:
                await browser.close()

        return jobs


# ---------------------------------------------------------------------------
# Indeed
# ---------------------------------------------------------------------------


class IndeedScraper(JobScraper):
    source = "indeed"

    async def scrape(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        max_results: int = 10,
    ) -> List[ScrapedJob]:
        jobs: List[ScrapedJob] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            base_url = "https://www.indeed.com/jobs"
            params = []
            if query:
                params.append(f"q={query.replace(' ', '+')}")
            if location:
                params.append(f"l={location.replace(' ', '+')}")
            url = f"{base_url}?{'&'.join(params)}" if params else base_url

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_selector("#mosaic-provider-jobcards", timeout=10000)

                for _ in range(max_results // 15 + 1):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)

                job_cards = await page.query_selector_all("div[data-jk]")

                for card in job_cards[:max_results]:
                    try:
                        title_elem = await card.query_selector("h2.jobTitle > a")
                        title = (await title_elem.inner_text()).strip() if title_elem else "N/A"

                        company_elem = await card.query_selector("span.companyName")
                        company = (await company_elem.inner_text()).strip() if company_elem else "N/A"

                        location_elem = await card.query_selector("div.companyLocation")
                        location_text = await location_elem.inner_text() if location_elem else ""
                        city = self._extract_city(location_text)

                        link_elem = await card.query_selector("h2.jobTitle > a")
                        relative_url = await link_elem.get_attribute("href") if link_elem else None
                        job_url = urljoin("https://www.indeed.com", relative_url) if relative_url else None

                        if job_url and title != "N/A" and company != "N/A":
                            jobs.append(
                                ScrapedJob(
                                    title=title,
                                    company=company,
                                    city=city,
                                    url=job_url,
                                    description=None,
                                    source=self.source,
                                )
                            )
                    except Exception as e:
                        logger.warning("Skipped Indeed card: %s", type(e).__name__)
                        continue
            except Exception as e:
                logger.error("Indeed scrape failed: %s", type(e).__name__)
            finally:
                await browser.close()

        return jobs


# ---------------------------------------------------------------------------
# Wellfound (formerly AngelList)
# ---------------------------------------------------------------------------


class WellfoundScraper(JobScraper):
    source = "wellfound"

    async def scrape(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        max_results: int = 10,
    ) -> List[ScrapedJob]:
        jobs: List[ScrapedJob] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            base_url = "https://wellfound.com/role/l/jobs"
            params = []
            if query:
                params.append(f"keywords={query.replace(' ', '%20')}")
            if location:
                params.append(f"location={location.replace(' ', '%20')}")
            url = f"{base_url}?{'&'.join(params)}" if params else base_url

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_selector("[data-test='JobCard']", timeout=10000)

                for _ in range(max_results // 20 + 1):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)

                job_cards = await page.query_selector_all("[data-test='JobCard']")

                for card in job_cards[:max_results]:
                    try:
                        title_elem = await card.query_selector("h3")
                        title = (await title_elem.inner_text()).strip() if title_elem else "N/A"

                        company_elem = await card.query_selector("[data-test='CompanyName']")
                        company = (await company_elem.inner_text()).strip() if company_elem else "N/A"

                        location_elem = await card.query_selector("[data-test='JobLocation']")
                        location_text = await location_elem.inner_text() if location_elem else ""
                        city = self._extract_city(location_text)

                        link_elem = await card.query_selector("a")
                        relative_url = await link_elem.get_attribute("href") if link_elem else None
                        job_url = urljoin("https://wellfound.com", relative_url) if relative_url else None

                        if job_url and title != "N/A" and company != "N/A":
                            jobs.append(
                                ScrapedJob(
                                    title=title,
                                    company=company,
                                    city=city,
                                    url=job_url,
                                    description=None,
                                    source=self.source,
                                )
                            )
                    except Exception as e:
                        logger.warning("Skipped Wellfound card: %s", type(e).__name__)
                        continue
            except Exception as e:
                logger.error("Wellfound scrape failed: %s", type(e).__name__)
            finally:
                await browser.close()

        return jobs


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_SCRAPERS = {
    "linkedin": LinkedInScraper,
    "indeed": IndeedScraper,
    "wellfound": WellfoundScraper,
}


def get_scraper(source: str) -> JobScraper:
    """Return an instance of the scraper for `source`.

    Raises ValueError for unknown sources. Source string is normalized to
    lowercase so callers can pass any case.
    """
    key = (source or "").strip().lower()
    cls = _SCRAPERS.get(key)
    if cls is None:
        raise ValueError(
            f"Unsupported source: {source!r}. "
            f"Supported sources: {', '.join(sorted(_SCRAPERS))}"
        )
    return cls()
