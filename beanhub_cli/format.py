import logging
import pathlib
import shutil
import sys
import tempfile
import typing

import click
from beancount_black.formatter import Formatter
from beancount_parser.parser import make_parser

from beanhub_cli.cli import LOG_LEVEL_MAP


def create_backup(src: pathlib.Path, suffix: str) -> pathlib.Path:
    """Create a backup file

    :param src: path of source file to create backup
    :param suffix: suffix of backup file
    :return: the path of backup file
    """
    conflicts = 0
    while True:
        backup_path: pathlib.Path = src.with_name(src.name + suffix)
        if conflicts > 0:
            backup_path = backup_path.with_name(f"{backup_path.name}.{conflicts}")
        if backup_path.exists():
            conflicts += 1
            continue
        shutil.copy2(src, backup_path)
        return backup_path


@click.command()
@click.argument("filename", type=click.Path(exists=False, dir_okay=False), nargs=-1)
@click.option(
    "--backup-suffix", type=str, default=".backup", help="suffix of backup file"
)
@click.option(
    "-s",
    "--stdin-mode",
    is_flag=True,
    help="Read beancount file data from stdin and output result to stdout",
)
@click.option(
    "-i",
    "--follow-include",
    is_flag=True,
    help="Follow include statements and also format the included bean files",
)
@click.option("-b", "--backup", is_flag=True, help="Create backup file")
def main(
    filename: typing.List[click.Path],
    backup_suffix: str,
    log_level: str,
    follow_include: bool,
    stdin_mode: bool,
    backup: bool,
):
    logging.basicConfig(level=LOG_LEVEL_MAP[log_level])
    logger = logging.getLogger(__name__)
    parser = make_parser()
    formatter = Formatter()
    if stdin_mode:
        logger.info("Processing in stdin mode")
        input_content = sys.stdin.read()
        tree = parser.parse(input_content)
        formatter.format(tree, sys.stdout)
    else:
        if not filename:
            # TODO: look up all beancount files, or just main?
            pass
        for name in filename:
            logger.info("Processing file %s", name)
            with open(name, "rt") as input_file:
                input_content = input_file.read()
                tree = parser.parse(input_content)
            with tempfile.NamedTemporaryFile(mode="wt+", suffix=".bean") as output_file:
                formatter.format(tree, output_file)
                output_file.seek(0)
                output_content = output_file.read()
                if input_content == output_content:
                    logger.info("File %s is not changed, skip", name)
                    continue
                if backup:
                    backup_path = create_backup(
                        src=pathlib.Path(str(name)), suffix=backup_suffix
                    )
                    logger.info("File %s changed, backup to %s", name, backup_path)
                output_file.seek(0)
                with open(name, "wt") as input_file:
                    shutil.copyfileobj(output_file, input_file)
    logger.info("done")


if __name__ == "__main__":
    main()
