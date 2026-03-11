# AI Prompt Builder

A desktop application for crafting optimized prompts for multiple AI models. Built with Python and PyQt5.

## Features

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

## Requirements

- Python 3.7+
- PyQt5

## Installation

```bash
pip install PyQt5
```

## Usage

```bash
python prompt_builder.py
```

### Workflow

1. Fill in the **shared fields** on the left panel (role, task type, context, instructions, etc.)
2. Click a **model tab** on the right (Claude, ChatGPT, Gemini, or Copilot)
3. Adjust any **model-specific options** at the top of the tab
4. Click **Generate Prompt** to produce a prompt optimized for that model
5. **Copy** or **Save** the result

Switch tabs freely — your shared input data is preserved across all models.

## Project Structure

```
ClaudePromptBuilder/
├── prompt_builder.py   # Main application (single-file)
└── README.md
```


