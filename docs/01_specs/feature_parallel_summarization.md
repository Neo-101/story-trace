# Feature: Parallel Chapter Summarization

## Overview
Currently, the chapter summarization process is synchronous and sequential. This means that chapter N+1 only starts processing after chapter N is fully completed. Given that LLM API calls are I/O bound and have high latency (several seconds per call), this approach is inefficient.

## Analysis
1.  **Independence**: Each chapter's summary depends ONLY on its own content and the Prompt template. There is no dependency on the previous chapter's summary result (Stateless).
2.  **I/O Bound**: The bottleneck is the network request to the LLM API, not CPU computation.
3.  **Concurrency Safety**:
    *   **API Rate Limits**: We must limit the number of concurrent requests to avoid 429 errors.
    *   **File I/O**: Writing to `summaries.jsonl` (append mode) from multiple threads/tasks requires synchronization (Lock) to prevent data corruption.
    *   **Order Preservation**: The final `summaries.json` list must maintain the original chapter order.

## Implementation Plan (Asyncio)

### 1. `LLMClient` (Async Support)
*   Add `async_chat_completion` method to `LLMClient` (and `OpenRouterClient`, `LocalLLMClient`).
*   Use `httpx` or `aiohttp` for non-blocking HTTP requests.

### 2. `SummaryGenerator` (Async Support)
*   Add `generate_summary_async` method.
*   This method will await `llm.async_chat_completion`.

### 3. `BatchProcessor` (New Logic in `main.py`)
*   Use `asyncio.Semaphore` to limit concurrency (default: 5).
*   Use `asyncio.gather` to run all tasks.
*   Use `asyncio.Lock` for writing to `summaries.jsonl` in real-time.
*   Collect results and save the final sorted list to `summaries.json`.

## Expected Benefits
*   **Speed**: With 5 concurrent requests, the total time should theoretically be reduced by ~4-5x (minus overhead).
*   **Efficiency**: Better utilization of network bandwidth and API quota.
