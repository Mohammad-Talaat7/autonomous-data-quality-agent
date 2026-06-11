# AI Integration

ADQA's Phase 4 provides optional LLM-powered explanation, classification, and remediation
proposals layered on top of the deterministic pipeline.

## Optional dependency

LLM features are behind the `llm` extra:

```bash
pip install "adqa[llm]"
```

Nothing breaks without it. The deterministic pipeline runs identically.

## Configuration

Enable LLM features via `ADQAConfig`:

```python
from adqa import ADQA, ADQAConfig

config = ADQAConfig(
    llm={
        "enabled": True,
        "model": "gpt-5.4-mini",
        "timeout_seconds": 30,
        "max_input_chars": 12000,
        "redact_samples": True,
    }
)
```

## Safety Rules

- LLMs **cannot** mutate data, decide PASS/WARN/FAIL, or bypass execution policy.
- Outputs are proposals and explanations only.
- Raw data is redacted by default.
- All LLM calls are traced with hashed inputs and outputs.

## Environment Variables

Provider configuration uses standard environment variables:

```bash
export OPENAI_API_KEY=sk-...
# or
export LITELLM_API_KEY=sk-...
```

See [LiteLLM provider docs](https://docs.litellm.ai/docs/providers) for setup.

## Examples

### Run analysis with LLM explanation

```python
from adqa import ADQA, ADQAConfig
import pandas as pd

df = pd.DataFrame({"email": ["a@x.com", None, None]})
config = ADQAConfig(llm={"enabled": True, "model": "gpt-4o-mini"})
result = ADQA.from_df(df, config=config).analyze()

if result.explanation:
    print(result.explanation.short_summary)
    print(result.explanation.recommended_next_steps)
```

### Run without LLM (deterministic only)

```python
from adqa import ADQA
import pandas as pd

df = pd.DataFrame({"email": ["a@x.com", None, None]})
result = ADQA.from_df(df).analyze()

# explanation is None — no LLM configured
assert result.explanation is None
print(result.summary())
```

### Use fake client in tests (no network)

```python
from adqa.llm.client import BaseLLMClient
from adqa.llm.models import LLMRequest, LLMResponse

class FakeLLMClient(BaseLLMClient):
    def complete(self, request: LLMRequest) -> LLMResponse:
        ...

from adqa import ADQA, ADQAConfig

config = ADQAConfig(llm={"enabled": True, "model": "test"})
result = ADQA.from_df(df, config=config, llm_client=FakeLLMClient()).analyze()
```

### Show remediation proposals

```python
from adqa.explanation.remediation import RemediationProposalEngine
from adqa import ADQA, ADQAConfig

config = ADQAConfig(
    llm={"enabled": True, "model": "gpt-4o-mini"},
    detection={"thresholds": {"missing_values_threshold": 0.1}},
)
result = ADQA.from_df(df, config=config).analyze()

engine = RemediationProposalEngine()
proposals = engine.propose(decision=result.decision, action_plan=result.plan)

for p in proposals.proposals:
    print(f"{p.issue_type}: {p.operational_mapping} — {p.plain_language}")
```

### CLI explain

```bash
adqa explain data.csv --llm-model gpt-5.4-mini
```

### CLI chat (interactive)

```bash
adqa explain data.csv --llm-model gpt-5.4-mini
adqa chat data.csv --llm-model gpt-5.4-mini
```
