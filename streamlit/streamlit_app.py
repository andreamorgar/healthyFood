import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import time
from neo4j import GraphDatabase
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
import json
import time
import re
import random

#------ 1 CARGAR E INICIALIZAR OLLAMA Y NEO4J ------

# LLM de Ollama
llm = OllamaLLM(model="llama3")

# Datos de la base de datos de  Neo4j
server = "neo4j://127.0.0.1:7687"
username = "neo4j"

# Inicializa el cliente de Neo4j
try:
    driver = GraphDatabase.driver(server, auth=(username, password))
except:
    print("Unable to reach Database")

# Función para usar el query de Neo4j
def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return result.data()

# Obtenemos la lista de ingredientes de la base de datos utilizando query.
try:
    list = run_query("MATCH (f:Composition) RETURN f.food_name AS food_name, f.id AS id, f.FooDB_ID AS food_id")
except:
    print("Unable to reach Database")

# Definimos el prompt para obtener los ingredientes según la receta
prompt_ingredients = PromptTemplate(
    input_variables=["topic"],
    template = """
Extract the preparation and the list of all required ingredients from the following recipe, serving size one person:

{topic}

Return the preparation method (as one word, e.g., 'raw', 'boiled', 'fried', 'baked') , ingredients, amount and weight of the ingredients, as a clean, JSON with no explanations, no preamble, and no extra text. Make sure all objects have data. Example:

{{
  "preparation": "fried",
  "ingredients": [
    {{
      "name": "chicken breast",
      "amount": "300 grams",
      "weight": "300 grams"
    }},
    {{
      "name": "granulated sugar",
      "amount": "1 cup",
      "weight": "60 grams"
    }},
    {{
      "name": "flour",
      "amount": "1/2 cup",
      "weight": "60 grams"
    }},
    {{
      "name": "eggs",
      "amount": "2 large eggs",
      "weight": "100 grams"
    }}
  ]
}}

Do not include anything else.
""")

#Convertimos la lista a DataFrame para mejor manejo
df = pd.DataFrame(list)
df['food_name'] = df['food_name'].fillna('').astype(str)



#------ 2 OBTENER INGREDIENTES MÁS NATURALES DE LA LISTA ------

# Función para obtener los alimentos que se indiquen "naturales" para darles prioridad
def is_raw_like(text):
    text = text.lower()
    return any(x in text for x in ["raw", "fresh", "whole", "unprocessed"])

# Función para obtener los alimentos que sean menos "naturales" para eliminarles prioridad
def is_processed_like(text):
    text = text.lower()
    return any(x in text for x in [
        "cooked", "boiled", "fried", "roasted", "processed", "steamed",
        "grilled", "dehydrated", "dried", "baked", "microwaved", "powdered", "smoked"
    ])

#Añadimos la información al dataframe
df['is_raw'] = df['food_name'].apply(is_raw_like)
df['is_processed'] = df['food_name'].apply(is_processed_like)

#------ 3 CODIFICAR DATAFRAME UTILIZANDO EMBEDDINGS ------
model = SentenceTransformer('all-MiniLM-L6-v2')
db_embeddings = model.encode(df['food_name'].tolist(), convert_to_tensor=True)



#------ 4 REALIZAR BÚSQUEDA INTELIGENTE ------

# Función para buscar los ingredientes más similares a los añadidos.
def find_best_matches(input_ingredients, df, db_embeddings, model, score_threshold=0.5):
    results = []

    for ingredient in input_ingredients:
        #Codificamos el ingrediente como embedding
        input_embedding = model.encode(ingredient, convert_to_tensor=True)

        #Obtenemos el score de similitud entre el ingrediente y la lista
        cosine_scores = cosine_similarity(
            input_embedding.cpu().numpy().reshape(1, -1),
            db_embeddings.cpu().numpy()
        )[0]

        df['cosine_score'] = cosine_scores
        df['name_match'] = df['food_name'].str.lower().str.contains(ingredient.lower())

        # Preferimos que el ingrediente no sea procesado.
        candidates = df[
            (df['name_match']) &
            (~df['is_processed']) &
            (df['cosine_score'] > score_threshold)
        ].copy()

        # Si en la lista de candidatos hay algún "crudo", lo indicamos como preferido
        if any(candidates['is_raw']):
            candidates = candidates[candidates['is_raw']]

        # Buscamos el más similar.
        if not candidates.empty:
            best_match = candidates.sort_values(by='cosine_score', ascending=False).iloc[0]
        else:
            fallback = df[~df['is_processed']]
            if fallback.empty:
                fallback = df
            best_match = fallback.sort_values(by='cosine_score', ascending=False).iloc[0]

        #Creamos respuesta devolviendo nombre, nombre resultado, id, FooDB_ID y score de similitud
        results.append({
            "input": ingredient,
            "food_name": best_match["food_name"],
            "id": int(best_match["id"]),
            "food_id": int(best_match["food_id"]),
            "score": round(float(best_match["cosine_score"]), 4)
        })

    return results

