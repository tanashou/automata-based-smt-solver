import os
from pathlib import Path

# --- 設定項目 ---

# 1. テストファイル群の親ディレクトリ
#    この中のサブディレクトリをそれぞれ処理します
BASE_SEARCH_DIR = Path("benchmarks/QF_LIA")

# 2. 生成したテキストファイルの出力先ディレクトリ
OUTPUT_DIR = Path("benchmarks/paths")

# 3. ファイルサイズの最大値（これより小さいものを対象とする）  # noqa: RUF003
MAX_SIZE_BYTES = 5 * 1024

# --- ここからスクリプト本体 ---


def process_subdirectory(subdir: Path):  # noqa: ANN201
    """一つのサブディレクトリを処理し、対応する.txtファイルを生成する関数"""  # noqa: D400, D415
    print(f"\n処理中のディレクトリ: {subdir.name}...")  # noqa: T201

    valid_file_paths = []

    # このサブディレクトリ内を再帰的に検索
    for file_path in subdir.rglob("*.smt2"):
        # ファイルサイズが上限未満かチェック
        if file_path.stat().st_size < MAX_SIZE_BYTES:
            # 出力ディレクトリからの相対パスを計算
            relative_path = os.path.relpath(file_path, start=OUTPUT_DIR)
            valid_file_paths.append(relative_path.replace("\\", "/"))

    # 条件に合うファイルがなければ、何もせず終了
    if not valid_file_paths:
        print("  -> 条件に合うファイルが見つかりませんでした。スキップします。")  # noqa: T201
        return

    # 見つかったパスをソートして一貫性を保つ
    valid_file_paths.sort()

    # 出力ファイル名を決定 (例: prime-cone -> prime-cone.txt)
    output_file = OUTPUT_DIR / f"{subdir.name}.txt"

    # 見つかったパスをファイルに書き込む
    with output_file.open("w", encoding="utf-8") as f:
        f.write("\n".join(valid_file_paths))
        f.write("\n")  # ファイルの最後に改行を追加

    print(  # noqa: T201
        f"  -> 完了！ {len(valid_file_paths)} 件のパスを '{output_file}' に書き込みました。"  # noqa: E501, RUF001
    )


def main():  # noqa: ANN201
    if not BASE_SEARCH_DIR.is_dir():
        print(f"エラー: 検索ディレクトリが見つかりません: {BASE_SEARCH_DIR}")  # noqa: T201
        return

    # 出力先ディレクトリがなければ作成
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"テキストファイルは '{OUTPUT_DIR}' に保存されます。")  # noqa: T201

    # BASE_SEARCH_DIR 直下の各アイテムをループ
    for item in BASE_SEARCH_DIR.iterdir():
        # ディレクトリであれば、処理を実行
        if item.is_dir():
            process_subdirectory(item)


if __name__ == "__main__":
    main()
    print("\nすべてのディレクトリの処理が完了しました。")  # noqa: T201
