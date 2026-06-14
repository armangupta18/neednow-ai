from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.logger import logger
from app.core.settings import settings
from app.services.gemini_service import GeminiService

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentValidationError(Exception):
    """Raised when agent input fails schema or business validation."""

    def __init__(self, agent_name: str, errors: list[Any]) -> None:
        self.agent_name = agent_name
        self.errors = errors
        super().__init__(f"{agent_name} input validation failed: {errors}")


class AgentExecutionError(Exception):
    """Raised when agent execution fails."""

    def __init__(self, agent_name: str, message: str) -> None:
        self.agent_name = agent_name
        self.message = message
        super().__init__(f"{agent_name}: {message}")


class AgentMetadata(BaseModel):
    """Serializable agent metadata for FastAPI routes and health checks."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class AgentInput(BaseModel):
    """Base Pydantic schema for agent request payloads."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AgentOutput(BaseModel):
    """Base Pydantic schema for agent response payloads."""

    model_config = ConfigDict(extra="forbid")


class LLMAgentConfig(BaseModel):
    """Gemini invocation defaults for LLM-backed agents."""

    model_config = ConfigDict(frozen=True)

    model_id: str = Field(default_factory=lambda: settings.GEMINI_MODEL_ID)
    max_tokens: int = Field(
        default_factory=lambda: settings.GEMINI_MAX_TOKENS,
        ge=1,
    )
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Abstract async agent contract shared across NeedNow AI agents.

    Subclasses declare ``name``, ``description``, ``input_model``, and
    ``output_model`` as class attributes and implement ``execute()``.
    ``validate_input()`` performs Pydantic coercion by default; override it
    or ``_validate_business_rules()`` for domain-specific checks.

    Optional ``GeminiService`` injection enables LLM calls via ``invoke_llm()``.
    """

    name: ClassVar[str]
    description: ClassVar[str]
    input_model: ClassVar[type[InputT]]
    output_model: ClassVar[type[OutputT]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls is BaseAgent:
            return
        for attr in ("name", "description", "input_model", "output_model"):
            if not getattr(cls, attr, None):
                raise TypeError(f"{cls.__name__} must define class attribute '{attr}'")

    def __init__(
        self,
        llm_service: GeminiService | None = None,
        llm_config: LLMAgentConfig | None = None,
    ) -> None:
        self._llm = llm_service
        self._llm_config = llm_config or LLMAgentConfig()
        self._logger = logger.getChild(self.name)

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(name=self.name, description=self.description)

    def coerce_input(self, data: InputT | dict[str, Any]) -> InputT:
        """Convert raw dict or model instance into a validated input model."""
        if isinstance(data, self.input_model):
            return data
        try:
            return self.input_model.model_validate(data)
        except ValidationError as exc:
            raise AgentValidationError(self.name, exc.errors()) from exc

    async def validate_input(self, data: InputT | dict[str, Any]) -> InputT:
        """
        Validate and normalize incoming data before execution.

        Override for custom validation logic; call ``super().validate_input``
        to retain schema coercion.
        """
        validated = self.coerce_input(data)
        await self._validate_business_rules(validated)
        return validated

    async def _validate_business_rules(self, data: InputT) -> None:
        """Hook for domain-specific validation beyond Pydantic schema checks."""
        return None

    @abstractmethod
    async def execute(self, data: InputT) -> OutputT:
        """Run the agent's core logic on validated input."""

    async def run(self, data: InputT | dict[str, Any]) -> OutputT:
        """
        Primary entry point: validate input, execute, and return typed output.

        Use this method from FastAPI route handlers and orchestrators.
        """
        validated = await self.validate_input(data)
        self._logger.debug("Executing agent", extra={"agent": self.name})
        try:
            return await self.execute(validated)
        except AgentExecutionError:
            raise
        except Exception as exc:
            raise AgentExecutionError(self.name, str(exc)) from exc

    async def invoke_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Invoke Google Gemini for LLM-backed agents.

        Requires ``GeminiService`` to be provided at construction time.
        """
        if self._llm is None:
            raise AgentExecutionError(
                self.name,
                "GeminiService is not configured for this agent",
            )

        _ = max_tokens or self._llm_config.max_tokens
        _ = temperature if temperature is not None else self._llm_config.temperature

        self._logger.debug(
            "Invoking LLM model",
            extra={
                "agent": self.name,
                "model_id": self._llm_config.model_id,
            },
        )
        return await self._llm.invoke(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
