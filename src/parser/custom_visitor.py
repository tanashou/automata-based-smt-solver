# ruff: noqa: N802: ignore snake_case naming style for visitor methods
import logging

from parser.antlr.SMTLIBv2Parser import SMTLIBv2Parser
from parser.antlr.SMTLIBv2Visitor import SMTLIBv2Visitor
from parser.smtlib_v2_statement import *
from parser.smtlib_v2_type import SMTLIBv2Type

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

        self._result.append(
            SMTLIBv2Function(variable_name, fun_arg_types, fun_return_type)
        )

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
                return SMTLIBv2Term(spec_constant=spec_constant)
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
            return (SMTLIBv2Type.GRW_Let, var_bindings, term)
        elif ctx.GRW_Forall():
            # Handle (forall (sorted_var+) term)
            sorted_vars = [self.visitSorted_var(var) for var in ctx.sorted_var()]
            term = self.visitTerm(ctx.term(0))
            logger.info("forall with sorted vars: %s and term: %s", sorted_vars, term)
            return (SMTLIBv2Type.GRW_Forall, sorted_vars, term)
        elif ctx.GRW_Exists():
            # Handle (exists (sorted_var+) term)
            sorted_vars = [self.visitSorted_var(var) for var in ctx.sorted_var()]
            term = self.visitTerm(ctx.term(0))
            logger.info("exists with sorted vars: %s and term: %s", sorted_vars, term)
            return (SMTLIBv2Type.GRW_Exists, sorted_vars, term)
        elif ctx.GRW_Match():
            # Handle (match term (match_case+))
            match_term = self.visitTerm(ctx.term(0))
            match_cases = [self.visitMatch_case(case) for case in ctx.match_case()]
            logger.info("match with term: %s and cases: %s", match_term, match_cases)
            return (SMTLIBv2Type.GRW_Match, match_term, match_cases)
        elif ctx.GRW_Exclamation():
            # Handle (! term attribute+)
            exclam_term = self.visitTerm(ctx.term(0))
            attributes = [self.visitAttribute(attr) for attr in ctx.attribute()]
            logger.info(
                "exclamation with term: %s and attributes: %s", exclam_term, attributes
            )
            return (SMTLIBv2Type.GRW_Exclamation, exclam_term, attributes)
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

    def visitSpec_constant(
        self, ctx: SMTLIBv2Parser.Spec_constantContext
    ) -> SpecConstant:
        # List of method references and their corresponding names
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
        return Identifier(ctx.symbol().getText())

    def visitQual_identifier(
        self, ctx: SMTLIBv2Parser.Qual_identifierContext
    ) -> QualIdentifier:
        if ctx.GRW_As():
            # QF_LIA には必要なさそうなので対応しない。
            mssg = "GRW_As is not supported"
            raise NotImplementedError(mssg)

        return QualIdentifier(self.visitIdentifier(ctx.identifier()))
