# Intersect_all トーナメント構造ベンチマークの使い方

このドキュメントでは、`test_intersect_all_permutation_benchmark.py`と`run_tournament_benchmark.py`を使って、
`intersect_all`のトーナメント構造（実行順序）による性能差を測定する方法を説明します。

## 概要

このベンチマークは、n個のオートマトンの交差演算において、全ての可能なトーナメント構造（順列×二分木構造）を試し、
最速/最遅の構造やメモリ使用量を比較します。

### トーナメント構造の数

オートマトンの数 `n` に対して、テストされる構造の数は **(n! × C(n-1)) / 2^(n-1)** となります:
- 3個: 3通り
- 4個: 15通り
- 5個: 105通り
- 6個: 945通り
- 7個: 10,395通り
- 8個: 135,135通り

※ C(n-1)はカタラン数（Catalan number）です
## 基本的な使い方

### 1. 特定のSMT2ファイルでベンチマークを実行（推奨）

```bash
python tests/run_tournament_benchmark.py benchmarks/QF_LIA/path/to/file.smt2
```

実行中は進捗が表示されます：
```
================================================================================
Starting benchmark: 10395 tournament structures for 7 automata
Source file: benchmarks/QF_LIA/prime-cone/prime_cone_sat_3.smt2
================================================================================
Progress: 1039/10395 (10.0%)
Progress: 2079/10395 (20.0%)
Progress: 3119/10395 (30.0%)
...
Progress: 10395/10395 (100.0%)
================================================================================
✓ Benchmark completed: prime_cone_sat_3
Results saved to: .benchmarks/tournament_structures/prime_cone_sat_3.csv
================================================================================
```

カスタム名を指定することもできます：
```bash
python tests/run_tournament_benchmark.py path/to/file.smt2 --name custom_name
```

### 2. 結果を解析

```bash
python scripts/analyze_benchmark_results.py prime_cone_sat_3
```

出力例：
```
================================================================================
BENCHMARK RESULTS ANALYSIS
================================================================================
Benchmark ID: prime_cone_sat_3
Number of automata: 7
Source file: benchmarks/QF_LIA/prime-cone/prime_cone_sat_3.smt2
Total tournament structures tested: 10395

================================================================================
TOP 10 FASTEST TOURNAMENT STRUCTURES
================================================================================
...

================================================================================
SUMMARY STATISTICS
================================================================================
Fastest structure:     ((2,(6,(0,1))),(4,(3,5)))
  Time:                0.010867 sec
  Memory:              0.00 MB

Slowest structure:     (1,(0,(4,(2,(3,(5,6))))))
  Time:                0.027903 sec
  Memory:              9.47 MB
...
```

### 3. pytestでベンチマークを実行（開発用）

```bash
pytest tests/test_intersect_all_permutation_benchmark.py::test_single_intersect_all_benchmark_all_structures --benchmark-only
```

このテストは、全てのトーナメント構造を実行し、以下の統計情報を出力します:
- `num_structures_tested`: テストしたトーナメント構造の数
- `mean_memory_mb`: 平均メモリ使用量
- `median_memory_mb`: メモリ使用量の中央値
- `max_memory_mb`: 最大メモリ使用量
- `min_memory_mb`: 最小メモリ使用量
- `fastest_structure` / `slowest_structure`: 最速/最遅の構造
- `lowest_memory_structure` / `highest_memory_structure`: 最小/最大メモリの構造

## メモリ測定について

このベンチマークは**ピークメモリ**を測定します：
- `tracemalloc`を使用して、処理中の最大メモリ使用量を正確に測定
- ガベージコレクションの影響を受けない
- 常に正の値（負の値は発生しない）

メモリ表示：
- 10 KB未満: KB単位で表示（例: `5.12 KB`）
- 10 KB以上: MB単位で表示（例: `2.45 MB`）

## カスタマイズ

### pytestで使用するSMT2を変更する

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

**注意**: オートマトンの数が増えると、実行時間が急激に増加します。7個を超える場合は数時間かかる可能性があります。

## 注意事項

### テスト実行時間

オートマトンの数によるトーナメント構造数と実行時間の目安:
- 3個: 3通り（数秒）
- 4個: 15通り（数秒）
- 5個: 105通り（数十秒）
- 6個: 945通り（数分）
- 7個: 10,395通り（30分〜数時間）
- 8個: 135,135通り（数時間〜1日）
- 9個以上: 非推奨（1日以上かかる可能性が高い）

### 進捗表示

ベンチマーク実行中は10%ごとに進捗が表示されます：
```
Progress: 1039/10395 (10.0%)
Progress: 2079/10395 (20.0%)
...
```

進捗を表示するには、`run_tournament_benchmark.py`を使用するか、
pytestで`-s`オプションを指定してください：
```bash
pytest tests/test_intersect_all_permutation_benchmark.py::test_single_intersect_all_benchmark_all_structures --benchmark-only -s
```

### CSV結果ファイル

ベンチマーク結果は自動的にCSV形式で保存されます：
- 保存先: `.benchmarks/tournament_structures/<benchmark_id>.csv`
- メタデータ: `.benchmarks/tournament_structures/<benchmark_id>_meta.json`

CSVファイルには各トーナメント構造ごとに以下が記録されます：
- `structure`: トーナメント構造のパターン（例: `((2,(6,(0,1))),(4,(3,5)))`）
- `time_sec`: 実行時間（秒）
- `memory_mb`: ピークメモリ使用量（MB）

### 利用可能なベンチマークの確認

```bash
# 実行済みベンチマーク一覧を表示
python scripts/analyze_benchmark_results.py

# 出力例:
# Available benchmarks:
#   - prime_cone_sat_2
#   - prime_cone_sat_3
#   - inline_abc123
```

## 実行例

### 1. 実際のSMT2ファイルでベンチマーク

```bash
# prime-coneベンチマークを実行（7個のオートマトン = 10,395通りのトーナメント構造）
python tests/run_tournament_benchmark.py benchmarks/QF_LIA/prime-cone/prime_cone_sat_3.smt2

# 結果を分析
python scripts/analyze_benchmark_results.py prime_cone_sat_3
```

### 2. 複数のファイルをバッチ実行

```bash
# 特定ディレクトリ内の全ファイルを実行
for file in benchmarks/QF_LIA/prime-cone/*.smt2; do
    echo "Running benchmark for: $file"
    python tests/run_tournament_benchmark.py "$file"
done

# 全結果を確認
for csv in .benchmarks/tournament_structures/*.csv; do
    id=$(basename "$csv" .csv)
    echo "=== $id ==="
    python scripts/analyze_benchmark_results.py "$id" | head -20
done
```

### 3. pytestでサンプルをテスト（開発用）

デフォルトの`SAMPLE_SMT2`には7個のアサーションがあり、10,395通りのトーナメント構造をテストします:

```bash
# 全構造の統計を取得（進捗表示あり）
pytest tests/test_intersect_all_permutation_benchmark.py::test_single_intersect_all_benchmark_all_structures --benchmark-only -s

# 詳細な出力を確認
pytest tests/test_intersect_all_permutation_benchmark.py::test_single_intersect_all_benchmark_all_structures --benchmark-only -rA
```

結果には、最も速い構造と最も遅い構造、メモリ使用量の差などが表示されます。
