# Bug Report: LLM Response JSON Parsing Failure

## Issue Description
During the summarization process (specifically observed in `Terminal#684-874`), the application fails to parse the JSON response from the LLM. This results in fallback behavior (plain text summary) or errors, preventing structured data (entities, relationships) from being extracted.

## Root Cause Analysis

### 1. Weak Parsing Logic
The current `_parse_json_response` method in `core/summarizer/generator.py` only performs simple string cleanup:
```python
cleaned = response.replace("```json", "").replace("```", "").strip()
```
This is insufficient for handling real-world LLM outputs, which often include:
*   **Chain of Thought (CoT)**: Content inside `<think>...</think>` tags (common in reasoning models like DeepSeek R1).
*   **Conversational Fillers**: Text before/after the JSON block (e.g., "Here is the JSON you requested:").
*   **Markdown Formatting**: Variations like ````json` (4 backticks) or plain text without blocks.

### 2. Prompt Ambiguity
The current system prompt might not strongly strictly enforce "JSON ONLY" output, leading the model to be "helpful" by adding explanations.

### 3. Model Behavior
The configured model `deepseek/deepseek-v3.2` might have a tendency to include reasoning steps or conversational wrappers by default.

## Fix Plan

### 1. Enhance `_parse_json_response`
Refactor the parsing logic to be more robust:
*   **Regex Extraction**: Use `r'\{.*\}'` with `DOTALL` to locate the outermost JSON object, ignoring surrounding text.
*   **Tag Stripping**: Explicitly remove `<think>...</think>` blocks before parsing.
*   **JSON Repair**: (Optional) Consider using a library like `json_repair` if available, or stick to robust regex + standard `json`.

### 2. Reinforce Prompts
Update `core/summarizer/prompts.py`:
*   Add a negative constraint: "Do not output any thinking process, explanations, or markdown code blocks outside the JSON."
*   Explicitly request raw JSON.

## Verification
*   Run a test summarization with the new parser.
*   Check logs to ensure `无法解析 JSON` errors are reduced.
