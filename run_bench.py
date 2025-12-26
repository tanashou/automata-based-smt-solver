import argparse
import subprocess
import sys
from pathlib import Path
import os
from datetime import datetime
import json
from collections import Counter


def summarize_results(json_path):
    if not Path(json_path).exists():
        print(f"\n⚠️ Warning: JSON file not found at {json_path}")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    stats = Counter()

    # JSONからステータスを集計
    for bench in data.get("benchmarks", []):
        # extra_info がない場合に備えて .get を使用
        extra = bench.get("extra_info", {})
        status = extra.get("status", "unknown")
        stats[status] += 1

    total = sum(stats.values())

    print("\n" + "=" * 20 + " SUMMARY " + "=" * 20)
    print(f"Total Tests: {total}")

    # Success (緑)
    print(f"\033[92mSuccess:      {stats['success']}\033[0m")

    # Wrong Answer (赤 + 太字)
    print(f"\033[91;1mWrong Answer: {stats['wrong_answer']}\033[0m")

    # Memout (黄色)
    print(f"\033[93mMemout:       {stats['memout']}\033[0m")

    # Timeout (黄色)
    print(f"\033[93mTimeout:      {stats['timeout']}\033[0m")

    # Unknown (その他)
    if stats["unknown"] > 0:
        print(f"Unknown:      {stats['unknown']}")

    print("=" * 49 + "\n")


def main():
    # 固定の出力先ディレクトリ名
    DEFAULT_OUT_DIR = "benchmark_result"

    # --- 1. 引数の定義 ---
    parser = argparse.ArgumentParser(
        description="Run solver benchmark and export to CSV."
    )

    # 必須: ベンチマーク対象のディレクトリ
    parser.add_argument("--dir", required=True, help="Path to the benchmark directory")

    # 任意: 最大時間 (デフォルト60秒)
    parser.add_argument("--time", default="60", help="Max time per test in seconds")

    args = parser.parse_args()

    # --- 2. パスの準備 ---
    target_dir_path = Path(args.dir).resolve()
    target_dir_str = str(target_dir_path)
    max_time = args.time

    # 保存先ディレクトリのパスを確定
    out_dir_path = Path(DEFAULT_OUT_DIR).resolve()

    # 保存先ディレクトリ作成
    out_dir_path.mkdir(parents=True, exist_ok=True)

    # --- ファイル名の決定ロジック (常に日時付き) ---
    # ディレクトリ名からプレフィックスを作成 (例: ./benchmarks/LIA/tptp/ → LIA_tptp)
    parts = target_dir_path.parts
    if len(parts) >= 2:
        name_parts = parts[-2:]
    else:
        name_parts = parts[-1:]

    base_prefix = "_".join(name_parts)

    # 現在の日時を取得 (例: 20241025_143005)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 結合: LIA_tptp_result_20241025_143005.json
    json_name = f"{base_prefix}_result_{timestamp}.json"

    # パスの確定
    json_path = out_dir_path / json_name
    csv_path = json_path.with_suffix(".csv")

    print(f"🚀 Benchmark Start")
    print(f"   Target Dir: {target_dir_str}")
    print(f"   Max Time:   {max_time}s")
    print(f"   Output:     {json_path} -> {csv_path}")
    print("-" * 50)

    env = os.environ.copy()
    env["BENCHMARK_TIMEOUT"] = str(args.time)

    try:
        # --- 3. Pytest 実行 ---
        cmd_test = [
            "pytest",
            "tests/test_solver_benchmark_cli.py",
            f"--benchmark-dir={target_dir_str}",
            f"--benchmark-max-time={max_time}",
            f"--benchmark-json={json_path}",
            "-v",
        ]

        subprocess.run(cmd_test, check=True, env=env)

        summarize_results(json_path)

        # --- 4. CSV 変換 ---
        print("\n🔄 Converting to CSV...")
        cmd_convert = [
            "python",
            "./scripts/pytest_benchmark_json_to_csv.py",
            str(json_path),
        ]
        subprocess.run(cmd_convert, check=True, env=env)

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error: Benchmark failed. (Exit code: {e.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    main()
