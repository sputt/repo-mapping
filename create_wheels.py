import argparse
from functools import partial
from multiprocessing.pool import ThreadPool
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from textwrap import dedent


def create_pkg_wheel(output_dir: Path, idx: int) -> None:

    temp_dir = Path(tempfile.mkdtemp())

    setup_py = temp_dir / "setup.py"

    install_requires = []
    if idx > 0:
        install_requires = f'"repo-mapping-pkg{idx-1}"'
    setup_py.write_text(
        dedent(
            f"""
from setuptools import setup
setup(
    name = "repo-mapping-pkg{idx}",
    version = "1.0",
    install_requires = [{install_requires}],
    packages = ["pkg"],
)
"""
        ),
        encoding="utf-8",
    )
    source_file = temp_dir / "pkg" / "__init__.py"
    source_file.parent.mkdir(parents=True)

    source_file.touch()

    subprocess.run(
        [
            sys.executable,
            "setup.py",
            "bdist_wheel",
        ],
        cwd=temp_dir,
    )
    shutil.copy(next(temp_dir.joinpath("dist").iterdir()), output_dir)
    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    workspace_dir = Path(os.environ["BUILD_WORKSPACE_DIRECTORY"])
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--output_dir", type=Path, default=workspace_dir)

    parsed_args = parser.parse_args()

    all_pkgs = []
    with ThreadPool() as pool:
        list(
            pool.imap_unordered(
                partial(create_pkg_wheel, parsed_args.output_dir),
                range(parsed_args.count),
            )
        )

    with workspace_dir.joinpath("test_requirements.txt").open(
        "w", encoding="utf-8"
    ) as output:
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "req_compile",
                "--hashes",
                "--find-links",
                str(parsed_args.output_dir),
            ],
            stdout=output,
            stdin=subprocess.PIPE,
            text=True,
            cwd=workspace_dir,
        )
        proc.communicate("\n".join(f"repo-mapping-pkg{idx}" for idx in range(parsed_args.count)))
        proc.wait()
