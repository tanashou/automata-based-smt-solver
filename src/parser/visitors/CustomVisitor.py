import logging

from parser.antlr.SMTLIBv2Parser import SMTLIBv2Parser
from parser.antlr.SMTLIBv2Visitor import SMTLIBv2Visitor

logger = logging.getLogger(__name__)


class CustomVisitor(SMTLIBv2Visitor):
    def __init__(self) -> None:
        self._result = []

    def visitStart(self, ctx: SMTLIBv2Parser.StartContext):
        # 最初に呼ばれる
        self.visitChildren(ctx)
        # visitor.visit(tree) の戻り値になる
        return self._result

    def visitCmd_declareFun(self, ctx: SMTLIBv2Parser.Cmd_declareFunContext):
        command_ctx = ctx.parentCtx
        symbol_ctx = command_ctx.symbol(0)
        variable_name = self.visitSymbol(symbol_ctx)
        sort_ctxs = command_ctx.sort()
        # declareFun で定義される関数は戻り値が1つのみ
        # 最後が戻り値の型なので、それ以外を引数とする
        *fun_arg_types, fun_return_type = [
            self.visitSort(sort_ctx) for sort_ctx in sort_ctxs
        ]
        logger.info(
            "Declare function: %s (%s) -> %s",
            variable_name,
            fun_arg_types,
            fun_return_type,
        )
        self._result.append(variable_name)

    def visitCmd_setLogic(self, ctx: SMTLIBv2Parser.Cmd_setLogicContext):
        command_ctx = ctx.parentCtx
        symbol = command_ctx.symbol(0)
        logic_name = self.visitSymbol(symbol)
        logger.info("Set logic: %s", logic_name)
        self._result.append(logic_name)

    def visitSymbol(self, ctx: SMTLIBv2Parser.SymbolContext):
        # Handle simpleSymbol and quotedSymbol
        rslt = None
        if ctx.simpleSymbol():
            rslt = self.visitSimpleSymbol(ctx.simpleSymbol())
        elif ctx.quotedSymbol():
            rslt = self.visitQuotedSymbol(ctx.quotedSymbol())
        return rslt

    def visitSimpleSymbol(self, ctx: SMTLIBv2Parser.SimpleSymbolContext):
        # Handle predefined symbols and undefined symbols
        rslt = None
        if ctx.predefSymbol():
            rslt = ctx.predefSymbol().getText()
        if ctx.UndefinedSymbol():
            rslt = ctx.UndefinedSymbol().getText()
        return rslt

    def visitQuotedSymbol(self, ctx: SMTLIBv2Parser.QuotedSymbolContext):
        return ctx.getText()
