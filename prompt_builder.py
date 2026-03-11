import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton, QGroupBox,
    QFormLayout, QSplitter, QMessageBox, QCheckBox,
    QScrollArea, QFrame, QFileDialog, QTabWidget, QMenu
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


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
# Each receives a dict with collected field values and returns the prompt string.

def _format_claude(d):
    """Claude: XML tags (recommended by Anthropic) or Markdown fallback."""
    use_xml = d["use_xml"]

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
    # -- System message: identity, behaviour, tone --
    sys_parts = [f"You are {d['role']}."]
    if d["guidance"]:
        sys_parts.append(d["guidance"])
    if d["lang"]:
        sys_parts.append(f"Use {d['lang']} as the programming language.")
    sys_parts.append(d["tone_line"])
    if d["creativity_hint"]:
        sys_parts.append(d["creativity_hint"])
    system_msg = " ".join(sys_parts)

    # -- User message: context → examples → data → task → constraints → reqs --
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
    if d["cot"]:
        user_parts.append(d["cot"])
    if d["citations"]:
        user_parts.append(
            "Please include references or sources where applicable.")
    if d["extra"]:
        user_parts.append(d["extra"])
    user_msg = "\n\n".join(user_parts)

    return f"# System Message\n{system_msg}\n\n# User Message\n{user_msg}"


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
        "xml_default": True,
        "show_xml_toggle": True,
        "cot_label": "Ask Claude to reason in <thinking> tags",
        "cot_text": (
            "Before answering, work through your reasoning inside "
            "<thinking> tags. Then provide your final answer outside "
            "those tags."
        ),
        "formatter": _format_claude,
    },
    {
        "name": "ChatGPT",
        "accent": "#10A37F",
        "accent_hover": "#0E8C6B",
        "xml_default": False,
        "show_xml_toggle": False,
        "cot_label": "Ask ChatGPT to think step-by-step",
        "cot_text": (
            "Let's approach this step by step. Think carefully "
            "before giving your final answer."
        ),
        "formatter": _format_chatgpt,
    },
    {
        "name": "Gemini",
        "accent": "#4285F4",
        "accent_hover": "#3367C7",
        "xml_default": False,
        "show_xml_toggle": False,
        "cot_label": "Ask Gemini to think step-by-step",
        "cot_text": (
            "Think through this step-by-step, explaining your reasoning "
            "at each stage before providing your final answer."
        ),
        "formatter": _format_gemini,
    },
    {
        "name": "Copilot",
        "accent": "#0078D4",
        "accent_hover": "#005FA3",
        "xml_default": False,
        "show_xml_toggle": False,
        "cot_label": "Ask Copilot to reason step-by-step",
        "cot_text": (
            "Break this down step by step. Show your reasoning "
            "before giving the final answer."
        ),
        "formatter": _format_copilot,
    },
]


# ── Reusable prompt-builder tab (one per model) ──

