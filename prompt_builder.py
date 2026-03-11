import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QGroupBox,
    QFormLayout, QSplitter, QMessageBox, QCheckBox,
    QScrollArea, QFrame, QFileDialog, QTabWidget, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor


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

def _glow(widget, color="#00FF41", radius=18, opacity=0.35):
    """Apply a subtle glow (drop-shadow) effect to a widget."""
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(radius)
    fx.setOffset(0, 0)
    fx.setColor(QColor(color))
    fx.setEnabled(True)
    # QGraphicsDropShadowEffect doesn't have setOpacity; control via color alpha
    c = QColor(color)
    c.setAlphaF(opacity)
    fx.setColor(c)
    widget.setGraphicsEffect(fx)


# ── Shared input fields panel (always visible, left side) ──

class SharedFieldsPanel(QWidget):
    """All input fields that are common across every model."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    @staticmethod
    def _required_label(text):
        lbl = QLabel(f'{text} <span style="color:#FF4444;">*</span>')
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
        task_form.addRow(self._required_label("Task Type:"), self.task_type)

        self.programming_lang = QComboBox()
        self.programming_lang.setEditable(True)
        self.programming_lang.addItems(PROGRAMMING_LANGUAGES)
        task_form.addRow("Programming Language:", self.programming_lang)

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
            self._required_label("Role / Persona:"), self.role_input)

        self.tone = QComboBox()
        self.tone.addItems([
            "Professional", "Casual / Friendly", "Technical",
            "Academic / Formal", "Concise / Direct", "Creative",
            "Instructional", "Empathetic",
        ])
        role_form.addRow(self._required_label("Tone:"), self.tone)

        self.audience = QComboBox()
        self.audience.setEditable(True)
        self.audience.addItems([
            "General audience", "Beginners", "Intermediate developers",
            "Senior engineers", "Non-technical stakeholders",
            "Students", "Executives", "Other",
        ])
        role_form.addRow("Target Audience:", self.audience)

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
            self._required_label("Context:"), self.context_input)

        self.instruction_input = QTextEdit()
        self.instruction_input.setPlaceholderText(
            "Describe the main task or question in detail...")
        self.instruction_input.setMaximumHeight(110)
        content_form.addRow(
            self._required_label("Main Instruction:"), self.instruction_input)

        self.input_data = QTextEdit()
        self.input_data.setPlaceholderText(
            "Paste any input data, code snippets, or text to process "
            "(optional)...")
        self.input_data.setMaximumHeight(90)
        content_form.addRow("Input Data:", self.input_data)

        self.constraints_input = QTextEdit()
        self.constraints_input.setPlaceholderText(
            "List constraints, rules, or things to avoid (optional)...")
        self.constraints_input.setMaximumHeight(80)
        content_form.addRow("Constraints:", self.constraints_input)

        self.examples_input = QTextEdit()
        self.examples_input.setPlaceholderText(
            "Provide example input -> output pairs for few-shot prompting "
            "(optional)...")
        self.examples_input.setMaximumHeight(80)
        content_form.addRow("Examples:", self.examples_input)

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
            self._required_label("Output Format:"), self.output_format)

        self.detail_level = QComboBox()
        self.detail_level.addItems([
            "Brief", "Moderate", "Detailed", "Comprehensive"])
        self.detail_level.setCurrentIndex(2)
        output_form.addRow(
            self._required_label("Detail Level:"), self.detail_level)

        self.output_language = QComboBox()
        self.output_language.setEditable(True)
        self.output_language.addItems([
            "English", "Spanish", "French", "German", "Italian",
            "Portuguese", "Chinese", "Japanese", "Korean",
            "Arabic", "Hindi", "Russian", "Dutch", "Slovenian", "Other",
        ])
        output_form.addRow("Output Language:", self.output_language)

        self.max_length = QComboBox()
        self.max_length.addItems([
            "No limit", "~100 words", "~250 words", "~500 words",
            "~1000 words", "~2000 words",
        ])
        output_form.addRow("Max Length:", self.max_length)

        output_group.setLayout(output_form)
        form_layout.addWidget(output_group)

        # --- Advanced Options ---
        adv_group = QGroupBox("Advanced Options")
        adv_form = QFormLayout()
        adv_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight)

        self.chain_of_thought = QCheckBox("Enable step-by-step reasoning")
        adv_form.addRow("Chain of Thought:", self.chain_of_thought)

        self.include_citations = QCheckBox("Request sources / references")
        adv_form.addRow("Citations:", self.include_citations)

        self.temperature_hint = QComboBox()
        self.temperature_hint.addItems([
            "Default", "Precise (low creativity)",
            "Balanced", "Creative (high creativity)",
        ])
        adv_form.addRow("Creativity Hint:", self.temperature_hint)

        self.additional_instructions = QLineEdit()
        self.additional_instructions.setPlaceholderText(
            "Any extra instructions to append...")
        adv_form.addRow("Extra Instructions:", self.additional_instructions)

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
                opts_form.addRow(opt["label"], widget)
            elif opt["type"] == "check":
                widget = QCheckBox(opt["label"])
                widget.setChecked(opt.get("default", False))
                opts_form.addRow("", widget)
            else:
                continue
            self.option_widgets[key] = widget

        opts_group.setLayout(opts_form)
        layout.addWidget(opts_group)

        # ── Generated output ──
        out_label = QLabel(f"\u25b8 output://{self.config['name'].lower()}")
        out_label.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        out_label.setObjectName("outputLabel")
        layout.addWidget(out_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setObjectName("outputArea")
        layout.addWidget(self.output_text, 1)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        generate_btn = self._make_btn(
            "GENERATE", "#00FF41", self._generate_prompt)
        _glow(generate_btn, "#00FF41", 20, 0.4)
        btn_row.addWidget(generate_btn)

        copy_btn = self._make_btn(
            "COPY", "#00BFFF", self._copy_to_clipboard)
        btn_row.addWidget(copy_btn)

        save_btn = self._make_btn(
            "SAVE", "#FFD700", self._save_to_file)
        btn_row.addWidget(save_btn)

        clear_btn = self._make_btn(
            "CLEAR", "#FF4444", self._clear_all)
        btn_row.addWidget(clear_btn)

        layout.addLayout(btn_row)

    @staticmethod
    def _make_btn(label, color, slot):
        btn = QPushButton(f"[ {label} ]")
        btn.setFixedHeight(36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background: #0c0c0c; color: {color}; "
            f"font-weight: bold; border: 1px solid {color}; "
            f"border-radius: 2px; padding: 0 16px; "
            f"font-family: Consolas; font-size: 9pt; }} "
            f"QPushButton:hover {{ background: {color}; color: #0a0a0a; }} "
            f"QPushButton:pressed {{ background: {color}; color: #0a0a0a; "
            f"border: 2px solid {color}; }}"
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

        # Title with glow
        title = QLabel("> AI_PROMPT_BUILDER")
        title.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("appTitle")
        _glow(title, "#00FF41", 30, 0.5)
        main_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "// select model tab  \u2192  configure  "
            "\u2192  generate optimized prompt")
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

        # ── Premium hacker stylesheet ──
        self.setStyleSheet("""
            /* ── Base ── */
            * {
                font-family: "Consolas", "Fira Code", "Courier New", monospace;
            }
            QMainWindow, QWidget {
                background: #08080a;
                color: #b0b8c0;
            }

            /* ── Title area ── */
            #appTitle {
                color: #00FF41;
                background: transparent;
                padding: 4px;
                letter-spacing: 2px;
            }
            #appSubtitle {
                color: #3a5a3a;
                font-size: 9pt;
                background: transparent;
                padding-bottom: 6px;
            }

            /* ── Group boxes ── */
            QGroupBox {
                font-weight: bold; font-size: 10pt;
                color: #00cc55;
                border: 1px solid #1a2e1a;
                border-radius: 3px;
                margin-top: 14px; padding-top: 20px;
                background: #0a0c0a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px; padding: 0 8px;
                color: #00cc55;
                background: #0a0c0a;
            }

            /* ── Labels ── */
            QLabel {
                font-size: 10pt;
                color: #8a9a8a;
                background: transparent;
            }

            /* ── Input fields ── */
            QLineEdit, QTextEdit, QComboBox {
                font-size: 10pt; padding: 5px 6px;
                background: #0e100e;
                color: #c0d0c0;
                border: 1px solid #1a2e1a;
                border-radius: 2px;
                selection-background-color: #00FF41;
                selection-color: #08080a;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:on {
                border: 1px solid #00cc55;
            }
            QLineEdit::placeholder, QTextEdit::placeholder {
                color: #2a3a2a;
            }
            QComboBox {
                min-height: 28px;
            }
            QComboBox::drop-down {
                border: none;
                background: #121412;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #00cc55;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background: #0e100e;
                color: #c0d0c0;
                border: 1px solid #00cc55;
                selection-background-color: #00cc55;
                selection-color: #08080a;
                outline: none;
                padding: 2px;
            }

            /* ── Checkboxes ── */
            QCheckBox {
                font-size: 10pt;
                color: #8a9a8a;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 1px solid #1a2e1a;
                border-radius: 2px;
                background: #0e100e;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #00cc55;
            }
            QCheckBox::indicator:checked {
                background: #00cc55;
                border: 1px solid #00cc55;
            }

            /* ── Tabs ── */
            QTabWidget::pane {
                border: 1px solid #1a2e1a;
                border-radius: 2px;
                background: #08080a;
                top: -1px;
            }
            QTabBar::tab {
                font-size: 9pt; font-weight: bold;
                padding: 7px 18px;
                color: #3a6a3a;
                background: #0a0c0a;
                border: 1px solid #1a2e1a;
                border-bottom: none;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #08080a;
                color: #00FF41;
                border-bottom: 2px solid #00FF41;
            }
            QTabBar::tab:!selected:hover {
                background: #0e120e;
                color: #00cc55;
            }

            /* ── Output area ── */
            #outputLabel {
                color: #00cc55;
                background: transparent;
                font-size: 11pt;
                padding: 2px 0;
            }
            #outputArea {
                background: #050605;
                color: #00FF41;
                border: 1px solid #0f1f0f;
                border-radius: 2px;
                padding: 10px;
            }
            #outputArea:focus {
                border: 1px solid #00cc55;
            }

            /* ── Scrollbars ── */
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #0a0c0a;
                width: 8px;
                border: none;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #1a2e1a;
                min-height: 40px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #00cc55;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0px;
                background: transparent;
            }
            QScrollBar:horizontal {
                background: #0a0c0a;
                height: 8px;
                border: none;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #1a2e1a;
                min-width: 40px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #00cc55;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                width: 0px;
                background: transparent;
            }

            /* ── Splitter ── */
            QSplitter::handle {
                background: #1a2e1a;
                width: 1px;
            }
            QSplitter::handle:hover {
                background: #00cc55;
            }

            /* ── Message boxes ── */
            QMessageBox {
                background: #0a0c0a;
            }
            QMessageBox QLabel {
                color: #c0d0c0;
                font-size: 10pt;
            }
            QMessageBox QPushButton {
                background: #0e100e;
                color: #00cc55;
                border: 1px solid #1a2e1a;
                border-radius: 2px;
                padding: 6px 24px;
                font-weight: bold;
                min-width: 70px;
            }
            QMessageBox QPushButton:hover {
                background: #00cc55;
                color: #08080a;
                border: 1px solid #00cc55;
            }

            /* ── File dialog ── */
            QFileDialog {
                background: #0a0c0a;
                color: #c0d0c0;
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
