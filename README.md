# PM Scenario Analyzer MVP

A Streamlit-based MVP for a reusable PM requirement analysis tool for conversational financial services.

## MVP capabilities

- Input Mode A: free-form PM notes
- Input Mode B: Figma screenshot image upload
- Input Mode C: structured requirement template
- Scenario Normalization into a common ScenarioSpec model
- Scenario Decomposition for large features
- PM Review Mode gap analysis
- Missing Questions generation
- Requirement Maturity reference level
- PM Review Mode as the default output
- Gap Fixing Iteration guidance before downstream handoff
- On-demand CX Agent Studio Package draft after Agent Ready or explicit PM request
- Mermaid Flow output

## MVP exclusions

This first version does not include Figma API, Dev Mode links, login, database, dashboard, multi-user collaboration, LLM API calls, or production agent generation. The default output is PM Review Mode; CX Agent Studio Package generation is gated until the requirement is Agent Ready or the PM explicitly requests a draft.

## Product flow

```text
Input
↓
Analyze
↓
PM Review Mode
↓
Gap Fixing Iteration
↓
Agent Ready
↓
Generate CX Agent Studio Package
```

The PM's primary goal is to find missing requirements and iterate. CX Agent Studio Package is not the default output.

## Local setup and run instructions

### 1. Prerequisites

- Python 3.11 or newer is recommended.
- `pip` must be available in the selected Python environment.
- No database, login service, Figma token, or LLM API key is required for the MVP.

### 2. Create and activate a virtual environment

From the repository root:

```bash
python -m venv .venv
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install `requirements.txt`

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

The current MVP dependencies are:

```text
streamlit==1.41.1
Pillow==11.0.0
```

### 4. Start Streamlit

Run the app from the repository root:

```bash
streamlit run app.py
```

Streamlit will print a local URL, usually:

```text
http://localhost:8501
```

Open that URL in a browser to use the MVP.

## How to test with `sample_data`

The repository includes three sample PM inputs:

```text
sample_data/card_loss_reissue.txt
sample_data/transaction_detail_inquiry.txt
sample_data/dispute_application.txt
```

To test from the UI:

1. Start the app with `streamlit run app.py`.
2. In the left panel, keep **Mode A：自由文字** selected.
3. Open one sample file locally.
4. Copy the full file content.
5. Paste it into the free-form PM notes text area.
6. Click **Analyze**.
7. Review the default **PM Review Mode** output.
8. Optionally switch to **Mermaid Flow**.
9. If you want an early CX draft before the requirement is Agent Ready, switch to **CX Agent Studio Package** and click **Generate CX Agent Studio Package Draft**.

For a quick command-line smoke test of the mock analyzer, run:

```bash
python - <<'PY'
from pathlib import Path
from services import analyze_requirement

sample = Path('sample_data/card_loss_reissue.txt').read_text()
result = analyze_requirement(free_text=sample)

print(result.scenario_spec.feature_name)
print(result.maturity_level, result.maturity_label)
print(result.mermaid_flow)
PY
```

Expected high-level result for `card_loss_reissue.txt`:

- Feature name: `信用卡掛失補發`
- Requirement maturity: `Level 3 Exception Coverage`
- Default UI output: PM Review Mode
- CX Agent Studio Package: gated until Agent Ready or explicit PM request

## Current MVP implementation status

### Completed

- Streamlit app entrypoint in `app.py`.
- Three PM input modes:
  - Mode A: free-form PM notes
  - Mode B: Figma screenshot image upload
  - Mode C: structured requirement template
- Supplemental notes field.
- Analyze button and in-memory Streamlit session state.
- Deterministic mock analyzer with no LLM/API calls.
- ScenarioSpec normalization model.
- Scenario decomposition for known sample scenarios.
- PM Review Mode as the default output.
- Gap analysis output:
  - covered areas
  - missing areas
  - missing business rules
  - missing decision tables
  - missing state definitions
  - missing journey entry/exit
  - recommended next actions
- Missing questions generation.
- Requirement Maturity Level as a reference-only indicator.
- Gap Fixing Iteration guidance.
- Mermaid flow generation.
- CX Agent Studio Package generation gated behind Agent Ready or explicit PM request.
- Sample PM input files under `sample_data/`.
- Prompt placeholder files under `prompts/` for future LLM-enabled versions.

### Not completed in MVP v1

- Real LLM-based requirement analysis.
- Real OCR or vision extraction from Figma screenshots.
- Figma API integration.
- Figma Dev Mode link support.
- Login, user roles, or access control.
- Database persistence.
- Saved analysis history.
- Dashboard or analytics.
- Multi-user collaboration.
- Editable ScenarioSpec review screen.
- Production Agent Instruction generation.
- Production prompt generation.
- Direct CX Agent Studio deployment.
- Real banking API execution.
- Automated compliance, risk, legal, or operational approval.

## Project structure

```text
app.py
models/
services/
sample_data/
prompts/
requirements.txt
```
