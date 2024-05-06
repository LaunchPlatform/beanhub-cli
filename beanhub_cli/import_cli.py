import pathlib

import click
import yaml
from beancount_black.formatter import Formatter
from beancount_parser.parser import make_parser
from beanhub_import.data_types import ImportDoc
from beanhub_import.post_processor import apply_change_set
from beanhub_import.post_processor import compute_changes
from beanhub_import.post_processor import extract_imported_transactions
from beanhub_import.post_processor import txn_to_text
from beanhub_import.processor import process_imports

from .cli import cli
from .environment import Environment
from .environment import pass_env

IMPORT_DOC_FILE = pathlib.Path(".beanhub") / "imports.yaml"


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
@pass_env
def main(env: Environment, config: str, workdir: str, beanfile: str):
    config_path = pathlib.Path(config)
    with config_path.open("rt") as fo:
        doc_payload = yaml.safe_load(fo)
    import_doc = ImportDoc.model_validate(doc_payload)
    workdir_path = pathlib.Path(workdir)
    env.logger.info("Loaded import doc from %s", config)

    generated_txns = []
    for generated_txn in process_imports(import_doc=import_doc, input_dir=workdir_path):
        env.logger.debug("Generated transaction %s", generated_txn)
        generated_txns.append(generated_txn)
    env.logger.info("Generated %s transactions", len(generated_txns))

    beanfile_path = pathlib.Path(beanfile)

    parser = make_parser()
    imported_txns = list(
        extract_imported_transactions(
            parser=parser,
            bean_file=beanfile_path,
        )
    )
    env.logger.info("Found %s existing imported transactions", len(imported_txns))

    formatter = Formatter()
    change_sets = compute_changes(
        generated_txns=generated_txns,
        imported_txns=imported_txns,
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
                "Applying change sets (add=%s, update=%s, remove=%s) to %s",
                len(change_set.add),
                len(change_set.update),
                len(change_set.remove),
                target_file,
            )
            tree = parser.parse(target_file.read_text())
            new_tree = apply_change_set(tree=tree, change_set=change_set)

        with target_file.open("wt") as fo:
            formatter.format(new_tree, fo)
    env.logger.info("done")
