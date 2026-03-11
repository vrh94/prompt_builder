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
    "gui_language": {
        "title": "GUI Language",
        "description": "Change the display language of the user interface. This affects labels, buttons, and group titles. It does not change the generated prompt content or help dialog details.",
        "examples": [
            "English \u2014 default interface language",
            "Sloven\u0161\u010dina \u2014 Slovenian interface",
            "Espa\u00f1ol \u2014 Spanish interface",
            "Deutsch \u2014 German interface",
            "Fran\u00e7ais \u2014 French interface",
        ],
    },
}

# ── GUI language translations ──

GUI_STRINGS = {
    "en": {
        "window_title": "AI Prompt Builder",
        "app_title": "AI Prompt Builder",
        "app_subtitle": "Select a model  \u2192  Configure  \u2192  Generate an optimized prompt",
        "gui_language": "GUI Language:",
        "group_task": "Task Configuration",
        "group_role": "Role & Tone",
        "group_content": "Prompt Content",
        "group_output": "Output Settings",
        "group_advanced": "Advanced Options",
        "lbl_task_type": "Task Type:",
        "lbl_prog_lang": "Programming Language:",
        "lbl_role": "Role / Persona:",
        "lbl_tone": "Tone:",
        "lbl_audience": "Target Audience:",
        "lbl_context": "Context:",
        "lbl_instruction": "Main Instruction:",
        "lbl_input_data": "Input Data:",
        "lbl_constraints": "Constraints:",
        "lbl_examples": "Examples:",
        "lbl_output_format": "Output Format:",
        "lbl_detail_level": "Detail Level:",
        "lbl_output_language": "Output Language:",
        "lbl_max_length": "Max Length:",
        "lbl_cot": "Chain of Thought:",
        "lbl_citations": "Citations:",
        "lbl_creativity": "Creativity Hint:",
        "lbl_extra": "Extra Instructions:",
        "chk_cot": "Enable step-by-step reasoning",
        "chk_citations": "Request sources / references",
        "opt_model": "Model:",
        "opt_mode": "Mode:",
        "opt_safety": "Safety Level:",
        "chk_xml_tags": "Wrap sections in XML tags (recommended)",
        "chk_extended_thinking": "Enable extended thinking",
        "chk_system_user_split": "Format as System + User messages",
        "chk_json_mode": "Strict JSON output mode",
        "chk_grounding": "Google Search grounding",
        "chk_code_first": "Code-first output (code before explanation)",
        "chk_web_search": "Enable web search references",
        "ph_role": "e.g. Senior Python developer, Technical writer ...",
        "ph_context": "Provide background information or context for the task...",
        "ph_instruction": "Describe the main task or question in detail...",
        "ph_input_data": "Paste any input data, code snippets, or text to process (optional)...",
        "ph_constraints": "List constraints, rules, or things to avoid (optional)...",
        "ph_examples": "Provide example input -> output pairs for few-shot prompting (optional)...",
        "ph_extra": "Any extra instructions to append...",
        "btn_generate": "Generate",
        "btn_engine": "Engine",
        "btn_copy": "Copy",
        "btn_save": "Save",
        "btn_clear": "Clear",
        "output_label": "Output \u2014 {model}",
        "options_label": "{model} Options",
        "msg_missing_input": "Missing Input",
        "msg_missing_instruction": "Please enter a Main Instruction.",
        "msg_missing_role": "Please enter a Role / Persona.",
        "msg_nothing_copy_title": "Nothing to Copy",
        "msg_nothing_copy": "Generate a prompt first.",
        "msg_copied_title": "Copied",
        "msg_copied": "Prompt copied to clipboard.",
        "msg_nothing_save_title": "Nothing to Save",
        "msg_nothing_save": "Generate a prompt first.",
        "msg_saved_title": "Saved",
        "msg_saved": "Prompt saved to {path}",
        "msg_error": "Error",
        "msg_save_fail": "Could not save file:\n{error}",
        "msg_engine_error": "Engine Error",
        "msg_engine_fail": "Prompt validation/render failed:\n{error}",
        "msg_save_dialog": "Save Prompt",
    },
    "sl": {
        "window_title": "Graditelj AI pozivov",
        "app_title": "Graditelj AI pozivov",
        "app_subtitle": "Izberite model  \u2192  Konfigurirajte  \u2192  Generirajte optimiziran poziv",
        "gui_language": "Jezik vmesnika:",
        "group_task": "Konfiguracija naloge",
        "group_role": "Vloga in ton",
        "group_content": "Vsebina poziva",
        "group_output": "Nastavitve izhoda",
        "group_advanced": "Napredne mo\u017enosti",
        "lbl_task_type": "Vrsta naloge:",
        "lbl_prog_lang": "Programski jezik:",
        "lbl_role": "Vloga / Persona:",
        "lbl_tone": "Ton:",
        "lbl_audience": "Ciljna publika:",
        "lbl_context": "Kontekst:",
        "lbl_instruction": "Glavno navodilo:",
        "lbl_input_data": "Vhodni podatki:",
        "lbl_constraints": "Omejitve:",
        "lbl_examples": "Primeri:",
        "lbl_output_format": "Format izhoda:",
        "lbl_detail_level": "Raven podrobnosti:",
        "lbl_output_language": "Jezik izhoda:",
        "lbl_max_length": "Najve\u010dja dol\u017eina:",
        "lbl_cot": "Veri\u017eno razmi\u0161ljanje:",
        "lbl_citations": "Citati:",
        "lbl_creativity": "Namig za kreativnost:",
        "lbl_extra": "Dodatna navodila:",
        "chk_cot": "Omogo\u010di razmi\u0161ljanje po korakih",
        "chk_citations": "Zahtevaj vire / reference",
        "opt_model": "Model:",
        "opt_mode": "Na\u010din:",
        "opt_safety": "Raven varnosti:",
        "chk_xml_tags": "Ovij razdelke v XML oznake (priporo\u010deno)",
        "chk_extended_thinking": "Omogo\u010di raz\u0161irjeno razmi\u0161ljanje",
        "chk_system_user_split": "Oblikuj kot Sistemsko + Uporabni\u0161ko sporo\u010dilo",
        "chk_json_mode": "Strog JSON izhodni na\u010din",
        "chk_grounding": "Google Search utemeljitev",
        "chk_code_first": "Najprej koda (koda pred razlago)",
        "chk_web_search": "Omogo\u010di reference spletnega iskanja",
        "ph_role": "npr. Vi\u0161ji Python razvijalec, Tehni\u010dni pisec ...",
        "ph_context": "Navedite ozadje ali kontekst naloge...",
        "ph_instruction": "Podrobno opi\u0161ite glavno nalogo ali vpra\u0161anje...",
        "ph_input_data": "Prilepite vhodne podatke, kodo ali besedilo za obdelavo (neobvezno)...",
        "ph_constraints": "Navedite omejitve, pravila ali stvari, ki se jim je treba izogniti (neobvezno)...",
        "ph_examples": "Navedite primere vhod -> izhod za few-shot pozivanje (neobvezno)...",
        "ph_extra": "Dodatna navodila za dodajanje...",
        "btn_generate": "Generiraj",
        "btn_engine": "Motor",
        "btn_copy": "Kopiraj",
        "btn_save": "Shrani",
        "btn_clear": "Po\u010disti",
        "output_label": "Izhod \u2014 {model}",
        "options_label": "Mo\u017enosti {model}",
        "msg_missing_input": "Manjkajo\u010d vnos",
        "msg_missing_instruction": "Prosim vnesite glavno navodilo.",
        "msg_missing_role": "Prosim vnesite vlogo / persono.",
        "msg_nothing_copy_title": "Ni za kopiranje",
        "msg_nothing_copy": "Najprej generirajte poziv.",
        "msg_copied_title": "Kopirano",
        "msg_copied": "Poziv kopiran v odlo\u017ei\u0161\u010de.",
        "msg_nothing_save_title": "Ni za shranjevanje",
        "msg_nothing_save": "Najprej generirajte poziv.",
        "msg_saved_title": "Shranjeno",
        "msg_saved": "Poziv shranjen v {path}",
        "msg_error": "Napaka",
        "msg_save_fail": "Datoteke ni mogo\u010de shraniti:\n{error}",
        "msg_engine_error": "Napaka motorja",
        "msg_engine_fail": "Validacija/generiranje poziva ni uspelo:\n{error}",
        "msg_save_dialog": "Shrani poziv",
    },
    "es": {
        "window_title": "Constructor de Prompts IA",
        "app_title": "Constructor de Prompts IA",
        "app_subtitle": "Seleccione un modelo  \u2192  Configure  \u2192  Genere un prompt optimizado",
        "gui_language": "Idioma de interfaz:",
        "group_task": "Configuraci\u00f3n de tarea",
        "group_role": "Rol y tono",
        "group_content": "Contenido del prompt",
        "group_output": "Configuraci\u00f3n de salida",
        "group_advanced": "Opciones avanzadas",
        "lbl_task_type": "Tipo de tarea:",
        "lbl_prog_lang": "Lenguaje de programaci\u00f3n:",
        "lbl_role": "Rol / Persona:",
        "lbl_tone": "Tono:",
        "lbl_audience": "P\u00fablico objetivo:",
        "lbl_context": "Contexto:",
        "lbl_instruction": "Instrucci\u00f3n principal:",
        "lbl_input_data": "Datos de entrada:",
        "lbl_constraints": "Restricciones:",
        "lbl_examples": "Ejemplos:",
        "lbl_output_format": "Formato de salida:",
        "lbl_detail_level": "Nivel de detalle:",
        "lbl_output_language": "Idioma de salida:",
        "lbl_max_length": "Longitud m\u00e1xima:",
        "lbl_cot": "Cadena de pensamiento:",
        "lbl_citations": "Citas:",
        "lbl_creativity": "Sugerencia de creatividad:",
        "lbl_extra": "Instrucciones adicionales:",
        "chk_cot": "Activar razonamiento paso a paso",
        "chk_citations": "Solicitar fuentes / referencias",
        "opt_model": "Modelo:",
        "opt_mode": "Modo:",
        "opt_safety": "Nivel de seguridad:",
        "chk_xml_tags": "Envolver secciones en etiquetas XML (recomendado)",
        "chk_extended_thinking": "Activar pensamiento extendido",
        "chk_system_user_split": "Formatear como mensajes Sistema + Usuario",
        "chk_json_mode": "Modo estricto de salida JSON",
        "chk_grounding": "Fundamentaci\u00f3n con Google Search",
        "chk_code_first": "C\u00f3digo primero (c\u00f3digo antes de explicaci\u00f3n)",
        "chk_web_search": "Activar referencias de b\u00fasqueda web",
        "ph_role": "ej. Desarrollador senior de Python, Escritor t\u00e9cnico ...",
        "ph_context": "Proporcione informaci\u00f3n de contexto para la tarea...",
        "ph_instruction": "Describa la tarea o pregunta principal en detalle...",
        "ph_input_data": "Pegue datos de entrada, fragmentos de c\u00f3digo o texto (opcional)...",
        "ph_constraints": "Liste restricciones, reglas o cosas a evitar (opcional)...",
        "ph_examples": "Proporcione pares de ejemplo entrada -> salida (opcional)...",
        "ph_extra": "Instrucciones adicionales para agregar...",
        "btn_generate": "Generar",
        "btn_engine": "Motor",
        "btn_copy": "Copiar",
        "btn_save": "Guardar",
        "btn_clear": "Limpiar",
        "output_label": "Salida \u2014 {model}",
        "options_label": "Opciones de {model}",
        "msg_missing_input": "Entrada faltante",
        "msg_missing_instruction": "Por favor ingrese una instrucci\u00f3n principal.",
        "msg_missing_role": "Por favor ingrese un rol / persona.",
        "msg_nothing_copy_title": "Nada para copiar",
        "msg_nothing_copy": "Primero genere un prompt.",
        "msg_copied_title": "Copiado",
        "msg_copied": "Prompt copiado al portapapeles.",
        "msg_nothing_save_title": "Nada para guardar",
        "msg_nothing_save": "Primero genere un prompt.",
        "msg_saved_title": "Guardado",
        "msg_saved": "Prompt guardado en {path}",
        "msg_error": "Error",
        "msg_save_fail": "No se pudo guardar el archivo:\n{error}",
        "msg_engine_error": "Error de motor",
        "msg_engine_fail": "La validaci\u00f3n/generaci\u00f3n del prompt fall\u00f3:\n{error}",
        "msg_save_dialog": "Guardar prompt",
    },
    "de": {
        "window_title": "KI-Prompt-Generator",
        "app_title": "KI-Prompt-Generator",
        "app_subtitle": "Modell w\u00e4hlen  \u2192  Konfigurieren  \u2192  Optimierten Prompt generieren",
        "gui_language": "Oberfl\u00e4chensprache:",
        "group_task": "Aufgabenkonfiguration",
        "group_role": "Rolle & Ton",
        "group_content": "Prompt-Inhalt",
        "group_output": "Ausgabeeinstellungen",
        "group_advanced": "Erweiterte Optionen",
        "lbl_task_type": "Aufgabentyp:",
        "lbl_prog_lang": "Programmiersprache:",
        "lbl_role": "Rolle / Persona:",
        "lbl_tone": "Ton:",
        "lbl_audience": "Zielgruppe:",
        "lbl_context": "Kontext:",
        "lbl_instruction": "Hauptanweisung:",
        "lbl_input_data": "Eingabedaten:",
        "lbl_constraints": "Einschr\u00e4nkungen:",
        "lbl_examples": "Beispiele:",
        "lbl_output_format": "Ausgabeformat:",
        "lbl_detail_level": "Detailgrad:",
        "lbl_output_language": "Ausgabesprache:",
        "lbl_max_length": "Maximale L\u00e4nge:",
        "lbl_cot": "Gedankenkette:",
        "lbl_citations": "Zitate:",
        "lbl_creativity": "Kreativit\u00e4tshinweis:",
        "lbl_extra": "Zus\u00e4tzliche Anweisungen:",
        "chk_cot": "Schrittweises Denken aktivieren",
        "chk_citations": "Quellen / Referenzen anfordern",
        "opt_model": "Modell:",
        "opt_mode": "Modus:",
        "opt_safety": "Sicherheitsstufe:",
        "chk_xml_tags": "Abschnitte in XML-Tags einwickeln (empfohlen)",
        "chk_extended_thinking": "Erweitertes Denken aktivieren",
        "chk_system_user_split": "Als System- + Benutzernachrichten formatieren",
        "chk_json_mode": "Strikter JSON-Ausgabemodus",
        "chk_grounding": "Google-Suche-Fundierung",
        "chk_code_first": "Code zuerst (Code vor Erkl\u00e4rung)",
        "chk_web_search": "Websuche-Referenzen aktivieren",
        "ph_role": "z.B. Senior Python-Entwickler, Technischer Autor ...",
        "ph_context": "Hintergrundinformationen oder Kontext f\u00fcr die Aufgabe...",
        "ph_instruction": "Beschreiben Sie die Hauptaufgabe oder Frage im Detail...",
        "ph_input_data": "Eingabedaten, Codeausschnitte oder Text einf\u00fcgen (optional)...",
        "ph_constraints": "Einschr\u00e4nkungen, Regeln oder zu Vermeidendes auflisten (optional)...",
        "ph_examples": "Beispielpaare Eingabe -> Ausgabe angeben (optional)...",
        "ph_extra": "Zus\u00e4tzliche Anweisungen zum Anh\u00e4ngen...",
        "btn_generate": "Generieren",
        "btn_engine": "Engine",
        "btn_copy": "Kopieren",
        "btn_save": "Speichern",
        "btn_clear": "Leeren",
        "output_label": "Ausgabe \u2014 {model}",
        "options_label": "{model}-Optionen",
        "msg_missing_input": "Fehlende Eingabe",
        "msg_missing_instruction": "Bitte geben Sie eine Hauptanweisung ein.",
        "msg_missing_role": "Bitte geben Sie eine Rolle / Persona ein.",
        "msg_nothing_copy_title": "Nichts zu kopieren",
        "msg_nothing_copy": "Generieren Sie zuerst einen Prompt.",
        "msg_copied_title": "Kopiert",
        "msg_copied": "Prompt in die Zwischenablage kopiert.",
        "msg_nothing_save_title": "Nichts zu speichern",
        "msg_nothing_save": "Generieren Sie zuerst einen Prompt.",
        "msg_saved_title": "Gespeichert",
        "msg_saved": "Prompt gespeichert unter {path}",
        "msg_error": "Fehler",
        "msg_save_fail": "Datei konnte nicht gespeichert werden:\n{error}",
        "msg_engine_error": "Engine-Fehler",
        "msg_engine_fail": "Prompt-Validierung/Generierung fehlgeschlagen:\n{error}",
        "msg_save_dialog": "Prompt speichern",
    },
    "fr": {
        "window_title": "Constructeur de Prompts IA",
        "app_title": "Constructeur de Prompts IA",
        "app_subtitle": "S\u00e9lectionnez un mod\u00e8le  \u2192  Configurez  \u2192  G\u00e9n\u00e9rez un prompt optimis\u00e9",
        "gui_language": "Langue de l\u2019interface :",
        "group_task": "Configuration de la t\u00e2che",
        "group_role": "R\u00f4le et ton",
        "group_content": "Contenu du prompt",
        "group_output": "Param\u00e8tres de sortie",
        "group_advanced": "Options avanc\u00e9es",
        "lbl_task_type": "Type de t\u00e2che :",
        "lbl_prog_lang": "Langage de programmation :",
        "lbl_role": "R\u00f4le / Persona :",
        "lbl_tone": "Ton :",
        "lbl_audience": "Public cible :",
        "lbl_context": "Contexte :",
        "lbl_instruction": "Instruction principale :",
        "lbl_input_data": "Donn\u00e9es d\u2019entr\u00e9e :",
        "lbl_constraints": "Contraintes :",
        "lbl_examples": "Exemples :",
        "lbl_output_format": "Format de sortie :",
        "lbl_detail_level": "Niveau de d\u00e9tail :",
        "lbl_output_language": "Langue de sortie :",
        "lbl_max_length": "Longueur maximale :",
        "lbl_cot": "Cha\u00eene de pens\u00e9e :",
        "lbl_citations": "Citations :",
        "lbl_creativity": "Indice de cr\u00e9ativit\u00e9 :",
        "lbl_extra": "Instructions suppl\u00e9mentaires :",
        "chk_cot": "Activer le raisonnement \u00e9tape par \u00e9tape",
        "chk_citations": "Demander des sources / r\u00e9f\u00e9rences",
        "opt_model": "Mod\u00e8le :",
        "opt_mode": "Mode :",
        "opt_safety": "Niveau de s\u00e9curit\u00e9 :",
        "chk_xml_tags": "Encadrer les sections avec des balises XML (recommand\u00e9)",
        "chk_extended_thinking": "Activer la r\u00e9flexion \u00e9tendue",
        "chk_system_user_split": "Formater en messages Syst\u00e8me + Utilisateur",
        "chk_json_mode": "Mode de sortie JSON strict",
        "chk_grounding": "Ancrage Google Search",
        "chk_code_first": "Code d\u2019abord (code avant explication)",
        "chk_web_search": "Activer les r\u00e9f\u00e9rences de recherche web",
        "ph_role": "ex. D\u00e9veloppeur Python senior, R\u00e9dacteur technique ...",
        "ph_context": "Fournissez des informations de contexte pour la t\u00e2che...",
        "ph_instruction": "D\u00e9crivez la t\u00e2che ou question principale en d\u00e9tail...",
        "ph_input_data": "Collez des donn\u00e9es, extraits de code ou texte \u00e0 traiter (optionnel)...",
        "ph_constraints": "Listez les contraintes, r\u00e8gles ou choses \u00e0 \u00e9viter (optionnel)...",
        "ph_examples": "Fournissez des paires d\u2019exemples entr\u00e9e -> sortie (optionnel)...",
        "ph_extra": "Instructions suppl\u00e9mentaires \u00e0 ajouter...",
        "btn_generate": "G\u00e9n\u00e9rer",
        "btn_engine": "Moteur",
        "btn_copy": "Copier",
        "btn_save": "Enregistrer",
        "btn_clear": "Effacer",
        "output_label": "Sortie \u2014 {model}",
        "options_label": "Options de {model}",
        "msg_missing_input": "Entr\u00e9e manquante",
        "msg_missing_instruction": "Veuillez entrer une instruction principale.",
        "msg_missing_role": "Veuillez entrer un r\u00f4le / persona.",
        "msg_nothing_copy_title": "Rien \u00e0 copier",
        "msg_nothing_copy": "G\u00e9n\u00e9rez d\u2019abord un prompt.",
        "msg_copied_title": "Copi\u00e9",
        "msg_copied": "Prompt copi\u00e9 dans le presse-papiers.",
        "msg_nothing_save_title": "Rien \u00e0 enregistrer",
        "msg_nothing_save": "G\u00e9n\u00e9rez d\u2019abord un prompt.",
        "msg_saved_title": "Enregistr\u00e9",
        "msg_saved": "Prompt enregistr\u00e9 dans {path}",
        "msg_error": "Erreur",
        "msg_save_fail": "Impossible d\u2019enregistrer le fichier :\n{error}",
        "msg_engine_error": "Erreur du moteur",
        "msg_engine_fail": "La validation/g\u00e9n\u00e9ration du prompt a \u00e9chou\u00e9 :\n{error}",
        "msg_save_dialog": "Enregistrer le prompt",
    },
}

