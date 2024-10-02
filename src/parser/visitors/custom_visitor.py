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
        self._result.append(self.visitTerm(command_ctx.term(0)))

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
                return spec_constant
            if ctx.qual_identifier():
                qual_ideitifier = self.visitQual_identifier(ctx.qual_identifier())
                return qual_ideitifier
        elif ctx.qual_identifier():
            # Handle (qual_identifier term+)
            qual_ideitifier = self.visitQual_identifier(ctx.qual_identifier())
            terms = [self.visitTerm(term) for term in ctx.term()]
            return (qual_ideitifier, terms)
        # QF_LIA では上3つだけ使用されるはず
        elif ctx.GRW_Let():
            # Handle (let (var_binding+) term)
            var_bindings = [
                self.visitVar_binding(binding) for binding in ctx.var_binding()
            ]
            term = self.visitTerm(ctx.term(0))
            logger.info("let with bindings: %s and term: %s", var_bindings, term)
            return ("let", var_bindings, term)
        elif ctx.GRW_Forall():
            # Handle (forall (sorted_var+) term)
            sorted_vars = [self.visitSorted_var(var) for var in ctx.sorted_var()]
            term = self.visitTerm(ctx.term(0))
            logger.info("forall with sorted vars: %s and term: %s", sorted_vars, term)
            return ("forall", sorted_vars, term)
        elif ctx.GRW_Exists():
            # Handle (exists (sorted_var+) term)
            sorted_vars = [self.visitSorted_var(var) for var in ctx.sorted_var()]
            term = self.visitTerm(ctx.term(0))
            logger.info("exists with sorted vars: %s and term: %s", sorted_vars, term)
            return ("exists", sorted_vars, term)
        elif ctx.GRW_Match():
            # Handle (match term (match_case+))
            match_term = self.visitTerm(ctx.term(0))
            match_cases = [self.visitMatch_case(case) for case in ctx.match_case()]
            logger.info("match with term: %s and cases: %s", match_term, match_cases)
            return ("match", match_term, match_cases)
        elif ctx.GRW_Exclamation():
            # Handle (! term attribute+)
            exclam_term = self.visitTerm(ctx.term(0))
            attributes = [self.visitAttribute(attr) for attr in ctx.attribute()]
            logger.info(
                "exclamation with term: %s and attributes: %s", exclam_term, attributes
            )
            return ("exclamation", exclam_term, attributes)
        else:
            # ここには到達しないはず
            raise NotImplementedError("Unknown term")
        return None

    def visitVar_binding(self, ctx: SMTLIBv2Parser.Var_bindingContext):
        pass

    def visitSorted_var(self, ctx: SMTLIBv2Parser.Sorted_varContext):
        return super().visitSorted_var(ctx)

    def visitMatch_case(self, ctx: SMTLIBv2Parser.Match_caseContext):
        return super().visitMatch_case(ctx)

    def visitAttribute(self, ctx: SMTLIBv2Parser.AttributeContext):
        return super().visitAttribute(ctx)

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
        # TODO: ほとんどがindiciesなし。戻り値に空リストが含まれて使いにくい。
        return (ctx.symbol().getText(), indicies)

    def visitQual_identifier(self, ctx: SMTLIBv2Parser.Qual_identifierContext):
        if ctx.GRW_As():
            # QF_LIA には必要なさそうなので対応しない。
            raise NotImplementedError("GRW_As is not supported")

        return self.visitIdentifier(ctx.identifier())
