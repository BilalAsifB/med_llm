from pathlib import Path

from loguru import logger
from zenml import pipeline

from steps.etl import crawl
from steps.infrastructure import (
    ingest_to_mongodb,
    save_documents_to_disk,
)

@pipeline
def etl(
    data_dir: Path,
    load_collection_name: str,
    max_workers: int = 10,
    base_url: str = "https://www.dvago.pk",
) -> None:
    crawled_data_dir = data_dir / "dvago"
    crawled_data = crawl(max_workers=max_workers, base_url=base_url)

    logger.info(f"Saving crawled data to {crawled_data_dir}")
    save_documents_to_disk(documents=crawled_data, output_dir=crawled_data_dir)

    logger.info(
        f"Saving crawled data to MongoDB collection '{load_collection_name}'"
    ) 
    ingest_to_mongodb(
        models=crawled_data,
        collection_name=load_collection_name,
        clear_collection=True,
    )   