GUI_LANGUAGES = {
    "English": "en",
    "Sloven\u0161\u010dina": "sl",
    "Espa\u00f1ol": "es",
    "Deutsch": "de",
    "Fran\u00e7ais": "fr",
}

_current_lang = "en"


def _t(key, fallback=None):
    """Look up a translated string for the current GUI language."""
    strings = GUI_STRINGS.get(_current_lang, GUI_STRINGS["en"])
    result = strings.get(key)
    if result is not None:
        return result
    result = GUI_STRINGS["en"].get(key)
    if result is not None:
        return result
    return fallback if fallback is not None else key


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

        self._groups = {}
        self._req_labels = {}
        self._labels = {}

        # --- Task Configuration ---
        self._groups["task"] = task_group = QGroupBox(_t("group_task"))
        task_form = QFormLayout()
        task_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.task_type = QComboBox()
        self.task_type.addItems(TASK_TYPES)
        self._req_labels["lbl_task_type"] = lbl = self._required_label(
            _t("lbl_task_type"))
        task_form.addRow(lbl, _with_help(self.task_type, "task_type"))

        self.programming_lang = QComboBox()
        self.programming_lang.setEditable(True)
        self.programming_lang.addItems(PROGRAMMING_LANGUAGES)
        self._labels["lbl_prog_lang"] = lbl = QLabel(_t("lbl_prog_lang"))
        task_form.addRow(lbl, _with_help(self.programming_lang,
                                         "programming_lang"))

        task_group.setLayout(task_form)
        form_layout.addWidget(task_group)

        # --- Role & Tone ---
        self._groups["role"] = role_group = QGroupBox(_t("group_role"))
        role_form = QFormLayout()
        role_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText(_t("ph_role"))
        self._req_labels["lbl_role"] = lbl = self._required_label(
            _t("lbl_role"))
        role_form.addRow(lbl, _with_help(self.role_input, "role"))

        self.tone = QComboBox()
        self.tone.addItems([
            "Professional", "Casual / Friendly", "Technical",
            "Academic / Formal", "Concise / Direct", "Creative",
            "Instructional", "Empathetic",
        ])
        self._req_labels["lbl_tone"] = lbl = self._required_label(
            _t("lbl_tone"))
        role_form.addRow(lbl, _with_help(self.tone, "tone"))

        self.audience = QComboBox()
        self.audience.setEditable(True)
        self.audience.addItems([
            "General audience", "Beginners", "Intermediate developers",
            "Senior engineers", "Non-technical stakeholders",
            "Students", "Executives", "Other",
        ])
        self._labels["lbl_audience"] = lbl = QLabel(_t("lbl_audience"))
        role_form.addRow(lbl, _with_help(self.audience, "audience"))

        role_group.setLayout(role_form)
        form_layout.addWidget(role_group)

        # --- Prompt Content ---
        self._groups["content"] = content_group = QGroupBox(
            _t("group_content"))
        content_form = QFormLayout()
        content_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.context_input = QTextEdit()
        self.context_input.setPlaceholderText(_t("ph_context"))
        self.context_input.setMaximumHeight(90)
        self._req_labels["lbl_context"] = lbl = self._required_label(
            _t("lbl_context"))
        content_form.addRow(lbl, _with_help(self.context_input, "context"))

        self.instruction_input = QTextEdit()
        self.instruction_input.setPlaceholderText(_t("ph_instruction"))
        self.instruction_input.setMaximumHeight(110)
        self._req_labels["lbl_instruction"] = lbl = self._required_label(
            _t("lbl_instruction"))
        content_form.addRow(lbl,
                            _with_help(self.instruction_input, "instruction"))

        self.input_data = QTextEdit()
        self.input_data.setPlaceholderText(_t("ph_input_data"))
        self.input_data.setMaximumHeight(90)
        self._labels["lbl_input_data"] = lbl = QLabel(_t("lbl_input_data"))
        content_form.addRow(lbl, _with_help(self.input_data, "input_data"))

        self.constraints_input = QTextEdit()
        self.constraints_input.setPlaceholderText(_t("ph_constraints"))
        self.constraints_input.setMaximumHeight(80)
        self._labels["lbl_constraints"] = lbl = QLabel(_t("lbl_constraints"))
        content_form.addRow(lbl,
                            _with_help(self.constraints_input, "constraints"))

        self.examples_input = QTextEdit()
        self.examples_input.setPlaceholderText(_t("ph_examples"))
        self.examples_input.setMaximumHeight(80)
        self._labels["lbl_examples"] = lbl = QLabel(_t("lbl_examples"))
        content_form.addRow(lbl,
                            _with_help(self.examples_input, "examples"))

        content_group.setLayout(content_form)
        form_layout.addWidget(content_group)

        # --- Output Settings ---
        self._groups["output"] = output_group = QGroupBox(
            _t("group_output"))
        output_form = QFormLayout()
        output_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.output_format = QComboBox()
        self.output_format.addItems([
            "Markdown", "Plain Text", "JSON", "XML", "Code Only",
            "Bullet Points", "Numbered List", "Table", "Essay / Prose",
            "Step-by-step Guide",
        ])
        self._req_labels["lbl_output_format"] = lbl = self._required_label(
            _t("lbl_output_format"))
        output_form.addRow(lbl,
                           _with_help(self.output_format, "output_format"))

        self.detail_level = QComboBox()
        self.detail_level.addItems([
            "Brief", "Moderate", "Detailed", "Comprehensive"])
        self.detail_level.setCurrentIndex(2)
        self._req_labels["lbl_detail_level"] = lbl = self._required_label(
            _t("lbl_detail_level"))
        output_form.addRow(lbl,
                           _with_help(self.detail_level, "detail_level"))

        self.output_language = QComboBox()
        self.output_language.setEditable(True)
        self.output_language.addItems([
            "English", "Spanish", "French", "German", "Italian",
            "Portuguese", "Chinese", "Japanese", "Korean",
            "Arabic", "Hindi", "Russian", "Dutch", "Slovenian", "Other",
        ])
        self._labels["lbl_output_language"] = lbl = QLabel(
            _t("lbl_output_language"))
        output_form.addRow(lbl,
                           _with_help(self.output_language, "output_language"))

        self.max_length = QComboBox()
        self.max_length.addItems([
            "No limit", "~100 words", "~250 words", "~500 words",
            "~1000 words", "~2000 words",
        ])
        self._labels["lbl_max_length"] = lbl = QLabel(_t("lbl_max_length"))
        output_form.addRow(lbl, _with_help(self.max_length, "max_length"))

        output_group.setLayout(output_form)
        form_layout.addWidget(output_group)

        # --- Advanced Options ---
        self._groups["advanced"] = adv_group = QGroupBox(
            _t("group_advanced"))
        adv_form = QFormLayout()
        adv_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.chain_of_thought = QCheckBox(_t("chk_cot"))
        self._labels["lbl_cot"] = lbl = QLabel(_t("lbl_cot"))
        adv_form.addRow(lbl,
                        _with_help(self.chain_of_thought, "chain_of_thought"))

        self.include_citations = QCheckBox(_t("chk_citations"))
        self._labels["lbl_citations"] = lbl = QLabel(_t("lbl_citations"))
        adv_form.addRow(lbl,
                        _with_help(self.include_citations, "citations"))

        self.temperature_hint = QComboBox()
        self.temperature_hint.addItems([
            "Default", "Precise (low creativity)",
            "Balanced", "Creative (high creativity)",
        ])
        self._labels["lbl_creativity"] = lbl = QLabel(_t("lbl_creativity"))
        adv_form.addRow(lbl,
                        _with_help(self.temperature_hint, "creativity_hint"))

        self.additional_instructions = QLineEdit()
        self.additional_instructions.setPlaceholderText(_t("ph_extra"))
        self._labels["lbl_extra"] = lbl = QLabel(_t("lbl_extra"))
        adv_form.addRow(lbl,
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

    def retranslate(self):
        """Update all visible text to match the current GUI language."""
        for key, lbl in self._req_labels.items():
            lbl.setText(
                f'{_t(key)} <span style="color:#FF3B30;">*</span>')
        for key, lbl in self._labels.items():
            lbl.setText(_t(key))
        group_keys = {
            "task": "group_task", "role": "group_role",
            "content": "group_content", "output": "group_output",
            "advanced": "group_advanced",
        }
        for gk, tk in group_keys.items():
            self._groups[gk].setTitle(_t(tk))
        self.chain_of_thought.setText(_t("chk_cot"))
        self.include_citations.setText(_t("chk_citations"))
        self.role_input.setPlaceholderText(_t("ph_role"))
        self.context_input.setPlaceholderText(_t("ph_context"))
        self.instruction_input.setPlaceholderText(_t("ph_instruction"))
        self.input_data.setPlaceholderText(_t("ph_input_data"))
        self.constraints_input.setPlaceholderText(_t("ph_constraints"))
        self.examples_input.setPlaceholderText(_t("ph_examples"))
        self.additional_instructions.setPlaceholderText(_t("ph_extra"))


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

        self._opt_labels = {}
        self._opt_checks = {}

        # ── Model-specific options ──
        self._opts_group = QGroupBox(
            _t("options_label").format(model=self.config["name"]))
        opts_form = QFormLayout()
        opts_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        for opt in self.config["specific_options"]:
            key = opt["key"]
            if opt["type"] == "combo":
                widget = QComboBox()
                widget.addItems(opt["items"])
                lbl = QLabel(_t(f"opt_{key}"))
                self._opt_labels[key] = lbl
                opts_form.addRow(lbl, _with_help(widget, key))
            elif opt["type"] == "check":
                widget = QCheckBox(_t(f"chk_{key}"))
                widget.setChecked(opt.get("default", False))
                self._opt_checks[key] = widget
                opts_form.addRow("", _with_help(widget, key))
            else:
                continue
            self.option_widgets[key] = widget

        self._opts_group.setLayout(opts_form)
        layout.addWidget(self._opts_group)

        # ── Generated output ──
        self._out_label = QLabel(
            _t("output_label").format(model=self.config["name"]))
        self._out_label.setFont(
            QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self._out_label.setObjectName("outputLabel")
        layout.addWidget(self._out_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Cascadia Code", 10))
        self.output_text.setObjectName("outputArea")
        _soft_shadow(self.output_text, "#000000", 16, 3, 0.06)
        layout.addWidget(self.output_text, 1)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self._generate_btn = self._make_btn(
            _t("btn_generate"), "#007AFF", self._generate_prompt,
            primary=True)
        btn_row.addWidget(_btn_with_help(self._generate_btn, "btn_generate"))

        self._engine_btn = self._make_btn(
            _t("btn_engine"), "#5856D6", self._generate_engine_prompt)
        btn_row.addWidget(_btn_with_help(self._engine_btn, "btn_engine"))

        self._copy_btn = self._make_btn(
            _t("btn_copy"), "#34C759", self._copy_to_clipboard)
        btn_row.addWidget(_btn_with_help(self._copy_btn, "btn_copy"))

        self._save_btn = self._make_btn(
            _t("btn_save"), "#FF9500", self._save_to_file)
        btn_row.addWidget(_btn_with_help(self._save_btn, "btn_save"))

        self._clear_btn = self._make_btn(
            _t("btn_clear"), "#FF3B30", self._clear_all)
        btn_row.addWidget(_btn_with_help(self._clear_btn, "btn_clear"))

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
            QMessageBox.warning(self, _t("msg_missing_input"),
                                _t("msg_missing_instruction"))
            return
        if not shared["role"]:
            QMessageBox.warning(self, _t("msg_missing_input"),
                                _t("msg_missing_role"))
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
            QMessageBox.warning(self, _t("msg_missing_input"),
                                _t("msg_missing_instruction"))
            return
        if not shared["role"]:
            QMessageBox.warning(self, _t("msg_missing_input"),
                                _t("msg_missing_role"))
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
                self, _t("msg_engine_error"),
                _t("msg_engine_fail").format(error=exc),
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
            QMessageBox.information(self, _t("msg_nothing_copy_title"),
                                    _t("msg_nothing_copy"))
            return
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, _t("msg_copied_title"),
                                _t("msg_copied"))

    def _save_to_file(self):
        text = self.output_text.toPlainText()
        if not text:
            QMessageBox.information(self, _t("msg_nothing_save_title"),
                                    _t("msg_nothing_save"))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, _t("msg_save_dialog"), "",
            "Text Files (*.txt);;Markdown (*.md);;All Files (*)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            except OSError as e:
                QMessageBox.critical(
                    self, _t("msg_error"),
                    _t("msg_save_fail").format(error=e))
                return
            QMessageBox.information(
                self, _t("msg_saved_title"),
                _t("msg_saved").format(path=path))

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

    def retranslate(self):
        """Update all visible text to match the current GUI language."""
        name = self.config["name"]
        self._opts_group.setTitle(
            _t("options_label").format(model=name))
        self._out_label.setText(
            _t("output_label").format(model=name))
        for key, lbl in self._opt_labels.items():
            lbl.setText(_t(f"opt_{key}"))
        for key, wid in self._opt_checks.items():
            wid.setText(_t(f"chk_{key}"))
        self._generate_btn.setText(_t("btn_generate"))
        self._engine_btn.setText(_t("btn_engine"))
        self._copy_btn.setText(_t("btn_copy"))
        self._save_btn.setText(_t("btn_save"))
        self._clear_btn.setText(_t("btn_clear"))


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
        self._title = QLabel(_t("app_title"))
        self._title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setObjectName("appTitle")
        main_layout.addWidget(self._title)

        # Subtitle + Language selector row
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        self._subtitle = QLabel(_t("app_subtitle"))
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setObjectName("appSubtitle")
        header_row.addWidget(self._subtitle, 1)

        self._lang_label = QLabel(_t("gui_language"))
        self._lang_label.setObjectName("appSubtitle")
        header_row.addWidget(self._lang_label)

        self._lang_combo = QComboBox()
        self._lang_combo.addItems(list(GUI_LANGUAGES.keys()))
        self._lang_combo.setFixedWidth(140)
        self._lang_combo.currentTextChanged.connect(self._change_language)
        header_row.addWidget(self._lang_combo)
        header_row.addWidget(_make_help_btn("gui_language"))

        main_layout.addLayout(header_row)

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

    def _change_language(self, display_name):
        """Switch the GUI language and retranslate all widgets."""
        global _current_lang
        lang_code = GUI_LANGUAGES.get(display_name, "en")
        if lang_code == _current_lang:
            return
        _current_lang = lang_code
        self.setWindowTitle(_t("window_title"))
        self._title.setText(_t("app_title"))
        self._subtitle.setText(_t("app_subtitle"))
        self._lang_label.setText(_t("gui_language"))
        self.shared_panel.retranslate()
        for tab in self.model_tabs:
            tab.retranslate()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PromptBuilderApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
