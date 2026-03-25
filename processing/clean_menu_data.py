import pandas as pd

from scraper.scrape_menus import scrape_all_menus

# if value is empty return none to avoid errors later
def clean_text(text):
    if pd.isna(text) or text is None:
        return None

    # make sure input is treated as string
    text = str(text)

    # replace weird characters and html spacing issues
    replacements = {
        "\xa0": " ",
        "Ã¨": "è",
        "Ã©": "é",
        "Ãª": "ê",
        "Ã«": "ë",
        "Ã¡": "á",
        "Ã ": "à",
        "Ã§": "ç",
        "Ã¶": "ö",
        "Ã¼": "ü",
        "Ã®": "î",
        "Ã¯": "ï",
        "Ã´": "ô",
        "Ã»": "û",
        "â": "–",
        "â": "—",
        "â": "’",
        "â": "‘",
        "â€œ": '"',
        "â€": '"',
        "Â ": "",
        "&nbsp;": " ",
    }

    # loop thru broken chars and replace them
    for wrong, right in replacements.items():
        text = text.replace(wrong, right)

    # clean up extra spaces
    text = " ".join(text.split()).strip()

    # return cleaned text or none if empty
    return text if text else None


# clean price values and turn them into floats
def clean_price(price):
    if pd.isna(price) or price is None:
        return None

    # make sure input is string and lowercase it
    price = str(price).strip().lower()

    # remove euro signs and other extra text
    replacements = {
        "€": "",
        ",": ".",
        "p.p.": "",
        "ps": "",
        "p.s.": "",
        "vanaf": "",
    }

    # replace unwanted text in price string
    for wrong, right in replacements.items():
        price = price.replace(wrong, right)

    # clean up extra spaces
    price = " ".join(price.split()).strip()

    import re
    # search for the first number in the text
    match = re.search(r"\d+(\.\d+)?", price)
    if not match:
        return None

    # try converting the found number to float
    try:
        return float(match.group())
    except ValueError:
        return None


# standardize menu type names so they all match
def standardize_menu_type(menu_type):
    if pd.isna(menu_type) or menu_type is None:
        return None

    # clean text and make lowercase for matching
    text = clean_text(menu_type).lower()

    # map common menu type names to one standard format
    mapping = {
        "lunch": "Lunch",
        "dinner": "Dinner",
        "dessert": "Dessert",
        "desserts": "Dessert",
    }

    # if not found in mapping just title case the cleaned text
    return mapping.get(text, clean_text(menu_type).title())


# standardize categories based on whether its lunch or dinner
def standardize_category(category, menu_type):
    if pd.isna(category) or category is None:
        return None

    # clean the values first
    category = clean_text(category)
    menu_type = standardize_menu_type(menu_type)

    # lunch categories and their standard names
    lunch_map = {
        "bowls": "Bowls",
        "pancakes": "Pancakes",
        "sandwiches": "Sandwiches",
        "salads": "Salads",
        "bakery": "Bakery",
        "kids food": "Kids Food",
        "soepen": "Soup",
        "soup": "Soup",
        "tosti's": "Toasties",
        "tostis": "Toasties",
        "koude broodjes": "Cold Sandwiches",
        "warme broodjes": "Hot Sandwiches",
        "eiergerechten": "Egg Dishes",
        "twaalfuurtjes": "Lunch Specials",
        "plates": "Plates",
        "broodjes": "Sandwiches",
        "wraps": "Wraps",
        "classics": "Classics",
        "salade": "Salads",
        "salades": "Salads",
        "maaltijdsalade": "Salads",
        "zuurdesem brood": "Sandwiches",
        "croissant bun": "Sandwiches",
        "roast eggs": "Egg Dishes",
        "burgers & buns": "Burgers",
        "burgers and buns": "Burgers",
        "lunchplank": "Lunch Specials",
    }

    # dinner categories and their standard names
    dinner_map = {
        "soepen": "Soup",
        "soup": "Soup",
        "salades": "Salads",
        "salade": "Salads",
        "voorgerechten": "Starters",
        "starters": "Starters",
        "starters to share": "Starters",
        "aperitivo": "Starters",
        "primi": "Starters",
        "bijgerechten": "Sides",
        "side dishes": "Sides",
        "hoofdgerechten": "Main",
        "main": "Main",
        "secondi": "Main",
        "pizza": "Pizza",
        "pasta": "Pasta",
        "dessert": "Dessert",
        "desserts": "Dessert",
        "dolci": "Dessert",
        "kindergerechten": "Kids",
        "kids food": "Kids",
        "kids drinks": "Kids",
        "vlees": "Main",
        "vis": "Main",
        "vega": "Main",
        "vegetarisch": "Main",
        "broiler": "Main",
        "bar bites en aperitieven": "Starters",
        "voor ieder wat wils - koude gerechten": "Starters",
        "voor ieder wat wils - warme gerechten": "Main",
        "voor ieder wat wils - desserts": "Dessert",
    }

    # lowercase category for easier matching
    key = category.lower()

    # use different category mapping depending on menu type
    if menu_type == "Lunch":
        return lunch_map.get(key, category.title())

    if menu_type == "Dinner":
        return dinner_map.get(key, category.title())

    if menu_type == "Dessert":
        return "Dessert"

    # if no menu type match just title case category
    return category.title()


