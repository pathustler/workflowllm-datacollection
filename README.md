# WorkflowLLM – Data Generation Pipeline

Transforms real-world technical manual content into structured workflow datasets for training LLMs on procedural reasoning.

---

## Prerequisites

Python 3.12.7+ required.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Playwright also needs its browser binary:

```bash
playwright install chromium
```

Set your OpenAI key in a `.env` file (required for QA generation only):

```
OPENAI_API_KEY=sk-...
```

---

## Repository Structure

```
WorkflowLLM/
├── crawl/                        # Stage 1 – collect manual metadata
│   ├── collect_manuals.py        # crawl all ManualsLib brands/products/models
│   ├── manualslib_list.py        # extract TOC sections from each manual
│   └── collect_marine.py         # targeted crawl for ABB Marine Equipment
├── expand/                       # Stage 2 – extract workflow steps
│   ├── manualslib_expand.py      # Playwright-based extractor (local use)
│   ├── manualslib_expand_seq.py  # HTTP-based extractor (server/HPC use)
│   ├── expand_marine.py          # full-manual extractor for MARINE dataset
│   └── ss_marine.py              # screenshot tool for MARINE manuals
├── qa/                           # QA pair generation
│   └── qa_gen.py
├── generate/                     # (not yet implemented)
├── enrich/                       # (not yet implemented)
├── filter/                       # (not yet implemented)
├── dataset/                      # (not yet implemented)
└── utils/
    └── llm.py
```

---

## Dataset 1 – Portable Generator Workflows

Step-by-step procedures extracted from portable generator manuals on ManualsLib.

**Output:** `portable_generator_workflows.json`

### Step 1 — Crawl all manuals

```bash
python3 crawl/collect_manuals.py
```

Walks the ManualsLib brand → product → model hierarchy and saves all manual URLs.

**Produces:** `manualslib_all_manuals.json`

### Step 2 — Extract table of contents sections

```bash
python3 crawl/manualslib_list.py
```

For each manual, fetches its TOC and saves each section as a separate entry with a direct page URL.

**Produces:** `portable_generator_toc_sections.json`

### Step 3 — Extract workflow steps

Choose one extractor depending on your environment:

**Local (uses Playwright/Chromium):**
```bash
python3 expand/manualslib_expand.py
# Resume from a specific index if interrupted:
python3 expand/manualslib_expand.py --start 500
```

**Server / HPC (uses requests + threading, no browser needed):**
```bash
python3 expand/manualslib_expand_seq.py
python3 expand/manualslib_expand_seq.py --start 500
```

Both render each manual page, parse the PDF viewer HTML, sort text blocks by position, and filter out headers and noise.

**Produces:** `portable_generator_workflows.json`

---

## Dataset 2 – MARINE

100 real-world automation workflows extracted from ABB Marine Equipment manuals on ManualsLib.

**Output:** `marine_workflows.json`

### Step 1 — Crawl ABB Marine manuals

```bash
python3 crawl/collect_marine.py
```

**Produces:** `abb_marine_manuals.json`

### Step 2 — Extract workflow steps

```bash
python3 expand/expand_marine.py
# Resume from a specific index if interrupted:
python3 expand/expand_marine.py --start 20
```

Paginates through each full manual (up to 300 pages), handles both PDF-viewer and HTML-rendered pages.

**Produces:** `marine_workflows.json`

### (Optional) Screenshot each manual page

```bash
python3 expand/ss_marine.py
```

Captures page-by-page JPEG screenshots of the first 100 manuals.

**Produces:** `ABB_Marine_Screenshots/<model>/<manual>_page_N.jpg`

---

## QA Pair Generation

Generates question-answer pairs from any extracted workflow dataset using GPT-4o-mini.

```bash
python3 qa/qa_gen.py
```

Reads from `portable_generator_workflows.json` by default. Edit `INPUT_FILE` at the top of the script to point at a different source (e.g. `marine_workflows.json`).

Produces 3–5 QA pairs per workflow chunk (procedural, reasoning, and edge-case questions).

**Produces:** `qa_output.json`

---

## Output Files Reference

| File | Description |
|---|---|
| `manualslib_all_manuals.json` | All ManualsLib manual URLs and metadata |
| `portable_generator_toc_sections.json` | Individual TOC section entries with page URLs |
| `portable_generator_workflows.json` | Extracted workflow steps (portable generator manuals) |
| `abb_marine_manuals.json` | ABB Marine Equipment manual URLs and metadata |
| `marine_workflows.json` | Extracted workflow steps (MARINE dataset) |
| `marine_workflows_cleaned.json` | Cleaned MARINE workflows (non-actionable steps removed) |
| `qa_output.json` | Generated QA pairs |
