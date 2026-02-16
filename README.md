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
python3 crawl/collect_manuals.py
python3 crawl/manualslib_list.py
```

This script scrapes ManualsLib for publicly available manual sections and saves the metadata to `portable_generator_toc_sections.json`.


```
python3 expand/manualslib_expand.py
```
This script processes the collected pdf data, extracts actionable workflows, and saves them to `portable_generator_workflows.json`.