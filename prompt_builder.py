import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QGroupBox,
    QFormLayout, QSplitter, QMessageBox, QCheckBox,
    QScrollArea, QFrame, QFileDialog, QTabWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor

from engine import PromptTemplate, build_from_gui


# ── Shared constants ──

TASK_TYPES = [
    "Code Generation", "Code Review / Debugging", "Code Explanation",
    "Writing / Content Creation", "Summarization", "Translation",
    "Data Analysis", "Research / Q&A", "Brainstorming",
    "Rewriting / Editing", "Conversation / Roleplay",
    "Math / Logic", "Custom",
]

PROGRAMMING_LANGUAGES = [
    "(not applicable)", "Python", "JavaScript", "TypeScript",
    "C", "C#", "C++", "Java", "Go", "Rust", "Ruby", "PHP",
    "Swift", "Kotlin", "Scala", "SQL", "HTML/CSS", "Shell/Bash",
    "PowerShell", "R", "Dart", "Lua", "Perl", "Haskell",
    "Elixir", "F#", "Julia", "Objective-C", "MATLAB", "Zig",
    "Assembly", "Other",
]

TASK_GUIDANCE = {
    "Code Generation":
        "Generate clean, well-structured, production-ready code. "
        "Include brief comments for non-obvious logic.",
    "Code Review / Debugging":
        "Review the provided code for bugs, security issues, performance "
        "problems, and adherence to best practices. Suggest concrete fixes.",
    "Code Explanation":
        "Explain the provided code clearly. Break down complex logic into "
        "understandable parts and describe what each section does and why.",
    "Writing / Content Creation":
        "Produce original, well-organized written content that matches "
        "the requested style and purpose.",
    "Summarization":
        "Provide a clear, accurate summary that captures the key points "
        "without omitting important details.",
    "Translation":
        "Provide an accurate, natural-sounding translation that preserves "
        "the meaning, tone, and nuance of the original.",
    "Data Analysis":
        "Analyze the provided data methodically. Identify patterns, "
        "anomalies, and actionable insights. Support conclusions with evidence.",
    "Research / Q&A":
        "Provide a thorough, accurate answer grounded in established knowledge. "
        "Distinguish facts from interpretation.",
    "Brainstorming":
        "Generate diverse, creative ideas. Explore unconventional angles "
        "and group suggestions by theme when helpful.",
    "Rewriting / Editing":
        "Improve the provided text for clarity, flow, and correctness "
        "while preserving the original meaning and voice.",
    "Conversation / Roleplay":
        "Stay in character consistently. Respond naturally and adapt to "
        "the conversational context.",
    "Math / Logic":
        "Solve the problem step-by-step, showing your work clearly. "
        "Verify your answer before presenting it.",
}

CREATIVITY_MAP = {
    "Precise (low creativity)": "Be precise and factual. Avoid speculation.",
    "Balanced": "Balance accuracy with moderate creativity.",
    "Creative (high creativity)":
        "Be creative, exploratory, and imaginative in your response.",
}

