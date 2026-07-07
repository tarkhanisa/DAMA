from __future__ import annotations

import string
from dataclasses import dataclass
from typing import Any, ClassVar


class PromptServiceError(RuntimeError):
    """Base exception for prompt service failures."""


class InvalidPromptTemplateError(PromptServiceError):
    """Raised when a prompt template is invalid."""


class MissingPromptVariableError(PromptServiceError):
    """Raised when a required prompt variable is missing."""


@dataclass(frozen=True, slots=True)
class PromptRenderResult:
    """Rendered prompt result."""

    template: str
    variables: dict[str, Any]
    rendered_prompt: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "template": self.template,
            "variables": self.variables,
            "rendered_prompt": self.rendered_prompt,
        }


class SafePromptFormatter(string.Formatter):
    """
    Strict prompt formatter.

    It rejects positional placeholders and requires named variables.
    Example allowed:
        {topic}

    Example rejected:
        {}
        {0}
    """

    def get_value(
        self,
        key: int | str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        if isinstance(key, int):
            raise InvalidPromptTemplateError(
                "Positional prompt placeholders are not supported. Use named placeholders like {topic}."
            )

        if key not in kwargs:
            raise MissingPromptVariableError(f"Missing prompt variable: {key}")

        return kwargs[key]


class PromptService:
    """Service layer for validating and rendering prompt templates."""

    FORMATTER: ClassVar[SafePromptFormatter] = SafePromptFormatter()

    @classmethod
    def extract_variables(cls, template: str) -> list[str]:
        """
        Extract named variables from a prompt template.

        Example:
            "Write about {topic} in a {tone} tone"
            -> ["topic", "tone"]
        """
        normalized_template = cls._normalize_template(template)

        variables: list[str] = []

        try:
            parsed_template = cls.FORMATTER.parse(normalized_template)
        except ValueError as exc:
            raise InvalidPromptTemplateError(str(exc)) from exc

        for _, field_name, _, _ in parsed_template:
            if field_name is None:
                continue

            if not field_name:
                raise InvalidPromptTemplateError(
                    "Empty prompt placeholders are not supported. Use named placeholders like {topic}."
                )

            root_field_name = field_name.split(".", maxsplit=1)[0].split("[", maxsplit=1)[0]

            if root_field_name.isdigit():
                raise InvalidPromptTemplateError(
                    "Numeric prompt placeholders are not supported. Use named placeholders like {topic}."
                )

            if root_field_name not in variables:
                variables.append(root_field_name)

        return variables

    @classmethod
    def render(
        cls,
        *,
        template: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Render a prompt template with strict validation.

        This method does not invent missing values.
        Missing variables raise MissingPromptVariableError.
        """
        normalized_template = cls._normalize_template(template)
        normalized_variables = cls._normalize_variables(variables or {})

        required_variables = cls.extract_variables(normalized_template)
        missing_variables = [
            variable for variable in required_variables
            if variable not in normalized_variables
        ]

        if missing_variables:
            raise MissingPromptVariableError(
                "Missing prompt variable(s): " + ", ".join(missing_variables)
            )

        try:
            rendered_prompt = cls.FORMATTER.format(
                normalized_template,
                **normalized_variables,
            )
        except PromptServiceError:
            raise
        except ValueError as exc:
            raise InvalidPromptTemplateError(str(exc)) from exc

        result = PromptRenderResult(
            template=normalized_template,
            variables=normalized_variables,
            rendered_prompt=rendered_prompt,
        )

        return result.to_dict()

    @classmethod
    def render_to_string(
        cls,
        *,
        template: str,
        variables: dict[str, Any] | None = None,
    ) -> str:
        """Render a prompt template and return only the final prompt string."""
        result = cls.render(template=template, variables=variables)
        return str(result["rendered_prompt"])

    @classmethod
    def validate_template(cls, template: str) -> bool:
        """Validate a prompt template and return True when it is valid."""
        cls.extract_variables(template)
        return True

    @staticmethod
    def _normalize_template(template: str) -> str:
        normalized_template = template.strip()

        if not normalized_template:
            raise InvalidPromptTemplateError("Prompt template cannot be empty.")

        return normalized_template

    @staticmethod
    def _normalize_variables(variables: dict[str, Any]) -> dict[str, Any]:
        normalized_variables: dict[str, Any] = {}

        for key, value in variables.items():
            normalized_key = str(key).strip()

            if not normalized_key:
                raise InvalidPromptTemplateError("Prompt variable names cannot be empty.")

            normalized_variables[normalized_key] = value

        return normalized_variables
