from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class WorkflowServiceError(RuntimeError):
    pass


class InvalidWorkflowRequestError(WorkflowServiceError):
    pass


@dataclass(frozen=True, slots=True)
class PlannedOutput:
    order: int
    project_id: str
    content_type: str
    title: str
    workflow_stage: str
    recommended_status: str
    generation_topic: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "order": self.order,
            "project_id": self.project_id,
            "content_type": self.content_type,
            "title": self.title,
            "workflow_stage": self.workflow_stage,
            "recommended_status": self.recommended_status,
            "generation_topic": self.generation_topic,
        }


class WorkflowService:
    @classmethod
    def build_output_plan(
        cls,
        *,
        project: dict[str, Any],
        topic: str | None = None,
    ) -> list[dict[str, Any]]:
        project_id = cls._required(project.get("id"), "Project ID")
        project_name = cls._required(project.get("name"), "Project name")
        content_types = project.get("content_types") or []

        if not content_types:
            raise InvalidWorkflowRequestError("Project has no content types.")

        generation_topic = topic.strip() if topic and topic.strip() else project_name

        planned_outputs: list[PlannedOutput] = []

        for index, content_type in enumerate(content_types, start=1):
            normalized_content_type = cls._required(str(content_type), "Content type")
            title = f"{project_name} - {cls._humanize_content_type(normalized_content_type)}"

            planned_outputs.append(
                PlannedOutput(
                    order=index,
                    project_id=project_id,
                    content_type=normalized_content_type,
                    title=title,
                    workflow_stage="draft",
                    recommended_status="draft",
                    generation_topic=generation_topic,
                )
            )

        return [planned_output.to_dict() for planned_output in planned_outputs]

    @classmethod
    def build_batch_generation_plan(
        cls,
        *,
        project: dict[str, Any],
        topic: str | None = None,
        content_types: list[str] | None = None,
        max_outputs: int | None = None,
    ) -> list[dict[str, Any]]:
        plan = cls.build_output_plan(project=project, topic=topic)

        if content_types:
            requested_types = {
                cls._normalize_content_type(content_type)
                for content_type in content_types
            }

            plan = [
                item
                for item in plan
                if item["content_type"] in requested_types
            ]

        if not plan:
            raise InvalidWorkflowRequestError("No planned outputs matched the request.")

        if max_outputs is not None:
            if max_outputs < 1:
                raise InvalidWorkflowRequestError("max_outputs must be greater than zero.")

            plan = plan[:max_outputs]

        return plan

    @classmethod
    def build_draft_asset_payloads(
        cls,
        *,
        project: dict[str, Any],
        topic: str | None = None,
        title_prefix: str | None = None,
    ) -> list[dict[str, Any]]:
        plan = cls.build_output_plan(project=project, topic=topic)
        project_name = cls._required(project.get("name"), "Project name")
        clean_prefix = title_prefix.strip() if title_prefix and title_prefix.strip() else project_name

        payloads: list[dict[str, Any]] = []

        for item in plan:
            content_type = item["content_type"]
            title = f"{clean_prefix} - {cls._humanize_content_type(content_type)}"
            body = (
                f"Workflow draft for {cls._humanize_content_type(content_type)}. "
                f"Project: {project_name}. "
                f"Topic: {item['generation_topic']}. "
                "This asset is ready for AI generation or manual writing."
            )

            payloads.append(
                {
                    "project_id": item["project_id"],
                    "content_type": content_type,
                    "title": title,
                    "body": body,
                    "status": "draft",
                    "source": "manual",
                    "metadata": {
                        "workflow": "draft_asset_generation",
                        "planned_order": item["order"],
                        "generation_topic": item["generation_topic"],
                    },
                }
            )

        return payloads

    @staticmethod
    def _required(value: Any, field_name: str) -> str:
        normalized_value = str(value or "").strip()

        if not normalized_value:
            raise InvalidWorkflowRequestError(f"{field_name} cannot be empty.")

        return normalized_value

    @staticmethod
    def _humanize_content_type(content_type: str) -> str:
        return content_type.replace("_", " ").strip().title()

    @staticmethod
    def _normalize_content_type(content_type: str) -> str:
        normalized_content_type = str(content_type or "").strip().lower()

        if not normalized_content_type:
            raise InvalidWorkflowRequestError("Content type cannot be empty.")

        return normalized_content_type