FIELD_HELP = {
    "task_type": {
        "title": "Task Type",
        "description": "Select the category that best describes what you want the AI to do. This automatically adds task-specific guidance to your prompt.",
        "examples": [
            "Code Generation \u2014 write new functions, classes, or scripts",
            "Code Review / Debugging \u2014 find bugs and suggest fixes",
            "Summarization \u2014 condense a long article into key points",
            "Brainstorming \u2014 generate creative ideas on a topic",
        ],
    },
    "programming_lang": {
        "title": "Programming Language",
        "description": "Choose the programming language for code-related tasks. The AI will use this language in its response. Pick \u2018(not applicable)\u2019 for non-code tasks.",
        "examples": [
            "Python \u2014 data science, scripting, web backends",
            "TypeScript \u2014 modern web applications",
            "Rust \u2014 systems programming with memory safety",
            "SQL \u2014 database queries and data manipulation",
        ],
    },
    "role": {
        "title": "Role / Persona",
        "description": "Define who the AI should act as. A specific persona helps the AI adopt the right expertise, vocabulary, and perspective.",
        "examples": [
            "Senior Python developer with 10 years of experience",
            "Technical writer specializing in API documentation",
            "Data scientist focused on machine learning",
            "Patient tutor explaining concepts to beginners",
        ],
    },
    "tone": {
        "title": "Tone",
        "description": "Set the communication style for the AI\u2019s response. This affects word choice, formality, and overall feel.",
        "examples": [
            "Professional \u2014 formal, polished, business-appropriate",
            "Casual / Friendly \u2014 conversational, approachable",
            "Technical \u2014 precise, domain-specific terminology",
            "Concise / Direct \u2014 straight to the point, no fluff",
        ],
    },
    "audience": {
        "title": "Target Audience",
        "description": "Specify who will read the AI\u2019s output. This adjusts complexity, jargon, and level of explanation.",
        "examples": [
            "Beginners \u2014 detailed explanations, minimal jargon",
            "Senior engineers \u2014 concise, assumes deep knowledge",
            "Non-technical stakeholders \u2014 business language, no code",
            "Students \u2014 educational tone with learning examples",
        ],
    },
    "context": {
        "title": "Context",
        "description": "Provide background information the AI needs. Include relevant project details, technology stack, or previous decisions.",
        "examples": [
            "I\u2019m building a REST API with FastAPI and PostgreSQL.",
            "This is a legacy Java 8 codebase migrating to Java 17.",
            "I\u2019m writing a blog post about renewable energy.",
        ],
    },
    "instruction": {
        "title": "Main Instruction",
        "description": "The core task or question for the AI. Be specific and clear about exactly what you need. This is the most important field.",
        "examples": [
            "Write a Python function that groups a list of dicts by a key.",
            "Review this code for security vulnerabilities and suggest fixes.",
            "Explain TCP vs UDP with real-world analogies.",
            "Summarize this 2000-word article in 5 bullet points.",
        ],
    },
    "input_data": {
        "title": "Input Data",
        "description": "Paste any code, text, data, or content the AI should process or analyze. This is the material the AI will work with.",
        "examples": [
            "A code snippet to review or refactor",
            "A JSON payload or dataset to analyze",
            "An article or passage to summarize",
            "Error logs or stack traces to debug",
        ],
    },
    "constraints": {
        "title": "Constraints",
        "description": "Specify rules, limitations, or things the AI should avoid. These guardrails ensure the output meets your requirements.",
        "examples": [
            "Do not use external libraries \u2014 standard library only.",
            "Keep the response under 300 words.",
            "Avoid recursion \u2014 use iterative approaches only.",
            "Do not include placeholder or TODO comments.",
        ],
    },
    "examples": {
        "title": "Examples (Few-Shot)",
        "description": "Provide example input/output pairs to show the AI the pattern you expect. Few-shot prompting significantly improves quality.",
        "examples": [
            "Input: \u2018hello world\u2019 \u2192 Output: \u2018Hello World\u2019",
            "Input: \u20182024-01-15\u2019 \u2192 Output: \u2018January 15, 2024\u2019",
            "Q: What is 2+2? A: 4",
            "Provide 2\u20133 examples for best results",
        ],
    },
    "output_format": {
        "title": "Output Format",
        "description": "Choose how the AI should structure its response. A format instruction is appended to your prompt automatically.",
        "examples": [
            "Markdown \u2014 headers, bold, lists, code blocks",
            "JSON \u2014 structured data in JSON format",
            "Code Only \u2014 pure code without explanations",
            "Table \u2014 organized data in rows and columns",
        ],
    },
    "detail_level": {
        "title": "Detail Level",
        "description": "Control how thorough the AI\u2019s response should be. Higher detail means longer, more comprehensive answers.",
        "examples": [
            "Brief \u2014 short, one-paragraph answer",
            "Moderate \u2014 covers main points with some explanation",
            "Detailed \u2014 thorough coverage with examples",
            "Comprehensive \u2014 exhaustive, covers edge cases",
        ],
    },
    "output_language": {
        "title": "Output Language",
        "description": "Select the natural language for the AI\u2019s response. The AI will write its entire response in this language.",
        "examples": [
            "English \u2014 default for most technical content",
            "Spanish / French / German \u2014 for localized content",
            "Japanese \u2014 for Japanese documentation",
            "Pick \u2018Other\u2019 and type any language not listed",
        ],
    },
    "max_length": {
        "title": "Max Length",
        "description": "Set an approximate word limit. \u2018No limit\u2019 lets the AI decide the appropriate length.",
        "examples": [
            "~100 words \u2014 quick, tweet-length answers",
            "~500 words \u2014 a solid paragraph or short explanation",
            "~1000 words \u2014 detailed explanations or short articles",
            "No limit \u2014 for comprehensive tasks",
        ],
    },
    "chain_of_thought": {
        "title": "Chain of Thought",
        "description": "When enabled, the AI shows its reasoning step-by-step before giving the final answer. Improves accuracy for complex problems.",
        "examples": [
            "Math problems \u2014 shows each calculation step",
            "Debugging \u2014 walks through logic to find issues",
            "Decision-making \u2014 weighs pros and cons",
            "Best for: complex reasoning, math, logic, multi-step tasks",
        ],
    },
    "citations": {
        "title": "Citations",
        "description": "When enabled, the AI is asked to include references or sources to back up its claims. Useful for research tasks.",
        "examples": [
            "Research papers or documentation links",
            "Official documentation references",
            "Relevant Stack Overflow answers",
            "Best for: research, technical writing, fact-based content",
        ],
    },
    "creativity_hint": {
        "title": "Creativity Hint",
        "description": "Guide how creative vs. factual the AI should be. Maps roughly to the \u2018temperature\u2019 setting in AI models.",
        "examples": [
            "Precise \u2014 for factual answers, code, data analysis",
            "Balanced \u2014 for general-purpose tasks",
            "Creative \u2014 for brainstorming, storytelling, marketing",
            "Default \u2014 lets the model use its standard setting",
        ],
    },
    "extra_instructions": {
        "title": "Extra Instructions",
        "description": "Any additional instructions that don\u2019t fit other fields. Appended to the end of the generated prompt.",
        "examples": [
            "Also include unit tests for the code.",
            "Use American English spelling.",
            "Structure the response with H2 headers per section.",
            "Include a TL;DR at the beginning.",
        ],
    },
    "btn_generate": {
        "title": "Generate",
        "description": "Build the final prompt using all your settings. The prompt is formatted specifically for the selected AI model using its corresponding formatter.",
        "examples": [
            "Claude \u2192 uses XML tags for structure",
            "ChatGPT \u2192 uses System + User message format",
            "Gemini \u2192 uses bold Markdown headers",
            "Copilot \u2192 uses concise, instruction-focused format",
        ],
    },
    "btn_engine": {
        "title": "Engine",
        "description": "Generate the prompt via the Pydantic/Jinja2 engine layer. Uses validated templates with automatic format suffix injection and provider-specific formatting.",
        "examples": [
            "Validates all fields with Pydantic before building",
            "Uses Jinja2 templates for rendering",
            "Auto-injects format instructions (JSON, XML, etc.)",
            "Supports Claude extended thinking mode",
        ],
    },
    "btn_copy": {
        "title": "Copy",
        "description": "Copy the generated prompt to your clipboard so you can paste it directly into any AI chat interface.",
        "examples": [
            "Paste into Claude at claude.ai",
            "Paste into ChatGPT at chat.openai.com",
            "Paste into any AI tool or API client",
            "Tip: generate the prompt first, then copy",
        ],
    },
    "btn_save": {
        "title": "Save",
        "description": "Save the generated prompt to a file on your computer. Useful for reusing prompts later or building a prompt library.",
        "examples": [
            "Save as .txt for plain text",
            "Save as .md for Markdown formatting",
            "Build a library of reusable prompt templates",
            "Share saved prompts with your team",
        ],
    },
    "btn_clear": {
        "title": "Clear",
        "description": "Reset all input fields and model-specific options to defaults. Clears shared fields, model settings, and the output area.",
        "examples": [
            "Resets Role, Context, Instruction, etc.",
            "Resets model-specific checkboxes and dropdowns",
            "Clears the generated output area",
            "Use to start a completely new prompt from scratch",
        ],
    },
    "model": {
        "title": "Model",
        "description": "Select which specific AI model you are targeting. Different models have different capabilities, speed, and cost tradeoffs.",
        "examples": [
            "Claude Opus 4 \u2014 most capable, best for complex tasks",
            "GPT-4.1 \u2014 strong reasoning and coding",
            "Gemini 2.5 Pro \u2014 Google\u2019s advanced model",
            "Smaller models (Haiku, mini) \u2014 faster and cheaper",
        ],
    },
    "xml_tags": {
        "title": "XML Tags",
        "description": "Wrap prompt sections in XML tags (e.g., &lt;role&gt;, &lt;instruction&gt;). Anthropic recommends this for Claude for best results.",
        "examples": [
            "&lt;role&gt;You are a Python expert.&lt;/role&gt;",
            "&lt;instruction&gt;Write a sorting function.&lt;/instruction&gt;",
            "Recommended ON for Claude models",
            "Turn OFF to use plain Markdown instead",
        ],
    },
    "extended_thinking": {
        "title": "Extended Thinking",
        "description": "Instructs the AI to reason deeply using extended thinking. The AI works through its reasoning thoroughly before responding.",
        "examples": [
            "Complex mathematical proofs",
            "Multi-step architectural decisions",
            "Detailed code analysis with many considerations",
            "Best for: problems requiring deep, careful reasoning",
        ],
    },
    "system_user_split": {
        "title": "System + User Messages",
        "description": "Format the prompt as separate System and User messages, following OpenAI\u2019s recommended chat format.",
        "examples": [
            "System: \u2018You are a Python expert. Be concise.\u2019",
            "User: \u2018Write a function to sort a list.\u2019",
            "Recommended ON for ChatGPT/GPT models",
            "Turn OFF to combine into a single message",
        ],
    },
    "json_mode": {
        "title": "Strict JSON Mode",
        "description": "Forces the AI to respond with valid JSON only, with no additional text. Use for machine-parseable output.",
        "examples": [
            "API response formatting",
            "Structured data extraction",
            "Configuration file generation",
            "Adds an explicit JSON-only instruction to the prompt",
        ],
    },
    "grounding": {
        "title": "Google Search Grounding",
        "description": "Instructs Gemini to ground its response with current, verifiable information from Google Search and cite sources.",
        "examples": [
            "Current events or recent developments",
            "Latest library versions or API changes",
            "Up-to-date statistics or data",
            "Fact-checking and verification",
        ],
    },
    "safety": {
        "title": "Safety Level",
        "description": "Control how strict the safety guidelines are for Gemini\u2019s output. Affects content filtering and restrictions.",
        "examples": [
            "Default \u2014 standard safety settings",
            "Strict \u2014 avoids speculative or unverified content",
            "Permissive \u2014 thorough discussion of nuanced topics",
        ],
    },
    "mode": {
        "title": "Mode",
        "description": "Set the operating mode for Copilot. This affects the tone, approach, and style of the generated prompt.",
        "examples": [
            "Balanced \u2014 general-purpose, well-rounded",
            "Creative \u2014 innovative solutions, exploratory thinking",
            "Precise \u2014 strictly factual, minimal speculation",
        ],
    },
    "code_first": {
        "title": "Code-First Output",
        "description": "Instructs the AI to lead with the code solution first, then provide brief explanations only where needed.",
        "examples": [
            "Shows the complete code block first",
            "Explanations come after the code, not before",
            "Great for quick implementation tasks",
            "Perfect for experienced developers",
        ],
    },
    "web_search": {
        "title": "Web Search References",
        "description": "Instructs Copilot to reference current web information where relevant and cite sources in its response.",
        "examples": [
            "Up-to-date info about libraries and frameworks",
            "Official documentation references",
            "Links to relevant resources",
            "Best for: research, latest practices",
        ],
    },
}


