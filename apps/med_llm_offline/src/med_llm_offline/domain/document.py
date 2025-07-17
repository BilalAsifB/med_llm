import json
from pathlib import Path

from pydantic import BaseModel, Field  

from src.med_llm_offline import utils


class DocumentMetadata(BaseModel):
    id: str
    url: str
    name: str
    properties: dict

    def obfuscate(self) -> "DocumentMetadata":
        """
        Create am obfuscated version of the metadata.

        Returns:
            DocumentMetadata: Self, with ID and URL obfuscated.
        """

        og_id = self.id.replace(":", "_")
        fake_id = utils.generate_random_hex(len(og_id))

        self.id = fake_id
        self.url = self.url.replace(og_id, fake_id)

        return self


class Document(BaseModel):
    id: str = Field(default_factory=lambda: utils.generate_random_hex(length=32))
    metadata: DocumentMetadata

    @classmethod
    def from_file(cls, file_path: Path) -> "Document":
        """
        Load a Document from a JSON file.

        Args:
            file_path (Path): Path to the JSON file.

        Returns:
            Document: The loaded document.
        """
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def write(
        self,
        output_dir: Path, 
        obfuscate: bool = False,
        also_save_as_txt: bool = False
    ) -> None:
        """
        Write the document to a JSON file.

        Args:
            output_dir (Path): Directory to save the document.
            obfuscate (bool): Whether to obfuscate the metadata.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        if obfuscate:
            self.metadata = self.metadata.obfuscate()

        json_data = self.model_dump_json()

        output_file = output_dir / f"{self.id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                json_data,
                f,
                indent=4,
                ensure_ascii=False,
            )

        if also_save_as_txt:
            txt_path = output_file.with_suffix(".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(self.metadata.name + "\n")

    def obfuscate(self) -> "Document":
        """
        Create an obfuscated version of the document.

        Returns:
            Document: Self, with ID and URL obfuscated.
        """
        self.metadata = self.metadata.obfuscate()
        self.parent_metadata = (
            self.parent_metadata.obfuscate() if self.parent_metadata else None
        )
        self.id = self.metadata.id

        return self

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Document):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)