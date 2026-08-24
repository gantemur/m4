"""Retrieve a small, documented NSO GDP-by-industry extract."""

from pathlib import Path

from m4.data import NsoClient


TABLE = "Economy%2C%20environment/National%20Accounts/DT_NSO_0500_004V1.px"


def main() -> None:
    client = NsoClient()
    metadata = client.metadata(TABLE)
    time_codes = metadata["variables"][2]["values"][:8]
    records = client.observations(
        TABLE,
        {
            "Статистик үзүүлэлт": ["0"],
            "Салбар": ["0", "1", "2", "5"],
            "Он": time_codes,
        },
        raw_directory=Path("data/raw/nso"),
    )
    print(f"Retrieved {len(records)} GDP observations from {metadata['title']!r}.")
    for row in records[:4]:
        print(row)


if __name__ == "__main__":
    main()