# ── Per-model prompt formatters ──

def _format_claude(d):
    """Claude: XML tags (recommended by Anthropic) or Markdown fallback."""
    use_xml = d.get("xml_tags", True)

    def sec(tag, content, md_label=None):
        if use_xml:
            return f"<{tag}>\n{content}\n</{tag}>"
        return f"**{md_label}:**\n{content}" if md_label else content

    parts = []
    parts.append(sec("role", f"You are {d['role']}.", "Role"))
    if d["guidance"]:
        parts.append(sec("task", d["guidance"], "Task"))
    if d["lang"]:
        parts.append(sec("language",
                         f"Use {d['lang']} as the programming language."))
    parts.append(sec("tone", d["tone_line"]))
    if d["context"]:
        parts.append(sec("context", d["context"], "Context"))
    if d["examples"]:
        parts.append(sec("examples", d["examples"], "Examples"))
    if d["input_data"]:
        parts.append(sec("input_data", d["input_data"], "Input Data"))
    parts.append(sec("instruction", d["instruction"], "Instruction"))
    if d["constraints"]:
        parts.append(sec("constraints", d["constraints"], "Constraints"))
    parts.append(sec("output_requirements", d["output_reqs"],
                      "Output Requirements"))
    if d.get("extended_thinking"):
        parts.append(sec(
            "thinking_instructions",
            "Use extended thinking to reason deeply about this problem. "
            "Work through your reasoning thoroughly before responding.",
        ))
    if d["cot"]:
        parts.append(sec("thinking_instructions", d["cot"]))
    if d["citations"]:
        parts.append(sec("citations",
                         "Include references or sources where applicable."))
    if d["creativity_hint"]:
        parts.append(sec("creativity", d["creativity_hint"]))
    if d["extra"]:
        parts.append(sec("additional", d["extra"]))
    return "\n\n".join(parts)


