import os
from pathlib import Path

# --- 設定項目 ---

# 1. テストファイル群の親ディレクトリ
#    LIAとQF_LIAの両方を処理します
BENCHMARK_BASE_DIR = Path(__file__).parent.parent / "benchmarks"

# 2. 生成したテキストファイルの出力先ディレクトリのベース
PATHS_BASE_DIR = Path(__file__).parent.parent / "benchmarks" / "paths"

# 3. ファイルサイズの最大値（これより小さいものを対象とする）  # noqa: RUF003
MAX_SIZE_BYTES = 5 * 1024

# --- ここからスクリプト本体 ---


def process_subdirectory(subdir: Path, output_dir: Path, skip_size_check: bool = False):  # noqa: ANN201
    """一つのサブディレクトリを処理し、対応する.txtファイルを生成する関数"""  # noqa: D400, D415
    print(f"\n処理中のディレクトリ: {subdir.name}...")  # noqa: T201

    valid_file_paths = []

    # このサブディレクトリ内を再帰的に検索
    for file_path in subdir.rglob("*.smt2"):
        # ファイルサイズが上限未満かチェック（skip_size_checkがTrueの場合はスキップ）
        if skip_size_check or file_path.stat().st_size < MAX_SIZE_BYTES:
            # 出力ディレクトリからの相対パスを計算
            relative_path = os.path.relpath(file_path, start=output_dir)
            valid_file_paths.append(relative_path.replace("\\", "/"))

    # 条件に合うファイルがなければ、何もせず終了
    if not valid_file_paths:
        print("  -> 条件に合うファイルが見つかりませんでした。スキップします。")  # noqa: T201
        return

    # 見つかったパスをソートして一貫性を保つ
    valid_file_paths.sort()

    # 出力ファイル名を決定 (例: prime-cone -> prime-cone.txt)
    output_file = output_dir / f"{subdir.name}.txt"

    # 見つかったパスをファイルに書き込む
    with output_file.open("w", encoding="utf-8") as f:
        f.write("\n".join(valid_file_paths))
        f.write("\n")  # ファイルの最後に改行を追加

    print(  # noqa: T201
        f"  -> 完了！ {len(valid_file_paths)} 件のパスを '{output_file}' に書き込みました。"  # noqa: E501, RUF001
    )


def process_benchmark_category(category_name: str):  # noqa: ANN201
    """LIAまたはQF_LIAのカテゴリを処理する関数"""  # noqa: D400, D415
    search_dir = BENCHMARK_BASE_DIR / category_name
    output_dir = PATHS_BASE_DIR / category_name

    if not search_dir.is_dir():
        print(f"警告: 検索ディレクトリが見つかりません: {search_dir}")  # noqa: T201
        return

    # 出力先ディレクトリがなければ作成
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n=== {category_name} の処理を開始 ===")  # noqa: T201
    print(f"テキストファイルは '{output_dir}' に保存されます。")  # noqa: T201

    # LIAの場合はファイルサイズチェックをスキップ
    skip_size_check = category_name == "LIA"

    # search_dir 直下の各アイテムをループ
    for item in search_dir.iterdir():
        # ディレクトリであれば、処理を実行
        if item.is_dir():
            process_subdirectory(item, output_dir, skip_size_check=skip_size_check)


def main():  # noqa: ANN201
    # LIAとQF_LIAの両方を処理
    for category in ["LIA", "QF_LIA"]:
        process_benchmark_category(category)


if __name__ == "__main__":
    main()
    print("\n=== すべてのディレクトリの処理が完了しました ===")  # noqa: T201
