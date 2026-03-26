Menu Recommender
This project is a simple menu recommendation system built using Python. It uses web-scraped restaurant menus from Leeuwarden and Groningen to help users find dishes based on their preferences.

Users can filter dishes by:
- Maximum price
- Dietary preference (vegetarian, vegan, meat, fish, spicy)
- Keyword (e.g. pasta, burger, salad)
- Menu type (lunch, dinner, dessert)
- City (Leeuwarden or Groningen)

The system then returns matching dishes along with their restaurant and location.

Features
- Web scraping of real restaurant menus --> scraper
- Data cleaning and standardisation --> processing
- Automatic tagging (vegetarian, vegan, etc.) --> processing
- Rule-based filtering system --> processing
- Interactive user interface using Streamlit --> recommender

Data
The dataset is created by scraping multiple restaurant websites. Each dish contains:
- Restaurant name
- City
- Dish name
- Menu type
- Category
- Price
- Description
- Tags

Example:
Dish: Mushroom risotto  
Price: €18.50  
Restaurant: De Dikke van Dale  
City: Leeuwarden  
Tags: vegetarian  

How to run the project
1. Clone the repository
git clone https://github.com/daninign/menu-recommender.git 
cd menu_recommender
2. Install dependencies
python -m pip install -r requirements.txt
3. Run the Streamlit app
python -m streamlit run main.py

Then open the link shown in the terminal (usually http://localhost:8501
).

How it works
The system follows these steps:
Scrape menu data from restaurant websites
Clean and standardise the data
Add tags based on keywords (e.g. vegetarian, spicy)
Apply filters based on user input
Return matching dishes sorted by price

Project structure
menu_recommender/
│ main.py
│ README.md
│ requirements.txt
│
├── data/
│   └── menus_cleaned.csv
│
├── scraper/
│   └── scrape_menus.py
│
├── processing/
│   └── clean_menu_data.py
│
└── recommender/
    └── recommended_dishes.py

Example usage
User input:
Vegetarian
Max price: €18
Keyword: pasta
Menu type: dinner

Output:
Truffle pasta – €17.50 (Baylings, Leeuwarden)
Pesto pasta – €14.50 (Roast, Leeuwarden)

Limitations
Not all restaurant websites provide structured or complete data
Dietary tags are generated using keyword matching and may not always be accurate
Some menus (e.g. PDF or dynamic content) could not be scraped
Categories are not fully standardised across all restaurants

Authors
Dani Noorlander (Leeuwarden scraping, data cleaning, UI)
Jill (Groningen scraping)