class PromptBuilderTab(QWidget):
    """Self-contained prompt builder form + output panel for one AI model."""

    # Set by PromptBuilderApp after all tabs are created
    send_to_callback = None

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._build_form()

    @staticmethod
    def _required_label(text):
        return QLabel(f'{text} <span style="color:red;">*</span>')

    def _build_form(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)

        # ── Left panel (scrollable inputs) ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(10)

        # --- Task Configuration ---
        task_group = QGroupBox("Task Configuration")
        task_form = QFormLayout()
        task_form.setLabelAlignment(Qt.AlignRight)

        self.task_type = QComboBox()
        self.task_type.addItems(TASK_TYPES)
        task_form.addRow(self._required_label("Task Type:"), self.task_type)

        self.programming_lang = QComboBox()
        self.programming_lang.setEditable(True)
        self.programming_lang.addItems(PROGRAMMING_LANGUAGES)
        task_form.addRow("Programming Language:", self.programming_lang)

        task_group.setLayout(task_form)
        left_layout.addWidget(task_group)

        # --- Role & Tone ---
        role_group = QGroupBox("Role & Tone")
        role_form = QFormLayout()
        role_form.setLabelAlignment(Qt.AlignRight)

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
        left_layout.addWidget(role_group)

        # --- Prompt Content ---
        content_group = QGroupBox("Prompt Content")
        content_form = QFormLayout()
        content_form.setLabelAlignment(Qt.AlignRight)

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
        left_layout.addWidget(content_group)

        # --- Output Settings ---
        output_group = QGroupBox("Output Settings")
        output_form = QFormLayout()
        output_form.setLabelAlignment(Qt.AlignRight)

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
        left_layout.addWidget(output_group)

        # --- Advanced Options ---
        adv_group = QGroupBox("Advanced Options")
        adv_form = QFormLayout()
        adv_form.setLabelAlignment(Qt.AlignRight)

        self.chain_of_thought = QCheckBox(self.config["cot_label"])
        adv_form.addRow("Chain of Thought:", self.chain_of_thought)

        self.include_citations = QCheckBox("Request sources / references")
        adv_form.addRow("Citations:", self.include_citations)

        # XML toggle — only shown for models that benefit from it
        self.xml_tags = QCheckBox("Wrap prompt sections in XML tags")
        self.xml_tags.setChecked(self.config["xml_default"])
        if self.config["show_xml_toggle"]:
            adv_form.addRow("XML Tags:", self.xml_tags)

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
        left_layout.addWidget(adv_group)

        left_layout.addStretch()
        scroll.setWidget(left_widget)
        splitter.addWidget(scroll)

        # ── Right panel (output + buttons) ──
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(8)

        out_label = QLabel(f"Generated Prompt — {self.config['name']}")
        out_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        right_layout.addWidget(out_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setStyleSheet(
            "QTextEdit { background: #1E1E2E; color: #CDD6F4; "
            "border: 1px solid #45475A; border-radius: 6px; padding: 8px; }"
        )
        right_layout.addWidget(self.output_text, 1)

        # Buttons
        btn_row = QHBoxLayout()
        accent = self.config["accent"]
        accent_hover = self.config["accent_hover"]

        self.generate_btn = QPushButton("Generate Prompt")
        self.generate_btn.setFixedHeight(38)
        self.generate_btn.setStyleSheet(
            f"QPushButton {{ background: {accent}; color: white; "
            f"font-weight: bold; border-radius: 6px; padding: 0 20px; }} "
            f"QPushButton:hover {{ background: {accent_hover}; }}"
        )
        self.generate_btn.clicked.connect(self._generate_prompt)
        btn_row.addWidget(self.generate_btn)

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setFixedHeight(38)
        copy_btn.setStyleSheet(
            "QPushButton { background: #6D28D9; color: white; "
            "font-weight: bold; border-radius: 6px; padding: 0 20px; } "
            "QPushButton:hover { background: #5B21B6; }"
        )
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_row.addWidget(copy_btn)

        save_btn = QPushButton("Save to File")
        save_btn.setFixedHeight(38)
        save_btn.setStyleSheet(
            "QPushButton { background: #059669; color: white; "
            "font-weight: bold; border-radius: 6px; padding: 0 20px; } "
            "QPushButton:hover { background: #047857; }"
        )
        save_btn.clicked.connect(self._save_to_file)
        btn_row.addWidget(save_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.setFixedHeight(38)
        clear_btn.setStyleSheet(
            "QPushButton { background: #DC2626; color: white; "
            "font-weight: bold; border-radius: 6px; padding: 0 20px; } "
            "QPushButton:hover { background: #B91C1C; }"
        )
        clear_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(clear_btn)

        # "Send to..." button with dropdown menu for other models
        self.send_btn = QPushButton("Send to...")
        self.send_btn.setFixedHeight(38)
        self.send_btn.setStyleSheet(
            "QPushButton { background: #475569; color: white; "
            "font-weight: bold; border-radius: 6px; padding: 0 20px; } "
            "QPushButton:hover { background: #334155; } "
            "QPushButton::menu-indicator { subcontrol-position: right center; "
            "subcontrol-origin: padding; right: 6px; }"
        )
        self.send_menu = QMenu(self)
        self.send_btn.setMenu(self.send_menu)
        btn_row.addWidget(self.send_btn)

        right_layout.addLayout(btn_row)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 5)

    # ── Collect field values into a dict for the formatter ──

    def _collect_fields(self):
        tone = self.tone.currentText()
        audience = self.audience.currentText()
        task = self.task_type.currentText()
        fmt = self.output_format.currentText()
        detail = self.detail_level.currentText()
        out_lang = self.output_language.currentText()
        max_len = self.max_length.currentText()

        reqs = [
            f"- Format the response as {fmt.lower()}.",
            f"- Provide a {detail.lower()} level of detail.",
        ]
        if out_lang != "English":
            reqs.append(f"- Respond in {out_lang}.")
        if max_len != "No limit":
            reqs.append(f"- Keep the response within {max_len}.")

        lang = self.programming_lang.currentText()

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
            "cot": (self.config["cot_text"]
                    if self.chain_of_thought.isChecked() else ""),
            "citations": self.include_citations.isChecked(),
            "creativity_hint": CREATIVITY_MAP.get(
                self.temperature_hint.currentText(), ""),
            "extra": self.additional_instructions.text().strip(),
            "use_xml": self.xml_tags.isChecked(),
        }

    # ── Actions ──

    def _generate_prompt(self):
        instruction = self.instruction_input.toPlainText().strip()
        if not instruction:
            QMessageBox.warning(self, "Missing Input",
                                "Please enter a Main Instruction.")
            return
        role = self.role_input.text().strip()
        if not role:
            QMessageBox.warning(self, "Missing Input",
                                "Please enter a Role / Persona.")
            return

        data = self._collect_fields()
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

    def export_state(self):
        """Return all user-entered field values as a dict."""
        return {
            "role": self.role_input.text(),
            "context": self.context_input.toPlainText(),
            "instruction": self.instruction_input.toPlainText(),
            "input_data": self.input_data.toPlainText(),
            "constraints": self.constraints_input.toPlainText(),
            "examples": self.examples_input.toPlainText(),
            "extra": self.additional_instructions.text(),
            "task_type": self.task_type.currentIndex(),
            "programming_lang": self.programming_lang.currentText(),
            "tone": self.tone.currentIndex(),
            "audience": self.audience.currentText(),
            "output_format": self.output_format.currentIndex(),
            "detail_level": self.detail_level.currentIndex(),
            "output_language": self.output_language.currentText(),
            "max_length": self.max_length.currentIndex(),
            "temperature_hint": self.temperature_hint.currentIndex(),
            "chain_of_thought": self.chain_of_thought.isChecked(),
            "include_citations": self.include_citations.isChecked(),
        }

    def import_state(self, state):
        """Populate all fields from a state dict."""
        self.role_input.setText(state.get("role", ""))
        self.context_input.setPlainText(state.get("context", ""))
        self.instruction_input.setPlainText(state.get("instruction", ""))
        self.input_data.setPlainText(state.get("input_data", ""))
        self.constraints_input.setPlainText(state.get("constraints", ""))
        self.examples_input.setPlainText(state.get("examples", ""))
        self.additional_instructions.setText(state.get("extra", ""))
        self.task_type.setCurrentIndex(state.get("task_type", 0))
        # Editable combos: set text directly to handle custom entries
        self.programming_lang.setEditText(state.get("programming_lang", ""))
        self.tone.setCurrentIndex(state.get("tone", 0))
        self.audience.setEditText(state.get("audience", ""))
        self.output_format.setCurrentIndex(state.get("output_format", 0))
        self.detail_level.setCurrentIndex(state.get("detail_level", 2))
        self.output_language.setEditText(state.get("output_language", ""))
        self.max_length.setCurrentIndex(state.get("max_length", 0))
        self.temperature_hint.setCurrentIndex(
            state.get("temperature_hint", 0))
        self.chain_of_thought.setChecked(state.get("chain_of_thought", False))
        self.include_citations.setChecked(
            state.get("include_citations", False))
        # Clear the generated output — user should re-generate for new model
        self.output_text.clear()

    def _clear_all(self):
        self.role_input.clear()
        self.context_input.clear()
        self.instruction_input.clear()
        self.input_data.clear()
        self.constraints_input.clear()
        self.examples_input.clear()
        self.additional_instructions.clear()
        self.output_text.clear()
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
        self.xml_tags.setChecked(self.config["xml_default"])


