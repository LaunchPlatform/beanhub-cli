import dataclasses
import os
import pathlib
import random
import typing

import pytest
import yaml
from beanhub_import.data_types import ActionAddTxn
from beanhub_import.data_types import AmountTemplate
from beanhub_import.data_types import ImportDoc
from beanhub_import.data_types import ImportRule
from beanhub_import.data_types import InputConfig
from beanhub_import.data_types import InputConfigDetails
from beanhub_import.data_types import PostingTemplate
from beanhub_import.data_types import SimpleTxnMatchRule
from beanhub_import.data_types import StrExactMatch
from beanhub_import.data_types import StrRegexMatch
from beanhub_import.data_types import TransactionTemplate

MERCURY_CSV_HEADER = (
    "Date (UTC),Description,Amount,Status,Source Account,Bank Description,"
    "Reference,Note,Last Four Digits,Name On Card,Category,GL Code,"
    "Timestamp,Original Currency"
)
CHASE_CSV_HEADER = "Transaction Date,Post Date,Description,Category,Type,Amount,Memo"
CITI_CSV_HEADER = "Status,Date,Description,Debit,Credit,Member Name"

BENCHMARK_NUM_TXNS = int(os.environ.get("BENCHMARK_NUM_TXNS", "50000"))
BENCHMARK_RANDOM_SEED = int(os.environ.get("BENCHMARK_RANDOM_SEED", "42"))

BENCHMARK_FILE_NAME_TEMPLATES = (
    "2024-{month:02d}.csv",
    "2025-{month:02d}.csv",
    "export-{year}{month:02d}{day:02d}.csv",
    "transactions-{month:02d}.csv",
    "manual-{idx:02d}.csv",
    "CREDIT_{year}{month:02d}.csv",
    "checking-{month:02d}.csv",
)


@dataclasses.dataclass(frozen=True)
class BenchmarkBankSpec:
    dirname: str
    extractor: str
    output_file: str
    asset_account: str
    share: float


@dataclasses.dataclass(frozen=True)
class BenchmarkCsvFile:
    relative_path: pathlib.Path
    num_rows: int
    row_offset: int


BENCHMARK_BANKS: tuple[BenchmarkBankSpec, ...] = (
    BenchmarkBankSpec(
        dirname="mercury",
        extractor="mercury",
        output_file="mercury-output.bean",
        asset_account="Assets:Bank:US:Mercury",
        share=0.4,
    ),
    BenchmarkBankSpec(
        dirname="chase",
        extractor="chase_credit_card",
        output_file="chase-output.bean",
        asset_account="Assets:Bank:US:Chase",
        share=0.3,
    ),
    BenchmarkBankSpec(
        dirname="citi",
        extractor="citi_credit_card",
        output_file="citi-output.bean",
        asset_account="Assets:Bank:US:Citi",
        share=0.3,
    ),
)


def split_txn_counts(total: int, shares: tuple[float, ...]) -> tuple[int, ...]:
    counts = [int(total * share) for share in shares]
    counts[-1] = total - sum(counts[:-1])
    return tuple(counts)


def split_into_varied_file_sizes(
    total: int, num_files: int, rng: random.Random
) -> list[int]:
    num_files = max(1, min(num_files, total))
    if num_files == 1:
        return [total]

    weights: list[float] = []
    for _ in range(num_files):
        roll = rng.random()
        if roll < 0.2:
            weights.append(rng.uniform(0.001, 0.02))
        elif roll < 0.5:
            weights.append(rng.uniform(0.02, 0.08))
        else:
            weights.append(rng.uniform(0.08, 0.5))

    total_weight = sum(weights)
    sizes = [max(1, int(total * weight / total_weight)) for weight in weights]

    diff = total - sum(sizes)
    idx = 0
    while diff != 0:
        target = idx % num_files
        if diff > 0:
            sizes[target] += 1
            diff -= 1
        elif sizes[target] > 1:
            sizes[target] -= 1
            diff += 1
        idx += 1

    rng.shuffle(sizes)
    return sizes


