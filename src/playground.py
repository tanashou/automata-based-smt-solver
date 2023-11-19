from src.my_automata.my_automata import MutableNFA as NFA
from automata.fa.nfa import NFA as BaseNFA
from src.my_automata.automata_algorithm import *


coefs = ["1", "-1", "1"]
mask1 = [True, True, False]
mask2 = [True, False, True]

builders = []  # リテラルのandの部分を入れる。andとorが混じっている場合は二重リストにする
builders.append(AutomataBuilder(coefs, 2, "equal", mask1, create_all=False))
builders.append(AutomataBuilder(coefs, 5, "equal", mask2, create_all=False))

loop = 0
while True:
    complete = [builder.next() for builder in builders]
    if not any(complete):  # all builders are already completed
        break

    for i, builder in enumerate(builders):
        builder.nfa.show_diagram(path=f"image/nfa{i}_{loop}.png")

    paired_list = [(builders[i], builders[i + 1]) for i in range(0, len(builders), 2)]
    for builder1, builder2 in paired_list:
        nfa = nfa_intersection(builder1.nfa, builder2.nfa, builder1.mask, builder2.mask)
        nfa.show_diagram(path=f"image/nfa_intersection{loop}.png")

    loop += 1
