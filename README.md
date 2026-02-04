# WorkflowLLM – Data Generation Pipeline

This repository implements the **data generation pipeline** described in the WorkflowLLM paper.  
The goal is to transform real-world automation metadata into a **hierarchically supervised dataset**
for training large language models on workflow reasoning.

The pipeline is intentionally modular and mirrors the paper’s stages:
1. Metadata collection (crawling)
2. Synthetic workflow generation
3. Validation, enrichment, and dataset construction

This README documents **Stage 1 only**: data collection.

---

## Repository Structure (Relevant Parts)

WorkflowLLM/
├── crawl/
│ ├── crawl_routinehub.py
│ └── crawl_shortcut_detail.py
├── generate/
├── enrich/
├── filter/
├── expand/
├── dataset/
├── utils/
├── raw_shortcuts.json
├── shortcuts_enriched.json
└── run_pipeline.py


## Stage 0: Prerequisites

Python 3.12.7 or higher is required.

```
source .venv/bin/activate

pip install -r requirements.txt
```


## Stage 1: Data Collection (Crawling)

The crawler collects **automation task metadata** from RoutineHub.
Due to paywalls, most workflows are not downloadable; this is expected and handled later via synthesis.

```
python3 crawl/crawl_routinehub.py
```

This script scrapes RoutineHub for publicly available shortcuts and saves the metadata to `raw_shortcuts.json`.