#------ 5 FUNCIONES AUXILIARES PARA LA APLICACIÓN ------

# Para obtener los compuestos y nutrientes de un alimento con FooDB_ID "id"
def get_composition(id):
    constituents = run_query(f'MATCH (c:Composition {{id: {id}}}) RETURN c.constituents')
    return json.loads(constituents[0]["c.constituents"])

# Para obtener las enfermedades relacionadas a un alimento con FooDB_ID "id"
def get_disease(id):
    disease = run_query(f'MATCH (f:Food {{FooDB_id:{id}}})-[r:Affects]->(d:Disease) RETURN d.Disease AS Disease, r.`Suitable for Disease` AS Suitable')
    return disease

# Para obtener la información sobre la preparación del alimento
def get_preparation(method):
    preparation = run_query(f'MATCH (m:Cooking_Methods {{Cooking_Method: "{method}"}}) RETURN m')
    return preparation[0]['m'] if preparation else None

# Actualizar la herramienta de búsqueda
def update_search():
    st.session_state.search_query = st.session_state.search_input

# Para extraer y ordenar los números de la tabla de nutrientes
def extract_numeric(val):
    if isinstance(val, (int, float)):
        return val
    match = re.search(r"[-+]?\d*\.?\d+", str(val))
    return float(match.group()) if match else 0

# Inicializar datos curiosos al realizar la busqueda
def load_facts(file_path="facts.txt"):
    with open(file_path, "r", encoding="utf-8") as file:
        facts = [line.strip() for line in file if line.strip()]
    return facts

# Para mostrar impacto en la salud de un alimento
def show_health_impact(food_id):
    diseases = get_disease(food_id)
    if diseases:
        st.markdown("#### 🧬 Health impact")
        for disease in diseases:
            if disease["Suitable"]:
                st.success(f"✅ Positive impact on **{disease['Disease']}**")
            else:
                st.error(f"⚠️ Negative impact on **{disease['Disease']}**")
    else:
        st.info("No known health impacts.")

# Para mostrar nutrientes ordenados de un alimento.
def show_nutrient_data(id):
    constituents = get_composition(id)

    # Orden descendente
    sorted_constituents = sorted(
        constituents.items(),
        key=lambda x: extract_numeric(x[1]),
        reverse=True
    )

    st.markdown("#### 🍽️ Nutrient Data")

    if not sorted_constituents:
        st.info("No nutrient data available.")
        return

    #Se remarcan los 3 nutrientes más importantes en grande
    st.markdown("##### Top 3 nutrients")
    top3 = sorted_constituents[:3]
    cols = st.columns(len(top3))
    for col, (nutrient, value) in zip(cols, top3):
        with col:
            st.metric(label=nutrient, value=value)

    #El restro se muestran en formato tabla
    if len(sorted_constituents) > 3:
        st.markdown("##### Full nutrient list")
        rest = sorted_constituents[3:]
        df_nutrients = pd.DataFrame(rest, columns=["Nutrient", "Value"])
        st.dataframe(df_nutrients, use_container_width=True, hide_index=True)


#------ 6 INICIALIZAR APLICACIÓN STREAMLIT ------
#Inicializamos estado de la app
st.set_page_config(
    page_title="Trabajo Final de Grado",
    layout="wide"
)

