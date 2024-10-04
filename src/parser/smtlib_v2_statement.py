# 1行の情報を保持するクラス。どんな型の変数か、引数は何か、戻り値は何か
# 再帰がかかるので、変数やterm, assert などそれぞれ定義したい

from dataclasses import dataclass, field
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

    def __str__(self):
        return str(self.value)


@dataclass
class QualIdentifier:
    value: "Identifier"

    def __str__(self):
        return str(self.value)


@dataclass
class Identifier:
    value: str
    # indicies はQF_LIA では使わないはず

    def __str__(self):
        return self.value


@dataclass
class SMTLIBv2Term:
    spec_constant: SpecConstant | None = None
    qual_identifier: QualIdentifier | None = None
    terms: list["SMTLIBv2Term"] = field(default_factory=list)

    def __str__(self):
        if self.spec_constant:
            return str(self.spec_constant)
        if self.terms:
            return (
                str(self.qual_identifier) + "(" + " ".join(map(str, self.terms)) + ")"
            )
        return f"{self.qual_identifier}"
