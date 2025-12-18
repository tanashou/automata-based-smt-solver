#!/usr/bin/env python3
"""
リストファイル（.txt）に載っていない .smt2 ファイルを削除するスクリプト。
- まず create_test_lists_by_dir.py でリストを生成しておくこと。
- LIA, QF_LIA どちらにも対応。
- 削除前に dry-run（削除予定ファイルの一覧表示）モードあり。
"""

import os
from pathlib import Path
import argparse

BENCHMARK_BASE_DIR = Path(__file__).parent.parent / "benchmarks"
PATHS_BASE_DIR = BENCHMARK_BASE_DIR / "paths"


def collect_valid_files_from_txt(txt_dir: Path) -> set[str]:
    """paths ディレクトリ配下の全 .txt から有効なファイルパスを集める"""
    valid = set()
    for txt_file in txt_dir.rglob("*.txt"):
        with txt_file.open("r", encoding="utf-8") as f:
            for line in f:
                path = line.strip()
                if path:
                    valid.add(path)
    return valid


def find_all_smt2_files(base_dir: Path) -> list[Path]:
    """base_dir 配下の全 .smt2 ファイルを絶対パスで集める"""
    return list(base_dir.rglob("*.smt2"))


def main():
    parser = argparse.ArgumentParser(description="リスト外の .smt2 ファイルを削除")
    parser.add_argument(
        "--category", choices=["LIA", "QF_LIA"], required=True, help="対象カテゴリ"
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="本当に削除を実行する（指定しないとdry-run）",
    )
    args = parser.parse_args()

    base_dir = BENCHMARK_BASE_DIR / args.category
    txt_dir = PATHS_BASE_DIR / args.category

    valid_relpaths = collect_valid_files_from_txt(txt_dir)
    all_files = find_all_smt2_files(base_dir)

    # 削除対象: valid_relpaths に含まれないもの
    to_delete = []
    for f in all_files:
        # txtファイルのリストは output_dir からの相対パスなので合わせる
        rel = os.path.relpath(f, start=txt_dir).replace("\\", "/")
        if rel not in valid_relpaths:
            to_delete.append(f)

    if not to_delete:
        print("削除対象はありません。")
        # 空ディレクトリ削除も実施
        if args.delete:
            remove_empty_dirs(base_dir)
        return

    print(f"削除対象 {len(to_delete)} 件:")
    for f in to_delete:
        print(f"  {f}")

    if args.delete:
        for f in to_delete:
            try:
                f.unlink()
            except Exception as e:
                print(f"  削除失敗: {f} ({e})")
        print("削除を実行しました。")
        # 削除後に空ディレクトリも削除
        remove_empty_dirs(base_dir)
    else:
        print("--delete を付けると実際に削除します（今はdry-runです）")


def remove_empty_dirs(root: Path):
    """root配下の空ディレクトリを再帰的に削除"""
    # 深い階層から順に削除するため、reverse=True
    dirs = [d for d in root.rglob("*") if d.is_dir()]
    for d in sorted(dirs, key=lambda x: len(str(x)), reverse=True):
        try:
            if not any(d.iterdir()):
                d.rmdir()
                print(f"空ディレクトリ削除: {d}")
        except Exception as e:
            print(f"  空ディレクトリ削除失敗: {d} ({e})")


if __name__ == "__main__":
    main()
