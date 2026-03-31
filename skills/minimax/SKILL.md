---
name: minimax
description: Use MiniMax API for chat completion, text-to-speech, and video generation. Activates when user mentions MiniMax API, text-to-speech, TTS, video generation, T2V, I2V, or when needing Chinese-optimized LLM capabilities.
---

# MiniMax API

Use the MiniMax API via direct curl calls for AI chat completion, text-to-speech, and video generation.

Official docs: https://platform.minimax.io/docs

## When to Use

Use this skill when you need:
- Chat completion with Chinese-optimized LLM (MiniMax-M1/M2)
- Text-to-speech with natural voices and emotion control
- Video generation from text prompts (T2V)
- Image-to-video conversion (I2V)

## Prerequisites

- Sign up at [MiniMax Platform](https://platform.minimax.io/)
- Go to Account Management > API Keys to create an API key
- Note: Global users should use api.minimaxi.chat (with extra "i")

export MINIMAX_API_KEY="your-api-key"

### API Hosts

| Region | Base URL |
|--------|----------|
| China | https://api.minimax.io |
| Global | https://api.minimaxi.chat |

## How to Use

All examples below assume you have MINIMAX_API_KEY set.

Authentication uses Bearer token in the Authorization header.

### 1. Basic Chat Completion

```bash
curl -s "https://api.minimax.io/v1/text/chatcompletion_v2" \
  -X POST \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-Text-01",
    "messages": [{"role": "user", "content": "Hello, who are you?"}]
  }' | jq '.choices[0].message.content'
```

Available models:
- **MiniMax-M2**: Reasoning model (best quality)
- **MiniMax-M1**: Reasoning model (balanced)
- **MiniMax-Text-01**: Standard model (fastest)

### 2. Chat with Temperature Control

```bash
curl -s "https://api.minimax.io/v1/text/chatcompletion_v2" \
  -X POST \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-Text-01",
    "messages": [{"role": "user", "content": "Write a short poem about AI."}],
    "temperature": 0.7,
    "max_tokens": 200
  }' | jq '.choices[0].message.content'
```

Parameters:
- **temperature** (0-1): Higher = more creative
- **top_p** (0-1, default 0.95): Sampling diversity
- **max_tokens**: Maximum output tokens

### 3. Streaming Response

```bash
curl -s "https://api.minimax.io/v1/text/chatcompletion_v2" \
  -X POST \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-M1",
    "messages": [{"role": "user", "content": "Explain quantum computing."}],
    "stream": true
  }'
```

### 4. Reasoning Model (M1/M2)

```bash
curl -s "https://api.minimax.io/v1/text/chatcompletion_v2" \
  -X POST \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-M1",
    "messages": [{"role": "user", "content": "Solve: A train travels 120km in 2 hours. What is its average speed in m/s?"}]
  }' | jq '.choices[0].message.reasoning_content, .choices[0].message.content'
```

Response includes `reasoning_content` field with thought process.

### 5. Text-to-Speech (Basic)

```bash
curl -s "https://api.minimax.io/v1/t2a_v2" \
  -X POST \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "speech-02-hd",
    "text": "Hello, this is a test of MiniMax text to speech.",
    "voice_id": "male-qn-qingse",
    "speed": 1.0,
    "format": "mp3"
  }' --output speech.mp3
```

### 6. TTS with Emotion

```bash
curl -s "https://api.minimax.io/v1/t2a_v2" \
  -X POST \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "speech-02-hd",
    "text": "I am so happy to meet you today!",
    "voice_id": "female-shaonv",
    "emotion": "happy",
    "speed": 1.0,
    "format": "mp3"
  }' --output happy_speech.mp3
```

Emotion options: happy, sad, angry, fearful, disgusted, surprised, neutral

### 7. TTS Voice IDs

Popular voices:
- **male-qn-qingse**: Male, young, clear
- **female-shaonv**: Female, girl, light
- **female-tianmei**: Female, sweet
- **male-jike**: Male, deep

Full list: https://platform.minimax.io/docs/T2A

### 8. Text-to-Video (T2V)

```bash
curl -s "https://api.minimax.io/v1/video_generation" \
  -X POST \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "T2V-01-Director",
    "prompt": "A cat playing with a ball of yarn [Static shot].",
    "duration": 6,
    "resolution": "1080P"
  }' | jq '.task_id'
```

Video generation is async - returns a task ID to poll for completion.

### 9. T2V with Camera Control

```bash
curl -s "https://api.minimax.io/v1/video_generation" \
  -X POST \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-Hailuo-2.3",
    "prompt": "A person walking through a forest [Tracking shot], then stops to look at a bird [Push in].",
    "duration": 6,
    "resolution": "1080P"
  }' | jq '.task_id'
```

Camera commands (in brackets):
- **Movement**: Truck left/right, Pan left/right, Push in/Pull out
- **Vertical**: Pedestal up/down, Tilt up/down
- **Zoom**: Zoom in/out
- **Special**: Shake, Tracking shot, Static shot

Combine with [Pan left, Pedestal up] (max 3 simultaneous).

### 10. Image-to-Video (I2V)

```bash
curl -s "https://api.minimax.io/v1/video_generation" \
  -X POST \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-Hailuo-2.3",
    "prompt": "The scene comes to life with gentle movement [Static shot].",
    "first_frame_image": "https://example.com/image.jpg",
    "duration": 6,
    "resolution": "1080P"
  }' | jq '.task_id'
```

Provide first_frame_image as URL or base64-encoded image.

### 11. Poll Video Task Status

```bash
curl -s "https://api.minimax.io/v1/video_generation_result?task_id=YOUR_TASK_ID" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" | jq '.task.status, .task.video_url'
```

### 12. Function Calling (Tools)

```bash
curl -s "https://api.minimax.io/v1/text/chatcompletion_v2" \
  -X POST \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-Text-01",
    "messages": [{"role": "user", "content": "What is the weather in Beijing?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {"type": "object", "properties": {"location": {"type": "string"}}}
      }
    }]
  }' | jq '.choices[0].message.tool_calls'
```

## Rate Limits

| Tier | RPM | TPM |
|------|-----|-----|
| Free | 5 | 100K |
| Pro | 100 | 10M |

Check your usage at: https://platform.minimax.io/account
