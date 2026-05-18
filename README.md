# FoodMedKG

This repository contains the code used for the manuscript  
**FoodMedKG: Integrating Biomedical Knowledge and Culinary Data for Health-Aware Decision Support**

---

## Project Description

FoodMedKG integrates artificial intelligence, NoSQL databases, and graph databases in the field of nutrition and health. The system has two main components:

1. **Interactive Application** — Users submit recipes in natural language; a language model extracts ingredients and preparation methods, which are used to query a biomedical knowledge graph. Results cover food composition, the effect of foods on pathologies and aging, and how cooking methods affect nutritional value.

2. **Evaluation Framework** — A benchmark suite that measures how accurately LLMs extract structured ingredient data from free-text recipes, at three levels of strictness (strict, flexible, and soft semantic matching), plus analysis of the ingredients models add beyond the ground truth.

---

## Repository Structure

```
healthyFood/
├── app/
│   ├── .streamlit/
│   │   └── config.toml          # Streamlit theme and layout
│   ├── facts.txt                # Fun facts shown during query processing
│   ├── requirements.txt         # App dependencies
│   └── streamlit_app.py         # Main Streamlit application
│
├── data/
│   ├── 1 FooDB_grupo_id.py      # Assigns group IDs to FooDB food entries
│   ├── 2 Food_Simplificada.py   # Simplified food dataset generation
│   ├── 3 FooDB_Pivotado.py      # Pivots FooDB data by nutrient
│   ├── 4 FooDB_Final.py         # Final FooDB dataset preparation
│   ├── 5 ES_Rango.py            # Computes nutrient ranges for Elasticsearch
│   ├── 6 ES_Completa.py         # Full Elasticsearch dataset builder
│   ├── 7 ES_Final.py            # Final Elasticsearch dataset preparation
│   └── data_preparation.txt     # Notes on data preparation steps
│
├── evaluation/
│   ├── benchmark.json           # Batch 1 — 15 recipes with ground-truth ingredients & variants
│   ├── benchmark_batch2.json    # Batch 2 — 35 recipes with ground-truth ingredients & variants
│   ├── evaluate.py              # Main evaluation script (Part A: LLM extraction)
│   ├── compute_extras.py        # Patches CSVs with extra_ingredients column
│   ├── visualize.py             # Generates all paper figures (PNG + PDF)
│   ├── run_all_models.sh        # Runs all models on both batches end-to-end
│   └── requirements.txt         # Evaluation dependencies
│
├── .gitignore
├── LICENSE
└── README.md
```

---

## Requirements

### Application

```bash
pip install -r app/requirements.txt
```

Dependencies: `streamlit`, `pandas`, `sentence-transformers`, `scikit-learn`, `numpy`, `neo4j`, `langchain`, `langchain-ollama`

### Evaluation

```bash
pip install -r evaluation/requirements.txt
```

Dependencies: `langchain`, `langchain-ollama`, `sentence-transformers`, `pandas`, `matplotlib`, `scipy`, `numpy`, `wordcloud`

---

## Running the Application

The application requires a running **Neo4j** database and a running **Ollama** model.

- Neo4j: https://neo4j.com/
- Ollama: https://ollama.com/

```bash
cd app
streamlit run streamlit_app.py
```

---

## Running the Evaluation

### Overview

The evaluation framework (Part A) benchmarks LLMs on structured ingredient extraction from recipe names. It computes:

| Metric | Description |
|---|---|
| **F1 Strict** | Token-overlap F1 against the canonical ground truth |
| **F1 Flexible** | Best F1 across the ground truth + 2 recipe variants |
| **F1 Soft** | Cosine similarity ≥ threshold (default 0.75) using sentence embeddings |
| **Prep Valid Rate** | Fraction of ingredients with a valid preparation method |
| **JSON Valid Rate** | Fraction of runs where the model returned parseable JSON |
| **Extra Ingredients** | Ingredients extracted by the model that are not in any ground truth variant |

### Benchmarks

| File | Recipes | Description |
|---|---|---|
| `benchmark.json` | 15 | Complex, multi-ingredient dishes (Batch 1) |
| `benchmark_batch2.json` | 35 | Simple everyday recipes (Batch 2) |

Each recipe has a canonical `expected_ingredients` list plus two `ingredient_variants` to allow flexible matching.

### Full run — all models, both batches

```bash
cd evaluation
nohup bash run_all_models.sh > nohup_all.log 2>&1 &
```

Quick test (1 recipe per model per batch):

```bash
bash run_all_models.sh --test
```

Models evaluated (pulled automatically via Ollama if not installed):

- `llama3.1:8b-instruct-q8_0`
- `qwen3:8b-q8_0`
- `gemma2:9b-instruct-q8_0`
- `mistral:7b-instruct-q8_0`
- `dolphin-llama3:8b-v2.9-q8_0`

Results are saved to `evaluation/results/batch1/` and `evaluation/results/batch2/`.

### Add extra-ingredient analysis to existing results

If you already have Part A CSVs and want to add the `extra_ingredients` column:

```bash
cd evaluation
python compute_extras.py --results results/batch1 --benchmark benchmark.json
python compute_extras.py --results results/batch2 --benchmark benchmark_batch2.json
```

### Generate figures

```bash
cd evaluation
python visualize.py
```

Reads from `results/batch1/` and `results/batch2/` by default. Every figure is saved as both PNG and PDF in `figures/`.

| Figure | Description |
|---|---|
| `a1` | Metric distributions (KDE) across all models |
| `a2_*` | Extraction scatter per model (extracted vs expected count) |
| `a3` | Grouped bar — model comparison across all metrics |
| `a4` | F1 box plot per model |
| `a5` | F1 violin — Strict / Flexible / Soft comparison |
| `a6` | Word clouds of extra ingredients per model |
| `a7` | Top extra ingredients bar chart (coloured by model agreement) |
| `a8` | Model agreement analysis — distribution + ranked pill grid |

Custom paths:

```bash
python visualize.py --results results/batch1 results/batch2 --out figures/ --format pdf
```

---

## License

This project was developed for academic purposes as part of a Final Degree Project.

It is distributed under the  
**Creative Commons Attribution – NonCommercial – ShareAlike 4.0 International (CC BY-NC-SA 4.0)** license.

![CC BY-NC-SA License](https://mirrors.creativecommons.org/presskit/buttons/88x31/png/by-nc-sa.png)

This means it may be shared and adapted as long as the author is properly credited, it is not used for commercial purposes, and any derivative works are published under the same license.

More information: https://creativecommons.org/licenses/by-nc-sa/4.0/

For inquiries or potential collaborations, feel free to contact the authors.
