from pipeline.ingest import nws, broward, miamidade, fldem
from pipeline.clean import clean_text
from pipeline.extract import extract_cards
from pipeline.dedup import dedup


def main() -> None:
    # Run ingestion steps sequentially.
    nws.ingest()
    broward.ingest()
    miamidade.ingest()
    fldem.ingest()

    # Cleaning step
    clean_text.ingest_clean()

    # Extraction step
    extract_cards.extract()

    # Deduplication step
    dedup.deduplicate()


if __name__ == "__main__":
    main()
