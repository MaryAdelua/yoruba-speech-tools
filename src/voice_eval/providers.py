"""Small standard-library OpenAI adapter; no downloads, secrets, or SDK on import."""

import json
import mimetypes
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from .rubric import RUBRIC, result_schema


class ProviderError(RuntimeError):
    pass


class OpenAIProvider:
    def __init__(self, judge_model, transcription_model="gpt-4o-transcribe"):
        self.key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not self.key:
            raise ProviderError("Set OPENAI_API_KEY locally; do not paste it into chat or commit it.")
        self.judge_model = judge_model
        self.transcription_model = transcription_model

    def _post(self, endpoint, data, content_type):
        request = urllib.request.Request(
            "https://api.openai.com/v1/" + endpoint, data=data,
            headers={"Authorization": "Bearer " + self.key, "Content-Type": content_type},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            # Do not echo response bodies, headers, keys, or transcripts to logs.
            raise ProviderError(f"OpenAI {endpoint}: HTTP {exc.code}; check access, quota and model ID.") from None
        except (OSError, ValueError) as exc:
            raise ProviderError(f"OpenAI {endpoint}: transport or response error ({type(exc).__name__}).") from None

    def transcribe(self, path):
        boundary = "voiceeval" + uuid.uuid4().hex
        chunks = []
        for key, value in {"model": self.transcription_model, "response_format": "json"}.items():
            chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
        # Neutral filename; no reference text, expected answer, or forced language.
        suffix = Path(path).suffix.lower()
        mime = mimetypes.guess_type("audio" + suffix)[0] or "application/octet-stream"
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="audio{suffix}"\r\nContent-Type: {mime}\r\n\r\n'.encode())
        chunks.extend([Path(path).read_bytes(), f"\r\n--{boundary}--\r\n".encode()])
        value = self._post("audio/transcriptions", b"".join(chunks), f"multipart/form-data; boundary={boundary}")
        if not isinstance(value.get("text"), str):
            raise ProviderError("Transcription response has no text")
        return {"text": value["text"], "source": "automatic_asr", "model": self.transcription_model}

    def judge(self, payload):
        request = {
            "model": self.judge_model, "store": False,
            "instructions": RUBRIC,
            "input": [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            "text": {"format": {"type": "json_schema", "name": "yoruba_interaction",
                                  "strict": True, "schema": result_schema()}},
            "max_output_tokens": 4000,
        }
        response = self._post("responses", json.dumps(request).encode(), "application/json")
        if response.get("status") != "completed":
            raise ProviderError("Judge did not complete; no scores produced")
        parts = [part for item in response.get("output", []) if item.get("type") == "message"
                 for part in item.get("content", [])]
        if any(part.get("type") == "refusal" for part in parts):
            raise ProviderError("Judge refused the evaluation; no scores produced")
        try:
            result = json.loads("".join(part["text"] for part in parts if part.get("type") == "output_text"))
        except (ValueError, KeyError):
            raise ProviderError("Judge returned invalid JSON; no scores produced") from None
        return result, {"provider": "openai", "requested_model": self.judge_model,
                        "returned_model": response.get("model"), "response_id": response.get("id"),
                        "usage": response.get("usage")}
