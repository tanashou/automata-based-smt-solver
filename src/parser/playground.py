from pysmt.rewritings import CNFizer
from pysmt.smtlib.parser import SmtLibParser

smt_file_path = "benchmarks/QF_LIA/convert/convert-jpg2gif-query-901.smt2"
parser = SmtLibParser()
smt_script = parser.get_script_fname(smt_file_path)
formula = smt_script.get_strict_formula().simplify()
print(formula)
print()

# Create a CNFizer instance
cnfizer = CNFizer()

# Convert the formula to CNF
cnf = cnfizer.convert_as_formula(formula)
automata_size = 1
for clause in cnf.args():
    automata_size *= len(clause.get_free_variables())

print(f"autoamta size: {automata_size}")

