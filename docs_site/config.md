# Configuration Reference

This page provides a detailed guide on how to configure the agents in the `orchast_agent` monorepo, including environment variables and LLM model selection.

## Model Selection

The agents are designed to be flexible, supporting both high-performance cloud models and privacy-focused local models via the [LiteLlm](https://docs.litellm.ai/) abstraction layer.

### Gemini Flash (Cloud)
**Default Choice.** Best for most users due to its high reliability in tool calling and rapid response times.
- **Requirement:** A Google Cloud Project with the Vertex AI API enabled.
- **Authentication:** Handled via Application Default Credentials (ADC).
  ```bash
  gcloud auth application-default login
  ```

### Ollama (Local)
Ideal for offline development, privacy-sensitive data, or avoiding cloud costs.
- **Requirement:** [Ollama](https://ollama.com/) installed and running on your local machine or a remote GPU server.
- **Connectivity:** Agents connect to the OpenAI-compatible endpoint at `http://localhost:11434/v1`.

---

## Environment Variables

Depending on the agent, you can override default behaviors using environment variables.

| Variable | Description | Example / Default | Required |
| :--- | :--- | :--- | :--- |
| `AGENT_MODEL` | Specifies the model to be used by the agent. If set, it typically triggers local LLM mode (Ollama). | `qwen3:32b`, `gemma4:31b` | No |
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID for Vertex AI requests. | `my-ai-project-123` | Yes (for Gemini) |
| `OLLAMA_HOST` | The host address of your Ollama server (if not localhost). | `http://192.168.1.50:11434` | No |

### Example: Running with a Local Model
To run an agent using a specific Ollama model, prefix the execution command:

```bash
AGENT_MODEL=qwen3:32b agents-cli playground
```

---

## Ollama Setup Guide

If you choose to use local models, follow these steps to prepare your environment:

### 1. Install Ollama
Download and install from [ollama.com](https://ollama.com/).

### 2. Pull a Compatible Model
Not all models are equal in their ability to perform tool-calling (function calling). We recommend the following:

```bash
# Highly recommended for tool creation/execution
ollama pull qwen3:32b

# Alternative option
ollama pull gemma4:31b
```

### 3. Verify Installation
Ensure Ollama is running by visiting `http://localhost:11434` in your browser or running:
```bash
ollama list
```

## Troubleshooting Configuration

- **Authentication Errors:** If you see "Permission Denied" when using Gemini, ensure you have run `gcloud auth application-default login` and that the quota for Vertex AI is active.
- **Model Loops:** Some local models may enter a loop of calling the same tool repeatedly. The agents include a `_limit_tool_loops` callback to prevent this, but switching to a larger model (e.g., 32B+) usually resolves the issue.
- **Port Conflicts:** If the playground UI fails to start on port 8000, you can specify a different port:
  ```bash
  agents-cli playground --port 8080
  ```
