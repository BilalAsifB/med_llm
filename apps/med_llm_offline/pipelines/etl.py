from pathlib import Path

from loguru import logger
from zenml import pipeline

from steps.etl import crawl
from steps.infrastructure import (
    ingest_to_mongodb
)

@pipeline
def etl(
    load_collection_name: str,
    max_workers: int = 10,
    base_url: str = "https://www.dvago.pk",
) -> None:
    logger.info(
        f"Starting ETL pipeline with max_workers={max_workers} and base_url={base_url}"
    )
    logger.info("Starting web crawling...")
    crawled_data = crawl(max_workers=max_workers, base_url=base_url)

    logger.info(
        f"Saving crawled data to MongoDB collection '{load_collection_name}'"
    ) 
    ingest_to_mongodb(
        models=crawled_data,
        collection_name=load_collection_name,
        clear_collection=True,
    )   