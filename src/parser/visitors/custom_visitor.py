import logging

from parser.antlr_generated.SMTLIBv2Parser import SMTLIBv2Parser
from parser.antlr_generated.SMTLIBv2Visitor import SMTLIBv2Visitor
from parser.statements.smtlib_v2_statement import *
from parser.types.smtlib_v2_type import SMTLIBv2Type, get_SMTLIBv2Type_by_value
from parser.types.sorts import Sorts

logger = logging.getLogger(__name__)


class CustomVisitor(SMTLIBv2Visitor):
    def __init__(self) -> None:
        self._result = []

    def visitStart(self, ctx: SMTLIBv2Parser.StartContext) -> list:
        # 最初に呼ばれる
        self.visitChildren(ctx)
        # visitor.visit(tree) の戻り値になる
        return self._result

    def visitCmd_declareFun(self, ctx: SMTLIBv2Parser.Cmd_declareFunContext):
        command_ctx = ctx.parentCtx
        symbol = command_ctx.symbol(0)
        variable_name = symbol.getText()
        sort_ctxs = command_ctx.sort()
        # declareFun で定義される関数は戻り値が1つのみ
        # 最後が戻り値の型なので、それ以外を引数とする
        *fun_arg_sorts, fun_return_sort = [
            self.visitSort(sort_ctx) for sort_ctx in sort_ctxs
        ]
        self._result.append(
            SMTLIBv2Function(variable_name, fun_arg_sorts, fun_return_sort)
        )

    def visitSort(self, ctx: SMTLIBv2Parser.SortContext) -> Sorts:
        sort_value = ctx.getText()
        try:
            return Sorts(sort_value)
        except ValueError:
            raise ValueError(f"Invalid Sort: {sort_value}")

    def visitCmd_assert(self, ctx: SMTLIBv2Parser.Cmd_assertContext):
        command_ctx = ctx.parentCtx
        self._result.append(self.visitTerm(command_ctx.term(0)))

    def visitCmd_setLogic(self, ctx: SMTLIBv2Parser.Cmd_setLogicContext):
        command_ctx = ctx.parentCtx
        symbol = command_ctx.symbol(0)
        logic_name = symbol.getText()
        logger.info("Set logic: %s", logic_name)
        self._result.append(logic_name)

    def visitTerm(self, ctx: SMTLIBv2Parser.TermContext) -> SMTLIBv2Term:
        # Handle spec_constant or qual_identifier without terms
        if not ctx.term():
            if ctx.spec_constant():
                spec_constant = self.visitSpec_constant(ctx.spec_constant())
                return SMTLIBv2Term(spec_constant=spec_constant)

            if ctx.qual_identifier():
                qual_identifier = self.visitQual_identifier(ctx.qual_identifier())
                return SMTLIBv2Term(qual_identifier=qual_identifier)

        # Handle (qual_identifier term+)
        if ctx.qual_identifier():
            qual_identifier = self.visitQual_identifier(ctx.qual_identifier())
            terms = [self.visitTerm(term) for term in ctx.term()]
            return SMTLIBv2Term(qual_identifier=qual_identifier, terms=terms)

        # Raise an error for unexpected cases
        mssg = "Unknown term encountered in visitTerm"
        raise NotImplementedError(mssg)

    def visitSpec_constant(
        self, ctx: SMTLIBv2Parser.Spec_constantContext
    ) -> SpecConstant:
        type_conversion_map = [
            (ctx.numeral, SMTLIBv2Type.Numeral, int),
            (ctx.decimal, SMTLIBv2Type.Decimal, float),
            # hex, binary は先頭に #b, #x がついているので、それを取り除いて変換する
            (ctx.hexadecimal, SMTLIBv2Type.HexDecimal, lambda x: hex(int(x[2:], 16))),
            (ctx.binary, SMTLIBv2Type.Binary, lambda x: bin(int(x[2:], 2))),
            (ctx.string, SMTLIBv2Type.String, str),
        ]

        for context_method, smt_type, conversion_func in type_conversion_map:
            if context_method():
                return SpecConstant(
                    smt_type, conversion_func(context_method().getText())
                )

        # ctx はいずれかに当てはまるため、ここには到達しない
        msg = "context did not match any spec_constant"
        raise ValueError(msg)

    def visitIdentifier(self, ctx: SMTLIBv2Parser.IdentifierContext) -> Identifier:
        if ctx.index():
            mssg = "QF_LIA does not use index"
            raise NotImplementedError(mssg)
        symbol = self.visitSymbol(ctx.symbol())
        return Identifier(symbol)

    def visitQual_identifier(
        self, ctx: SMTLIBv2Parser.Qual_identifierContext
    ) -> QualIdentifier:
        if ctx.GRW_As():
            # QF_LIA には必要なさそうなので対応しない。
            mssg = "GRW_As is not supported"
            raise NotImplementedError(mssg)

        return QualIdentifier(self.visitIdentifier(ctx.identifier()))

    def visitSymbol(self, ctx: SMTLIBv2Parser.SymbolContext) -> Symbol:
        return self.visitChildren(ctx)

    def visitSimpleSymbol(self, ctx: SMTLIBv2Parser.SimpleSymbolContext) -> Symbol:
        if symbol_type := get_SMTLIBv2Type_by_value(ctx.getText()):
            return Symbol(symbol_type, ctx.getText())
        return Symbol(SMTLIBv2Type.UndefinedSymbol, ctx.getText())

    def visitQuotedSymbol(self, ctx: SMTLIBv2Parser.QuotedSymbolContext) -> Symbol:
        return Symbol(SMTLIBv2Type.QuotedSymbol, ctx.getText())
