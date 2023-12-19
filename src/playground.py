from my_automata.automata_algorithms import AutomataBuilder, nfa_intersection
from my_automata.mutable_nfa import MutableNFA as NFA
from functools import reduce

coefs1 = [1, -1, 0, 0]
coefs2 = [2, 0, 1, 0]
coefs3 = [0, 0, 1, -2]


builders = []  # TODO: リテラルのandの部分を入れる。andとorが混じっている場合は二重リストにする
builders.append(AutomataBuilder(coefs1, 2, "equal", create_all=False))
builders.append(AutomataBuilder(coefs2, 5, "equal", create_all=False))
builders.append(AutomataBuilder(coefs3, 3, "equal", create_all=False))


loop = 0
is_sat = False
while not is_sat:  # TODO: 終了条件を、nfa_intersectionで出てきたnfaが受理できるかにする。dfsで探索する
    success_states = [builder.next() for builder in builders]  # FIXME: nfa.is_sat を取得して使う。
    if not any(success_states):  # all builders are already completed
        break

    # 個々のリテラルのオートマトンを出力
    for i, builder in enumerate(builders):
        builder.nfa.show_diagram(path=f"image/nfa{i}_{loop}.png")

    # 全てのintersectionをとる
    result_automata = reduce(nfa_intersection, [builder.nfa for builder in builders])
    is_sat = result_automata.dfs_with_path()

    result_automata.show_diagram(path=f"image/nfa_intersection{loop}.png")

    loop += 1
