---
name: gamma
description: Create presentations, documents, webpages, and social posts using the Gamma API. Use when the user asks to create slides, presentations, decks, documents, pitch decks, reports, or any visual content. Also use when they say things like "make a deck", "turn this into slides", "create a pptx", "I need a presentation for my meeting", or want to convert notes/text into polished visual content. Also use when the task is about generating presentations or documents from text.
argument-hint: [topic or content description]
---

# Gamma CLI — Agent Skill

Create presentations, documents, webpages, and social posts via the Gamma API using the `gamma` CLI.

## Before You Start

Check if the API key is configured:

```bash
gamma config get apiKey
```

If it returns `null`, the user needs to set one up. Tell them:
- "You'll need a Gamma API key to create content. You can get one at gamma.app/settings (requires a Pro+ plan)."
- They can either set it globally: `gamma config set apiKey sk-gamma-xxxxx`

## Commands

### Generate Content

```bash
# Simple — just a topic
gamma generate -i "Quarterly Business Review" -m generate

# User provided actual content to preserve
gamma generate -i "the user's full text here" -m preserve --type document

# All options
gamma generate -i "Topic description" -m generate \
  --type presentation \
  --amount detailed \
  --tone professional \
  --audience "国企管理层" \
  --language zh \
  --image-source aiGenerated \
  --image-style "minimalist flat illustrations" \
  --dimensions 16x9 \
  -n 12 \
  --export pdf

# Open in browser when done
gamma generate -i "Sales deck" -m generate --open
```

### Check Status

```bash
gamma status GENERATION_ID --wait
```

## Key Options

| Flag | Values | Description |
|------|--------|-------------|
| `-m, --mode` | `generate`, `preserve`, `condense` | How to handle input |
| `--type` | `presentation`, `document`, `webpage`, `social` | Content type |
| `-n, --num-cards` | 1-75 | Number of slides |
| `--amount` | `brief`, `medium`, `detailed`, `extensive` | Text density |
| `--export` | `pdf`, `pptx` | Export format |
| `--open` | - | Open result in browser |

## Workflow

**Blocking:** Just run it and wait (20-60 seconds).
```bash
gamma generate -i "..." -m generate --open
```

**Async:** 
```bash
gamma generate -i "..." -m generate --no-wait
# Returns: {"generationId":"abc","status":"submitted"}
gamma status abc --wait
```

## Presenting Results

When generation completes, share the `gammaUrl` with the user. If they asked for `--export pdf`, also share the `exportUrl`.

## Error Recovery

- **"No API key"** → Guide user to gamma.app/settings for Pro+ plan
- **Timeout** → Use `gamma status GENERATION_ID --wait`
