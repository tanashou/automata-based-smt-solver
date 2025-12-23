import argparse
import subprocess
import sys
from pathlib import Path
import os


def main():
    out_dir = "benchmark_result"

    # --- 1. 引数の定義 ---
    parser = argparse.ArgumentParser(
        description="Run solver benchmark and export to CSV."
    )

    # 必須: ベンチマーク対象のディレクトリ
    parser.add_argument("--dir", required=True, help="Path to the benchmark directory")

    # 任意: 最大時間 (デフォルト60秒)
    parser.add_argument("--time", default="60", help="Max time per test in seconds")

    # 保存先ディレクトリ (デフォルト: ./benchmark_result)
    parser.add_argument("--out-dir", default=out_dir, help="Directory to save results")

    # ファイル名 (デフォルト: result.json)
    parser.add_argument(
        "--name", default="result.json", help="Output filename (e.g., test1.json)"
    )

    args = parser.parse_args()

    # --- 2. パスの準備 ---
    target_dir = str(Path(args.dir).resolve())
    max_time = args.time

    # 保存先ディレクトリとファイル名を結合
    out_dir = Path(args.out_dir).resolve()
    json_path = out_dir / args.name
    csv_path = json_path.with_suffix(".csv")

    # 保存先ディレクトリがなければ自動作成
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Benchmark Start")
    print(f"   Target Dir: {target_dir}")
    print(f"   Max Time:   {max_time}s")
    print(f"   Output:     {json_path} -> {csv_path}")
    print("-" * 50)

    env = os.environ.copy()
    env["BENCHMARK_TIMEOUT"] = str(args.time)  # ここで値をセット

    try:
        # --- 3. Pytest 実行 ---
        cmd_test = [
            "pytest",
            "tests/test_solver_benchmark_cli.py",
            f"--benchmark-dir={target_dir}",
            f"--benchmark-max-time={max_time}",
            f"--benchmark-json={json_path}",  # 結合したパスを指定
            "-v",
        ]

        subprocess.run(cmd_test, check=True, env=env)

        # --- 4. CSV 変換 ---
        print("\n🔄 Converting to CSV...")
        cmd_convert = [
            "pytest-benchmark",
            "compare",
            str(json_path),
            f"--csv={csv_path}",
        ]
        subprocess.run(cmd_convert, check=True, env=env)

        print(f"\n✅ Success! Saved to directory: {out_dir}")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error: Benchmark failed. (Exit code: {e.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    main()
