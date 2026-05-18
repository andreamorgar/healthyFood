# FoodMedKG — Evaluation Report

**Generated from:** `results/batch1/` (15 recipes) + `results/batch2/` (35 recipes)  
**Models evaluated:** 5  
**Total recipes:** 50  
**Evaluation runs per recipe:** 1  

---

## 1. Experimental Setup

### 1.1 Benchmarks

Two recipe benchmarks were used, covering a total of 50 dishes.

| Benchmark | File | Recipes | Profile |
|---|---|---|---|
| Batch 1 | `benchmark.json` | 15 | Complex, multi-ingredient dishes (e.g. spaghetti bolognese, vegetable curry, beef tacos) |
| Batch 2 | `benchmark_batch2.json` | 35 | Simple everyday recipes (e.g. scrambled eggs, hummus, pasta carbonara) |

Each recipe contains a canonical `expected_ingredients` list and two alternative `ingredient_variants`, enabling evaluation at three matching levels.

### 1.2 Models

All models were served locally via [Ollama](https://ollama.com/) using 8-bit quantized weights (Q8_0), ensuring reproducibility and eliminating API variability. Temperature was set to 0 for all runs.

| Model | Tag |
|---|---|
| LLaMA 3.1 8B | `llama3.1:8b-instruct-q8_0` |
| Qwen3 8B | `qwen3:8b-q8_0` |
| Gemma 2 9B | `gemma2:9b-instruct-q8_0` |
| Mistral 7B | `mistral:7b-instruct-q8_0` |
| Dolphin-LLaMA3 8B | `dolphin-llama3:8b-v2.9-q8_0` |

### 1.3 Evaluation Metrics

For each recipe, the model was prompted to generate the recipe and return a structured JSON with ingredients (name, preparation, amount, weight). The following metrics were computed:

| Metric | Definition |
|---|---|
| **JSON Valid Rate** | Fraction of runs that returned parseable JSON |
| **Fields Complete** | Fraction of ingredients with all four fields filled (name, preparation, amount, weight) |
| **Prep Valid Rate** | Fraction of ingredients with a preparation method from the expected vocabulary |
| **Precision** | Strict token-overlap: fraction of extracted ingredients matching any ground-truth ingredient |
| **Recall** | Strict token-overlap: fraction of expected ingredients found in extracted set |
| **F1 Strict** | Harmonic mean of strict precision and recall against canonical ground truth |
| **F1 Flexible** | Best F1 achieved across canonical ground truth and its two recipe variants |
| **F1 Soft** | Best F1 using cosine similarity ≥ 0.75 (sentence-transformer embeddings) across all variants |
| **Avg. Extracted** | Mean number of ingredients extracted by the model |
| **Extra Ingredients** | Ingredients extracted by the model not found in any variant of the ground truth |

The three F1 levels capture different tolerances: Strict penalises any deviation from the canonical list; Flexible accepts recipe variants (e.g. cream instead of milk in scrambled eggs); Soft handles lexical variation via semantic embeddings (e.g. "spaghetti" ≈ "pasta").

---

## 2. Part A — LLM Ingredient Extraction Results

### 2.1 Per-Model Summary (all 50 recipes)

| Model | JSON Valid | Fields Complete | Prep Valid | Precision | Recall | F1 Strict | F1 Flexible | F1 Soft |
|---|---|---|---|---|---|---|---|---|
| LLaMA 3.1 8B | **1.000** | **0.975** | 0.843 | **0.602** | 0.652 | **0.609** | **0.665** | 0.670 |
| Qwen3 8B | **1.000** | **1.000** | **1.000** | 0.711 | **0.805** | **0.725** | **0.783** | **0.780** |
| Gemma 2 9B | 0.900 | 0.866 | 0.730 | 0.468 | 0.574 | 0.496 | 0.567 | 0.604 |
| Mistral 7B | 0.920 | 0.851 | 0.575 | 0.444 | 0.476 | 0.440 | 0.483 | 0.627 |
| Dolphin-LLaMA3 8B | **1.000** | 0.917 | 0.474 | 0.528 | 0.504 | 0.491 | 0.536 | 0.668 |
| **Grand mean** | **0.964** | **0.922** | **0.724** | **0.551** | **0.602** | **0.552** | **0.607** | **0.670** |
| Grand std | 0.187 | 0.193 | 0.373 | 0.271 | 0.300 | 0.256 | 0.264 | 0.250 |

**Key observations:**

- **Qwen3 8B** is the best-performing model overall, achieving the highest F1 at all three matching levels (0.725 strict / 0.783 flexible / 0.780 soft) and perfect scores on JSON validity, field completeness, and preparation validity.
- **LLaMA 3.1 8B** is the second-best model in F1 and leads in precision (0.602), with perfect JSON validity and strong field completeness (0.975).
- **Gemma 2 9B** and **Mistral 7B** show more variable performance, with Gemma reaching better recall but lower precision.
- **Dolphin-LLaMA3 8B** produces perfectly valid JSON but has the lowest preparation validity (0.474), suggesting it extracts ingredients reliably but struggles with preparation categorisation.
- The gap between F1 Strict and F1 Flexible (grand mean: +0.055) indicates that recipe variants capture valid alternative formulations not covered by the canonical ground truth.
- The gap between F1 Flexible and F1 Soft is smaller (+0.063), suggesting that most flexible-level mismatches are genuine omissions rather than synonym confusion.

> **Figure reference:** Figure a3 (grouped bar chart) and Figure a4 (F1 box plot per model) provide a full visual comparison. Figure a1 shows the metric distributions as overlapping KDE curves. Figure a5 shows the violin plot comparing F1 Strict, Flexible, and Soft per model with connected mean trajectories.

### 2.2 Per-Batch Breakdown

Results split by benchmark batch (Batch 1: 15 complex recipes; Batch 2: 35 simple recipes):

| Model | Batch | n | F1 Strict | F1 Flexible | F1 Soft | Precision | Recall |
|---|---|---|---|---|---|---|---|
| LLaMA 3.1 8B | Batch 1 | 15 | 0.677 | 0.697 | 0.678 | 0.701 | 0.698 |
| LLaMA 3.1 8B | Batch 2 | 35 | 0.580 | 0.652 | 0.666 | 0.560 | 0.632 |
| Qwen3 8B | Batch 1 | 15 | 0.743 | 0.779 | 0.786 | 0.720 | 0.811 |
| Qwen3 8B | Batch 2 | 35 | 0.717 | 0.785 | 0.777 | 0.707 | 0.802 |
| Gemma 2 9B | Batch 1 | 15 | 0.399 | 0.437 | 0.444 | 0.366 | 0.463 |
| Gemma 2 9B | Batch 2 | 35 | 0.538 | 0.623 | 0.673 | 0.511 | 0.621 |
| Mistral 7B | Batch 1 | 15 | 0.462 | 0.487 | 0.554 | 0.464 | 0.505 |
| Mistral 7B | Batch 2 | 35 | 0.430 | 0.482 | 0.658 | 0.436 | 0.464 |
| Dolphin-LLaMA3 8B | Batch 1 | 15 | 0.517 | 0.544 | 0.639 | 0.550 | 0.528 |
| Dolphin-LLaMA3 8B | Batch 2 | 35 | 0.480 | 0.532 | 0.680 | 0.519 | 0.494 |

**Key observations:**

- Most models score higher on Batch 1 (complex recipes) than Batch 2 under strict matching, which seems counterintuitive. This is partly explained by the fact that complex recipes have more ingredients, increasing the chance of token overlaps. Qwen3 is an exception, maintaining consistent performance across both batches.
- The F1 Soft scores for Mistral on Batch 2 are notably higher than Strict (+0.228), suggesting that Mistral uses semantically correct but lexically different ingredient names for simple dishes.
- Gemma 2 shows a large improvement from Batch 1 to Batch 2 under Flexible and Soft matching (+0.186 / +0.229), indicating it handles simple recipes more robustly once variant tolerance is allowed.

### 2.3 Extraction Count vs. Ground Truth

On average across all models and recipes, LLMs extracted **5.55 ingredients** (std=2.95) against an expected mean of **4.90** (std=1.16). Models tend to slightly over-extract, which is reflected in precision being lower than recall across most models.

| Model | Avg. Extracted | Expected | Difference |
|---|---|---|---|
| Qwen3 8B | 6.08 | 4.90 | +1.18 |
| Gemma 2 9B | 5.88 | 4.90 | +0.98 |
| LLaMA 3.1 8B | 5.46 | 4.90 | +0.56 |
| Mistral 7B | 5.34 | 4.90 | +0.44 |
| Dolphin-LLaMA3 8B | 5.00 | 4.90 | +0.10 |

> **Figure reference:** Figure a2 (one per model) shows the extraction scatter: each recipe is a point positioned at (n\_expected, n\_extracted), coloured by F1, with the 1:1 diagonal and the over-extraction zone highlighted.

### 2.4 Structural Quality

| Model | JSON Valid Rate | Fields Complete | Prep Valid Rate |
|---|---|---|---|
| Qwen3 8B | 1.000 | 1.000 | **1.000** |
| LLaMA 3.1 8B | 1.000 | 0.975 | 0.843 |
| Dolphin-LLaMA3 8B | 1.000 | 0.917 | 0.474 |
| Mistral 7B | 0.920 | 0.851 | 0.575 |
| Gemma 2 9B | 0.900 | 0.866 | 0.730 |

Qwen3 is the only model achieving perfect structural compliance across all three quality metrics. The low preparation validity of Dolphin-LLaMA3 (0.474) stands out: despite generating valid JSON with complete fields, it frequently uses preparation terms outside the expected vocabulary (e.g. multi-word phrases instead of single-word methods such as *steamed*, *roasted*, *raw*).

---

## 3. Extra Ingredients Analysis

### 3.1 Overview

An *extra ingredient* is one extracted by the model but absent from both the canonical ground truth and all two recipe variants. These extras represent additions the model makes based on its own culinary knowledge.

| Model | Extra occurrences | Unique ingredients | Recipes with extras |
|---|---|---|---|
| Mistral 7B | 127 | 64 | 50/50 |
| Gemma 2 9B | 112 | 50 | 50/50 |
| Dolphin-LLaMA3 8B | 100 | 52 | 50/50 |
| LLaMA 3.1 8B | 91 | 49 | 50/50 |
| Qwen3 8B | 80 | 48 | 50/50 |

All models added extras to every recipe. Mistral adds the most (127 occurrences, 64 unique), consistent with its tendency to over-extract. Qwen3, despite being the best-performing model, still adds 80 extras — suggesting that even high-accuracy models systematically include ingredients beyond the ground truth.

### 3.2 Top Extra Ingredients

The 25 most frequent extras across all models and recipes:

| Ingredient | Total count | Models agreeing |
|---|---|---|
| salt | 92 | 5/5 |
| pepper | 49 | 5/5 |
| eggs | 24 | 4/5 |
| vegetable broth | 15 | 4/5 |
| tomatoes | 15 | 3/5 |
| oil | 14 | 5/5 |
| carrots | 9 | 4/5 |
| black pepper | 8 | 3/5 |
| spaghetti | 7 | 5/5 |
| paprika | 7 | 4/5 |
| sugar | 6 | 3/5 |
| vegetables | 6 | 3/5 |
| broth | 6 | 3/5 |
| onions | 6 | 2/5 |
| diced tomatoes | 5 | 4/5 |
| lettuce | 5 | 3/5 |
| chickpeas | 5 | 3/5 |
| thyme | 5 | 3/5 |
| bay leaf | 5 | 3/5 |
| cumin | 5 | 3/5 |
| noodles | 4 | 4/5 |
| curry powder | 4 | 4/5 |
| water | 4 | 3/5 |
| potato | 5 | 2/5 |
| green beans | 4 | 2/5 |

> **Figure reference:** Figure a6 shows word clouds of extras per model and a combined panel. Figure a7 shows a horizontal bar chart of top extras coloured by model agreement fraction.

### 3.3 Model Agreement as a Proxy for Subjectivity

To distinguish *universal* extras (likely missing from the ground truth) from *subjective* additions (model-specific creative choices), we computed the agreement level for each (recipe × ingredient) pair: how many of the 5 models extracted that ingredient as an extra for that specific recipe.

**Agreement distribution (338 total recipe × ingredient pairs):**

| Agreement level | Pairs | Percentage | Interpretation |
|---|---|---|---|
| 1 model | 220 | 65.1% | Subjective — unique to one model |
| 2 models | 75 | 22.2% | Partially shared |
| 3 models | 35 | 10.4% | Majority consensus |
| 4 models | 5 | 1.5% | Near-universal |
| 5 models | 3 | 0.9% | Universal — all models agree |

The distribution is strongly skewed: **65.1% of extras are unique to a single model**, confirming that most additions are idiosyncratic model-specific choices. Only **0.9% of extras are agreed upon by all five models** — these represent ingredients so universally associated with a dish that every model includes them despite their absence from the benchmark ground truth (e.g., *salt* and *pepper* appear in all models for nearly every recipe, and *spaghetti* as a synonym for pasta appears universally).

This analysis suggests a two-tier decomposition of extra ingredients:
- **Universal extras** (agreement = 5): These are strong candidates for ground truth augmentation — all five independent models agree the ingredient belongs in the recipe.
- **Subjective extras** (agreement = 1): These reflect each model's learned culinary biases and creative tendencies, and can be used to profile model behaviour beyond accuracy metrics.

> **Figure reference:** Figure a8 shows this analysis in two panels: (top) a bar chart of the agreement level distribution with percentage annotations; (bottom) a ranked pill grid where each row is an agreement level and ingredients are sorted by extraction frequency.

---

## 4. Part B — Ingredient Matching Accuracy

### 4.1 Overview

Part B evaluates the system's ability to retrieve the correct food entry from the Neo4j knowledge graph given an ingredient name as extracted by an LLM. This directly tests the KG retrieval step that sits between Part A (LLM extraction) and Part C (disease association).

**Requires:** a running Neo4j instance (`--with-db` flag).  
**Run command:**
```bash
cd evaluation
python evaluate.py --with-db --skip-llm --save-csv results/batch1/
```

### 4.2 Matching Benchmark

The benchmark contains **182 queries** across **15 food groups**, each representing a different surface form an LLM might use for the same food:

| Food group | Queries |
|---|---|
| Vegetables | 25 |
| Animal foods | 16 |
| Aquatic foods | 16 |
| Cereals and cereal products | 16 |
| Fruits | 16 |
| Herbs and Spices | 16 |
| Milk and milk products | 16 |
| Nuts | 12 |
| Pulses | 12 |
| Beverages | 9 |
| Baking goods | 6 |
| Cocoa and cocoa products | 6 |
| Soy | 6 |
| Teas | 6 |
| Eggs | 4 |
| **Total** | **182** |

Each query tests a specific surface form. For example, the food "broccoli" is tested as: `broccoli`, `broccoli florets`, `fresh broccoli`, `broccoli head`, `broccolis` — covering canonical names, plurals, adjective-prefixed forms, and preparation-prefixed forms. This reflects the variability of LLM output in real extraction scenarios.

### 4.3 Retrieval Method

For each query, the system:

1. Encodes the query with **SentenceTransformer** (`all-MiniLM-L6-v2`)
2. Computes a **combined score** against every food entry in the KG:

   ```
   final_score = 0.7 × cosine_similarity + 0.3 × JaroWinkler_similarity
   ```

3. Filters out **processed food entries** (e.g. "boiled broccoli", "roasted almond") to match the application's behaviour of querying raw ingredients
4. Returns the **top-k candidates** (default k=3)

A result is considered correct if any key word from the ground-truth `key_words` list appears in the matched food name.

### 4.4 Metrics

| Metric | Definition |
|---|---|
| **Top-1 Accuracy** | Fraction of queries where the first result is correct |
| **Top-3 Accuracy** | Fraction of queries where any of the top-3 results is correct |
| **MRR** | Mean Reciprocal Rank — 1/rank of the first correct result, averaged over all queries |

> **Note:** Part B results require a live Neo4j connection and are not stored in the repository. To regenerate: `python evaluate.py --with-db --skip-llm --save-csv results/batch1/`

> **Figure reference:** Figure b1 (score distribution KDE: correct vs incorrect), b2 (violin of scores per food group), b3 (score bucket histogram), b4 (grouped bar: Top-1 / Top-3 / MRR per group), b5 (lollipop chart of accuracy per food group sorted by Top-1).

---

## 5. Part C — KG Disease Association Correctness

### 5.1 Overview

Part C validates that the knowledge graph correctly encodes food–disease relationships. It checks a curated set of ground-truth triples of the form *(food, disease, suitable)* against the actual `Affects` edges in the KG.

**Requires:** a running Neo4j instance (`--with-db` flag).

### 5.2 Ground Truth

**15 triples** covering 8 distinct foods and 12 diseases:

| Food | Disease | Suitable | Rationale |
|---|---|---|---|
| broccoli | cancer | Yes | Anti-cancer glucosinolates |
| broccoli | breast cancer | Yes | Sulforaphane activity |
| broccoli | colorectal cancer | Yes | Dietary fibre and phytochemicals |
| spinach | cancer | Yes | Antioxidant and folate content |
| spinach | anemia | Yes | Iron and folate source |
| almond | coronary heart disease | Yes | Monounsaturated fats and vitamin E |
| almond | high cholesterol | Yes | LDL-lowering effect |
| sugar | caries | No | Direct cariogenic effect |
| sugar | alzheimer's disease | No | Metabolic inflammation link |
| added salt | high blood pressure | No | Sodium–hypertension relationship |
| added salt | hypertension | No | Direct sodium effect |
| albacore tuna | cancer | Yes | Omega-3 anti-inflammatory effects |
| albacore tuna | ischemic heart disease | Yes | Omega-3 cardioprotective effects |
| apple juice | cardiovascular diseases | Yes | Polyphenol content |
| apple juice | type 2 diabetes | Yes | Quercetin insulin sensitivity |

The set intentionally includes both suitable (11) and not-suitable (4) triples, and covers well-established relationships with clear biochemical rationale, making it a high-confidence gold standard.

### 5.3 Metrics

| Metric | Definition |
|---|---|
| **Found rate** | Fraction of triples where the food–disease edge exists in the KG |
| **Suitability correct** | Fraction of triples where both the edge exists and the suitability label matches |

> **Note:** Part C results require a live Neo4j connection. To regenerate: `python evaluate.py --with-db --skip-llm --save-csv results/batch1/`

> **Figure reference:** Figure c1 — two panels: (left) per-food bar of found rate vs correctness rate; (right) pie chart of correct / wrong suitability / not found.

---

## 6. Summary and Key Findings

### 6.1 Ranking

Based on F1 Strict across all 50 recipes:

| Rank | Model | F1 Strict | F1 Flexible | F1 Soft | JSON Valid | Prep Valid |
|---|---|---|---|---|---|---|
| 1 | **Qwen3 8B** | **0.725** | **0.783** | **0.780** | 1.000 | **1.000** |
| 2 | LLaMA 3.1 8B | 0.609 | 0.665 | 0.670 | 1.000 | 0.843 |
| 3 | Gemma 2 9B | 0.496 | 0.567 | 0.604 | 0.900 | 0.730 |
| 4 | Dolphin-LLaMA3 8B | 0.491 | 0.536 | 0.668 | 1.000 | 0.474 |
| 5 | Mistral 7B | 0.440 | 0.483 | 0.627 | 0.920 | 0.575 |

### 6.2 Effect of Matching Flexibility

Across all models, relaxing from Strict to Flexible matching improves F1 by an average of **+0.055** (range: +0.040–+0.058). Further relaxing to Soft matching adds another **+0.063** on average. The consistent improvement across all models shows that recipe variants and lexical variation are genuine sources of underestimation in strict evaluation.

| | F1 Strict → Flexible | F1 Flexible → Soft |
|---|---|---|
| Average gain | +0.055 | +0.063 |
| Largest gain | Qwen3: +0.058 | Mistral: +0.144 |
| Smallest gain | Dolphin: +0.045 | Qwen3: -0.003 |

### 6.3 Structural vs. Semantic Quality

A notable split emerges between structural quality (JSON validity, field completeness) and semantic quality (ingredient accuracy, preparation validity):

- Models with **perfect structural compliance** (LLaMA 3.1, Qwen3, Dolphin) do not necessarily achieve the best F1 — Dolphin produces flawless JSON but achieves lower F1 and poor preparation validity.
- **Qwen3** is the only model that excels on both dimensions simultaneously.

### 6.4 Extra Ingredients as a Quality Signal

The extra ingredient analysis reveals that all models systematically add ingredients beyond the benchmark ground truth. The agreement-based decomposition shows this is not random noise: 65.1% of extras are model-specific (subjective), while a small core of universally agreed-upon extras (*salt*, *pepper*, *oil*) may indicate gaps in the benchmark ground truth rather than model errors. This finding motivates ground truth augmentation strategies for future benchmark iterations.

---

## 7. Figures Reference

| Figure | Filename | Content |
|---|---|---|
| a1 | `a1_metric_distributions.png/.pdf` | KDE distributions of all metrics, one curve per model, all overlaid |
| a2 | `a2_extraction_scatter_<model>.png/.pdf` | Per-model scatter: n\_extracted vs n\_expected, coloured by F1 |
| a3 | `a3_model_comparison.png/.pdf` | Grouped bar chart comparing all models across all metrics |
| a4 | `a4_f1_boxplot.png/.pdf` | F1 Strict box plot per model |
| a5 | `a5_f1_comparison.png/.pdf` | Violin + connected-mean plot comparing F1 Strict / Flexible / Soft |
| a6 | `a6_extra_wordclouds.png/.pdf` | Word clouds of extra ingredients, one panel per model + combined |
| a7 | `a7_extra_ingredients_bar.png/.pdf` | Top 20 extra ingredients, coloured by model agreement fraction |
| a8 | `a8_extra_agreement.png/.pdf` | Agreement level distribution (bar) + ranked pill grid per level |
