"""
Prompt-building engine with Pydantic V2 validation, Jinja2 rendering,
multi-provider formatting, smart suffix injection, and Claude 4.6
<thinking>-tag optimizations.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from jinja2 import BaseLoader, Environment, TemplateSyntaxError, meta
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


# ────────────────────────────────────────────────────────────────────
# 1.  Pydantic V2 validated prompt template
# ────────────────────────────────────────────────────────────────────

# Shared Jinja2 environment (sandboxed, no filesystem access)
_JINJA_ENV = Environment(loader=BaseLoader(), autoescape=False)


def _extract_template_variables(template_str: str) -> set[str]:
    """Return the set of undeclared variable names in a Jinja2 template."""
    ast = _JINJA_ENV.parse(template_str)
    return meta.find_undeclared_variables(ast)


class PromptTemplate(BaseModel):
    """
    A validated prompt template backed by Jinja2.

    • ``template`` – a Jinja2 template string
    • ``variables`` – a dict of variable-name → value used to render it
    • ``role``  – the system-level persona (always required)
    • ``requested_format`` – desired output format (drives suffix injection)
    • ``provider`` – target LLM provider
    """

    model_config = ConfigDict(strict=False, arbitrary_types_allowed=True)

    template: str
    variables: dict[str, Any] = {}
    role: str = "a helpful assistant"
    requested_format: Literal[
        "text", "markdown", "json", "xml", "code", "bullets",
        "numbered_list", "table", "essay", "step_by_step",
    ] = "text"
    provider: Literal["openai", "anthropic", "generic"] = "generic"
    enable_thinking: bool = False
    examples: list[dict[str, str]] | None = None

    # ── Validators ──

    @field_validator("template")
    @classmethod
    def _validate_template_syntax(cls, v: str) -> str:
        try:
            _JINJA_ENV.parse(v)
        except TemplateSyntaxError as exc:
            raise ValueError(f"Invalid Jinja2 template: {exc}") from exc
        return v

    @model_validator(mode="after")
    def _check_required_variables(self) -> "PromptTemplate":
        required: set[str] = _extract_template_variables(self.template)
        provided: set[str] = set(self.variables.keys())
        missing: set[str] = required - provided
        if missing:
            raise ValueError(
                f"Missing required template variables: {sorted(missing)}"
            )
        return self

    # ── Rendering ──

    def render(self) -> str:
        """Render the Jinja2 template with the supplied variables."""
        tpl = _JINJA_ENV.from_string(self.template)
        return tpl.render(**self.variables)

    def render_for_provider(
        self,
        provider: str | None = None,
    ) -> list[dict[str, str]] | str:
        """
        Render the prompt and format it for the target provider.

        Returns
        -------
        - ``'openai'``     → ``list[dict]`` with ``{"role": …, "content": …}``
        - ``'anthropic'``  → XML-wrapped string (Claude 4.6 conventions)
        - ``'generic'``    → plain string
        """
        target: str = provider or self.provider
        body: str = self.render()
        body = self._inject_suffix(body)

        if target == "openai":
            return self._format_openai(body)
        if target == "anthropic":
            return self._format_anthropic(body)
        return body

    # ── Provider formatters ──

    def _format_openai(self, body: str) -> list[dict[str, str]]:
        """OpenAI chat-completion format: list of role/content dicts."""
        messages: list[dict[str, str]] = [
            {"role": "system", "content": f"You are {self.role}."},
        ]
        if self.examples:
            messages.extend(self._build_few_shot_messages())
        messages.append({"role": "user", "content": body})
        return messages

    def _format_anthropic(self, body: str) -> str:
        """Anthropic Claude 4.6 format: XML-wrapped structured string."""
        sections: list[str] = []
        sections.append(f"<role>\nYou are {self.role}.\n</role>")

        if self.enable_thinking and self.examples:
            sections.append(self._build_thinking_block())

        if self.examples:
            examples_xml = self._build_few_shot_xml()
            sections.append(f"<examples>\n{examples_xml}\n</examples>")

        sections.append(f"<instruction>\n{body}\n</instruction>")
        return "\n\n".join(sections)

    # ── Smart suffix injection (§3) ──

    _SUFFIX_MAP: dict[str, str] = {
        "json": (
            "\n\nIMPORTANT: Respond with valid JSON only. "
            "Do not include any preamble, explanation, or text outside "
            "the JSON structure. Wrap your output in ```json``` fences."
        ),
        "xml": (
            "\n\nIMPORTANT: Respond with well-formed XML only. "
            "Do not include preambles or commentary outside the XML document."
        ),
        "code": (
            "\n\nIMPORTANT: Respond with code only. "
            "Do not include explanations unless explicitly requested. "
            "Use appropriate language fences."
        ),
        "markdown": (
            "\n\nFormat your entire response as clean Markdown. "
            "Use headers, lists, and code fences where appropriate."
        ),
        "bullets": (
            "\n\nPresent your response as a bullet-point list. "
            "Each point should be concise and self-contained."
        ),
        "numbered_list": (
            "\n\nPresent your response as a numbered list. "
            "Each item should be concise and self-contained."
        ),
        "table": (
            "\n\nPresent your response as a Markdown table "
            "with clear column headers."
        ),
        "step_by_step": (
            "\n\nOrganize your response as a numbered step-by-step guide. "
            "Each step should be actionable and clearly described."
        ),
    }

    def _inject_suffix(self, body: str) -> str:
        """Append format-specific instructions based on ``requested_format``."""
        suffix: str = self._SUFFIX_MAP.get(self.requested_format, "")
        if suffix:
            return body + suffix
        return body

    # ── Claude 4.6 thinking-tag optimizations (§4) ──

    def _build_thinking_block(self) -> str:
        """
        Wrap reasoning about multi-shot examples inside <thinking> tags
        so Claude 4.6 can reason internally before answering.
        """
        lines: list[str] = [
            "<thinking>",
            "I have been given the following few-shot examples. "
            "Let me analyze the pattern before responding:",
            "",
        ]
        for i, ex in enumerate(self.examples or [], 1):
            user_text = ex.get("user", ex.get("input", ""))
            assistant_text = ex.get("assistant", ex.get("output", ""))
            lines.append(f"Example {i}:")
            lines.append(f"  Input:  {user_text}")
            lines.append(f"  Output: {assistant_text}")
            lines.append("")
        lines.append(
            "Based on these examples I can identify the expected "
            "pattern and will apply it consistently."
        )
        lines.append("</thinking>")
        return "\n".join(lines)

    def _build_few_shot_xml(self) -> str:
        """Build XML few-shot example blocks for Anthropic."""
        parts: list[str] = []
        for i, ex in enumerate(self.examples or [], 1):
            user_text = ex.get("user", ex.get("input", ""))
            assistant_text = ex.get("assistant", ex.get("output", ""))
            parts.append(
                f"<example index=\"{i}\">\n"
                f"  <input>{user_text}</input>\n"
                f"  <output>{assistant_text}</output>\n"
                f"</example>"
            )
        return "\n".join(parts)

    def _build_few_shot_messages(self) -> list[dict[str, str]]:
        """Build OpenAI-style few-shot messages."""
        msgs: list[dict[str, str]] = []
        for ex in self.examples or []:
            user_text = ex.get("user", ex.get("input", ""))
            assistant_text = ex.get("assistant", ex.get("output", ""))
            msgs.append({"role": "user", "content": user_text})
            msgs.append({"role": "assistant", "content": assistant_text})
        return msgs


# ────────────────────────────────────────────────────────────────────
# Convenience factory – build a PromptTemplate from the GUI data dict
# ────────────────────────────────────────────────────────────────────

_FORMAT_KEY_MAP: dict[str, str] = {
    "Markdown": "markdown",
    "Plain Text": "text",
    "JSON": "json",
    "XML": "xml",
    "Code Only": "code",
    "Bullet Points": "bullets",
    "Numbered List": "numbered_list",
    "Table": "table",
    "Essay / Prose": "essay",
    "Step-by-step Guide": "step_by_step",
}

_PROVIDER_KEY_MAP: dict[str, str] = {
    "Claude": "anthropic",
    "ChatGPT": "openai",
    "Gemini": "generic",
    "Copilot": "generic",
}


def build_from_gui(
    data: dict[str, Any],
    *,
    model_name: str = "Claude",
    output_format_label: str = "Markdown",
    enable_thinking: bool = False,
    examples_raw: str = "",
) -> PromptTemplate:
    """
    Construct a ``PromptTemplate`` from the dict produced by the GUI's
    ``SharedFieldsPanel.collect()`` merged with model-specific fields.

    This is the bridge between the Qt front-end and the engine.
    """
    provider: str = _PROVIDER_KEY_MAP.get(model_name, "generic")
    req_fmt: str = _FORMAT_KEY_MAP.get(output_format_label, "text")

    # Assemble a Jinja2 template from the structured fields
    tpl_parts: list[str] = []
    variables: dict[str, Any] = {}

    if data.get("guidance"):
        tpl_parts.append("Task guidance: {{ guidance }}")
        variables["guidance"] = data["guidance"]

    if data.get("lang"):
        tpl_parts.append("Programming language: {{ lang }}")
        variables["lang"] = data["lang"]

    tpl_parts.append("Tone: {{ tone_line }}")
    variables["tone_line"] = data.get("tone_line", "")

    if data.get("context"):
        tpl_parts.append("Context:\n{{ context }}")
        variables["context"] = data["context"]

    if data.get("input_data"):
        tpl_parts.append("Input data:\n{{ input_data }}")
        variables["input_data"] = data["input_data"]

    tpl_parts.append("Instruction:\n{{ instruction }}")
    variables["instruction"] = data.get("instruction", "")

    if data.get("constraints"):
        tpl_parts.append("Constraints:\n{{ constraints }}")
        variables["constraints"] = data["constraints"]

    tpl_parts.append("Output requirements:\n{{ output_reqs }}")
    variables["output_reqs"] = data.get("output_reqs", "")

    if data.get("cot"):
        tpl_parts.append("{{ cot }}")
        variables["cot"] = data["cot"]

    if data.get("citations"):
        tpl_parts.append("Include references or sources where applicable.")

    if data.get("creativity_hint"):
        tpl_parts.append("{{ creativity_hint }}")
        variables["creativity_hint"] = data["creativity_hint"]

    if data.get("extra"):
        tpl_parts.append("{{ extra }}")
        variables["extra"] = data["extra"]

    template_str: str = "\n\n".join(tpl_parts)

    # Parse examples (simple "input -> output" lines)
    examples: list[dict[str, str]] | None = None
    if examples_raw.strip():
        examples = _parse_examples(examples_raw)

    return PromptTemplate(
        template=template_str,
        variables=variables,
        role=data.get("role", "a helpful assistant"),
        requested_format=req_fmt,
        provider=provider,
        enable_thinking=enable_thinking,
        examples=examples,
    )


def _parse_examples(raw: str) -> list[dict[str, str]]:
    """
    Parse example text where each example is separated by a blank line
    and uses ``Input:`` / ``Output:`` or ``->`` notation.
    """
    examples: list[dict[str, str]] = []
    blocks = re.split(r"\n{2,}", raw.strip())
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Try "Input: … / Output: …" format
        m = re.search(
            r"(?:input|user)\s*:\s*(.*?)(?:\n\s*(?:output|assistant)\s*:\s*(.*))",
            block,
            re.IGNORECASE | re.DOTALL,
        )
        if m:
            examples.append({"user": m.group(1).strip(),
                             "assistant": m.group(2).strip()})
            continue
        # Try "X -> Y" format
        if "->" in block:
            parts = block.split("->", 1)
            examples.append({"user": parts[0].strip(),
                             "assistant": parts[1].strip()})
            continue
        # Fallback: treat as user input only
        examples.append({"user": block, "assistant": ""})
    return examples
