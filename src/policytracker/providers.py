"""Transport contract; implementations must negotiate real authenticated capabilities.

No provider is silently mocked and no paid call is made by this module.
"""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelSelection:
    route: str
    model: str
    effort: str


@dataclass(frozen=True)
class Capabilities:
    route: str
    models: dict[str, tuple[str, ...]]
    structured_output: bool
    max_input_tokens: int | None
    output_limit_supported: bool
    authenticated: bool
    inference_verified: bool

    def check(self, selected: ModelSelection):
        if not self.authenticated or self.route != selected.route:
            raise ValueError("Requested route is not authenticated")
        if selected.model not in self.models or selected.effort not in self.models[selected.model]:
            raise ValueError("Requested model/effort is not in this route's catalog; no fallback")
        if not self.structured_output:
            raise ValueError("This structured task needs an explicitly supported output strategy")
        # The worker must still execute a canary; catalog presence is not entitlement.


@dataclass(frozen=True)
class InferenceTask:
    task_id: str
    selection: ModelSelection
    instructions: str
    input_json: str
    output_schema: dict
    input_fingerprint: str
    owner_scope: str


@dataclass(frozen=True)
class InferenceResult:
    request_id: str
    status: str
    output: dict | None
    requested_selection: ModelSelection
    actual_model: str | None
    confirmed_effort: str | None
    input_tokens: int | None
    output_tokens: int | None
    reasoning_tokens: int | None
    error_code: str | None


class Provider(Protocol):
    def capabilities(self) -> Capabilities: ...
    def generate(self, task: InferenceTask) -> InferenceResult: ...
    def cancel(self, request_id: str) -> bool: ...
