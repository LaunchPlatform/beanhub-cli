import pathlib
import re

import pytest
from click.testing import CliRunner
from pytest_benchmark.fixture import BenchmarkFixture

from beanhub_cli.main import cli


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "benchmark_workers", [1, 4, 8], ids=["workers-1", "workers-4", "workers-8"]
)
def test_import_cli_large_csv(
    benchmark: BenchmarkFixture,
    benchmark_import_project: pathlib.Path,
    benchmark_num_txns: int,
    benchmark_workers: int,
    cli_runner: CliRunner,
) -> None:
    config_path = benchmark_import_project / ".beanhub" / "imports.yaml"
    generated_txn_pattern = re.compile(r"Generated (\d+) transactions")
    output_files = tuple(benchmark_import_project.glob("*-output.bean"))

    def run_import() -> int:
        for output_file in output_files:
            output_file.unlink(missing_ok=True)

        result = cli_runner.invoke(
            cli,
            [
                "import",
                "--config",
                str(config_path),
                "--workdir",
                str(benchmark_import_project),
                "--beanfile",
                "main.bean",
                "-j",
                str(benchmark_workers),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        match = generated_txn_pattern.search(result.output)
        assert match is not None, result.output
        generated_count = int(match.group(1))
        assert generated_count == benchmark_num_txns
        return generated_count

    benchmark.pedantic(run_import, rounds=1, iterations=1)