def _format_chatgpt(d):
    """ChatGPT: System message + User message structure."""
    use_split = d.get("system_user_split", True)

    sys_parts = [f"You are {d['role']}."]
    if d["guidance"]:
        sys_parts.append(d["guidance"])
    if d["lang"]:
        sys_parts.append(f"Use {d['lang']} as the programming language.")
    sys_parts.append(d["tone_line"])
    if d["creativity_hint"]:
        sys_parts.append(d["creativity_hint"])
    system_msg = " ".join(sys_parts)

    user_parts = []
    if d["context"]:
        user_parts.append(f"## Context\n{d['context']}")
    if d["examples"]:
        user_parts.append(f"## Examples\n{d['examples']}")
    if d["input_data"]:
        user_parts.append(f"## Input Data\n{d['input_data']}")
    user_parts.append(f"## Task\n{d['instruction']}")
    if d["constraints"]:
        user_parts.append(f"## Constraints\n{d['constraints']}")
    user_parts.append(f"## Output Requirements\n{d['output_reqs']}")
    if d.get("json_mode"):
        user_parts.append(
            "IMPORTANT: Respond with valid JSON only. "
            "No additional text outside the JSON structure.")
    if d["cot"]:
        user_parts.append(d["cot"])
    if d["citations"]:
        user_parts.append(
            "Please include references or sources where applicable.")
    if d["extra"]:
        user_parts.append(d["extra"])
    user_msg = "\n\n".join(user_parts)

    if use_split:
        return (f"# System Message\n{system_msg}\n\n"
                f"# User Message\n{user_msg}")
    return f"{system_msg}\n\n{user_msg}"


def _format_gemini(d):
    """Gemini: bold Markdown headers, flat structure."""
    parts = []
    parts.append(f"**Role:** You are {d['role']}.")
    if d["guidance"]:
        parts.append(f"**Task:** {d['guidance']}")
    if d["lang"]:
        parts.append(f"**Language:** Use {d['lang']}.")
    parts.append(f"**Tone:** {d['tone_line']}")
    if d["context"]:
        parts.append(f"**Context:**\n{d['context']}")
    if d["examples"]:
        parts.append(f"**Examples:**\n{d['examples']}")
    if d["input_data"]:
        parts.append(f"**Input Data:**\n{d['input_data']}")
    parts.append(f"**Instructions:**\n{d['instruction']}")
    if d["constraints"]:
        parts.append(f"**Constraints:**\n{d['constraints']}")
    parts.append(f"**Output Format:**\n{d['output_reqs']}")
    if d.get("grounding"):
        parts.append(
            "Ground your response with current, verifiable information. "
            "Cite sources where applicable.")
    safety = d.get("safety", "Default")
    if safety == "Strict":
        parts.append(
            "Apply strict safety guidelines. Avoid speculative, "
            "harmful, or unverified content.")
    elif safety == "Permissive":
        parts.append(
            "Be thorough and complete in your response. "
            "Discuss nuanced topics with appropriate context.")
    if d["cot"]:
        parts.append(d["cot"])
    if d["citations"]:
        parts.append("Include references or sources where applicable.")
    if d["creativity_hint"]:
        parts.append(d["creativity_hint"])
    if d["extra"]:
        parts.append(d["extra"])
    return "\n\n".join(parts)


def _format_copilot(d):
    """Copilot: concise, instruction-focused, direct."""
    parts = []
    parts.append(f"You are {d['role']}.")

    task_bits = []
    if d["guidance"]:
        task_bits.append(d["guidance"])
    if d["lang"]:
        task_bits.append(f"Use {d['lang']}.")
    if task_bits:
        parts.append(f"Task: {' '.join(task_bits)}")

    mode = d.get("mode", "Balanced")
    if mode == "Creative":
        parts.append("Tone: Be creative and exploratory. "
                      "Offer innovative solutions and ideas.")
    elif mode == "Precise":
        parts.append("Tone: Be precise, concise, and strictly factual. "
                      "Minimize speculation.")
    else:
        parts.append(f"Tone: {d['tone_line']}")

    if d["context"]:
        parts.append(f"Context:\n{d['context']}")
    if d["examples"]:
        parts.append(f"Examples:\n{d['examples']}")
    if d["input_data"]:
        parts.append(f"Input:\n{d['input_data']}")
    parts.append(f"Instructions:\n{d['instruction']}")
    if d["constraints"]:
        parts.append(f"Constraints:\n{d['constraints']}")
    parts.append(f"Requirements:\n{d['output_reqs']}")
    if d.get("code_first"):
        parts.append(
            "Prioritize code output. Lead with the code solution, "
            "then provide brief explanations only where needed.")
    if d.get("web_search"):
        parts.append(
            "Reference current web information where relevant. "
            "Cite sources.")
    if d["cot"]:
        parts.append(d["cot"])
    if d["citations"]:
        parts.append("Include references or sources where applicable.")
    if d["creativity_hint"]:
        parts.append(d["creativity_hint"])
    if d["extra"]:
        parts.append(d["extra"])
    return "\n\n".join(parts)


# ── Model configurations ──

MODEL_CONFIGS = [
    {
        "name": "Claude",
        "accent": "#D97706",
        "accent_hover": "#B45309",
        "cot_text": (
            "Before answering, work through your reasoning inside "
            "<thinking> tags. Then provide your final answer outside "
            "those tags."
        ),
        "formatter": _format_claude,
        "specific_options": [
            {"type": "combo", "key": "model", "label": "Model:",
             "items": ["Claude Opus 4", "Claude Sonnet 4",
                       "Claude Haiku 3.5"]},
            {"type": "check", "key": "xml_tags",
             "label": "Wrap sections in XML tags (recommended)",
             "default": True},
            {"type": "check", "key": "extended_thinking",
             "label": "Enable extended thinking",
             "default": False},
        ],
    },
    {
        "name": "ChatGPT",
        "accent": "#10A37F",
        "accent_hover": "#0E8C6B",
        "cot_text": (
            "Let's approach this step by step. Think carefully "
            "before giving your final answer."
        ),
        "formatter": _format_chatgpt,
        "specific_options": [
            {"type": "combo", "key": "model", "label": "Model:",
             "items": ["GPT-4.1", "GPT-4.1 mini", "GPT-4o",
                       "GPT-4o mini", "o3", "o4-mini"]},
            {"type": "check", "key": "system_user_split",
             "label": "Format as System + User messages",
             "default": True},
            {"type": "check", "key": "json_mode",
             "label": "Strict JSON output mode",
             "default": False},
        ],
    },
    {
        "name": "Gemini",
        "accent": "#4285F4",
        "accent_hover": "#3367C7",
        "cot_text": (
            "Think through this step-by-step, explaining your reasoning "
            "at each stage before providing your final answer."
        ),
        "formatter": _format_gemini,
        "specific_options": [
            {"type": "combo", "key": "model", "label": "Model:",
             "items": ["Gemini 2.5 Pro", "Gemini 2.5 Flash",
                       "Gemini 2.0 Flash"]},
            {"type": "check", "key": "grounding",
             "label": "Google Search grounding",
             "default": False},
            {"type": "combo", "key": "safety", "label": "Safety Level:",
             "items": ["Default", "Permissive", "Strict"]},
        ],
    },
    {
        "name": "Copilot",
        "accent": "#0078D4",
        "accent_hover": "#005FA3",
        "cot_text": (
            "Break this down step by step. Show your reasoning "
            "before giving the final answer."
        ),
        "formatter": _format_copilot,
        "specific_options": [
            {"type": "combo", "key": "mode", "label": "Mode:",
             "items": ["Balanced", "Creative", "Precise"]},
            {"type": "check", "key": "code_first",
             "label": "Code-first output (code before explanation)",
             "default": False},
            {"type": "check", "key": "web_search",
             "label": "Enable web search references",
             "default": False},
        ],
    },
]


