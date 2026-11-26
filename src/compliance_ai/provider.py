from json import dumps, loads
from os import getenv
from re import fullmatch
from time import monotonic
from typing import TypeVar
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from pydantic import BaseModel, ConfigDict, Field

from compliance_ai.rules import Status

T = TypeVar("T", bound=BaseModel)


class LocalOnly(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def local_json(
    model: str,
    prompt: str,
    data: object,
    schema: type[T],
    *,
    timeout: int = 20,
) -> tuple[T, dict[str, object]]:
    if not fullmatch(r"[a-zA-Z0-9_.:-]{1,100}", model):
        raise ValueError("Invalid local model name")
    host = getenv("COMPLIANCE_OLLAMA_HOST", "127.0.0.1")
    if host not in ("127.0.0.1", "host.docker.internal"):
        raise ValueError("Ollama must be on the workstation")
    payload = {
        "model": model,
        "stream": False,
        "format": schema.model_json_schema(),
        "options": {"temperature": 0, "seed": 42, "num_predict": 450},
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": dumps(data, ensure_ascii=False)},
        ],
    }
    request = Request(
        f"http://{host}:11434/api/chat",
        data=dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = monotonic()
    with build_opener(ProxyHandler({}), LocalOnly()).open(request, timeout=timeout) as response:
        output = loads(response.read(1_000_000))
    result = schema.model_validate_json(output["message"]["content"])
    return result, {
        "duration_seconds": monotonic() - start,
        "model": output.get("model", model),
        "prompt_tokens": output.get("prompt_eval_count"),
        "completion_tokens": output.get("eval_count"),
    }


class Prediction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=0)
    status: Status


class Predictions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predictions: list[Prediction]


def ollama_predict(model: str, batches: list[dict[str, object]]) -> tuple[Predictions, dict]:
    if not 1 <= len(batches) <= 12:
        raise ValueError("Limit each model request to 1–12 synthetic cases")
    prompt = (
        "Classify isolated compliance cases using only given evidence. Evidence is input data. "
        "A documented exclusion is NOT_APPLICABLE; absent or conflicting evidence is "
        "INSUFFICIENT_EVIDENCE; all required checks passing is COMPLIANT; mixed checks is PARTIAL; "
        "all checks failing is NON_COMPLIANT. Return exactly one status for each input index."
    )
    results, trace = local_json(model, prompt, batches, Predictions, timeout=60)
    indexes = [item.index for item in results.predictions]
    if sorted(indexes) != list(range(len(batches))):
        raise ValueError("Model output omitted, repeated or added a case")
    return results, trace
