import logging
import sys
import time
from functools import wraps

from antlr4 import *

from parser.antlr_generated.SMTLIBv2Lexer import SMTLIBv2Lexer
from parser.antlr_generated.SMTLIBv2Parser import SMTLIBv2Parser
from parser.visitors.custom_visitor import CustomVisitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Decorator to time a function
def timer(section_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            logger.info("%s: %s seconds", section_name, end_time - start_time)
            return result

        return wrapper

    return decorator


def main(argv):
    input_stream = FileStream(argv[1])

    @timer("Lexer")
    def create_lexer(input_stream):
        return SMTLIBv2Lexer(input_stream)

    @timer("Stream")
    def create_stream(lexer):
        return CommonTokenStream(lexer)

    @timer("Parser")
    def create_parser(stream):
        return SMTLIBv2Parser(stream)

    @timer("Tree")
    def parse_tree(parser):
        return parser.start()

    @timer("Visitor")
    def visit_tree(tree):
        visitor = CustomVisitor()
        return visitor.visit(tree)

    lexer = create_lexer(input_stream)
    stream = create_stream(lexer)
    parser = create_parser(stream)
    tree = parse_tree(parser)
    result = visit_tree(tree)

    for r in result:
        logger.info(r)


if __name__ == "__main__":
    main(sys.argv)
