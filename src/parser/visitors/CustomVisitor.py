import logging

from parser.antlr.SMTLIBv2Parser import SMTLIBv2Parser
from parser.antlr.SMTLIBv2Visitor import SMTLIBv2Visitor

logger = logging.getLogger(__name__)


class CustomVisitor(SMTLIBv2Visitor):
    def __init__(self) -> None:
        self._result = []

    def visitStart(self, ctx: SMTLIBv2Parser.StartContext):
        self.visitChildren(ctx)
        return self._result
    # visitChildren を呼び出さないと、子ノードが再帰的に訪問されない
    # 中の処理でvisitChildrenを呼び出していればいい。戻り値にしなくてもいい。戻り値は Driver.py のresult に格納される
    def visitCommand(self, ctx: SMTLIBv2Parser.CommandContext):
        if ctx.cmd_declareFun():
            # 引数を持つ関数は想定しない。
            if len(ctx.sort()) > 1:
                error_message = "Function with 1 or more arguments is not supported"
                raise ValueError(error_message)

            # 同じ command 内に複数の declare-fun が存在しないので0を指定
            symbol_ctx = ctx.symbol(0)
            variable_name = self.visitSymbol(symbol_ctx)
            if variable_name:
                logger.info("Declare function: %s", variable_name)
                self._result.append(variable_name)
                return
        elif ctx.cmd_setLogic():
            # 同じ command 内に複数の set-logic が存在しないので0を指定
            symbol = ctx.symbol(0)
            rslt = self.visitSymbol(symbol)
            logger.info("Set logic: %s", rslt)
        return  # これ以上探索する必要がないため

    def visitSymbol(self, ctx: SMTLIBv2Parser.SymbolContext):
        # Handle simpleSymbol and quotedSymbol
        if ctx.simpleSymbol():
            return self.visitSimpleSymbol(ctx.simpleSymbol())
        if ctx.quotedSymbol():
            return self.visitQuotedSymbol(ctx.quotedSymbol())
        return None

    def visitSimpleSymbol(self, ctx: SMTLIBv2Parser.SimpleSymbolContext):
        # Handle predefined symbols and undefined symbols
        if ctx.predefSymbol():
            return ctx.predefSymbol().getText()
        if ctx.UndefinedSymbol():
            return ctx.UndefinedSymbol().getText()
        return None

    def visitQuotedSymbol(self, ctx: SMTLIBv2Parser.QuotedSymbolContext):
        # Return the text of the quoted symbol, stripping the surrounding '|'
        text = ctx.getText()
        return text[1:-1]  # Remove the leading and trailing '|'
