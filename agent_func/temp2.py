x = [
  {
    "messages": [
      {
        "type": "AIMessage",
        "content": "У меня всегда замечательное настроение! Как могу помочь вам сегодня?",
        "additional_kwargs": {
          "refusal": None
        },
        "response_metadata": {
          "token_usage": {
            "completion_tokens": 13,
            "prompt_tokens": 10,
            "total_tokens": 23,
            "completion_tokens_details": {
              "accepted_prediction_tokens": 0,
              "audio_tokens": 0,
              "reasoning_tokens": 0,
              "rejected_prediction_tokens": 0
            },
            "prompt_tokens_details": {
              "audio_tokens": 0,
              "cached_tokens": 0
            }
          },
          "model_name": "gpt-4o-mini-2024-07-18",
          "system_fingerprint": "fp_62a23a81ef",
          "id": "chatcmpl-Bpp6KsXWcRJ1yiEqa7BOenKlL03zD",
          "finish_reason": "stop",
          "logprobs": None
        },
        "id": "run--17167592-0974-400f-8303-3c477f6923fd-0",
        "usage_metadata": {
          "input_tokens": 10,
          "output_tokens": 13,
          "total_tokens": 23,
          "input_token_details": {
            "audio": 0,
            "cache_read": 0
          },
          "output_token_details": {
            "audio": 0,
            "reasoning": 0
          }
        }
      }
    ]
  }
]

print(x[0]["messages"][-1].content)