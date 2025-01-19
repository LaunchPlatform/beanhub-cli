import io
import logging
import tarfile


def extract_tar(input_file: io.BytesIO, logger: logging.Logger):
    with tarfile.open(fileobj=input_file, mode="r:gz") as tar_file:
        if hasattr(tarfile, "data_filter"):
            tar_file.extractall(filter="data")
        else:
            logger.warning("Performing unsafe tar file extracting")
            tar_file.extractall()
