"""Print transparent descriptive statistics for NSO quarterly construction GDP."""

from collections import defaultdict
from statistics import mean, stdev

from m4.data import NsoClient


TABLE = "Economy%2C%20environment/National%20Accounts/DT_NSO_0500_004V1.px"


def main() -> None:
    client = NsoClient()
    metadata = client.metadata(TABLE)
    records = client.observations(
        TABLE,
        {
            "Статистик үзүүлэлт": ["0"],  # current-price GDP
            "Салбар": ["0", "1", "2", "5"],  # total, agriculture, mining, construction
            "Он": metadata["variables"][2]["values"],
        },
    )
    by_time: dict[str, dict[str, float]] = defaultdict(dict)
    for row in records:
        by_time[row["Он"]][row["Салбар"].strip()] = float(row["value"])
    shares = [100 * row["Construction"] / row["GDP"] for row in by_time.values() if row["GDP"]]
    print(f"quarters: {len(shares)}")
    print(f"construction share of current-price GDP: mean={mean(shares):.2f}%, min={min(shares):.2f}%, max={max(shares):.2f}%")
    if len(shares) > 1:
        print(f"share standard deviation: {stdev(shares):.2f} percentage points")
    print("No causal interpretation is made: this script does not join fiscal, credit, or mine-investment data.")


if __name__ == "__main__":
    main()
