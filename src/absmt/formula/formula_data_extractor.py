# ruff: noqa: ANN201, ANN204, ANN001
from typing import TypeAlias

from pysmt.fnode import FNode
from pysmt.operators import AND, EQUALS, EXISTS, LE, OR
from pysmt.shortcuts import Minus

from absmt.formula.type import FormulaData, FormulaNodeType, FormulaType, QuantifierType

from .polynomial_normalizer import PolynomialNormalizer

FormulaTree: TypeAlias = dict[str, FormulaNodeType | list["FormulaTree | FormulaData"]]


class FormulaDataExtractor:
    """A simple recursive walker to perform top-down context propagation."""

    def __init__(self):
        self.normalizer = PolynomialNormalizer()
        self.memoization = {}
        # Map node types from pysmt.operators to walk methods.
        self.functions = {
            EXISTS: self.walk_exists,
            AND: self.walk_and,
            OR: self.walk_or,
            LE: self.walk_le,
            EQUALS: self.walk_equals,
            # Assumes that LT and FORALL have been eliminated in a pre-processing step.
        }

    def extract_data(self, formula: FNode) -> FormulaTree:
        initial_context = {
            "quantifier_type": QuantifierType.NONE,
            "quantifier_vars": set(),
        }
        return self._walk(formula, initial_context)

    def _get_key(self, formula, context) -> tuple:
        context_tuple = frozenset(
            (
                k,
                frozenset(v) if isinstance(v, set) else v,
            )  # Convert set to frozenset to make it hashable.
            for k, v in sorted(context.items())
        )
        return (formula, context_tuple)

    def _walk(self, formula, context) -> FormulaTree:
        key = self._get_key(formula, context)
        if key in self.memoization:
            return self.memoization[key]

        # Use the FNode type (int) directly as the key.
        node_type = formula.node_type()
        func = self.functions.get(node_type)

        result = func(formula, context) if func else {}
        self.memoization[key] = result
        return result

    def _get_normalized_data(self, formula, context) -> FormulaData:
        left, right = formula.arg(0), formula.arg(1)
        expr_to_normalize = Minus(left, right)
        coeffs, const = self.normalizer.walk(expr_to_normalize)
        final_const = -const
        formula_type = FormulaType.EQ if formula.is_equals() else FormulaType.LE
        return FormulaData(
            quantifier_type=context["quantifier_type"],
            quantifier_vars=context["quantifier_vars"],
            coeffs=coeffs,
            const=final_const,
            formula_type=formula_type,
        )

    def walk_exists(self, formula, context):
        q_vars = {v.symbol_name() for v in formula.quantifier_vars()}
        new_context = context.copy()
        new_context["quantifier_type"] = QuantifierType.EXISTS
        new_context["quantifier_vars"] = q_vars | context.get("quantifier_vars", set())

        # Process the child node with the new context.
        child_result = self._walk(formula.arg(0), new_context)

        # Wrap the result in a list if it's not already a list.
        if isinstance(child_result, list):
            return child_result
        if child_result is not None:
            return [child_result]
        return []

    def walk_and(self, formula, context):
        args = [self._walk(arg, context) for arg in formula.args()]
        return {
            "type": FormulaNodeType.AND,
            "args": [arg for arg in args if arg is not None],
        }

    def walk_or(self, formula, context):
        args = [self._walk(arg, context) for arg in formula.args()]
        return {
            "type": FormulaNodeType.OR,
            "args": [arg for arg in args if arg is not None],
        }

    def walk_le(self, formula, context):
        return {
            "type": FormulaNodeType.ATOM,
            "args": [self._get_normalized_data(formula, context)],
        }

    def walk_equals(self, formula, context):
        if formula.arg(0).get_type().is_bool_type():
            return None  # Iff is not supported.
        return {
            "type": FormulaNodeType.ATOM,
            "args": [self._get_normalized_data(formula, context)],
        }


def collect_literals_from_tree(tree: FormulaTree) -> list[FormulaData]:
    """Recursively collects all FormulaData objects (literals).

    Args:
        tree: The return value of extractor.extract_data().

    Returns:
        A set of all unique FormulaData objects contained in the formula.

    """
    literals = []
    _recursive_collect(tree, literals)
    return literals


def _recursive_collect(
    node: FormulaTree | FormulaData,
    literals: list[FormulaData],
) -> None:
    """Perform the recursive collection of FormulaData objects."""
    if isinstance(node, dict):
        # For AND/OR/ATOM nodes, recurse on the list of children.
        args = node.get("args", [])
        if isinstance(args, list):
            for child_node in args:
                _recursive_collect(child_node, literals)
        elif isinstance(args, FormulaData):
            literals.append(args)
    elif isinstance(node, list):
        # Recurse on each item in the list.
        for item in node:
            _recursive_collect(item, literals)
    elif isinstance(node, FormulaData):
        # If the node is a FormulaData object, it's a literal leaf.
        literals.append(node)
    # Do nothing for None or other types.
