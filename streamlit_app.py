# Importamos los paquetes que utilizaremos
import streamlit as st
from streamlit.components.v1 import html as ht
import leafmap.foliumap as leafmap
import folium
import pandas as pd
import numpy as np
import geopandas as gpd
import altair as alt
import matplotlib.pyplot as plt
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Nobel Awards Dashboard",
    layout="wide",
    initial_sidebar_state="expanded")

# Agregamos un título con color personalizado usando HTML y CSS
st.markdown(
    """
    <style>
    .custom-title {
        font-size: 50px;  /* Tamaño de fuente del título */
        color: #D65A31;   /* Color del título (naranja oscuro) */
        text-align: center;  /* Centrar el texto */
    }
    </style>
    <h1 class="custom-title">Nobel Awards Dashboard</h1>
    """,
    unsafe_allow_html=True
)

# Cargamos los datos de los laureados
laureates = pd.read_csv('nobel_laureates_clean.csv')

# Descargamos el archivo GeoJSON del mundo
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
world_df = pd.DataFrame(world)

# Guardamos los países del GeoJSON
json_countries = world_df['name'].unique()

# Creamos el dataframe con el número de premios por país
prizes_per_country = laureates.groupby(by=['ISO-ALPHA-3','latitude','longitude','officialCountryName']).count().reset_index()

# Creamos el mapa
m = leafmap.Map()

# Agregamos el mapa
folium.Choropleth(
    geo_data=world,
    name='choropleth',
    data=prizes_per_country,
    columns=['officialCountryName', 'id'],
    key_on='feature.properties.name',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    nan_fill_color='white',  # Color para países sin datos
    nan_fill_opacity=0.7,
    legend_name='Prizes per country'
).add_to(m)

# Agregamos los marcadores al mapa
for index, row in laureates.iterrows():
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"Country:{row['officialCountryName']} Prizes: {row['id']}",
        icon=folium.Icon(icon = 'info-sign', color='grey', icon_size=(15,15))
    ).add_to(m)

# Representamos el mapa
mapa_html = m._repr_html_()

# Creamos el índice de selección en Streamlit. El mapa aparecerá al cargar la app por defecto.
selected_tab = st.sidebar.radio("Select an option", ["Nobel Awards World Map", "Laureates by Year", "Awards by Category", "Laureates by Gender"])

# Creamos las opciones
# Opción 1: Nobel Awards World Map
if selected_tab == "Nobel Awards World Map":
    st.subheader("Nobel Awards World Map")  # Título más pequeño, alineado a la izquierda
    # Cargamos el mapa en Streamlit
    ht(mapa_html, height=600, width=800, scrolling=True)

# Opción 2: Laureates by Year
laureates_year = laureates[['firstname','surname','bornCountry','gender','prize_years','prize_categories','prize_motivation']]

# Dividimos en columnas los años y categorías cuando los laureados reciben más de 1 premio
laureates_year = laureates[['firstname','surname','bornCountry','gender','prize_years','prize_categories','prize_motivation']]
years_split = laureates_year['prize_years'].str.split(',', expand=True)
laureates_year['prize_years_1'] = years_split[0]
laureates_year['prize_years_2'] = years_split[1]
cat_split = laureates_year['prize_categories'].str.split(',', expand=True)
laureates_year['prize_cat_1'] = cat_split[0]
laureates_year['prize_cat_2'] = cat_split[1]
laureates_year = laureates_year.drop(columns=['prize_years','prize_categories'])

# Convertimos columnas en filas
laureates_year_melted_1 = laureates_year.melt(
    id_vars=['firstname', 'surname', 'bornCountry','gender','prize_motivation','prize_cat_1','prize_cat_2'], 
    value_vars=['prize_years_1','prize_years_2'], 
    value_name='prize_year')

laureates_year_melted_2 = laureates_year_melted_1.melt(
    id_vars=['firstname', 'surname', 'bornCountry','gender','prize_motivation','prize_year'], 
    value_vars=['prize_cat_1','prize_cat_2'], 
    value_name='prize_category')

# Eliminamos la columna 'variable' 
laureates_year_melted = laureates_year_melted_2.drop(columns='variable')

