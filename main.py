import pandas as pd
import streamlit as st

# set up the streamlit page layout and title
st.set_page_config(page_title="Menu Recommender", layout="wide")
st.title("Menu Recommender")
st.write("Find dishes based on your preferences.")

# try importing the recommender function, stop app if it fails
try:
    from recommender.recommended_dishes import recommend_dishes
except Exception as e:
    st.error(f"Import error: {e}")
    st.stop()

# cache data so it does not reload every time the app refreshes
@st.cache_data
def load_data():
    return pd.read_csv("data/menus_cleaned.csv")

# try loading dataset, stop app if it fails
try:
    df = load_data()
    st.success("Dataset loaded successfully.")
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

# create 5 columns for user inputs
col1, col2, col3, col4, col5 = st.columns(5)

# input for maximum price filter
with col1:
    max_price = st.number_input("Maximum price", min_value=0.0, value=20.0, step=0.5)

# dropdown for dietary preference
with col2:
    dietary = st.selectbox(
        "Dietary preference",
        ["", "vegetarian", "vegan", "meat", "fish", "spicy"]
    )

# dropdown for menu type
with col3:
    menu_type = st.selectbox(
        "Menu type",
        ["", "Lunch", "Dinner", "Dessert"]
    )

# dropdown for city selection
with col4:
    city = st.selectbox(
        "City",
        ["", "Leeuwarden", "Groningen"]
    )

# text input for keyword search
with col5:
    keyword = st.text_input("Keyword", placeholder="e.g. pasta, burger")
    

# when user clicks the button run the recommender
if st.button("Get recommendations"):
    try:
        # call recommender with selected filters
        results = recommend_dishes(
            df,
            city=city if city else None,
            max_price=max_price if max_price > 0 else None,
            keyword=keyword if keyword else None,
            dietary=dietary if dietary else None,
            menu_type=menu_type if menu_type else None
        )

        # show message if no results found
        if results.empty:
            st.warning("No matching dishes found.")
        else:
            # show number of results and display dataframe
            st.success(f"Found {len(results)} matching dishes.")
            st.dataframe(results, use_container_width=True)
    except Exception as e:
        # show error if something goes wrong
        st.error(f"Recommendation error: {e}")