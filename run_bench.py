import argparse
import subprocess
import sys
from pathlib import Path
import os
from datetime import datetime
import json
from collections import Counter
import psutil


def parse_memory_str(mem_str):
    """'6GB', '512MB' などの文字列をバイト数(int)に変換"""
    if not mem_str:
        return None

    units = {"GB": 1024**3, "MB": 1024**2, "KB": 1024}
    upper_str = mem_str.upper()

    for unit, factor in units.items():
        if upper_str.endswith(unit):
            try:
                val = float(upper_str.replace(unit, ""))
                return int(val * factor)
            except ValueError:
                pass

    try:
        return int(mem_str)
    except ValueError:
        print(
            f"Error: Invalid memory format '{mem_str}'. Use format like '8GB' or '4096MB'."
        )
        sys.exit(1)


def summarize_results(json_path):
    if not Path(json_path).exists():
        print(f"\n⚠️ Warning: JSON file not found at {json_path}")
        return

    with open(json_path, "r") as f:
        data = json.load(f)

    stats = Counter()
    status_files = {"wrong_answer": [], "memout": [], "timeout": [], "unknown": []}

    # JSONからステータスを集計
    for bench in data.get("benchmarks", []):
        # extra_info がない場合に備えて .get を使用
        extra = bench.get("extra_info", {})
        status = extra.get("status", "unknown")
        stats[status] += 1

        # success以外のステータスの場合、ファイル名を記録
        param = bench.get("param", "unknown")
        if status != "success" and status in status_files:
            status_files[status].append(param)

    total = sum(stats.values())

    print("\n" + "=" * 20 + " SUMMARY " + "=" * 20)
    print(f"Total Tests: {total}")

    # Success (緑)
    print(f"\033[92mSuccess:      {stats['success']}\033[0m")

    # Wrong Answer (赤 + 太字)
    print(f"\033[91;1mWrong Answer: {stats['wrong_answer']}\033[0m")
    for file in status_files["wrong_answer"]:
        print(f"  - {file}")

    # Memout (黄色)
    print(f"\033[93mMemout:       {stats['memout']}\033[0m")
    for file in status_files["memout"]:
        print(f"  - {file}")

    # Timeout (黄色)
    print(f"\033[93mTimeout:      {stats['timeout']}\033[0m")
    for file in status_files["timeout"]:
        print(f"  - {file}")

    # Unknown (その他)
    if stats["unknown"] > 0:
        print(f"Unknown:      {stats['unknown']}")
        for file in status_files["unknown"]:
            print(f"  - {file}")

    print("=" * 49 + "\n")


def main():
    DEFAULT_OUT_DIR = "benchmark_result"

    parser = argparse.ArgumentParser(
        description="Run solver benchmark and export to CSV."
    )

    parser.add_argument("--dir", required=True, help="Path to the benchmark directory")
    parser.add_argument("--time", default="60", help="Max time per test in seconds")

    # --- 追加: メモリ制限オプション ---
    parser.add_argument(
        "--mem-limit",
        help="Memory limit (e.g., '8GB', '4000MB'). Default: Auto (80% of RAM).",
    )

    args = parser.parse_args()

    # --- メモリ制限値の計算 ---
    if args.mem_limit:
        mem_limit_bytes = parse_memory_str(args.mem_limit)
        if mem_limit_bytes is None:
            print("Error: Failed to parse memory limit.")
            sys.exit(1)
        mem_display = f"{args.mem_limit} ({mem_limit_bytes / (1024**3):.2f} GB)"
    else:
        # 表示用: 自動設定される値を計算
        mem_limit_bytes = int(psutil.virtual_memory().total * 0.8)
        mem_display = f"Auto ({mem_limit_bytes / (1024**3):.2f} GB)"

    target_dir_path = Path(args.dir).resolve()
    target_dir_str = str(target_dir_path)
    max_time = args.time

    out_dir_path = Path(DEFAULT_OUT_DIR).resolve()
    out_dir_path.mkdir(parents=True, exist_ok=True)

    parts = target_dir_path.parts
    if len(parts) >= 2:
        name_parts = parts[-2:]
    else:
        name_parts = parts[-1:]
    base_prefix = "_".join(name_parts)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_name = f"{base_prefix}_result_{timestamp}.json"
    json_path = out_dir_path / json_name
    csv_path = json_path.with_suffix(".csv")

    print(f"🚀 Benchmark Start")
    print(f"   Target Dir: {target_dir_str}")
    print(f"   Max Time:   {max_time}s")
    print(f"   Mem Limit:  {mem_display}")  # 追加
    print(f"   Output:     {json_path} -> {csv_path}")
    print("-" * 50)

    # 現在の環境変数をコピーし、タイムアウトとメモリ制限をセット
    env = os.environ.copy()
    env["BENCHMARK_TIMEOUT"] = str(args.time)

    # 計算済みのバイト数を文字列として環境変数にセット
    if args.mem_limit:
        env["BENCHMARK_MEM_LIMIT"] = str(mem_limit_bytes)

    try:
        cmd_test = [
            "pytest",
            "tests/test_solver_benchmark_cli.py",
            f"--benchmark-dir={target_dir_str}",
            f"--benchmark-max-time={max_time}",
            f"--benchmark-json={json_path}",
            "-v",
        ]

        # env=env を渡すことで、子プロセス(pytest)に環境変数が引き継がれる
        subprocess.run(cmd_test, check=True, env=env)

        summarize_results(json_path)

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