def make_unique_csv_filename(rng: random.Random, used_names: set[str], idx: int) -> str:
    for _ in range(100):
        month = rng.randint(1, 12)
        year = rng.choice([2023, 2024, 2025])
        day = rng.randint(1, 28)
        template = rng.choice(BENCHMARK_FILE_NAME_TEMPLATES)
        name = template.format(month=month, year=year, day=day, idx=idx)
        if name not in used_names:
            used_names.add(name)
            return name
    fallback = f"import-{idx}.csv"
    used_names.add(fallback)
    return fallback


def plan_bank_csv_files(
    bank: BenchmarkBankSpec, total_rows: int, rng: random.Random
) -> list[BenchmarkCsvFile]:
    if total_rows == 0:
        return []

    min_files = min(4, total_rows)
    max_files = min(24, max(min_files, total_rows // 25 + 3))
    num_files = rng.randint(min_files, max(min_files, max_files))
    sizes = split_into_varied_file_sizes(total_rows, num_files, rng)

    used_names: set[str] = set()
    files: list[BenchmarkCsvFile] = []
    row_offset = 0
    for idx, size in enumerate(sizes):
        filename = make_unique_csv_filename(rng, used_names, idx)
        if rng.random() < 0.35:
            year = rng.choice([2023, 2024, 2025])
            month = rng.randint(1, 12)
            relative_path = (
                pathlib.Path(bank.dirname) / str(year) / f"{month:02d}" / filename
            )
        else:
            relative_path = pathlib.Path(bank.dirname) / filename
        files.append(
            BenchmarkCsvFile(
                relative_path=relative_path,
                num_rows=size,
                row_offset=row_offset,
            )
        )
        row_offset += size
    return files


def write_mercury_csv(
    csv_path: pathlib.Path, num_rows: int, row_offset: int = 0
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("wt", encoding="utf-8") as fo:
        fo.write(MERCURY_CSV_HEADER)
        fo.write("\n")
        for i in range(num_rows):
            idx = row_offset + i
            amount = -(idx % 1000) - (idx % 100) / 100
            fo.write(
                "04-17-2024,"
                f"Vendor {idx},"
                f"{amount:.2f},"
                "Sent,"
                "Mercury Checking xx1234,"
                f"Bank desc {idx},"
                ",,,,,,"
                "04-17-2024 21:30:40,"
                "\n"
            )


def write_chase_csv(csv_path: pathlib.Path, num_rows: int, row_offset: int = 0) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("wt", encoding="utf-8") as fo:
        fo.write(CHASE_CSV_HEADER)
        fo.write("\n")
        for i in range(num_rows):
            idx = row_offset + i
            amount = -(idx % 1000) - (idx % 100) / 100
            fo.write(
                f"04/03/2024,04/05/2024,Vendor {idx},Shopping,Sale,{amount:.2f},\n"
            )


def write_citi_csv(csv_path: pathlib.Path, num_rows: int, row_offset: int = 0) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("wt", encoding="utf-8") as fo:
        fo.write(CITI_CSV_HEADER)
        fo.write("\n")
        for i in range(num_rows):
            idx = row_offset + i
            amount = (idx % 1000) + (idx % 100) / 100
            fo.write(
                f"Cleared,04/17/2024,Vendor {idx},{amount:.2f},,Member {idx % 5},\n"
            )


BANK_CSV_WRITERS: dict[str, typing.Callable[[pathlib.Path, int, int], None]] = {
    "mercury": write_mercury_csv,
    "chase": write_chase_csv,
    "citi": write_citi_csv,
}


def write_benchmark_bank_csvs(
    workdir: pathlib.Path, txn_counts: dict[str, int]
) -> list[BenchmarkCsvFile]:
    planned_files: list[BenchmarkCsvFile] = []
    for bank in BENCHMARK_BANKS:
        rng = random.Random(f"{BENCHMARK_RANDOM_SEED}:{bank.dirname}")
        bank_files = plan_bank_csv_files(bank, txn_counts[bank.dirname], rng)
        writer = BANK_CSV_WRITERS[bank.dirname]
        for csv_file in bank_files:
            writer(
                workdir / csv_file.relative_path,
                csv_file.num_rows,
                csv_file.row_offset,
            )
        planned_files.extend(bank_files)
    return planned_files


@dataclasses.dataclass(frozen=True)
class BenchmarkDataset:
    workdir: pathlib.Path
    csv_files: list[BenchmarkCsvFile]


def make_large_import_doc() -> ImportDoc:
    return ImportDoc(
        inputs=[
            InputConfig(
                match=StrRegexMatch(regex=rf".*{bank.dirname}/.*\.csv$"),
                config=InputConfigDetails(
                    extractor=bank.extractor,
                    default_file=bank.output_file,
                ),
            )
            for bank in BENCHMARK_BANKS
        ],
        imports=[
            ImportRule(
                match=SimpleTxnMatchRule(
                    extractor=StrExactMatch(equals=bank.extractor),
                ),
                actions=[
                    ActionAddTxn(
                        file=bank.output_file,
                        txn=TransactionTemplate(
                            narration="{{ desc }}",
                            postings=[
                                PostingTemplate(
                                    account=bank.asset_account,
                                    amount=AmountTemplate(
                                        number="{{ amount }}",
                                        currency="{{ currency | default('USD', true) }}",
                                    ),
                                ),
                                PostingTemplate(
                                    account="Expenses:Misc",
                                    amount=AmountTemplate(
                                        number="{{ -amount }}",
                                        currency="{{ currency | default('USD', true) }}",
                                    ),
                                ),
                            ],
                        ),
                    )
                ],
            )
            for bank in BENCHMARK_BANKS
        ],
    )


def write_benchmark_import_project(
    workdir: pathlib.Path, import_doc: ImportDoc
) -> None:
    beanhub_dir = workdir / ".beanhub"
    beanhub_dir.mkdir(exist_ok=True)
    imports_yaml = beanhub_dir / "imports.yaml"
    imports_yaml.write_text(
        yaml.safe_dump(
            import_doc.model_dump(mode="json", exclude_none=True),
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    main_bean = workdir / "main.bean"
    main_bean.write_text("", encoding="utf-8")


@pytest.fixture(scope="session")
def benchmark_num_txns() -> int:
    return BENCHMARK_NUM_TXNS


@pytest.fixture(scope="session")
def benchmark_txn_counts(benchmark_num_txns: int) -> dict[str, int]:
    counts = split_txn_counts(
        benchmark_num_txns, tuple(bank.share for bank in BENCHMARK_BANKS)
    )
    return {bank.dirname: count for bank, count in zip(BENCHMARK_BANKS, counts)}


@pytest.fixture(scope="session")
def benchmark_dataset(
    tmp_path_factory, benchmark_txn_counts: dict[str, int]
) -> BenchmarkDataset:
    workdir = tmp_path_factory.mktemp("benchmark_import")
    csv_files = write_benchmark_bank_csvs(workdir, benchmark_txn_counts)
    return BenchmarkDataset(workdir=workdir, csv_files=csv_files)


@pytest.fixture(scope="session")
def benchmark_csv_files(benchmark_dataset: BenchmarkDataset) -> list[BenchmarkCsvFile]:
    return benchmark_dataset.csv_files


@pytest.fixture(scope="session")
def large_import_dir(benchmark_dataset: BenchmarkDataset) -> pathlib.Path:
    return benchmark_dataset.workdir


@pytest.fixture(scope="session")
def large_import_doc() -> ImportDoc:
    return make_large_import_doc()


@pytest.fixture(scope="session")
def benchmark_import_project(
    benchmark_dataset: BenchmarkDataset,
    large_import_doc: ImportDoc,
) -> pathlib.Path:
    write_benchmark_import_project(benchmark_dataset.workdir, large_import_doc)
    return benchmark_dataset.workdir