# ── Helpers ──

def _soft_shadow(widget, color="#000000", radius=20, offset_y=4, opacity=0.10):
    """Apply a soft shadow effect to a widget (Apple-style depth)."""
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(radius)
    fx.setOffset(0, offset_y)
    c = QColor(color)
    c.setAlphaF(opacity)
    fx.setColor(c)
    widget.setGraphicsEffect(fx)


def _show_help_dialog(source_widget, title, description, examples):
    """Show an Apple-styled help information dialog."""
    parent = source_widget.window()
    msg = QMessageBox(parent)
    msg.setWindowTitle(f"Help \u2014 {title}")
    msg.setIcon(QMessageBox.Icon.NoIcon)
    html = (f"<h3 style='margin-bottom:6px;'>{title}</h3>"
            f"<p style='font-size:10pt;'>{description}</p>")
    if examples:
        html += "<p style='font-size:10pt;'><b>Examples:</b></p>"
        html += "<ul style='font-size:10pt;'>"
        for ex in examples:
            html += f"<li>{ex}</li>"
        html += "</ul>"
    msg.setTextFormat(Qt.TextFormat.RichText)
    msg.setText(html)
    msg.exec()


def _make_help_btn(help_key, parent=None):
    """Create a small circular \u2018?\u2019 button linked to a help entry."""
    btn = QPushButton("?")
    btn.setFixedSize(22, 22)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setObjectName("helpBtn")
    btn.setToolTip("Click for help")
    info = FIELD_HELP.get(help_key, {})
    title = info.get("title", help_key.replace("_", " ").title())
    desc = info.get("description", "No description available.")
    examples = info.get("examples", [])
    btn.clicked.connect(
        lambda _=False, t=title, d=desc, e=examples: _show_help_dialog(
            btn, t, d, e))
    return btn


def _with_help(widget, help_key):
    """Create a layout containing a widget and a help (?) button."""
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    layout.addWidget(widget, 1)
    layout.addWidget(_make_help_btn(help_key, widget), 0,
                     Qt.AlignmentFlag.AlignTop)
    return layout


def _btn_with_help(btn, help_key):
    """Group an action button with its help (?) button."""
    container = QWidget()
    container.setObjectName("helpWrapper")
    lay = QHBoxLayout(container)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(2)
    lay.addWidget(btn)
    lay.addWidget(_make_help_btn(help_key, container))
    return container


# ── Shared input fields panel (always visible, left side) ──

