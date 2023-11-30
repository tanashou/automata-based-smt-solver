from my_automata.automata_algorithms import AutomataBuilder, nfa_intersection
from my_automata.mutable_nfa import MutableNFA as NFA
from functools import reduce


coefs = ["1", "-1", "1", '-2']  # TODO: str か int のどっちで管理するか検討。
mask1 = [True, True, False, False]
mask2 = [True, False, True, False]
mask3 = [False, False, True, True]

builders = []  # TODO: リテラルのandの部分を入れる。andとorが混じっている場合は二重リストにする
builders.append(AutomataBuilder(coefs, 2, "equal", mask1, create_all=False))
builders.append(AutomataBuilder(coefs, 5, "equal", mask2, create_all=False))
builders.append(AutomataBuilder(coefs, 3, 'equal', mask3))


def intersection_all(builders: list[AutomataBuilder]) -> NFA:
    return reduce(
        lambda acc, bld: nfa_intersection(acc[0], bld.nfa, acc[1], bld.mask),
        builders[1:],
        (builders[0].nfa, builders[0].mask),
    )[0]


loop = 0
is_sat = False
while not is_sat:  # TODO: 終了条件を、nfa_intersectionで出てきたnfaが受理できるかにする。dfsで探索する
    success_states = [builder.next() for builder in builders]
    if not any(success_states):  # all builders are already completed
        break

    # 個々のリテラルのオートマトンを出力
    for i, builder in enumerate(builders):
        builder.nfa.show_diagram(path=f"image/nfa{i}_{loop}.png")

    # 全てのintersectionをとる
    result_automata = intersection_all(builders)
    is_sat = result_automata.dfs()

    result_automata.show_diagram(path=f"image/nfa_intersection{loop}.png")

    loop += 1