# Eliminamos filas con valores nulos
laureates_year_final = laureates_year_melted.dropna(subset=['prize_year','prize_category'])
laureates_year_final['prize_year'] = laureates_year_final['prize_year'].astype(int)
if selected_tab == "Laureates by Year":
    st.subheader("Laureates by Year")  # Título más pequeño, alineado a la izquierda
    # Creamos un slider para seleccionar el año
    selected_year = st.slider("Select a Year", int(laureates_year_final['prize_year'].min())
                              , int(laureates_year_final['prize_year'].max()))
    # Filtramos el DataFrame por el año seleccionado
    filtered_df = laureates_year_final[laureates_year_final['prize_year'] == selected_year]
    filtered_df.rename(columns={'firstname':'NAME','surname':'SURNAME','bornCountry': 'COUNTRY','gender':'GENDER','prize_category':'CATEGORY'}, inplace=True)

    # Mostramos los laureados en la tabla
    st.write(f"Laureates in {filtered_df['prize_year'].iloc[0]}:")
    st.table(filtered_df[['NAME', 'SURNAME', 'COUNTRY', 'GENDER','CATEGORY']].reset_index(drop=True))
    
# Opción 3: Laureates by Genre
laureates_genre = laureates_year_final[['firstname','gender','prize_year']]
laureates_genre = laureates_genre.groupby(['prize_year','gender']).count().reset_index()
laureates_genre.rename(columns={'firstname': 'num_laureates'}, inplace=True)
#print(laureates_genre)

# Opción 3: Laureates by Gender
if selected_tab == "Laureates by Gender":
    st.subheader("Awards by Gender")
    # Creamos el gráfico de barras apiladas
    fig = px.bar(
        laureates_genre, 
        x='prize_year', 
        y='num_laureates', 
        color='gender', 
        color_discrete_map={'Female': '#D65A31', 'Male': '#000080'},
        labels={'num_laureates':'Number of Laureates', 'prize_year':'Year', 'gender':'Gender'},
        title="Number of Laureates by Gender and Year",
        hover_data={'num_laureates': True, 'gender': False}  # Mostrar solo el número de laureados en el hover
    )

    # Ajustamos el diseño para una mejor visualización
    fig.update_layout(
        barmode='stack',
        xaxis_title='Year',
        yaxis_title='Number of Laureates',
        legend_title='Gender',
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(255,255,255,1)'  
    )

    # Mostramos el gráfico en Streamlit
    st.markdown(
        """
        <style>
        .centered-chart {
            display: flex;
            justify-content: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Centramos el gráfico usando un contenedor HTML
    st.markdown('<div class="centered-chart">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    #st.plotly_chart(fig)
    
# Opción 4: Awards by Category
laureates_cat = laureates_year_final[['firstname','surname','bornCountry','prize_motivation','prize_year','prize_category']]
laureates_cat.rename(columns={'bornCountry':'country','prize_motivation':'prize motivation'}, inplace=True)

if selected_tab == "Awards by Category":
    st.subheader("Awards by Category")
    # Creamos selección de categoría
    category_options = laureates_cat['prize_category'].unique()
    selected_category = st.selectbox("Select a Category", category_options)

    # Creamos selección de rango de años
    min_year = int(laureates_cat['prize_year'].min())
    max_year = int(laureates_cat['prize_year'].max())

    start_year, end_year = st.slider(
        "Select a Year Range", min_year, max_year, (min_year, min_year + 1))

    # Validación de que el segundo año sea al menos 1 año más que el primero
    if end_year <= start_year:
        st.error("The end year must be at least one year greater than the start year.")
    else:
        # Filtramos el DataFrame por la categoría seleccionada y el rango de años
        filtered_df = laureates_cat[
            (laureates_cat['prize_category'] == selected_category) &
            (laureates_cat['prize_year'] >= start_year) &
            (laureates_cat['prize_year'] <= end_year)
        ]
        
        grouped_df = filtered_df.groupby(['prize_category', 'prize_year']).apply(
            lambda x: pd.DataFrame({
                'YEAR': x['prize_year'],
                'NAME': x['firstname'],
                'SURNAME': x['surname'],
                'COUNTRY': x['country'],
                'MOTIVATION': x['prize motivation']
            })
        ).reset_index(drop=True)

        # Mostramos los datos filtrados
        if grouped_df.empty:
            st.write("No laureates found for the selected category and year range.")
        else:
            st.write(f"Laureates in {selected_category} from {start_year} to {end_year}:")
            st.table(grouped_df)
            
            