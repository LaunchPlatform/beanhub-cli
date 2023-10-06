import pathlib

import yaml
from beanhub_forms.data_types.form import FormDoc


def format_loc(loc: tuple[str, ...]) -> str:
    parts: list[str] = []
    for item in loc:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            if parts:
                parts.append(".")
            parts.append(item)
    return "".join(parts)


def errors_to_tree():
    pass


def validate_doc(form_doc_path: pathlib.Path) -> FormDoc:
    if not form_doc_path.exists():
        raise ValueError(f"Form document at {form_doc_path} does not exist")
    with form_doc_path.open("rt") as fo:
        payload = yaml.safe_load(fo)
        return FormDoc.model_validate(payload)
