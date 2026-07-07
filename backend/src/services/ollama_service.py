from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import ClassVar


class OllamaServiceError(RuntimeError):
    """Base exception for Ollama service failures."""


class OllamaNotInstalledError(OllamaServiceError):
    """Raised when the Ollama executable cannot be found."""


class OllamaCommandError(OllamaServiceError):
    """Raised when an Ollama CLI command fails."""

    def __init__(
        self,
        message: str,
        *,
        command: list[str],
        returncode: int | None = None,
        stderr: str | None = None,
    ) -> None:
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class OllamaModel:
    """A locally installed Ollama model parsed from `ollama list`."""

    name: str
    id: str | None
    size: str
    modified: str

    def to_dict(self) -> dict[str, str | None]:
        return {
            "name": self.name,
            "id": self.id,
            "size": self.size,
            "modified": self.modified,
        }


@dataclass(frozen=True, slots=True)
class OllamaGeneration:
    """A text generation result returned by Ollama."""

    model: str
    response: str

    def to_dict(self) -> dict[str, str]:
        return {
            "model": self.model,
            "response": self.response,
        }


class OllamaService:
    """Service layer for interacting with the local Ollama installation."""

    OLLAMA_COMMAND: ClassVar[str] = "ollama"

    DEFAULT_TIMEOUT_SECONDS: ClassVar[int] = 10
    LIST_TIMEOUT_SECONDS: ClassVar[int] = 15
    GENERATE_TIMEOUT_SECONDS: ClassVar[int] = 120

    VERSION_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9_.-]+)?"
    )

    ANSI_ESCAPE_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
    )

    CURRENT_LIST_ROW_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<name>\S+)\s+"
        r"(?P<model_id>\S+)\s+"
        r"(?P<size>\d+(?:\.\d+)?\s*(?:B|KB|MB|GB|TB|PB|KiB|MiB|GiB|TiB|PiB))\s+"
        r"(?P<modified>.+)$",
        re.IGNORECASE,
    )

    OLD_LIST_ROW_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<name>\S+)\s+"
        r"(?P<size>\d+(?:\.\d+)?\s*(?:B|KB|MB|GB|TB|PB|KiB|MiB|GiB|TiB|PiB))\s+"
        r"(?P<modified>.+)$",
        re.IGNORECASE,
    )

    @classmethod
    def is_installed(cls) -> bool:
        """
        Return True if Ollama is installed and callable.

        This checks both PATH discovery and actual command execution.
        """
        if shutil.which(cls.OLLAMA_COMMAND) is None:
            return False

        try:
            cls._run_ollama(["--version"], timeout=cls.DEFAULT_TIMEOUT_SECONDS)
        except OllamaServiceError:
            return False

        return True

    @classmethod
    def version(cls) -> str:
        """
        Return the installed Ollama version.

        Example raw output:
            ollama version is 0.23.0

        Returned value:
            0.23.0
        """
        output = cls._run_ollama(["--version"], timeout=cls.DEFAULT_TIMEOUT_SECONDS)

        match = cls.VERSION_RE.search(output)
        if match is None:
            return output.strip()

        return match.group(0)

    @classmethod
    def list_models(cls) -> list[dict[str, str | None]]:
        """
        Return locally available Ollama models.

        Uses the real `ollama list` command and parses its table output.
        Returns an empty list when Ollama has no local models installed.
        """
        output = cls._run_ollama(["list"], timeout=cls.LIST_TIMEOUT_SECONDS)
        models = cls._parse_list_output(output)

        return [model.to_dict() for model in models]

    @classmethod
    def generate(
        cls,
        *,
        model: str,
        prompt: str,
        timeout: int | None = None,
    ) -> dict[str, str]:
        """
        Generate text using a real local Ollama model.

        This method uses the real `ollama run <model> <prompt>` command.
        It does not return mock data and does not use placeholders.
        """
        normalized_model = model.strip()
        normalized_prompt = prompt.strip()

        if not normalized_model:
            raise ValueError("Model name cannot be empty.")

        if not normalized_prompt:
            raise ValueError("Prompt cannot be empty.")

        command_timeout = timeout or cls.GENERATE_TIMEOUT_SECONDS

        output = cls._run_ollama(
            ["run", normalized_model, normalized_prompt],
            timeout=command_timeout,
        )

        cleaned_output = cls._clean_output(output)

        generation = OllamaGeneration(
            model=normalized_model,
            response=cleaned_output,
        )

        return generation.to_dict()

    @classmethod
    def _run_ollama(cls, args: list[str], *, timeout: int) -> str:
        command = [cls.OLLAMA_COMMAND, *args]

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
                shell=False,
            )
        except FileNotFoundError as exc:
            raise OllamaNotInstalledError(
                "Ollama executable was not found. Make sure Ollama is installed and available in PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise OllamaCommandError(
                f"Ollama command timed out after {timeout} seconds.",
                command=command,
                returncode=None,
                stderr=str(exc),
            ) from exc

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()

        if completed.returncode != 0:
            raise OllamaCommandError(
                "Ollama command failed.",
                command=command,
                returncode=completed.returncode,
                stderr=stderr,
            )

        return stdout

    @classmethod
    def _parse_list_output(cls, output: str) -> list[OllamaModel]:
        """
        Parse `ollama list` output.

        Current expected format:

            NAME                ID              SIZE      MODIFIED
            llama3.2:latest     a80c4f17acd5    2.0 GB    6 weeks ago

        Also supports the older format without the ID column:

            NAME                SIZE      MODIFIED
            llama2:7b           3.8 GB    10 seconds ago
        """
        if not output.strip():
            return []

        models: list[OllamaModel] = []

        for raw_line in output.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            if cls._is_header_line(line):
                continue

            model = cls._parse_current_list_row(line)

            if model is None:
                model = cls._parse_old_list_row(line)

            if model is None:
                model = cls._parse_column_spaced_row(line)

            if model is None:
                raise OllamaServiceError(
                    f"Unable to parse `ollama list` output row: {line!r}"
                )

            models.append(model)

        return models

    @staticmethod
    def _is_header_line(line: str) -> bool:
        normalized = re.sub(r"\s+", " ", line.strip()).upper()
        return normalized.startswith("NAME ") and "MODIFIED" in normalized

    @classmethod
    def _parse_current_list_row(cls, line: str) -> OllamaModel | None:
        match = cls.CURRENT_LIST_ROW_RE.match(line)

        if match is None:
            return None

        return OllamaModel(
            name=match.group("name"),
            id=match.group("model_id"),
            size=cls._normalize_spaces(match.group("size")),
            modified=cls._normalize_spaces(match.group("modified")),
        )

    @classmethod
    def _parse_old_list_row(cls, line: str) -> OllamaModel | None:
        match = cls.OLD_LIST_ROW_RE.match(line)

        if match is None:
            return None

        return OllamaModel(
            name=match.group("name"),
            id=None,
            size=cls._normalize_spaces(match.group("size")),
            modified=cls._normalize_spaces(match.group("modified")),
        )

    @classmethod
    def _parse_column_spaced_row(cls, line: str) -> OllamaModel | None:
        """
        Fallback parser for table rows separated by two or more spaces.

        This intentionally does not invent missing values.
        If an ID column is missing, ID remains None.
        """
        columns = [column.strip() for column in re.split(r"\s{2,}", line) if column.strip()]

        if len(columns) >= 4:
            return OllamaModel(
                name=columns[0],
                id=columns[1],
                size=cls._normalize_spaces(columns[2]),
                modified=cls._normalize_spaces(" ".join(columns[3:])),
            )

        if len(columns) == 3:
            return OllamaModel(
                name=columns[0],
                id=None,
                size=cls._normalize_spaces(columns[1]),
                modified=cls._normalize_spaces(columns[2]),
            )

        return None

    @classmethod
    def _clean_output(cls, value: str) -> str:
        without_ansi = cls.ANSI_ESCAPE_RE.sub("", value)
        return without_ansi.strip()

    @staticmethod
    def _normalize_spaces(value: str) -> str:
        return re.sub(r"\s+", " ", value.strip())
