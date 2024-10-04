from dataclasses import dataclass, field
from typing import Any

from parser.types.smtlib_v2_type import SMTLIBv2Type
from parser.types.sorts import Sorts


@dataclass
class SMTLIBv2Function:
    name: str
    args: list["Sorts"] | None
    return_type: "Sorts"

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
    symbol: "Symbol"
    # indicies はQF_LIA では使わないはず

    def __str__(self):
        return str(self.symbol)


@dataclass
class Symbol:
    type: SMTLIBv2Type
    value: str

    def __str__(self):
        if self.type == SMTLIBv2Type.UndefinedSymbol:
            return self.value
        return self.type


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
