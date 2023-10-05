import pathlib

import yaml
from beanhub_forms.data_types.form import FormDoc
from pydantic import TypeAdapter


def validate_doc(form_doc_path: pathlib.Path):
    if not form_doc_path.exists():
        raise ValueError(f"Form document at {form_doc_path} does not exist")
    with form_doc_path.open("rt") as fo:
        payload = yaml.safe_load(fo)
        TypeAdapter(FormDoc).validate_python(payload)
