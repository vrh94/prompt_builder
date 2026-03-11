# AI Prompt Builder

A desktop application for crafting optimized prompts for multiple AI models. Built with Python, PyQt6, and a Pydantic V2 + Jinja2 engine layer.

## Features

### GUI (prompt_builder.py)

- **Multi-model support** — dedicated prompt builders for Claude, ChatGPT, Gemini, and Copilot
- **Shared input fields** — fill in your task once, switch between model tabs to generate model-specific prompts instantly
- **Model-specific options** — each model tab includes settings tailored to that platform:

  | Model | Specific Options |
  |-------|-----------------|
  | Claude | Model selector, XML tags toggle, Extended thinking |
  | ChatGPT | Model selector, System/User message split, JSON mode |
  | Gemini | Model selector, Google Search grounding, Safety level |
  | Copilot | Mode (Balanced/Creative/Precise), Code-first output, Web search |

- **13 task types** — Code Generation, Code Review, Summarization, Translation, Data Analysis, and more
- **30+ programming languages** — Python, JavaScript, C, C++, Rust, Go, and many others
- **Prompt best practices baked in** — each formatter follows the target model's recommended prompt structure (XML tags for Claude, System/User split for ChatGPT, etc.)
- **Export options** — copy to clipboard or save to file
- **Two generation modes** — `GENERATE` (model-specific formatter) and `ENGINE` (Pydantic-validated Jinja2 pipeline)

### Engine (engine.py)

- **Pydantic V2 Validation** — `PromptTemplate` model validates Jinja2 template syntax and ensures all required template variables are present before rendering
- **Universal Formatting Layer** — `render_for_provider(provider)` returns the correct structure per provider:
  - `'openai'` → `list[dict]` with `{"role": …, "content": …}` messages (system + few-shot + user)
  - `'anthropic'` → XML-wrapped string following Claude 4.6 conventions (`<role>`, `<instruction>`, `<examples>`)
  - `'generic'` → plain rendered string
- **Smart Suffix Injection** — automatically appends format-specific instructions based on `requested_format` (e.g., JSON → "respond with valid JSON only, no preamble"; Code → "respond with code only")
- **Claude 4.6 `<thinking>` Optimizations** — wraps multi-shot example analysis inside `<thinking>` tags so Claude can reason about few-shot patterns internally before answering

## Requirements

- Python 3.10+
- PyQt6
- pydantic >= 2.0
- jinja2

## Installation

```bash
pip install PyQt6 pydantic jinja2
```

## Usage

### GUI

```bash
python prompt_builder.py
```

#### Workflow

1. Fill in the **shared fields** on the left panel (role, task type, context, instructions, etc.)
2. Click a **model tab** on the right (Claude, ChatGPT, Gemini, or Copilot)
3. Adjust any **model-specific options** at the top of the tab
4. Click **GENERATE** for the model-specific formatter, or **ENGINE** for the Pydantic/Jinja2 pipeline
5. **COPY** or **SAVE** the result

Switch tabs freely — your shared input data is preserved across all models.

### Engine (programmatic)

```python
from engine import PromptTemplate

# Validated template — raises if variables are missing
tpl = PromptTemplate(
    template="Write a {{ lang }} function that {{ task }}",
    variables={"lang": "Python", "task": "sorts a list"},
    role="a senior software engineer",
    requested_format="code",
    provider="anthropic",
    enable_thinking=True,
    examples=[
        {"user": "reverse a string", "assistant": "def reverse(s): return s[::-1]"},
    ],
)

# Render for the target provider
result = tpl.render_for_provider()  # XML-wrapped string with <thinking> tags
```

## Project Structure

```
ClaudePromptBuilder/
├── prompt_builder.py   # PyQt6 GUI application
├── engine.py           # Pydantic V2 + Jinja2 prompt engine
├── .gitignore
└── README.md
```


