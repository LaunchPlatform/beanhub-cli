import pathlib
import sys

import click
import rich
import yaml
from beancount_black.formatter import Formatter
from beancount_parser.parser import make_parser
from beanhub_extract.utils import strip_base_path
from beanhub_import.data_types import DeletedTransaction
from beanhub_import.data_types import GeneratedTransaction
from beanhub_import.data_types import ImportDoc
from beanhub_import.data_types import UnprocessedTransaction
from beanhub_import.post_processor import apply_change_set
from beanhub_import.post_processor import compute_changes
from beanhub_import.post_processor import extract_existing_transactions
from beanhub_import.post_processor import txn_to_text
from beanhub_import.processor import process_imports
from rich import box
from rich.markup import escape
from rich.padding import Padding
from rich.table import Table

from .cli import cli
from .environment import Environment
from .environment import pass_env

IMPORT_DOC_FILE = pathlib.Path(".beanhub") / "imports.yaml"
TABLE_HEADER_STYLE = "yellow"
TABLE_COLUMN_STYLE = "cyan"


@cli.command(
    name="import",
    help="Import data into Beancount files based on the beanhub-import config file",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    default=".beanhub/imports.yaml",
    help="The path to import config file",
)
@click.option(
    "-w",
    "--workdir",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    default=str(pathlib.Path.cwd()),
    help="The beanhub project path to work on",
)
@click.option(
    "-b",
    "--beanfile",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default="main.bean",
    help="The path to main entry beancount file",
)
@click.option(
    "--remove-dangling",
    is_flag=True,
    help="Remove dangling transactions (existing imported transactions in Beancount files without corresponding generated transactions)",
)
@pass_env
def main(
    env: Environment, config: str, workdir: str, beanfile: str, remove_dangling: bool
):
    config_path = pathlib.Path(config)
    with config_path.open("rt") as fo:
        doc_payload = yaml.safe_load(fo)
    import_doc = ImportDoc.model_validate(doc_payload)
    workdir_path = pathlib.Path(workdir)
    env.logger.info(
        "Loaded import doc from [green]%s[/]",
        config,
        extra={"markup": True, "highlighter": None},
    )

    generated_txns: list[GeneratedTransaction] = []
    deleted_txns: list[DeletedTransaction] = []
    unprocessed_txns: list[UnprocessedTransaction] = []
    for txn in process_imports(import_doc=import_doc, input_dir=workdir_path):
        if isinstance(txn, GeneratedTransaction):
            generated_file_path = (workdir_path / txn.file).resolve()
            env.logger.info(
                "Generated transaction [green]%s[/] to file [green]%s[/]",
                txn.id,
                strip_base_path(workdir_path.resolve(), generated_file_path),
                extra={"markup": True, "highlighter": None},
            )
            generated_txns.append(txn)
        elif isinstance(txn, DeletedTransaction):
            env.logger.info(
                "Deleted transaction [green]%s[/]",
                txn.id,
                extra={"markup": True, "highlighter": None},
            )
            deleted_txns.append(txn)
        elif isinstance(txn, UnprocessedTransaction):
            env.logger.info(
                "Skipped input transaction %s at [green]%s[/]:[blue]%s[/]",
                txn.import_id,
                txn.txn.file,
                txn.txn.lineno,
                extra={"markup": True, "highlighter": None},
            )
            unprocessed_txns.append(txn)
        else:
            raise ValueError(f"Unexpected type {type(txn)}")
    env.logger.info("Generated %s transactions", len(generated_txns))
    env.logger.info("Deleted %s transactions", len(deleted_txns))
    env.logger.info("Skipped %s transactions", len(unprocessed_txns))

    beanfile_path = (workdir_path / pathlib.Path(beanfile)).resolve()
    if workdir_path.resolve().absolute() not in beanfile_path.absolute().parents:
        env.logger.error(
            "The provided beanfile path %s is not a sub-path of workdir %s",
            beanfile_path,
            workdir_path,
        )
        sys.exit(-1)

    env.logger.info(
        "Collecting existing imported transactions from Beancount books ..."
    )
    parser = make_parser()
    existing_txns = list(
        extract_existing_transactions(
            parser=parser,
            bean_file=beanfile_path,
            root_dir=workdir_path,
        )
    )
    imported_txns_with_override = frozenset(
        txn.id for txn in existing_txns if txn.override is not None
    )
    env.logger.info(
        "Found %s existing imported transactions in Beancount books, %s with override",
        len(existing_txns),
        len(imported_txns_with_override),
    )

    change_sets = compute_changes(
        generated_txns=generated_txns,
        imported_txns=existing_txns,
        deleted_txns=deleted_txns,
        work_dir=workdir_path,
    )
    for target_file, change_set in change_sets.items():
        if not target_file.exists():
            if change_set.remove or change_set.update:
                raise ValueError("Expect new transactions to add only")
            env.logger.info(
                "Create new bean file %s with %s transactions",
                target_file,
                len(change_set.add),
            )

            bean_content = "\n\n".join(map(txn_to_text, change_set.add))
            new_tree = parser.parse(bean_content)
        else:
            env.logger.info(
                "Applying change sets (add=%s, update=%s, remove=%s, dangling=%s) with remove_dangling=%s to %s",
                len(change_set.add),
                len(change_set.update),
                len(change_set.remove),
                len(change_set.dangling),
                remove_dangling,
                target_file,
            )
            tree = parser.parse(target_file.read_text())
            new_tree = apply_change_set(
                tree=tree, change_set=change_set, remove_dangling=remove_dangling
            )

        with target_file.open("wt") as fo:
            formatter = Formatter()
            formatter.format(new_tree, fo)

    table = Table(
        title="Deleted transactions",
        box=box.SIMPLE,
        header_style=TABLE_HEADER_STYLE,
        expand=True,
    )
    table.add_column("File", style=TABLE_COLUMN_STYLE)
    table.add_column("Id", style=TABLE_COLUMN_STYLE)
    deleted_txn_ids = frozenset(txn.id for txn in deleted_txns)
    for target_file, change_set in change_sets.items():
        for txn in change_set.remove:
            if txn.id not in deleted_txn_ids:
                continue
            table.add_row(
                escape(str(target_file)) + f":{txn.lineno}",
                str(txn.id),
            )
    rich.print(Padding(table, (1, 0, 0, 4)))

    dangling_action = "Delete" if remove_dangling else "Ignored"
    table = Table(
        title=f"Dangling Transactions ({dangling_action})",
        box=box.SIMPLE,
        header_style=TABLE_HEADER_STYLE,
        expand=True,
    )
    table.add_column("File", style=TABLE_COLUMN_STYLE)
    table.add_column("Id", style=TABLE_COLUMN_STYLE)
    for target_file, change_set in change_sets.items():
        for txn in change_set.dangling:
            table.add_row(
                escape(str(target_file)) + f":{txn.lineno}",
                str(txn.id),
            )
    rich.print(Padding(table, (1, 0, 0, 4)))

    table = Table(
        title="Generated transactions",
        box=box.SIMPLE,
        header_style=TABLE_HEADER_STYLE,
        expand=True,
    )
    # TODO: add src info
    table.add_column("File", style=TABLE_COLUMN_STYLE)
    table.add_column("Id", style=TABLE_COLUMN_STYLE)
    table.add_column("Source", style=TABLE_COLUMN_STYLE)
    table.add_column("Date", style=TABLE_COLUMN_STYLE)
    table.add_column("Narration", style=TABLE_COLUMN_STYLE)
    for txn in generated_txns:
        table.add_row(
            escape(str(txn.file)),
            str(txn.id),
            escape(str(":".join(txn.sources))),
            escape(str(txn.date)),
            escape(txn.narration),
        )
    rich.print(Padding(table, (1, 0, 0, 4)))

    table = Table(
        title="Open transactions",
        box=box.SIMPLE,
        header_style=TABLE_HEADER_STYLE,
        expand=True,
    )
    table.add_column("File", style=TABLE_COLUMN_STYLE)
    table.add_column("Line", style=TABLE_COLUMN_STYLE)
    table.add_column("Id", style=TABLE_COLUMN_STYLE)
    table.add_column("Extractor", style=TABLE_COLUMN_STYLE)
    table.add_column("Date", style=TABLE_COLUMN_STYLE)
    table.add_column("Desc", style=TABLE_COLUMN_STYLE)
    table.add_column("Bank Desc", style=TABLE_COLUMN_STYLE)
    table.add_column("Amount", style=TABLE_COLUMN_STYLE, justify="right")
    table.add_column("Currency", style=TABLE_COLUMN_STYLE)
    for txn in unprocessed_txns:
        if txn.import_id in imported_txns_with_override:
            continue
        table.add_row(
            escape(txn.txn.file),
            str(txn.txn.lineno),
            txn.import_id,
            escape(str(txn.txn.extractor)),
            escape(str(txn.txn.date)) if txn.txn.date is not None else "",
            escape(txn.txn.desc) if txn.txn.desc is not None else "",
            escape(txn.txn.bank_desc) if txn.txn.bank_desc is not None else "",
            escape(str(txn.txn.amount)) if txn.txn.amount is not None else "",
            escape(txn.txn.currency) if txn.txn.currency is not None else "",
        )
    rich.print(Padding(table, (1, 0, 0, 4)))

    env.logger.info("done")
