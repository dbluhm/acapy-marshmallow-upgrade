import sys
import ast
import astor
from typing import Any, List, TypeVar, Tuple


ARG = TypeVar("ARG")  # TODO: bind str
VALUE = TypeVar("VALUE")  # TODO: bind Any
PATH = TypeVar("PATH")  # TODO: bind str

RENAME_ARGUMENTS: dict = {
    "default": "dump_default",
    "missing": "load_default",
}

_FIELD_ARGUMENTS: list = [
    # 'default',
    # 'missing',
    "data_key",
    "attribute",
    "validate",
    "required",
    "allow_none",
    "load_only",
    "dump_only",
    "error_messages",
    "metadata",
]

__fields_args = _FIELD_ARGUMENTS.copy()
__fields_args.extend(RENAME_ARGUMENTS.keys())
__fields_args.extend(RENAME_ARGUMENTS.values())

field_arguments = set(__fields_args)
field_specific_arguments = {
    "Dict": {"keys", "values"},
    "Constant": {"constant"},
    "Nested": {"many"},
    None: set(),
}

other_known_fields = {
    "StrOrDictField",
    "StrOrNumberField",
    "DictOrDictListField",
    "UriOrDictField",
}


def is_fields_call(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Attribute):
        attr = node.func
        if isinstance(attr.value, ast.Attribute):
            if isinstance(attr.value.value, ast.Name):
                if attr.value.attr == "fields":
                    return True

        if isinstance(attr.value, ast.Name):
            if node.func.value.id == "fields":
                return True

    if isinstance(node.func, ast.Name):
        if node.func.id in other_known_fields:
            return True

    return False


class ReplaceAsMetadataKW(ast.NodeTransformer):
    def visit_Call(self, node: ast.Call) -> Any:
        node.args = [self.visit(arg) for arg in node.args]

        if not is_fields_call(node):
            node.keywords = [self.visit(keyword) for keyword in node.keywords]
            return node

        for kw_obj in node.keywords:
            if kw_obj.arg == "metadata":
                node.keywords = [self.visit(keyword) for keyword in node.keywords]
                return node

        kws = node.keywords[:]
        node.keywords.clear()
        metadata: List[Tuple[ARG, VALUE]] = []

        if isinstance(node.func, ast.Attribute):
            field_func = str(node.func.attr)
        else:
            field_func = None

        for kw_obj in kws:
            # metadata
            if (
                kw_obj.arg
                and kw_obj.arg not in field_arguments
                and kw_obj.arg not in field_specific_arguments.get(field_func, set())
            ):
                metadata.append((kw_obj.arg, kw_obj.value))
            # the sig.parameters
            else:
                node.keywords.append(kw_obj)

        if metadata:
            node.keywords.append(
                ast.keyword(
                    arg="metadata",
                    value=ast.Dict(
                        keys=[
                            ast.Constant(value=arg, kind=None) for arg, _ in metadata
                        ],
                        values=[value for _, value in metadata],
                    ),
                )
            )

        node.keywords = [self.visit(keyword) for keyword in node.keywords]
        return node

    def visit_keyword(self, node: ast.keyword):
        node.value = self.visit(node.value)
        return node


class ReplaceDefaultAndMissing(ast.NodeTransformer):
    def visit_Call(self, node: ast.Call) -> Any:
        kws = node.keywords[:]
        node.keywords.clear()
        # rename = []
        for kw_obj in kws:
            if kw_obj.arg in RENAME_ARGUMENTS:
                # rename.append()
                node.keywords.append(
                    ast.keyword(arg=RENAME_ARGUMENTS[kw_obj.arg], value=kw_obj.value)
                )
            else:
                node.keywords.append(kw_obj)

        return node


def chunks():
    buffer = ""
    for line in sys.stdin:
        if line == "\0\n":
            return
        if line == "\n":
            yield buffer
            buffer = ""
            continue
        buffer += line
    yield buffer


def remove_indentation(field: str):
    spaces = 0
    for char in field:
        if char != " ":
            break
        spaces += 1

    indentation = int(spaces / 4)
    field = "\n".join([line[indentation * 4 :] for line in field.split("\n")])
    return field, indentation


def indent(field: str, indentation: int):
    return "\n".join([" " * 4 * indentation + line for line in field.split("\n")])


def modify_field(field: str):
    tree = ast.parse(field)
    tree = ReplaceAsMetadataKW().visit(tree)
    tree = ReplaceDefaultAndMissing().visit(tree)
    return astor.to_source(tree)


def main():
    for field in chunks():
        field, indentation = remove_indentation(field)
        field = modify_field(field)
        print(indent(field, indentation).rstrip(), flush=True)


if __name__ == "__main__":
    main()
