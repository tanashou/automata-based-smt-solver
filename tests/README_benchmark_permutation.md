# Intersect_all 順列ベンチマークの使い方

このドキュメントでは、`test_intersect_all_permutation_benchmark.py`を使って、
`intersect_all`の順序依存性を測定する方法を説明します。

## 設定

### MAX_AUTOMATA 定数

テストファイル内の`MAX_AUTOMATA`定数で、テストするオートマトンの最大数を制御します。

```python
# test_intersect_all_permutation_benchmark.py 内
MAX_AUTOMATA = 10  # この値を変更してください
```

オートマトンの数 `n` に対して、順列の数は `n!` となります:
- 3個: 6通り
- 4個: 24通り
- 5個: 120通り
- 6個: 720通り
- 7個: 5,040通り（デフォルトのMAX_AUTOMATA=10で実行可能）
- 8個: 40,320通り

## 基本的な使い方

### 1. 全順列を一度に実行して統計を取る（推奨）

```bash
pytest tests/test_intersect_all_permutation_benchmark.py::test_single_intersect_all_benchmark_all_orders --benchmark-only
```

このテストは、全ての順列を実行し、以下の統計情報を出力します:
- `num_orders_tested`: テストした順列の数
- `mean_memory_mb`: 平均メモリ使用量
- `median_memory_mb`: メモリ使用量の中央値
- `max_memory_mb`: 最大メモリ使用量
- `min_memory_mb`: 最小メモリ使用量
- `num_automata`: オートマトンの数
- `result_empty`: 結果が空かどうか

### 2. 個別の順列ごとにベンチマークを取る

```bash
pytest tests/test_intersect_all_permutation_benchmark.py::TestIntersectAllPermutationBenchmark::test_intersect_all_permutation --benchmark-only
```

このテストは、各順列を個別のベンチマークケースとして実行します。
各ケースには以下の情報が含まれます:
- `order_pattern`: 実行した順序パターン（例: "0-1-2-3-4-5-6"）
- `num_automata`: オートマトンの数
- `peak_memory_mb`: ピークメモリ使用量
- `result_empty`: 結果が空かどうか

## カスタマイズ

### テスト対象のSMT2を変更する

ファイル内の`SAMPLE_SMT2`変数を編集して、テストしたいSMT2テキストを設定します:

```python
# test_intersect_all_permutation_benchmark.py 内
SAMPLE_SMT2 = """
(set-logic QF_LIA)
(declare-fun x () Int)
(declare-fun y () Int)
(assert (and
    (<= (+ x y) 10)
    (>= x 0)
    (>= y 0)
))
(check-sat)
"""
```

### オートマトン数の上限を変更する

より多くのオートマトンをテストしたい場合は、`MAX_AUTOMATA`を増やします:

```python
MAX_AUTOMATA = 15  # 例: 15個まで許可
```

**注意**: オートマトンの数が増えると、実行時間が急激に増加します。

## 注意事項

### テスト実行時間

オートマトンの数による実行時間の目安:
- 3個: 6通り（数秒）
- 4個: 24通り（数秒）
- 5個: 120通り（数十秒）
- 6個: 720通り（数分）
- 7個: 5,040通り（10分以上）
- 8個: 40,320通り（1時間以上）

### 結果の確認

ベンチマーク結果は、以下のオプションで詳細に確認できます:

```bash
# すべての詳細情報を表示
pytest ... --benchmark-only -rA

# 順序パターンでグループ化
pytest ... --benchmark-only --benchmark-group-by=param:order_pattern

# 結果をJSONで保存
pytest ... --benchmark-only --benchmark-json=output.json

# 結果を比較
pytest ... --benchmark-only --benchmark-compare=output.json
```

### CSV出力

結果をCSV形式で保存するには、以下のようにします:

```bash
pytest tests/test_intersect_all_permutation_benchmark.py::test_single_intersect_all_benchmark_all_orders \
  --benchmark-only \
  --benchmark-json=benchmark_results.json

# JSONをCSVに変換（別途スクリプトが必要）
python -c "
import json
import csv

with open('benchmark_results.json') as f:
    data = json.load(f)

with open('benchmark_results.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Name', 'Min', 'Max', 'Mean', 'Median', 'StdDev', 'Rounds', 'Extra Info'])
    for benchmark in data['benchmarks']:
        extra = benchmark.get('extra_info', {})
        writer.writerow([
            benchmark['name'],
            benchmark['stats']['min'],
            benchmark['stats']['max'],
            benchmark['stats']['mean'],
            benchmark['stats']['median'],
            benchmark['stats']['stddev'],
            benchmark['stats']['rounds'],
            str(extra)
        ])
"
```

## 実行例

### 7個のオートマトンのケース

デフォルトの`SAMPLE_SMT2`には7個のアサーションがあり、7! = 5,040通りの順列をテストします:

```bash
# 全順列の統計を取得（約10-15分）
pytest tests/test_intersect_all_permutation_benchmark.py::test_single_intersect_all_benchmark_all_orders --benchmark-only

# 詳細な出力を確認
pytest tests/test_intersect_all_permutation_benchmark.py::test_single_intersect_all_benchmark_all_orders --benchmark-only -rA
```

結果には、最も速い順序パターンと最も遅い順序パターンのメモリ使用量の差が表示されます。