class SharedFieldsPanel(QWidget):
    """All input fields that are common across every model."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    @staticmethod
    def _required_label(text):
        lbl = QLabel(f'{text} <span style="color:#FF3B30;">*</span>')
        return lbl

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        form_layout = QVBoxLayout(inner)
        form_layout.setSpacing(10)

        # --- Task Configuration ---
        task_group = QGroupBox("Task Configuration")
        task_form = QFormLayout()
        task_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight)

        self.task_type = QComboBox()
        self.task_type.addItems(TASK_TYPES)
        task_form.addRow(self._required_label("Task Type:"),
                         _with_help(self.task_type, "task_type"))

        self.programming_lang = QComboBox()
        self.programming_lang.setEditable(True)
        self.programming_lang.addItems(PROGRAMMING_LANGUAGES)
        task_form.addRow("Programming Language:",
                         _with_help(self.programming_lang, "programming_lang"))

        task_group.setLayout(task_form)
        form_layout.addWidget(task_group)

        # --- Role & Tone ---
        role_group = QGroupBox("Role & Tone")
        role_form = QFormLayout()
        role_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight)

        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText(
            "e.g. Senior Python developer, Technical writer ...")
        role_form.addRow(
            self._required_label("Role / Persona:"),
            _with_help(self.role_input, "role"))

        self.tone = QComboBox()
        self.tone.addItems([
            "Professional", "Casual / Friendly", "Technical",
            "Academic / Formal", "Concise / Direct", "Creative",
            "Instructional", "Empathetic",
        ])
        role_form.addRow(self._required_label("Tone:"),
                         _with_help(self.tone, "tone"))

        self.audience = QComboBox()
        self.audience.setEditable(True)
        self.audience.addItems([
            "General audience", "Beginners", "Intermediate developers",
            "Senior engineers", "Non-technical stakeholders",
            "Students", "Executives", "Other",
        ])
        role_form.addRow("Target Audience:",
                         _with_help(self.audience, "audience"))

        role_group.setLayout(role_form)
        form_layout.addWidget(role_group)

        # --- Prompt Content ---
        content_group = QGroupBox("Prompt Content")
        content_form = QFormLayout()
        content_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight)

        self.context_input = QTextEdit()
        self.context_input.setPlaceholderText(
            "Provide background information or context for the task...")
        self.context_input.setMaximumHeight(90)
        content_form.addRow(
            self._required_label("Context:"),
            _with_help(self.context_input, "context"))

        self.instruction_input = QTextEdit()
        self.instruction_input.setPlaceholderText(
            "Describe the main task or question in detail...")
        self.instruction_input.setMaximumHeight(110)
        content_form.addRow(
            self._required_label("Main Instruction:"),
            _with_help(self.instruction_input, "instruction"))

        self.input_data = QTextEdit()
        self.input_data.setPlaceholderText(
            "Paste any input data, code snippets, or text to process "
            "(optional)...")
        self.input_data.setMaximumHeight(90)
        content_form.addRow("Input Data:",
                            _with_help(self.input_data, "input_data"))

        self.constraints_input = QTextEdit()
        self.constraints_input.setPlaceholderText(
            "List constraints, rules, or things to avoid (optional)...")
        self.constraints_input.setMaximumHeight(80)
        content_form.addRow("Constraints:",
                            _with_help(self.constraints_input, "constraints"))

        self.examples_input = QTextEdit()
        self.examples_input.setPlaceholderText(
            "Provide example input -> output pairs for few-shot prompting "
            "(optional)...")
        self.examples_input.setMaximumHeight(80)
        content_form.addRow("Examples:",
                            _with_help(self.examples_input, "examples"))

        content_group.setLayout(content_form)
        form_layout.addWidget(content_group)

        # --- Output Settings ---
        output_group = QGroupBox("Output Settings")
        output_form = QFormLayout()
        output_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight)

        self.output_format = QComboBox()
        self.output_format.addItems([
            "Markdown", "Plain Text", "JSON", "XML", "Code Only",
            "Bullet Points", "Numbered List", "Table", "Essay / Prose",
            "Step-by-step Guide",
        ])
        output_form.addRow(
            self._required_label("Output Format:"),
            _with_help(self.output_format, "output_format"))

        self.detail_level = QComboBox()
        self.detail_level.addItems([
            "Brief", "Moderate", "Detailed", "Comprehensive"])
        self.detail_level.setCurrentIndex(2)
        output_form.addRow(
            self._required_label("Detail Level:"),
            _with_help(self.detail_level, "detail_level"))

        self.output_language = QComboBox()
        self.output_language.setEditable(True)
        self.output_language.addItems([
            "English", "Spanish", "French", "German", "Italian",
            "Portuguese", "Chinese", "Japanese", "Korean",
            "Arabic", "Hindi", "Russian", "Dutch", "Slovenian", "Other",
        ])
        output_form.addRow("Output Language:",
                           _with_help(self.output_language, "output_language"))

        self.max_length = QComboBox()
        self.max_length.addItems([
            "No limit", "~100 words", "~250 words", "~500 words",
            "~1000 words", "~2000 words",
        ])
        output_form.addRow("Max Length:",
                           _with_help(self.max_length, "max_length"))

        output_group.setLayout(output_form)
        form_layout.addWidget(output_group)

        # --- Advanced Options ---
        adv_group = QGroupBox("Advanced Options")
        adv_form = QFormLayout()
        adv_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight)

        self.chain_of_thought = QCheckBox("Enable step-by-step reasoning")
        adv_form.addRow("Chain of Thought:",
                        _with_help(self.chain_of_thought, "chain_of_thought"))

        self.include_citations = QCheckBox("Request sources / references")
        adv_form.addRow("Citations:",
                        _with_help(self.include_citations, "citations"))

        self.temperature_hint = QComboBox()
        self.temperature_hint.addItems([
            "Default", "Precise (low creativity)",
            "Balanced", "Creative (high creativity)",
        ])
        adv_form.addRow("Creativity Hint:",
                        _with_help(self.temperature_hint, "creativity_hint"))

        self.additional_instructions = QLineEdit()
        self.additional_instructions.setPlaceholderText(
            "Any extra instructions to append...")
        adv_form.addRow("Extra Instructions:",
                        _with_help(self.additional_instructions,
                                   "extra_instructions"))

        adv_group.setLayout(adv_form)
        form_layout.addWidget(adv_group)

        form_layout.addStretch()
        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def collect(self):
        """Return all shared field values as a dict."""
        tone = self.tone.currentText()
        audience = self.audience.currentText()
        task = self.task_type.currentText()
        fmt = self.output_format.currentText()
        detail = self.detail_level.currentText()
        out_lang = self.output_language.currentText()
        max_len = self.max_length.currentText()
        lang = self.programming_lang.currentText()

        reqs = [
            f"- Format the response as {fmt.lower()}.",
            f"- Provide a {detail.lower()} level of detail.",
        ]
        if out_lang != "English":
            reqs.append(f"- Respond in {out_lang}.")
        if max_len != "No limit":
            reqs.append(f"- Keep the response within {max_len}.")

        return {
            "role": self.role_input.text().strip(),
            "guidance": TASK_GUIDANCE.get(task, ""),
            "lang": lang if lang != "(not applicable)" else "",
            "tone_line": (
                f"Use a {tone.lower()} tone, "
                f"targeting {audience.lower()}."
            ),
            "context": self.context_input.toPlainText().strip(),
            "examples": self.examples_input.toPlainText().strip(),
            "input_data": self.input_data.toPlainText().strip(),
            "instruction": self.instruction_input.toPlainText().strip(),
            "constraints": self.constraints_input.toPlainText().strip(),
            "output_reqs": "\n".join(reqs),
            "citations": self.include_citations.isChecked(),
            "creativity_hint": CREATIVITY_MAP.get(
                self.temperature_hint.currentText(), ""),
            "extra": self.additional_instructions.text().strip(),
        }

    def clear_all(self):
        """Reset every shared field to its default."""
        self.role_input.clear()
        self.context_input.clear()
        self.instruction_input.clear()
        self.input_data.clear()
        self.constraints_input.clear()
        self.examples_input.clear()
        self.additional_instructions.clear()
        self.task_type.setCurrentIndex(0)
        self.programming_lang.setCurrentIndex(0)
        self.tone.setCurrentIndex(0)
        self.audience.setCurrentIndex(0)
        self.output_format.setCurrentIndex(0)
        self.detail_level.setCurrentIndex(2)
        self.output_language.setCurrentIndex(0)
        self.max_length.setCurrentIndex(0)
        self.temperature_hint.setCurrentIndex(0)
        self.chain_of_thought.setChecked(False)
        self.include_citations.setChecked(False)


# ── Model-specific tab (right side, one per model) ──

class ModelTab(QWidget):
    """Model-specific options + output + buttons."""

    def __init__(self, config, shared_panel, parent=None):
        super().__init__(parent)
        self.config = config
        self.shared = shared_panel
        self.option_widgets = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # ── Model-specific options ──
        opts_group = QGroupBox(f"{self.config['name']} Options")
        opts_form = QFormLayout()
        opts_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight)

        for opt in self.config["specific_options"]:
            key = opt["key"]
            if opt["type"] == "combo":
                widget = QComboBox()
                widget.addItems(opt["items"])
                opts_form.addRow(opt["label"],
                                _with_help(widget, key))
            elif opt["type"] == "check":
                widget = QCheckBox(opt["label"])
                widget.setChecked(opt.get("default", False))
                opts_form.addRow("", _with_help(widget, key))
            else:
                continue
            self.option_widgets[key] = widget

        opts_group.setLayout(opts_form)
        layout.addWidget(opts_group)

        # ── Generated output ──
        out_label = QLabel(f"Output — {self.config['name']}")
        out_label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        out_label.setObjectName("outputLabel")
        layout.addWidget(out_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Cascadia Code", 10))
        self.output_text.setObjectName("outputArea")
        _soft_shadow(self.output_text, "#000000", 16, 3, 0.06)
        layout.addWidget(self.output_text, 1)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        generate_btn = self._make_btn(
            "Generate", "#007AFF", self._generate_prompt, primary=True)
        btn_row.addWidget(_btn_with_help(generate_btn, "btn_generate"))

        engine_btn = self._make_btn(
            "Engine", "#5856D6", self._generate_engine_prompt)
        btn_row.addWidget(_btn_with_help(engine_btn, "btn_engine"))

        copy_btn = self._make_btn(
            "Copy", "#34C759", self._copy_to_clipboard)
        btn_row.addWidget(_btn_with_help(copy_btn, "btn_copy"))

        save_btn = self._make_btn(
            "Save", "#FF9500", self._save_to_file)
        btn_row.addWidget(_btn_with_help(save_btn, "btn_save"))

        clear_btn = self._make_btn(
            "Clear", "#FF3B30", self._clear_all)
        btn_row.addWidget(_btn_with_help(clear_btn, "btn_clear"))

        layout.addLayout(btn_row)

    @staticmethod
    def _make_btn(label, color, slot, primary=False):
        btn = QPushButton(label)
        btn.setFixedHeight(32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            btn.setStyleSheet(
                f"QPushButton {{ background: {color}; color: #FFFFFF; "
                f"font-weight: 600; border: none; "
                f"border-radius: 8px; padding: 0 20px; "
                f"font-size: 10pt; }} "
                f"QPushButton:hover {{ background: qlineargradient("
                f"x1:0, y1:0, x2:0, y2:1, stop:0 {color}, "
                f"stop:1 #005EC4); }} "
                f"QPushButton:pressed {{ background: #004EA2; }}"
            )
        else:
            btn.setStyleSheet(
                f"QPushButton {{ background: #F2F2F7; color: {color}; "
                f"font-weight: 600; border: 1px solid #D1D1D6; "
                f"border-radius: 8px; padding: 0 16px; "
                f"font-size: 10pt; }} "
                f"QPushButton:hover {{ background: #E5E5EA; }} "
                f"QPushButton:pressed {{ background: #D1D1D6; }}"
            )
        btn.clicked.connect(slot)
        return btn

    # ── Data collection ──

    def _collect_model_fields(self):
        result = {}
        for key, widget in self.option_widgets.items():
            if isinstance(widget, QCheckBox):
                result[key] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                result[key] = widget.currentText()
        return result

    # ── Actions ──

    def _generate_prompt(self):
        shared = self.shared.collect()

        if not shared["instruction"]:
            QMessageBox.warning(self, "Missing Input",
                                "Please enter a Main Instruction.")
            return
        if not shared["role"]:
            QMessageBox.warning(self, "Missing Input",
                                "Please enter a Role / Persona.")
            return

        data = {**shared, **self._collect_model_fields()}
        data["cot"] = (self.config["cot_text"]
                       if self.shared.chain_of_thought.isChecked() else "")

        prompt = self.config["formatter"](data)
        self.output_text.setPlainText(prompt)

    def _generate_engine_prompt(self):
        """Generate a prompt via the Pydantic/Jinja2 engine layer."""
        shared = self.shared.collect()

        if not shared["instruction"]:
            QMessageBox.warning(self, "Missing Input",
                                "Please enter a Main Instruction.")
            return
        if not shared["role"]:
            QMessageBox.warning(self, "Missing Input",
                                "Please enter a Role / Persona.")
            return

        data = {**shared, **self._collect_model_fields()}
        data["cot"] = (self.config["cot_text"]
                       if self.shared.chain_of_thought.isChecked() else "")

        model_name: str = self.config["name"]
        fmt_label: str = self.shared.output_format.currentText()
        examples_raw: str = self.shared.examples_input.toPlainText().strip()
        enable_thinking: bool = data.get("extended_thinking", False)

        try:
            tpl: PromptTemplate = build_from_gui(
                data,
                model_name=model_name,
                output_format_label=fmt_label,
                enable_thinking=enable_thinking,
                examples_raw=examples_raw,
            )
            result = tpl.render_for_provider()
        except Exception as exc:
            QMessageBox.critical(
                self, "Engine Error",
                f"Prompt validation/render failed:\n{exc}",
            )
            return

        if isinstance(result, list):
            # OpenAI format: pretty-print the message list
            import json
            output = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            output = result

        self.output_text.setPlainText(output)

    def _copy_to_clipboard(self):
        text = self.output_text.toPlainText()
        if not text:
            QMessageBox.information(self, "Nothing to Copy",
                                    "Generate a prompt first.")
            return
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied",
                                "Prompt copied to clipboard.")

    def _save_to_file(self):
        text = self.output_text.toPlainText()
        if not text:
            QMessageBox.information(self, "Nothing to Save",
                                    "Generate a prompt first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Prompt", "",
            "Text Files (*.txt);;Markdown (*.md);;All Files (*)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            except OSError as e:
                QMessageBox.critical(self, "Error",
                                     f"Could not save file:\n{e}")
                return
            QMessageBox.information(self, "Saved",
                                    f"Prompt saved to {path}")

    def _clear_all(self):
        for opt in self.config["specific_options"]:
            widget = self.option_widgets.get(opt["key"])
            if widget is None:
                continue
            if isinstance(widget, QCheckBox):
                widget.setChecked(opt.get("default", False))
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
        self.output_text.clear()
        self.shared.clear_all()


# ── Main window ──

class PromptBuilderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Prompt Builder")
        self.setMinimumSize(1100, 800)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(10)

        # Title
        title = QLabel("AI Prompt Builder")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("appTitle")
        main_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "Select a model  \u2192  Configure  "
            "\u2192  Generate an optimized prompt")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("appSubtitle")
        main_layout.addWidget(subtitle)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)

        self.shared_panel = SharedFieldsPanel()
        splitter.addWidget(self.shared_panel)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setElideMode(Qt.TextElideMode.ElideNone)
        self.model_tabs = []
        for cfg in MODEL_CONFIGS:
            tab = ModelTab(cfg, self.shared_panel)
            self.tabs.addTab(tab, cfg["name"])
            self.model_tabs.append(tab)
        splitter.addWidget(self.tabs)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)

        # ── Apple-inspired stylesheet ──
        self.setStyleSheet("""
            /* ── Base ── */
            * {
                font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue",
                             "Arial", sans-serif;
            }
            QMainWindow, QWidget {
                background: #F5F5F7;
                color: #1D1D1F;
            }

            /* ── Title area ── */
            #appTitle {
                color: #1D1D1F;
                background: transparent;
                padding: 8px 4px 0px 4px;
            }
            #appSubtitle {
                color: #86868B;
                font-size: 10pt;
                background: transparent;
                padding-bottom: 8px;
            }

            /* ── Group boxes (card style) ── */
            QGroupBox {
                font-weight: 600; font-size: 10pt;
                color: #1D1D1F;
                border: 1px solid #D1D1D6;
                border-radius: 12px;
                margin-top: 16px; padding: 22px 14px 14px 14px;
                background: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px; padding: 0 8px;
                color: #1D1D1F;
                background: #FFFFFF;
            }

            /* ── Labels ── */
            QLabel {
                font-size: 10pt;
                color: #3A3A3C;
                background: transparent;
            }

            /* ── Input fields ── */
            QLineEdit, QTextEdit, QComboBox {
                font-size: 10pt; padding: 6px 10px;
                background: #FFFFFF;
                color: #1D1D1F;
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                selection-background-color: #007AFF;
                selection-color: #FFFFFF;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:on {
                border: 2px solid #007AFF;
            }
            QLineEdit::placeholder, QTextEdit::placeholder {
                color: #AEAEB2;
            }
            QComboBox {
                min-height: 30px;
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
                width: 28px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #86868B;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: #FFFFFF;
                color: #1D1D1F;
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                selection-background-color: #007AFF;
                selection-color: #FFFFFF;
                outline: none;
                padding: 4px;
            }

            /* ── Checkboxes ── */
            QCheckBox {
                font-size: 10pt;
                color: #3A3A3C;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px; height: 18px;
                border: 2px solid #C7C7CC;
                border-radius: 5px;
                background: #FFFFFF;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #007AFF;
            }
            QCheckBox::indicator:checked {
                background: #007AFF;
                border: 2px solid #007AFF;
            }

            /* ── Tabs (segmented control look) ── */
            QTabWidget::pane {
                border: 1px solid #D1D1D6;
                border-radius: 12px;
                background: #FFFFFF;
                top: -1px;
            }
            QTabBar::tab {
                font-size: 10pt; font-weight: 500;
                padding: 8px 22px;
                color: #86868B;
                background: #E5E5EA;
                border: 1px solid #D1D1D6;
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                color: #007AFF;
                border-bottom: 2px solid #007AFF;
            }
            QTabBar::tab:!selected:hover {
                background: #F2F2F7;
                color: #3A3A3C;
            }

            /* ── Output area ── */
            #outputLabel {
                color: #1D1D1F;
                background: transparent;
                font-size: 12pt;
                padding: 4px 0;
            }
            #outputArea {
                background: #FAFAFA;
                color: #1D1D1F;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                padding: 12px;
                font-family: "Cascadia Code", "SF Mono", "Menlo",
                             "Consolas", monospace;
            }
            #outputArea:focus {
                border: 2px solid #007AFF;
            }

            /* ── Scrollbars (minimal, Apple-style) ── */
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                border: none;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #C7C7CC;
                min-height: 40px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #AEAEB2;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px;
                background: transparent;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                border: none;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #C7C7CC;
                min-width: 40px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #AEAEB2;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                width: 0px;
                background: transparent;
            }

            /* ── Splitter ── */
            QSplitter::handle {
                background: #E5E5EA;
                width: 1px;
            }
            QSplitter::handle:hover {
                background: #007AFF;
            }

            /* ── Message boxes ── */
            QMessageBox {
                background: #F5F5F7;
            }
            QMessageBox QLabel {
                color: #1D1D1F;
                font-size: 10pt;
            }
            QMessageBox QPushButton {
                background: #007AFF;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 6px 24px;
                font-weight: 600;
                min-width: 70px;
            }
            QMessageBox QPushButton:hover {
                background: #005EC4;
            }

            /* ── File dialog ── */
            QFileDialog {
                background: #F5F5F7;
                color: #1D1D1F;
            }

            /* ── Form layout spacing ── */
            QFormLayout {
                spacing: 8px;
            }

            /* ── Help buttons ── */
            #helpBtn {
                background: #E5E5EA;
                color: #007AFF;
                border: none;
                border-radius: 11px;
                font-size: 9pt;
                font-weight: 700;
            }
            #helpBtn:hover {
                background: #007AFF;
                color: #FFFFFF;
            }
            #helpBtn:pressed {
                background: #005EC4;
                color: #FFFFFF;
            }
            #helpWrapper {
                background: transparent;
                border: none;
            }
        """)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PromptBuilderApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
