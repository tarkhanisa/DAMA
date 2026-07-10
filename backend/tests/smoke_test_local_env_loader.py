from pathlib import Path
import os
import tempfile

from src.core.env_loader import load_env_file, parse_env_line


def main() -> None:
    assert parse_env_line("DAMA_TEST_KEY=value") == ("DAMA_TEST_KEY", "value")
    assert parse_env_line("export DAMA_TEST_KEY='quoted value'") == (
        "DAMA_TEST_KEY",
        "quoted value",
    )
    assert parse_env_line("# comment") is None

    key = "DAMA_LOCAL_ENV_LOADER_SMOKE"
    os.environ.pop(key, None)

    with tempfile.TemporaryDirectory() as directory:
        env_path = Path(directory) / ".env.local"
        env_path.write_text(
            f"""
# smoke env
{key}=loaded-from-file
DAMA_QUOTED_VALUE="hello world"
""".strip()
            + "\n",
            encoding="utf-8",
        )

        loaded = load_env_file(env_path)

    assert loaded[key] == "loaded-from-file"
    assert os.getenv(key) == "loaded-from-file"
    assert os.getenv("DAMA_QUOTED_VALUE") == "hello world"

    print("Local env loader smoke test passed.")


if __name__ == "__main__":
    main()
