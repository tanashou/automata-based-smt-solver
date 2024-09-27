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

    def visitCmd_assert(self, ctx: SMTLIBv2Parser.Cmd_assertContext):
        command_ctx = ctx.parentCtx
        return super().visitCmd_assert(ctx)

    def visitCmd_setLogic(self, ctx: SMTLIBv2Parser.Cmd_setLogicContext):
        command_ctx = ctx.parentCtx
        symbol = command_ctx.symbol(0)
        logic_name = self.visitSymbol(symbol)
        logger.info("Set logic: %s", logic_name)
        self._result.append(logic_name)

    def visitSymbol(self, ctx: SMTLIBv2Parser.SymbolContext):
        return ctx.getText()

    def visitTerm(self, ctx: SMTLIBv2Parser.TermContext):
        if not ctx.term():
            # spec_constant or qual_identifier
            if ctx.spec_constant():
                logger.info("spec constant: %s", ctx.spec_constant().getText())
            elif ctx.qual_identifier():
                logger.info("qual identifier: %s", ctx.qual_identifier().getText())
        return super().visitTerm(ctx)
