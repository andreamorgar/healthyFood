# Interactive Application on Healthy Nutrition
This repository contains the code used for the manuscript **FoodMedKG: Integrating Biomedical Knowledgeand Culinary Data for Health-Aware Decision Support**

# Project Description

This Final Degree Project focuses on the integration of various technologies — specifically artificial intelligence, NoSQL databases, and graph databases — in the field of nutrition and health. To demonstrate the possibilities this integration can offer, an interactive application has been developed. Users can submit recipes written in natural language, and a language model extracts the most relevant ingredients and data from the recipe, which are then used to query the data graph.

This application is designed for both everyday users with no background in nutrition and for researchers and experts, as the information it provides is written in a simple and clear manner, with the option to access the original sources for further detail.

The information covers food composition, the effect of foods on various pathologies, the effect of foods on human aging, and how cooking methods can affect both the food and human health.

This information is displayed clearly and concisely through labels, with the option to explore it in more detail via expandable sections for each food item, and even further by following the link to the original data source.

# Requirements
To run the application correctly, the following dependencies must be installed:

* streamlit
* pandas
* sentence-transformers
* scikit-learn
* numpy
* neo4j
* langchain
* langchain-ollama

These can be installed by running:
```bash
pip install -r requirements.txt
```

# Usage
The application requires a Neo4j database to connect to for queries, and an Ollama language model to handle natural language input.

Neo4j can be obtained and installed by following the guide at https://neo4j.com/ .

Ollama can be obtained and installed by following the guide at https://ollama.com/

Once the graph database and the language model are running, the application can be launched with:


```bash
cd app
streamlit run .\streamlit_app.py
```

# Repository Structure


```
Healthy-Food-App
    ├── app/
    │     ├── .streamlit/
    │     │           └── config.toml       # Streamlit configuration file, contains the application theme and layout.
    │     │
    │     ├── facts.txt                     # List of fun facts displayed randomly while queries are being processed.
    │     ├── requirements.txt              # List of dependencies required to run the application
    │     └── streamlit_app.py              # Main Streamlit application code
    │
    ├── data/
    │     ├── 1 FooDB_grupo_id.py           # Assigns group IDs to FooDB food entries
    │     ├── 2 Food_Simplificada.py        # Simplified food dataset generation
    │     ├── 3 FooDB_Pivotado.py           # Pivots FooDB data by nutrient
    │     ├── 4 FooDB_Final.py              # Final FooDB dataset preparation
    │     ├── 5 ES_Rango.py                 # Computes nutrient ranges for Elasticsearch
    │     ├── 6 ES_Completa.py              # Full Elasticsearch dataset builder
    │     ├── 7 ES_Final.py                 # Final Elasticsearch dataset preparation
    │     └── data_preparation.txt          # Notes on data preparation steps
    │
    ├── .gitignore                          # Git exclusions
    ├── README.md                           # Project documentation
    └── LICENSE                             # Creative Commons License
```

# License

This project was developed for academic purposes, as part of a Final Degree Project.

It is distributed under the  
**Creative Commons Attribution – NonCommercial – ShareAlike 4.0 International (CC BY-NC-SA 4.0)** license.  
![CC BY-NC-SA License](https://mirrors.creativecommons.org/presskit/buttons/88x31/png/by-nc-sa.png)

This means it may be shared and adapted as long as the author is properly credited, it is not used for commercial purposes, and any derivative works are published under the same license.

🔗 More information about the terms of this license:  
[https://creativecommons.org/licenses/by-nc-sa/4.0/](https://creativecommons.org/licenses/by-nc-sa/4.0/)

For inquiries or potential collaborations, feel free to contact the authors
