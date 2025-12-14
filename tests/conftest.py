from pathlib import Path


def pytest_addoption(parser):
    parser.addoption(
        "--benchmark-dir",
        action="store",
        default=None,
        help="Root directory containing .smt2 files for benchmarking",
    )
    parser.addoption(
        "--benchmark-timeout",
        action="store",
        type=int,
        default=120,
        help="Timeout in seconds for each benchmark test (default: 120)",
    )


def pytest_generate_tests(metafunc):
    # テスト関数が "benchmark_file" 引数を持っている場合のみ動作
    if "benchmark_file" in metafunc.fixturenames:
        dir_option = metafunc.config.getoption("--benchmark-dir")
        smt2_files = []
        root_dir = None

        if dir_option:
            root_dir = Path(dir_option).resolve()
            if root_dir.exists():
                smt2_files = sorted(root_dir.rglob("*.smt2"))

        # ID生成関数
        def make_id(p: Path) -> str:
            if root_dir:
                try:
                    return str(p.relative_to(root_dir))
                except ValueError:
                    return p.name
            return p.name

        # オプションが無い場合でも空リストで呼ぶことでエラーを防ぐ
        metafunc.parametrize("benchmark_file", smt2_files, ids=make_id)
