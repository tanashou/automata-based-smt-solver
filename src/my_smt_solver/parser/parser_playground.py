import sys
import time

from antlr4 import *

from my_smt_solver.parser.generated.SMTLIBv2Lexer import SMTLIBv2Lexer
from my_smt_solver.parser.generated.SMTLIBv2Parser import SMTLIBv2Parser
from my_smt_solver.parser.visitors.CustomVisitor import CustomVisitor


def traverse(tree, visitor):
    if tree.getChildCount() == 0:
        print(f"Leaf: {tree.getText()}")
    else:
        print(f"Node: {type(tree).__name__}")
        for i in range(tree.getChildCount()):
            child = tree.getChild(i)
            traverse(child, visitor)


def main(argv):
    input_stream = FileStream(argv[1])
    start_time = time.time()
    lexer = SMTLIBv2Lexer(input_stream)
    read_time = time.time()
    print(f"Read time: {read_time - start_time}")
    stream = CommonTokenStream(lexer)
    stream_time = time.time()
    print(f"Stream time: {stream_time - read_time}")
    parser = SMTLIBv2Parser(stream)
    end_time = time.time()
    print(f"Parser time: {end_time - stream_time}")

    tree = parser.start()
    tree_time = time.time()
    print(f"Tree time: {tree_time - end_time}")
    visitor = CustomVisitor()
    result = visitor.visit(tree)
    print(result)
    visitor_time = time.time()
    print(f"Visitor time: {visitor_time - tree_time}")


if __name__ == "__main__":
    main(sys.argv)
