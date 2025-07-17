from loguru import logger
from typing_extensions import Annotated
from zenml import step, get_step_context

from src.med_llm_offline.application.crawlers import Crawl4AIMedicineCrawler
from src.med_llm_offline.domain import Document

@step(enable_cache=False, name="crawl")
def crawl(
    max_workers: int,
    base_url: str,
) -> Annotated[list[Document], "crawled_documents"]:
    crawler = Crawl4AIMedicineCrawler(
        max_concurrent_requests=max_workers, 
        base_url=base_url
    )
    documents = crawler()
    documents = list(documents)

    logger.info(f"Crawled {len(documents)} documents.")

    step_context = get_step_context()
    step_context.add_output_metadata(
        output_name="crawled_documents",
        metadata={
            "count": len(documents),
            "base_url": base_url,
            "max_workers": max_workers
        },
    )

    return documents
