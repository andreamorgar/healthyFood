# Aplicación interactiva sobre nutrición saludable
Este repositorio contendrá el código utilizado para la aplicación interactiva creada para el Trabajo Final de Grado ***"Extracción y representación de conocimiento sobre nutrición saludable con Inteligencia Artificial"**

# Descripción del proyecto

Este TFG trata sobre la integración de diversas tecnologías, en concreto inteligencia artificial, bases de datos NoSQL y bases de datos basadas en grafos, en el ámbito de la nutrición y salud. Para demostrar las posibilidades que puede aportar esta integración, se ha decidido crear una aplicación interactiva, a la cual se le pueden entregar recetas escritas con lenguaje natural, y mediante un modelo de lenguaje se obtienen los ingredientes y datos más relevantes de la receta, los cuales se utilizarán para realizar las consultas al grafo de datos.

Esta aplicación está pensada tanto para usuarios corrientes sin experiencia en el ámbito de la nutrición como para investigadores y expertos, gracias a que la información que aporta está redactada de manera sencilla y clara, con la opción de acceder a las fuentes de las que se obtuvo para mayor detalle.

La información que aporta trata sobre la composición de los alimentos, el efecto de los alimentos en diversas patologías, el efecto de los alimentos en el envejecimiento humano y cómo el método de cocinado puede afectar tanto al alimento como a la salud humana.

Esta información se mostrará de manera clara y concisa mediante etiquetas, pero se tiene la opción de comprobarla de manera más detallada en los desplegables de cada alimento, e incluso de manera más detallada entrando al enlace de la fuente de las que se obtuvieron los datos.

# Requisitos
Para el correcto funcionamiento de la aplicación, es necesario instalar las siguientes dependencias:

* streamlit
* pandas
* sentence-transformers
* scikit-learn
* numpy
* neo4j
* langchain
* langchain-ollama

Estas se pueden instalar ejecutando
```bash
pip install -r requirements.txt
```

# Uso
La aplicación necesita una base de datos de Neo4j a la que conectarse para realizar las consultas, y un modelo de lenguaje de Ollama para poder manejar el lenguaje natural.

Neo4j se puede conseguir e instalar siguiendo la guía que aparece en https://neo4j.com/ .

Ollama se puede conseguir e instalar siguiendo la guía que aparece en https://ollama.com/

Una vez tengamos la base de datos de grafos y el modelo de lenguaje iniciados, se puede ejecutar el código utilizando


```bash
cd app
streamlit run .\streamlit_app.py
```

# Estructura del repositorio


```
Healthy-Food-App
    ├── app/
    │     ├── .streamlit/
    │     │           └── config.toml       # Archivo de configuración para Streamlit, contiene tema y diseño de la aplicación.
    │     │
    │     ├── facts.txt                     # Lista de datos curiosos que se muestran aleatoriamente mientras se realizan consultas.
    │     ├── requirements.txt              # Lista de requisitos para el funcionamiento de la aplicación
    │     └── streamlit_app.py              # Código principal de la aplicación de Streamlit
    │
    ├── .gitignore                          # Exclusiones del frontend
    ├── README.md                           # Instrucciones del frontend
    └── LICENSE                             # Licencia de Creative Commons
```

# Licencia

Este proyecto ha sido desarrollado con fines académicos, en el marco de un Trabajo Fin de Grado.

Se distribuye bajo la licencia  
**Creative Commons Atribución – No Comercial – Compartir Igual 4.0 Internacional (CC BY-NC-SA 4.0)**.  
![Licencia CC BY-NC-SA](https://mirrors.creativecommons.org/presskit/buttons/88x31/png/by-nc-sa.png)

Esto significa que puede ser compartido y adaptado siempre que se cite correctamente al autor, no se utilice con fines comerciales y cualquier obra derivada se publique bajo la misma licencia.

🔗 Más información sobre los términos de esta licencia:  
[https://creativecommons.org/licenses/by-nc-sa/4.0/deed.es](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.es)

Para consultas o posibles colaboraciones, puedes contactar con el autor.

Autor: Amadeo Martínez Sánchez 
Universidad de Granada – Grado en Ingeniería Informática  
Correo: amadeoms@correo.ugr.es
