import pathlib

import yaml
from beanhub_forms.data_types.form import FormDoc
from rich.markup import escape
from rich.tree import Tree

CHILDREN_KEY = "__children__"
TREE_NODE_STYLE = "yellow"
TREE_LEAF_ATTR_STYLE = "bold magenta"
TREE_LEAF_VALUE_STYLE = "green"


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


def merge_index_loc(loc: tuple[str, ...]) -> tuple[str, ...]:
    new_loc: list[str] = []
    for item in loc:
        if isinstance(item, int):
            previous = ""
            if new_loc:
                previous = new_loc.pop(-1)
            new_item = f"{previous}[{item}]"
            new_loc.append(new_item)
            continue
        new_loc.append(item)
    return tuple(new_loc)


def _errors_to_tree(tree: dict, loc: tuple[str, ...], error: dict):
    if not loc:
        tree.setdefault(CHILDREN_KEY, [])
        tree[CHILDREN_KEY].append(error)
        return
    key = loc[0]
    subtree = tree.setdefault(key, {})
    _errors_to_tree(subtree, loc[1:], error)


def errors_to_tree(errors: list[dict]) -> dict:
    tree = {}
    for error in errors:
        _errors_to_tree(tree, loc=merge_index_loc(error["loc"]), error=error)
    return tree


def _enrich_tree(rich_tree: Tree, tree: dict):
    for key, value in tree.items():
        if key == CHILDREN_KEY:
            continue
        if isinstance(key, int):
            key_name = f"[{key}]"
        else:
            key_name = key
        subtree = rich_tree.add(
            f"[{TREE_NODE_STYLE}]{escape(key_name)}[/{TREE_NODE_STYLE}]"
        )
        _enrich_tree(subtree, value)
    children = tree.get(CHILDREN_KEY, None)
    if children is not None:
        for error in children:
            items = []
            for key in ("type", "msg", "url"):
                if key not in error:
                    continue
                items.append(
                    f"[{TREE_LEAF_ATTR_STYLE}]{escape(key)}[/{TREE_LEAF_ATTR_STYLE}]",
                )
                label = escape(error[key])
                items.append(
                    f"[{TREE_LEAF_VALUE_STYLE}]{label}[/{TREE_LEAF_VALUE_STYLE}]",
                )
            rich_tree.add(" ".join(items))


def enrich_tree(tree: dict) -> Tree:
    root = Tree(":cross_mark:")
    _enrich_tree(rich_tree=root, tree=tree)
    return root


def validate_doc(form_doc_path: pathlib.Path) -> FormDoc:
    if not form_doc_path.exists():
        raise ValueError(f"Form document at {form_doc_path} does not exist")
    with form_doc_path.open("rt") as fo:
        payload = yaml.safe_load(fo)
        return FormDoc.model_validate(payload)
