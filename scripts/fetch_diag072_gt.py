from __future__ import annotations

from pathlib import Path
import time

from kaggle.api.kaggle_api_extended import KaggleApi


COMPETITION = "biohub-cell-tracking-during-development"
STEMS = (
    "44b6_12dfb391",
    "44b6_267148e4",
    "44b6_2a2eff9f",
    "44b6_341df25f",
    "6bba_062c8d37",
    "6bba_07e24132",
    "6bba_085bf656",
    "6bba_09961292",
)
DEST = Path("experiments/diag_072_fork_protected_ep015_stage0/ground_truth")


def main() -> None:
    api = KaggleApi()
    api.authenticate()
    prefixes = tuple(f"train/{stem}.geff/" for stem in STEMS)
    wanted: list[str] = []
    token: str | None = None
    while True:
        for attempt in range(8):
            try:
                response = api.competition_list_files(COMPETITION, token, 200)
                break
            except Exception as exc:
                if "429" not in str(exc) or attempt == 7:
                    raise
                delay = min(60, 5 * (2**attempt))
                print(f"Kaggle rate limit while listing; retrying in {delay}s")
                time.sleep(delay)
        for item in response.files or []:
            name = str(item.name)
            if name.startswith(prefixes):
                wanted.append(name)
        token = response.next_page_token
        if not token:
            break
        time.sleep(1.0)

    found_stems = {name.split("/", 2)[1][:-5] for name in wanted}
    missing = sorted(set(STEMS) - found_stems)
    if missing:
        raise RuntimeError(f"Missing ground-truth GEFF files for: {missing}")

    for index, name in enumerate(sorted(wanted), start=1):
        target = DEST / name
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(8):
            try:
                api.competition_download_file(
                    COMPETITION,
                    name,
                    path=str(target.parent),
                    force=False,
                    quiet=True,
                )
                break
            except Exception as exc:
                if "429" not in str(exc) or attempt == 7:
                    raise
                delay = min(60, 5 * (2**attempt))
                print(f"Kaggle rate limit while downloading; retrying in {delay}s")
                time.sleep(delay)
        downloaded = target.parent / Path(name).name
        if downloaded != target and downloaded.exists():
            downloaded.replace(target)
        print(f"[{index}/{len(wanted)}] {name}")
        time.sleep(0.25)

    print(f"Recovered {len(wanted)} files for {len(found_stems)} held-out GT graphs under {DEST}")


if __name__ == "__main__":
    main()