# ── Main window with tabbed interface ──

class PromptBuilderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Prompt Builder")
        self.setMinimumSize(1000, 800)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Title
        title = QLabel("AI Prompt Builder")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #334155; padding: 6px;")
        main_layout.addWidget(title)

        # Tab widget — one tab per AI model
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.model_tabs = []
        for cfg in MODEL_CONFIGS:
            tab = PromptBuilderTab(cfg)
            self.tabs.addTab(tab, cfg["name"])
            self.model_tabs.append(tab)
        main_layout.addWidget(self.tabs, 1)

        # Wire up "Send to..." menus — each tab gets actions for other models
        for src_idx, src_tab in enumerate(self.model_tabs):
            for dst_idx, dst_cfg in enumerate(MODEL_CONFIGS):
                if dst_idx == src_idx:
                    continue
                action = src_tab.send_menu.addAction(dst_cfg["name"])
                # Capture indices via default args
                action.triggered.connect(
                    lambda _checked, s=src_idx, d=dst_idx:
                        self._send_to_model(s, d)
                )

    def _send_to_model(self, src_idx, dst_idx):
        """Copy all fields from source tab to destination tab and switch."""
        state = self.model_tabs[src_idx].export_state()
        self.model_tabs[dst_idx].import_state(state)
        self.tabs.setCurrentIndex(dst_idx)

        self.setStyleSheet("""
            QMainWindow { background: #F8FAFC; }
            QGroupBox {
                font-weight: bold; font-size: 11pt;
                border: 1px solid #CBD5E1; border-radius: 8px;
                margin-top: 14px; padding-top: 18px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 12px; padding: 0 6px;
            }
            QLabel { font-size: 10pt; }
            QLineEdit, QTextEdit, QComboBox {
                font-size: 10pt; padding: 4px;
                border: 1px solid #CBD5E1; border-radius: 4px;
            }
            QComboBox { min-height: 26px; }
            QCheckBox { font-size: 10pt; }
            QTabWidget::pane {
                border: 1px solid #CBD5E1; border-radius: 6px;
                background: #F8FAFC;
            }
            QTabBar::tab {
                font-size: 9pt; font-weight: bold;
                padding: 6px 16px;
                border: 1px solid #CBD5E1;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                background: #E2E8F0;
            }
            QTabBar::tab:selected {
                background: #F8FAFC;
                border-bottom: 2px solid #F8FAFC;
            }
            QTabBar::tab:hover {
                background: #F1F5F9;
            }
        """)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PromptBuilderApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
