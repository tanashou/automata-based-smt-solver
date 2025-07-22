# ruff: noqa: ANN201, ANN204, ANN001, ANN003, ARG002
from pysmt.shortcuts import Minus
from pysmt.walkers import DagWalker

from absmt.formula.type import FormulaData, FormulaNodeType, FormulaType, QuantifierType

from .polynomial_normalizer import PolynomialNormalizer


class FormulaDataExtractorQF(DagWalker):
    """Walker to extract a list of FormulaData from LIA formulas with quantifiers.

    Improved robustness with top-down context propagation logic.
    """

    def __init__(self, env=None):
        # Memoization must be disabled to pass context
        super().__init__(env=env, invalidate_memoization=True)
        self.normalizer = PolynomialNormalizer(env=env)

    def extract_data(self, formula) -> object:
        initial_context = {
            "quantifier_type": QuantifierType.NONE,
            "quantifier_vars": [],
        }
        return self.walk(formula, **initial_context)

    def _get_key(self, formula, *args, **kwargs):  # noqa: ANN002, ANN202
        # kwargsのアイテムを処理し、リストがあればタプルに変換する
        key_items = []
        # 安定したハッシュ値を得るため、キーでソートしてから処理する
        for key in sorted(kwargs.keys()):
            value = kwargs[key]
            if isinstance(value, list):
                # リストをタプルに変換してハッシュ化可能にする
                key_items.append((key, tuple(value)))
            else:
                key_items.append((key, value))

        # イミュータブルなアイテムのリストからfrozensetを作成
        context_frozenset = frozenset(key_items)
        return (formula, context_frozenset)

    def _get_normalized_data(self, formula, context) -> FormulaData:
        left, right = formula.arg(0), formula.arg(1)

        # L <= R  -->  L - R <= 0
        # L = R   -->  L - R = 0
        expr_to_normalize = Minus(left, right)

        coeffs, const = self.normalizer.walk(expr_to_normalize)

        # Sum(c_i * x_i) + const <= 0  -->  Sum(c_i * x_i) <= -const
        final_const = -const

        # Determine type based on FormulaType Enum
        formula_type = FormulaType.LE
        if formula.is_equals():
            formula_type = FormulaType.EQ

        return FormulaData(
            quantifier_type=context["quantifier_type"],
            quantifier_vars=context["quantifier_vars"],
            coeffs=coeffs,
            const=final_const,
            formula_type=formula_type,
        )

    def walk_forall(self, formula, args, **kwargs):
        msg = "FORALL should be eliminated before this walker."
        raise NotImplementedError(msg)

    def walk_exists(self, formula, args, **kwargs):
        q_type = QuantifierType.EXISTS
        q_vars = [v.symbol_name() for v in formula.quantifier_vars()]
        new_context = kwargs.copy()
        new_context["quantifier_type"] = q_type
        # Add current scope variables to the front of the nested quantifier list
        new_context["quantifier_vars"] = q_vars + kwargs.get("quantifier_vars", [])

        # Recursively process child node with new context
        return self.walk(formula.arg(0), **new_context)

    def walk_le(self, formula, args, **kwargs):
        return [self._get_normalized_data(formula, kwargs)]

    def walk_lt(self, formula, args, **kwargs):
        msg = "LT should be eliminated before this walker."
        raise NotImplementedError(msg)

    def walk_equals(self, formula, args, **kwargs):
        # Distinguish Iff(bool, bool) and Equals(term, term)
        if formula.arg(0).get_type().is_bool_type():
            return None
        return [self._get_normalized_data(formula, kwargs)]

    def walk_and(self, formula, args, **kwargs):
        # Return a dictionary representing an 'and' node
        return {"type": FormulaNodeType.AND, "args": args}

    def walk_or(self, formula, args, **kwargs):
        # Return a dictionary representing an 'or' node
        return {"type": FormulaNodeType.OR, "args": args}

    def walk_symbol(self, formula, args, **kwargs):
        return formula

    def walk_int_constant(self, formula, args, **kwargs):
        return formula
