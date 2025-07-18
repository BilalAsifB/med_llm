# apps/med_llm_offline/run_etl.py

import yaml
from pathlib import Path
from pydantic import BaseModel

from pipelines.etl import etl

CONFIG_PATH = Path(__file__).parent / "configs" / "etl.yaml"


class ETLConfig(BaseModel):
    data_dir: Path
    load_collection_name: str
    max_workers: int 
    base_url: str 


def load_config(path: Path) -> ETLConfig:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return ETLConfig(**data["parameters"])


if __name__ == "__main__":
    config = load_config(CONFIG_PATH)

    etl(
        load_collection_name=config.load_collection_name,
        max_workers=config.max_workers,
        base_url=config.base_url,
    )
