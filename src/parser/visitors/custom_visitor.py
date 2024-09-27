import logging

from parser.antlr.SMTLIBv2Parser import SMTLIBv2Parser
from parser.antlr.SMTLIBv2Visitor import SMTLIBv2Visitor

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
        logic_name = symbol.getText()
        logger.info("Set logic: %s", logic_name)
        self._result.append(logic_name)

    def visitTerm(self, ctx: SMTLIBv2Parser.TermContext):
        if not ctx.term():
            # spec_constant or qual_identifier
            if ctx.spec_constant():
                spec_constant = self.visitSpec_constant(ctx.spec_constant())
                logger.info("spec constant: %s", spec_constant)
            elif ctx.qual_identifier():
                qual_ideitifier = self.visitQual_identifier(ctx.qual_identifier())
                logger.info("qual identifier: %s", qual_ideitifier)
        return super().visitTerm(ctx)

    def visitSpec_constant(self, ctx: SMTLIBv2Parser.Spec_constantContext) -> tuple:
        # List of method references and their corresponding names
        methods = [
            (ctx.numeral, "numeral"),
            (ctx.decimal, "decimal"),
            (ctx.hexadecimal, "hexadecimal"),
            (ctx.binary, "binary"),
            (ctx.string, "string"),
        ]

        for method, name in methods:
            if method():
                return (name, method().getText())

        # ctx はいずれかに当てはまるため、ここには到達しない
        msg = "context did not match any spec_constant"
        raise ValueError(msg)

    def visitIdentifier(
        self, ctx: SMTLIBv2Parser.IdentifierContext
    ) -> tuple[str, list]:
        indicies = []
        if ctx.index():
            indicies = [self.visitSymbol(index).getText() for index in ctx.index()]
        return (ctx.symbol().getText(), indicies)

    def visitQual_identifier(self, ctx: SMTLIBv2Parser.Qual_identifierContext):
        if ctx.GRW_As():
            # QF_LIA には必要なさそうなので対応しない。
            raise NotImplementedError("GRW_As is not supported")

        return self.visitIdentifier(ctx.identifier())
