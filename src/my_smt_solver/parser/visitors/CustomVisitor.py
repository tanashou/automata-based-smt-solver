from antlr4 import *

from my_smt_solver.parser.generated.SMTLIBv2Visitor import SMTLIBv2Visitor


class CustomVisitor(SMTLIBv2Visitor):
    def __init__(self):
        self.indent = 0

    # visitChildren を呼び出さないと、子ノードが再帰的に訪問されない
    # 中の処理でvisitChildrenを呼び出していればいい。戻り値にしなくてもいい。戻り値は Driver.py のresult に格納される
    def visitChildren(self, ctx):
        self.indent += 1
        super().visitChildren(ctx)
        self.indent -= 1
        return "hello"

    def visitStart(self, ctx):
        self.visitChildren(ctx)
        return "hello start"

    def visitScript(self, ctx):
        return self.visitChildren(ctx)

    # TODO: この関数を拡張していく。
    def visitCommand(self, ctx):
        if ctx.cmd_declareFun():
            pass
        elif ctx.cmd_setLogic():
            symbol = ctx.symbol()[0]  # should be only one symbol
            rslt = self.visitSymbol(symbol)
            print(rslt)
        return self.visitChildren(ctx)

    def visitSymbol(self, ctx):
        return self.visitChildren(ctx)

    def visitSort(self, ctx):
        return self.visitChildren(ctx)

    def visitIdentifier(self, ctx):
        return self.visitChildren(ctx)

    def visitSimpleSymbol(self, ctx):
        return self.visitChildren(ctx)

    def visitTerm(self, ctx):
        return self.visitChildren(ctx)
