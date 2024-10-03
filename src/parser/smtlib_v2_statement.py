# 1行の情報を保持するクラス。どんな型の変数か、引数は何か、戻り値は何か
# 再帰がかかるので、変数やterm, assert などそれぞれ定義したい

from dataclasses import dataclass, field
from os import name
from typing import Any

from parser.smtlib_v2_type import SMTLIBv2Type


@dataclass
class SMTLIBv2Function:
    name: str
    args: list[SMTLIBv2Type] | None
    return_type: SMTLIBv2Type

    def __str__(self) -> str:
        args_str = ", ".join(map(str, self.args)) if self.args else ""
        return f"{self.name}({args_str}) -> {self.return_type}"


@dataclass
class SpecConstant:
    type: SMTLIBv2Type
    value: Any


@dataclass
class QualIdentifier:
    value: "Identifier"

@dataclass
class Identifier:
    value: str
    # indicies はQF_LIA では使わないはず


@dataclass
class SMTLIBv2Term:
    spec_constant: SpecConstant | None = None
    qual_identifier: QualIdentifier | None = None
    sub_terms: list["SMTLIBv2Term"] = field(default_factory=list)
