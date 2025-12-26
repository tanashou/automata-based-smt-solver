import pandas as pd
import json
import sys
from pathlib import Path

# 引数チェック
if len(sys.argv) < 2:
    print("Usage: python script_name.py <json input path>")
    sys.exit(1)

# 引数から入力パスを取得し、Pathオブジェクトにする
input_path = Path(sys.argv[1])

# 入力パスの拡張子を .csv に変更して出力パスを作成
# 例: benchmark_result/data.json -> benchmark_result/data.csv
output_path = input_path.with_suffix(".csv")

# JSONファイルの読み込み
try:
    with open(input_path, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"エラー: ファイルが見つかりません: {input_path}")
    sys.exit(1)

# データをフラットなテーブルに変換
if "benchmarks" not in data:
    print("エラー: JSON内に 'benchmarks' キーが見つかりません")
    sys.exit(1)

df = pd.json_normalize(data["benchmarks"])

# 'param' を 'filename' にリネーム
df.rename(columns={"param": "filename"}, inplace=True)

# 削除したいカラムのリスト
columns_to_drop = {
    "group",
    "name",
    "fullname",
    "params.benchmark_file",
    "options.disable_gc",
    "options.timer",
    "options.warmup",
}

# カラムが存在する場合のみ削除
df.drop(columns=[c for c in columns_to_drop if c in df.columns], inplace=True)

# カラムの並べ替え（filenameを先頭に）
cols = df.columns.tolist()
if "filename" in cols:
    cols.insert(0, cols.pop(cols.index("filename")))
    df = df[cols]

# カラム名をきれいにする（extra_info. や stats. を削除）
new_columns = []
for c in df.columns:
    # filenameはそのまま、それ以外はプレフィックスを削除
    if c == "filename":
        new_columns.append(c)
    else:
        name = c.replace("extra_info.", "").replace("stats.", "")
        new_columns.append(name)

df.columns = new_columns

# CSV出力
df.to_csv(output_path, index=False)
print(f"Completed: {output_path}")