# detect tags like vegan vegetarian meat fish or spicy
def detect_tags(dish, description, existing_tags=None):
    # combine dish and description into one lowercase text string
    text = f"{dish or ''} {description or ''}".lower()

    # use set so tags dont repeat
    tags = set()

    # keep any tags that already existed
    if existing_tags and not pd.isna(existing_tags):
        for tag in str(existing_tags).split(","):
            tag = tag.strip().lower()
            if tag:
                tags.add(tag)

    # keywords for vegan dishes
    vegan_keywords = {
        "vegan", "plant-based", "plantaardig", "veganistisch"
    }

    # keywords that suggest vegetarian dishes
    vegetarian_keywords = {
        "vegetarian", "vegetarisch", "mozzarella", "burrata", "brie",
        "goat cheese", "geitenkaas", "parmezaan", "parmesan", "gorgonzola",
        "cheddar", "kaas", "egg", "ei", "mascarpone", "yoghurt", "room",
        "crème fraîche", "ricotta", "feta", "halloumi", "burrata",
        "mozzarella", "fontina", "pecorino", "grana padano"
    }

    # keywords that suggest meat dishes
    meat_keywords = {
        "chicken", "kip", "beef", "rund", "runder", "carpaccio", "steak",
        "biefstuk", "burger", "ham", "serranoham", "prosciutto", "salami",
        "spek", "bacon", "pork", "varkens", "rib", "spareribs", "saté",
        "duck", "eend", "lamb", "lam", "pastrami", "kebab", "mortadella",
        "nduja", "worst", "sausage", "ossenhaas", "stoofpot", "rendang",
        "buikspek", "rib-eye", "ribeye", "varkenshaas", "lamshaas",
        "gehakt", "frikandel", "kroket", "bitterbal"
    }

    # keywords that suggest fish dishes
    fish_keywords = {
        "fish", "vis", "salmon", "zalm", "tuna", "tonijn", "shrimp", "gamba",
        "prawn", "cod", "kabeljauw", "sea bass", "zeebaars", "makreel",
        "mackerel", "herring", "haring", "oyster", "oester", "halibut",
        "heilbot", "sardine", "ansjovis", "anchovy", "scallop", "coquille",
        "sashimi", "tataki", "mussels", "mosselen", "garnalen", "garnaal",
        "schelvis", "zalmfilet", "tonijntartaar", "makreelsalade"
    }

    # keywords that suggest spicy dishes
    spicy_keywords = {
        "spicy", "pikant", "pittig", "chili", "chilli", "jalapeño",
        "jalapeno", "sriracha", "hot honey", "gochujang", "piccante",
        "nduja", "sambal", "rode peper", "peper", "kimchi", "wasabi"
    }

    # add tags if matching keywords are found
    if any(word in text for word in vegan_keywords):
        tags.add("vegan")

    if any(word in text for word in fish_keywords):
        tags.add("fish")

    if any(word in text for word in meat_keywords):
        tags.add("meat")

    if any(word in text for word in spicy_keywords):
        tags.add("spicy")

    # only call something vegetarian if it is not already vegan fish or meat
    if "vegan" not in tags and "fish" not in tags and "meat" not in tags:
        if any(word in text for word in vegetarian_keywords):
            tags.add("vegetarian")

    # return all tags as one string or none if empty
    return ", ".join(sorted(tags)) if tags else None


# clean the full scraped dataframe and standardize everything
def clean_menu_data(df):
    # make a copy so original df stays unchanged
    df = df.copy()

    # columns the final dataset should have
    expected_columns = [
        "restaurant",
        "city",
        "menu_type",
        "category",
        "dish",
        "price",
        "description",
        "tags",
    ]

    # add missing columns if they dont exist yet
    for col in expected_columns:
        if col not in df.columns:
            df[col] = None

    # clean all text-based columns
    for col in ["restaurant", "city", "menu_type", "category", "dish", "description", "tags"]:
        df[col] = df[col].apply(clean_text)

    # clean price column
    df["price"] = df["price"].apply(clean_price)

    # standardize menu type values
    df["menu_type"] = df["menu_type"].apply(standardize_menu_type)

    # standardize categories based on menu type
    df["category"] = df.apply(
        lambda row: standardize_category(row["category"], row["menu_type"]),
        axis=1
    )

    # automatically detect tags from dish and description
    df["tags"] = df.apply(
        lambda row: detect_tags(row["dish"], row["description"], row["tags"]),
        axis=1
    )

    # remove rows without dish names
    df = df[df["dish"].notna()].copy()

    # remove duplicates
    df = df.drop_duplicates(
        subset=["restaurant", "city", "menu_type", "category", "dish", "price"]
    ).reset_index(drop=True)

    return df


# run scraping and cleaning pipeline
def main():
    # scrape raw menu data
    raw_df = scrape_all_menus()
    # clean the scraped data
    clean_df = clean_menu_data(raw_df)

    # print some info to check results
    print("Raw rows:", len(raw_df))
    print("Clean rows:", len(clean_df))
    print(clean_df.head(20))

    # save cleaned dataset to csv
    clean_df.to_csv("data/menus_cleaned.csv", index=False)
    print("\nSaved cleaned dataset to: data/menus_cleaned.csv")


# only run main if this file is executed directly
if __name__ == "__main__":
    main()