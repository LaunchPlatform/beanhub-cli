import io
import logging
import pathlib
import sys
import tarfile


def extract_tar(input_file: io.BytesIO, logger: logging.Logger):
    with tarfile.open(fileobj=input_file, mode="r:gz") as tar_file:
        if hasattr(tarfile, "data_filter"):
            tar_file.extractall(filter="data")
        else:
            logger.warning("Performing unsafe tar file extracting")
            tar_file.extractall()


def extract_inbox_tar(
    input_file: io.BytesIO,
    email_output_paths: dict[str, pathlib.Path],
    workdir_path: pathlib.Path,
    unsafe_tar_extract: bool,
    logger: logging.Logger,
):
    with tarfile.open(fileobj=input_file, mode="r:gz") as tar_file:
        for member in tar_file:
            if not member.isreg():
                continue
            member_path = pathlib.PurePosixPath(member.name)
            email_id = member_path.stem
            output_path = email_output_paths.get(email_id)
            if output_path is None:
                logger.error("Cannot find output path for email %s", email_id)
                sys.exit(-1)
            output_path.parent.mkdir(exist_ok=True, parents=True)
            logger.info(
                "Writing email [green]%s[/] to [green]%s[/]",
                email_id,
                output_path,
                extra={"markup": True, "highlighter": None},
            )
            full_output_path = workdir_path / output_path
            has_data_filter = hasattr(tarfile, "data_filter")
            if not has_data_filter and not unsafe_tar_extract:
                logger.error(
                    "You need to use Python >= 3.11 in order to safely unpack the downloaded tar file, or you need to pass "
                    "in --unsafe-tar-extract argument to allow unsafe tar file extracting"
                )
                sys.exit(-1)
            member.name = output_path.name
            tar_file.extract(
                member,
                full_output_path.parent,
                set_attrs=False,
                filter="data" if has_data_filter else None,
            )
