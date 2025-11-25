import random
from pathlib import Path


def generate_mixed_smt2(filename, total_asserts=5, total_vars_pool=20):
    """構造（密・疎）、変数の数（1-8）、定数の大小が混在したsmt2ファイルを生成する
    変更点: assert数をデフォルト5に、係数範囲を最大100に設定
    """
    lines = []
    lines.append("(set-info :smt-lib-version 2.6)")
    lines.append("(set-logic QF_LIA)")
    lines.append('(set-info :category "mixed-benchmark")')
    lines.append("(set-info :status unknown)")

    # 全体の変数プール (x_0 ... x_19)
    all_vars = [f"x_{i}" for i in range(total_vars_pool)]
    for v in all_vars:
        lines.append(f"(declare-fun {v} () Int)")

    assert_definitions = []

    # --- 設定: 内訳の調整 (合計5つになるように配分) ---
    # total_asserts が 5 の場合: Dense=2, Sparse=2, Random=1 となります
    if total_asserts >= 5:
        num_dense = 2
        num_sparse = 2
    else:
        # 5未満が指定された場合の安全策
        num_dense = total_asserts // 2
        num_sparse = total_asserts - num_dense

    num_random = total_asserts - num_dense - num_sparse

    # 密結合用の変数サブセット (x_0 〜 x_3 を使い回す)
    dense_pool = all_vars[:4]
    # 疎結合用の変数サブセット (残りの変数)
    sparse_pool = all_vars[4:]

    # --- 関数: 個別の式(assert)を作成するヘルパー ---
    def create_assert(pool, term_count_range, magnitude):
        # 変数の個数を決める (1〜8個、ただしプールのサイズを超えない範囲)
        num_terms = random.randint(*term_count_range)
        num_terms = min(num_terms, len(pool))

        num_terms = max(num_terms, 1)

        # 変数を選択
        selected_vars = random.sample(pool, num_terms)

        # 定数の範囲設定
        if magnitude == "small":
            # 小さい係数パターン
            coeff_range = (-5, 5)
            rhs_range = (-10, 10)
        else:  # large
            # 大きい係数パターン（ご指定通り最大100）
            coeff_range = (-50, 50)
            # 右辺の定数は状態数爆発を誘発するため大きめを維持しますが、
            # もし右辺も100以下が良い場合はここを (-100, 100) に変更してください
            rhs_range = (-50, 50)

        terms = []
        for var in selected_vars:
            coeff = random.randint(*coeff_range)
            # 係数0は無意味なので1にする（またはスキップする）
            if coeff == 0:
                coeff = 1
            terms.append(f"(* {coeff} {var})")

        # 1変数の場合や項の結合
        if len(terms) == 1:
            lhs_expr = terms[0]
        else:
            lhs_expr = f"(+ {' '.join(terms)})"

        rhs = random.randint(*rhs_range)
        op = random.choice(["<=", ">=", "="])

        return f"(assert ({op} {lhs_expr} {rhs}))"

    # --- 1. 密結合グループ (Dense Cluster) の生成 ---
    # 特徴: 係数小、変数密度高
    for _ in range(num_dense):
        assert_definitions.append(
            create_assert(pool=dense_pool, term_count_range=(3, 4), magnitude="small")
        )

    # --- 2. 疎結合グループ (Sparse / Independent) の生成 ---
    # 特徴: 係数大(〜100)、変数密度低
    for _ in range(num_sparse):
        assert_definitions.append(
            create_assert(pool=sparse_pool, term_count_range=(1, 3), magnitude="large")
        )

    # --- 3. ランダムグループ (Random Bridge) の生成 ---
    # 特徴: 全体から変数を選ぶ、係数は小
    for _ in range(num_random):
        assert_definitions.append(
            create_assert(pool=all_vars, term_count_range=(1, 8), magnitude="small")
        )

    # --- 4. 順序のシャッフル ---
    random.shuffle(assert_definitions)

    lines.extend(assert_definitions)
    lines.append("(check-sat)")
    lines.append("(exit)")

    with open(filename, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated Mixed Case: {filename} (Asserts: {total_asserts})")


def generate_mixed_smt2_sat(filename, total_asserts=5, total_vars_pool=20):
    """SAT（充足可能）が保証されたmixed-benchmarkを生成する。
    修正点:
    - 右辺の定数(RHS)を小さく(±50以内)保つため、左辺の計算結果(lhs_value)自体が
      小さくなるような係数の組み合わせをRejection Sampling（選別）で探す。
    - これにより、不自然な調整項なしで、移項後も定数が小さい式を生成する。
    """
    lines = []
    lines.append("(set-info :smt-lib-version 2.6)")
    lines.append("(set-logic QF_LIA)")
    lines.append('(set-info :category "mixed-benchmark-sat")')
    lines.append("(set-info :status sat)")

    all_vars = [f"x_{i}" for i in range(total_vars_pool)]
    for v in all_vars:
        lines.append(f"(declare-fun {v} () Int)")

    # --- SAT解の生成 ---
    # 左辺の合計を小さく保ちやすくするため、解自体の絶対値を少し抑える (-10〜10)
    # これにより、係数が大きくても合計が爆発しにくくなる
    target_solution = {v: random.randint(-10, 10) for v in all_vars}

    assert_definitions = []

    if total_asserts >= 5:
        num_dense = 2
        num_sparse = 2
    else:
        num_dense = total_asserts // 2
        num_sparse = total_asserts - num_dense
    num_random = total_asserts - num_dense - num_sparse

    dense_pool = all_vars[:4]
    sparse_pool = all_vars[4:]

    def create_assert(pool, term_count_range, magnitude):
        # 目標とする右辺の最大値
        MAX_RHS = 50

        # 係数の範囲
        if magnitude == "small":
            coeff_range = (-5, 5)
        else:
            coeff_range = (-50, 50)

        # 項数の決定
        num_terms = random.randint(*term_count_range)
        num_terms = min(num_terms, len(pool))
        num_terms = max(num_terms, 1)

        selected_vars = random.sample(pool, num_terms)

        # --- Rejection Sampling ---
        # lhs_value が ±MAX_RHS の範囲に収まる係数の組み合わせが見つかるまで試行する
        # これにより、後で移項しても定数が小さい式になる

        best_terms = []
        best_lhs_val = 0
        best_op = "="
        best_rhs = 0

        found = False

        # 無限ループ防止のため最大試行回数を設定
        for attempt in range(1000):
            terms = []
            lhs_value = 0

            # 係数をランダムに生成して計算
            for var in selected_vars:
                coeff = random.randint(*coeff_range)
                if coeff == 0:
                    coeff = 1
                terms.append(f"(* {coeff} {var})")
                lhs_value += coeff * target_solution[var]

            # ここで判定: lhs_value があまりに大きいと、どうRHSを設定しても定数が大きくなる
            # 許容範囲: 例えば [-40, 40] くらいなら、RHSを少しずらしても ±50 に収まる
            if abs(lhs_value) <= (MAX_RHS - 10):
                # 採用！

                # RHSと演算子の決定
                op = random.choice(["<=", ">=", "="])
                rhs = 0

                # SATを満たすような RHS を設定 (かつ RHS も ±50以内)
                if op == "=":
                    rhs = lhs_value
                elif op == "<=":
                    # lhs <= rhs. rhs は lhs 以上であればよい。
                    # lhs 〜 50 の間で選ぶ
                    lower = lhs_value
                    upper = MAX_RHS
                    if lower > upper:  # 万が一
                        rhs = lower
                    else:
                        rhs = random.randint(lower, upper)
                elif op == ">=":
                    # lhs >= rhs. rhs は lhs 以下であればよい。
                    # -50 〜 lhs の間で選ぶ
                    lower = -MAX_RHS
                    upper = lhs_value
                    if lower > upper:
                        rhs = upper
                    else:
                        rhs = random.randint(lower, upper)

                # 最終チェック: RHSが本当に範囲内か
                if abs(rhs) <= MAX_RHS:
                    best_terms = terms
                    best_lhs_val = lhs_value
                    best_op = op
                    best_rhs = rhs
                    found = True
                    break

        # もし1000回やっても見つからなかった場合（稀）
        # 強制的に係数を小さくして生成するか、あるいは最もマシなものを使う等の処理が必要だが
        # ここでは単純に「係数を小さくして」再トライする安全策を入れる
        if not found:
            # 救済措置: 係数を (-2, 2) にして再生成
            terms = []
            lhs_value = 0
            for var in selected_vars:
                coeff = random.randint(-2, 2)
                if coeff == 0:
                    coeff = 1
                terms.append(f"(* {coeff} {var})")
                lhs_value += coeff * target_solution[var]
            best_terms = terms
            best_op = "="
            best_rhs = lhs_value  # 等式なら必ず成立

        # 式の組み立て
        if len(best_terms) == 1:
            lhs_expr = best_terms[0]
        else:
            lhs_expr = f"(+ {' '.join(best_terms)})"

        return f"(assert ({best_op} {lhs_expr} {best_rhs}))"

    # --- グループ生成 ---
    for _ in range(num_dense):
        assert_definitions.append(
            create_assert(pool=dense_pool, term_count_range=(3, 4), magnitude="small")
        )

    for _ in range(num_sparse):
        assert_definitions.append(
            create_assert(pool=sparse_pool, term_count_range=(1, 3), magnitude="large")
        )

    for _ in range(num_random):
        assert_definitions.append(
            create_assert(pool=all_vars, term_count_range=(1, 8), magnitude="small")
        )

    random.shuffle(assert_definitions)

    lines.extend(assert_definitions)
    lines.append("(check-sat)")
    lines.append("(exit)")

    with open(filename, "w") as f:
        f.write("\n".join(lines))
    print(f"Generated SAT Case (Small RHS): {filename}")


# --- 実行 ---
OUTPUT_DIR = Path(__file__).parent.parent / "benchmarks" / "crafted"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

generate_mixed_smt2_sat(OUTPUT_DIR / "mixed_case_sat_01.smt2", total_asserts=5)
for i in range(2, 6):
    generate_mixed_smt2_sat(
        OUTPUT_DIR / f"mixed_case_sat_{i:02d}.smt2", total_asserts=5
    )

# --- 実行: ファイル生成 ---

# パターンA: 1つのファイルを作成
generate_mixed_smt2(OUTPUT_DIR / "mixed_case_01.smt2", total_asserts=5)

# パターンB: ベンチマーク用に複数作成する場合 (例: 2〜5番を作成)
for i in range(2, 6):
    generate_mixed_smt2(OUTPUT_DIR / f"mixed_case_{i:02d}.smt2", total_asserts=5)
