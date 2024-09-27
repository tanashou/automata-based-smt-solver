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

    def visitCommand(self, ctx: SMTLIBv2Parser.CommandContext):
        if ctx.cmd_declareFun():
            # 同じ command 内に複数の declare-fun が存在しないので0を指定
            symbol_ctx = ctx.symbol(0)
            variable_name = self.visitSymbol(symbol_ctx)
            sort_ctxs = ctx.sort()
            # declareFun で定義される関数は戻り値が1つのみ。
            # 最後が戻り値の型なので、それ以外を引数とする。
            *fun_args, fun_return_type = [
                self.visitSort(sort_ctx) for sort_ctx in sort_ctxs
            ]

            logger.info(
                "Declare function: %s (%s) -> %s",
                variable_name,
                fun_args,
                fun_return_type,
            )
            # TODO: 変数名、引数、戻り値を結果に入れたい
            self._result.append(variable_name)

        elif ctx.cmd_setLogic():
            # 同じ command 内に複数の set-logic が存在しないので0を指定
            symbol = ctx.symbol(0)
            logic_name = self.visitSymbol(symbol)
            if logic_name:
                logger.info("Set logic: %s", logic_name)
                self._result.append(logic_name)
                return
        return  # これ以上探索する必要がない

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
        # Return the text of the quoted symbol, stripping the surrounding '|'
        text = ctx.getText()
        return text[1:-1]  # Remove the leading and trailing '|'
