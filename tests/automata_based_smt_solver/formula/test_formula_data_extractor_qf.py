from pysmt.shortcuts import LE, And, Exists, Int, Or, Symbol
from pysmt.typing import INT

# FormulaDataExtractorQF と collect_literals_from_tree をインポート
from absmt.formula.formula_data_extractor_qf import (
    FormulaDataExtractorQF,
    collect_literals_from_tree,
)
from absmt.formula.type import FormulaType, QuantifierType


def test_formula_data_extractor_qf_and_or():
    """Tests simple AND/OR formulas by checking the collected literals."""
    x = Symbol("x", INT)
    y = Symbol("y", INT)
    formula = And(LE(x, Int(1)), LE(y, Int(2)))

    # 1. Extractorで木構造を取得し、そこからリテラルのセットを収集
    extractor = FormulaDataExtractorQF()
    tree_result = extractor.extract_data(formula)
    literals = collect_literals_from_tree(tree_result)

    # 2. 収集されたリテラルの内容を検証
    assert len(literals) == 2
    # 簡単にアクセスできるよう、変数名で辞書に変換
    literals_by_var = {
        next(iter(literal.coeffs.keys())): literal for literal in literals
    }

    assert "x" in literals_by_var
    assert literals_by_var["x"].const == 1
    assert literals_by_var["x"].quantifier_type == QuantifierType.NONE

    assert "y" in literals_by_var
    assert literals_by_var["y"].const == 2
    assert literals_by_var["y"].quantifier_type == QuantifierType.NONE


def test_formula_data_extractor_qf_exists():
    """Tests a simple EXISTS formula by checking the collected literal."""
    x = Symbol("x", INT)
    formula = Exists([x], LE(x, Int(5)))

    # 1. Extractorで木構造を取得し、そこからリテラルのセットを収集
    extractor = FormulaDataExtractorQF()
    tree_result = extractor.extract_data(formula)
    literals = collect_literals_from_tree(tree_result)

    # 2. 収集されたリテラルの内容を検証
    assert len(literals) == 1

    # セットから唯一の要素を取得
    data = literals.pop()

    assert data.quantifier_type == QuantifierType.EXISTS
    assert data.quantifier_vars == {"x"}
    assert data.coeffs == {"x": 1}
    assert data.const == 5
    assert data.formula_type == FormulaType.LE


def test_formula_data_extractor_qf_nested():
    """Tests a complex nested formula by checking the collected literals."""
    x = Symbol("x", INT)
    y = Symbol("y", INT)
    z = Symbol("z", INT)
    # ∃x (x ≤ 1 and (y ≤ 2 or ∃z (z ≤ 3)))
    formula = Exists(
        [x], And(LE(x, Int(1)), Or(LE(y, Int(2)), Exists([z], LE(z, Int(3)))))
    )

    # 1. Extractorで木構造を取得し、そこからリテラルのセットを収集
    extractor = FormulaDataExtractorQF()
    tree_result = extractor.extract_data(formula)
    literals = collect_literals_from_tree(tree_result)

    # 2. 収集された3つのリテラルの内容をそれぞれ検証
    assert len(literals) == 3
    # 簡単にアクセスできるよう、変数名で辞書に変換
    literals_by_var = {
        next(iter(literal.coeffs.keys())): literal for literal in literals
    }

    # Literal: x <= 1
    data_x = literals_by_var["x"]
    assert data_x.quantifier_type == QuantifierType.EXISTS
    assert data_x.quantifier_vars == {"x"}
    assert data_x.const == 1

    # Literal: y <= 2
    data_y = literals_by_var["y"]
    assert data_y.quantifier_type == QuantifierType.EXISTS
    assert data_y.quantifier_vars == {"x"}  # yはxのスコープ内にある
    assert data_y.const == 2

    # Literal: z <= 3
    data_z = literals_by_var["z"]
    assert data_z.quantifier_type == QuantifierType.EXISTS
    assert data_z.quantifier_vars == {"x", "z"}  # zはxとzの両方のスコープ内にある
    assert data_z.const == 3