#Inicializamos query y búsqueda
if "search_mode" not in st.session_state:
    st.session_state.search_mode = "recipes"
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

#Cargamos los datos curiosos del archivo para tenerlos en caché
facts = load_facts()


#------ 7 APLICACIÓN ------

#Encabezado
st.markdown(f"""
    <h1 style='text-align: center; color: #D9572A;'>
        Trabajo Final de Grado
    </h1>
    <h3 style='text-align: center; color: #9AA3A8; font-weight: normal;'>
        Find what your meal is composed of
    </h3>
""", unsafe_allow_html=True)

#3 partes: barra lateral, separador y parte principal
sidebar, divider, main = st.columns([1, 0.05, 2])

#--- Separador ---
with divider:
    st.markdown(
        "<div style='border-left: 1px solid #ccc; height: 100%;'></div>",
        unsafe_allow_html=True
    )

#--- Barra lateral ---
with sidebar:
    st.markdown("### 🔍 Search options")
    
    if st.button("🍅 Search Ingredients"):
        st.session_state.search_mode = "ingredients"
    if st.button("🍲 Search Recipes"):
        st.session_state.search_mode = "recipes"

    st.write(f"Currently searching: **{st.session_state.search_mode.capitalize()}**")

    st.text_input(
        "Enter your search:",
        key="search_input",
        on_change=update_search,
        placeholder="Example: spaghetti with meatballs",
        width=300
    )

#--- Centro ---
with main:
    query = st.session_state.search_query.lower()

    # Si se ha buscado algo:
    if query:
        # Generamos un spinner mostrando un dato curioso aleatorio
        with st.spinner(f"🔎 {random.choice(facts)}"):
            time.sleep(1)

            # - Búsqueda de recetas -
            if st.session_state.search_mode == "recipes":

                # Enviamos el nombre de la receta a la LLM de Ollama y obtenemos un JSON
                chain = prompt_ingredients | llm
                respuesta = chain.invoke({"topic": query})
                data = json.loads(respuesta)

                #Mostramos la preparación de la receta, indicando la información adicional si posee alguna
                st.markdown("## 🍲 Recipe")

                preparation = get_preparation(data["preparation"])
                if preparation:
                    if preparation["Health_Impact"] == "bad":
                        st.error(
                            f"**Preparation method:** {data['preparation']}  \n"
                            f"❌{preparation['Sentence']}"
                        )
                    elif preparation["Health_Impact"] == "moderate":
                        st.warning(
                            f"**Preparation method:** {data['preparation']}  \n"
                            f"⚠️ {preparation['Sentence']}"
                        )
                    elif preparation["Health_Impact"] == "good":
                        st.success(
                            f"**Preparation method:** {data['preparation']}  \n"
                            f"✅ {preparation['Sentence']}"
                        )
                else:
                    st.markdown(f"**Preparation method:** {data['preparation']}")

                # Mostrar lista de ingredientes + cantidad
                st.markdown("### Ingredients")
                input_ingredients = [i["name"] for i in data["ingredients"]]
                amounts = [i["amount"] for i in data["ingredients"]]

                #Buscar ingredientes en la base de datos
                results = find_best_matches(input_ingredients, df, db_embeddings, model)
                ids = [r["id"] for r in results]

                #Crear un desplegable para cada ingrediente, mostrando enfermedades asociadas y datos nutricionales
                for i, (ingredient, amount, id) in enumerate(zip(input_ingredients, amounts, ids)):
                    st.markdown(f"- **{ingredient}**: {amount}")
                    with st.expander(f"Most similar ingredient found: {results[i]['food_name']}"):
                        show_health_impact(results[i]["food_id"])
                        show_nutrient_data(id)

            # - Búsqueda de ingredientes - 
            elif st.session_state.search_mode == "ingredients":

                # Buscar ingrediente en la base de datos
                results = find_best_matches([query], df, db_embeddings, model)
                food_name = results[0]["food_name"]
                st.success(f"Found most similar ingredient: `{food_name}`")
                id = results[0]["id"]

                # Mostrar enfermedades asociadas y datos nutricionales del ingrediente
                show_health_impact(results[0]["food_id"])
                show_nutrient_data(id)