# imports
import requests
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
import pandas as pd
import re
import warnings


# =========================
# HELPER FUNCTIONS
# =========================

# if the input is empty return none to avoid errors
def clean_text(text):
    if not text:
        return None
    
    # cleaning whitespace
    text = " ".join(text.replace("\xa0", " ").split())
    # replace strange characters
    replacements = {
        "Ã¨": "è", "Ã©": "é", "Ãª": "ê", "Ã«": "ë",
        "Ã¡": "á", "Ã ": "à", "Ã§": "ç",
        "Ã¶": "ö", "Ã¼": "ü",
        "Ã®": "î", "Ã¯": "ï",
        "Ã´": "ô", "Ã»": "û",
        "â": "–", "â": "—", "â": "’",
        "Â ": "", "&nbsp;": " ",
    }
    # loop thru every broken char and replace it
    for wrong, right in replacements.items():
        text = text.replace(wrong, right)
    # remove spaces at the start and end
    return text.strip()

# make sure all prices have the same format 
def clean_price_whole_decimal(price_whole, price_decimal):
    whole = clean_text(price_whole) if price_whole else ""
    decimal = clean_text(price_decimal) if price_decimal else ""
    price = f"{whole}.{decimal}" if decimal else whole
    try:
        return float(price)
    except:
        return None

# =========================
# PIZZA BEPPE
# =========================

# set the url and browser header
def scrape_pizza_beppe():
    url = "https://www.pizzabeppe.nl/menu"
    headers = {"User-Agent": "Mozilla/5.0"}
    # download page and parse html
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    # store the results and keep track of which sections being used
    dishes = []
    current_category = None
    # standardize category names
    category_map = {
        "Pizza": "Pizza",
        "Starters to share": "Starters",
        "Dolci": "Desserts"
    }
    # grabs all h2 headings and div.menu_row elements in menu section
    elements = soup.select("section.c-section.is--menu h2, section.c-section.is--menu div.menu_row")
    # loop thru every selected html element one by one
    for el in elements:
        # get text, clean, map, store
        if el.name == "h2":
            heading = clean_text(el.get_text(" ", strip=True))
            current_category = category_map.get(heading)
            continue
        # only continue if category is already known
        if "menu_row" in el.get("class", []):
            if not current_category:
                continue
            # find all dish blocks
            items = el.select("div.menu_item")
            # extract dish information
            for item in items:
                title_tag = item.select_one("h3.c-h3-small")
                desc_tag = item.select_one("p.menu_item-ingredients")
                price_whole_tag = item.select_one("div.c-menu-price-txt")
                price_decimal_tag = item.select_one("div.is--price-small")
                # skip items without title or price
                if not title_tag or not price_whole_tag:
                    continue
                # extract and clean dish name and description
                dish = clean_text(title_tag.get_text(" ", strip=True))
                description = clean_text(desc_tag.get_text(" ", strip=True)) if desc_tag else None
                # combine price
                price = clean_price_whole_decimal(
                    price_whole_tag.get_text(" ", strip=True) if price_whole_tag else None,
                    price_decimal_tag.get_text(" ", strip=True) if price_decimal_tag else None
                )
                # empty list for tags
                tag_list = []
                # get icon data for tags
                icon_urls = [
                    img.get("src", "").lower()
                    for img in item.select("img.c-icon, img.c-tip")
                ]
                # check the image filenames to get tags
                if any("vegetarisch" in src for src in icon_urls):
                    tag_list.append("vegetarian")
                if any("vegan" in src for src in icon_urls):
                    tag_list.append("vegan")
                if any("tip" in src for src in icon_urls):
                    tag_list.append("tip")
                # convert list into one string or none
                tags = ", ".join(tag_list) if tag_list else None
                # store result
                dishes.append({
                    "restaurant": "Pizza Beppe",
                    "city": "Leeuwarden",
                    "menu_type": "Dinner",
                    "category": current_category,
                    "dish": dish,
                    "price": price,
                    "description": description,
                    "tags": tags
                })
# turn list into df and emove duplicates
    df = pd.DataFrame(dishes).drop_duplicates(
        subset=["restaurant", "city", "menu_type", "category", "dish", "price"]
    )
    # return cleaned results as a list of dictionaries
    return df.to_dict(orient="records")

# =========================
# BROODHUYS
# =========================

# scrape lunch dishes from broodhuys website
def scrape_broodhuys():
    url = "https://www.hetbroodhuys.nl/nl/"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # store results
    dishes = []

    # get all tab sections on the page
    panes = soup.select("div.tab-pane")

    for pane in panes:
        # find the category name
        category_tag = pane.find("h3")
        if not category_tag:
            continue

        category = category_tag.get_text(" ", strip=True)

        # skip drinks because we only want food items
        if category.lower() == "drinken":
            continue

        # loop through all paragraph blocks in the section
        for p in pane.find_all("p"):
            # find the price part
            price_tags = p.select("span.tab")

            # only keep lines with exactly one price
            if len(price_tags) != 1:
                continue

            price = price_tags[0].get_text(" ", strip=True)
            full_text = p.get_text(" ", strip=True)

            # remove the price from the full text to get the dish name
            dish_text = full_text.replace(price, "").strip()

            # skip empty dish names
            if not dish_text:
                continue

            # skip helper text that is not an actual dish
            if dish_text.lower().startswith(("geserveerd op", "keuze uit", "met verrassing")):
                continue

            # store result
            dishes.append({
                "restaurant": "Broodhuys",
                "city": "Leeuwarden",
                "menu_type": "Lunch",
                "category": category,
                "dish": dish_text,
                "price": price,
                "description": None,
                "tags": None
            })

    # turn list into df and remove duplicates
    df = pd.DataFrame(dishes).drop_duplicates(
        subset=["restaurant", "city", "menu_type", "category", "dish", "price"]
    )

    # return cleaned results as list of dictionaries
    return df.to_dict(orient="records")

# =========================
# JACK AND JACKY'S
# =========================

# scrape menu items from jack and jacky's
def scrape_jack_and_jackys():
    url = "https://jackandjackys.nl/menu-leeuwarden/"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    # store results and keep track of category
    dishes = []
    current_category = None

    # only keep the categories we want
    allowed_categories = {
        "BOWLS", "PANCAKES", "SANDWICHES",
        "SALADS", "BAKERY", "KIDS FOOD"
    }

    # get both headings and menu rows
    elements = soup.select("h2.elementor-heading-title, div.menu-row")

    for el in elements:
        # update current category when a heading is found
        if el.name == "h2":
            current_category = el.get_text(" ", strip=True)
            continue

        if "menu-row" in el.get("class", []):
            # skip rows outside the allowed categories
            if current_category not in allowed_categories:
                continue

            # get the parts of each menu row
            name_tag = el.select_one("span.name")
            price_tag = el.select_one("span.price")
            extra_tag = el.select_one("span.extra")

            # skip rows with missing info or extra labels
            if extra_tag or not name_tag or not price_tag:
                continue

            # description is sometimes inside italic text
            i_tag = name_tag.find("i")
            description = clean_text(i_tag.get_text()) if i_tag else None

            # rebuild dish name without italic text and line breaks
            dish_parts = [
                str(c).strip()
                for c in name_tag.contents
                if getattr(c, "name", None) not in ["i", "br"] and str(c).strip()
            ]

            dish = clean_text(" ".join(dish_parts))

            # store result
            dishes.append({
                "restaurant": "Jack and Jacky's",
                "city": "Leeuwarden",
                "menu_type": "Lunch",
                "category": current_category,
                "dish": dish,
                "price": clean_text(price_tag.get_text()),
                "description": description,
                "tags": None
            })

    # turn list into df and remove duplicates
    df = pd.DataFrame(dishes).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    )

    # return cleaned results as list of dictionaries
    return df.to_dict(orient="records")


# =========================
# ROAST (LUNCH + DINNER)
# =========================

# scrape roast lunch menu
def scrape_roast_lunch():
    url = "https://roastleeuwarden.nl/menukaarten/lunchkaart/"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    # store results and current category
    dishes = []
    current_category = None

    # get both category headings and price list sections
    elements = soup.select("span.elementor-heading-title, div.elementor-widget-price-list")

    for el in elements:
        # update category when heading is found
        if el.name == "span":
            current_category = clean_text(el.get_text())
            continue

        if "elementor-widget-price-list" in el.get("class", []):
            # loop through all dishes in the price list
            for item in el.select("li.elementor-price-list-item"):
                title = item.select_one("span.elementor-price-list-title")
                price = item.select_one("span.elementor-price-list-price")
                desc = item.select_one("p.elementor-price-list-description")

                # skip incomplete dishes
                if not title or not price:
                    continue

                # store result
                dishes.append({
                    "restaurant": "Roast",
                    "city": "Leeuwarden",
                    "menu_type": "Lunch",
                    "category": current_category,
                    "dish": clean_text(title.get_text()),
                    "price": clean_text(price.get_text()),
                    "description": clean_text(desc.get_text()) if desc else None,
                    "tags": None
                })

    # return cleaned results
    return pd.DataFrame(dishes).drop_duplicates().to_dict(orient="records")

# scrape roast dinner menu
def scrape_roast_dinner():
    url = "https://roastleeuwarden.nl/menukaarten/dinerkaart/"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    # store results and current category
    dishes = []
    current_category = None

    # get both category headings and price list sections
    elements = soup.select("span.elementor-heading-title, div.elementor-widget-price-list")

    for el in elements:
        # update category when heading is found
        if el.name == "span":
            current_category = clean_text(el.get_text())
            continue

        if "elementor-widget-price-list" in el.get("class", []):
            # loop through all dishes in the price list
            for item in el.select("li.elementor-price-list-item"):
                title = item.select_one("span.elementor-price-list-title")
                price = item.select_one("span.elementor-price-list-price")
                desc = item.select_one("p.elementor-price-list-description")

                # skip incomplete dishes
                if not title or not price:
                    continue

                # store result
                dishes.append({
                    "restaurant": "Roast",
                    "city": "Leeuwarden",
                    "menu_type": "Dinner",
                    "category": current_category,
                    "dish": clean_text(title.get_text()),
                    "price": clean_text(price.get_text()),
                    "description": clean_text(desc.get_text()) if desc else None,
                    "tags": None
                })

    # return cleaned results
    return pd.DataFrame(dishes).drop_duplicates().to_dict(orient="records")

# =========================
# BAYLINGS
# =========================

# scrape baylings menu and keep track of menu type and category
def scrape_baylings():
    url = "https://baylings.nl/menu/"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    # store results and current menu labels
    dishes = []
    current_menu_type = None
    current_category = None

    # get headings and menu items in order
    elements = soup.select("h6.pt-title, div.pt-food-menu-item")

    for el in elements:
        # headings can mean lunch/dinner sections or real categories
        if el.name == "h6":
            title = clean_text(el.get_text()).upper()

            if title == "LUNCH":
                current_menu_type = "Lunch"
                current_category = None
            elif title in ["STARTERS", "MAIN"]:
                current_menu_type = "Dinner"
                current_category = None
            elif title == "DESSERTS":
                current_menu_type = "Dinner"
                current_category = "Dessert"
            else:
                current_category = title.title()
            continue

        if "pt-food-menu-item" in el.get("class", []):
            # get title, price and description
            title_tag = el.select_one("span.title-wrap")
            price_tag = el.select_one("span.pt-food-menu-price")
            desc_tag = el.select_one("p.pt-food-menu-details")

            # skip incomplete dishes
            if not title_tag or not price_tag:
                continue

            # store result
            dishes.append({
                "restaurant": "Baylings",
                "city": "Leeuwarden",
                "menu_type": current_menu_type,
                "category": current_category or current_menu_type,
                "dish": clean_text(title_tag.get_text()),
                "price": clean_text(price_tag.get_text()),
                "description": clean_text(desc_tag.get_text()) if desc_tag else None,
                "tags": None
            })

    # return cleaned results
    return pd.DataFrame(dishes).drop_duplicates().to_dict(orient="records")


# =========================
# DIKKE VAN DALE (LUNCH + DINNER)
# =========================
# scrape lunch menu from de dikke van dale
def scrape_dikke_van_dale_lunch():
    url = "https://www.dedikkevandale.nl/lekker-lunchen"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    # store results and current category
    dishes = []
    current_category = None

    # only keep the lunch categories we want
    allowed_categories = {
        "Soepen","Salades","Tosti's","Koude Broodjes",
        "Twaalfuurtjes","Warme Broodjes","Eiergerechten","Plates"
    }

    # get headings and content containers
    elements = soup.select("h5.framer-text, div[class*='container']")

    for el in elements:
        # update category when heading is found
        if el.name == "h5":
            cat = clean_text(el.get_text()).title()
            if cat in allowed_categories:
                current_category = cat
            else:
                current_category = None
            continue

        # skip content if no valid category is active
        if not current_category:
            continue

        text_tag = el.select_one("p.framer-text")
        price_tag = el.select_one("div.framer-uf3a4z p")

        # skip incomplete dishes
        if not text_tag or not price_tag:
            continue

        text = clean_text(text_tag.get_text())
        price = clean_text(price_tag.get_text())

        # split dish and description if both are in one text string
        if " - " in text:
            dish, description = text.split(" - ", 1)
        else:
            dish, description = text, None

        # store result
        dishes.append({
            "restaurant": "De Dikke van Dale",
            "city": "Leeuwarden",
            "menu_type": "Lunch",
            "category": current_category,
            "dish": clean_text(dish),
            "price": price,
            "description": clean_text(description) if description else None,
            "tags": None
        })

    # return cleaned results
    return pd.DataFrame(dishes).drop_duplicates().to_dict(orient="records")

# scrape dinner menu from de dikke van dale
def scrape_dikke_van_dale_dinner():
    url = "https://www.dedikkevandale.nl/sfeervol-dineren"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    # store results and current category
    dishes = []
    current_category = None

    # get headings and text blocks
    elements = soup.select("h5.framer-text, p.framer-text")

    for el in elements:
        # update category when heading is found
        if el.name == "h5":
            current_category = clean_text(el.get_text()).title()
            continue

        # skip lines without a category or without a strong tag for the dish name
        if not current_category or not el.find("strong"):
            continue

        # get full text, dish name and description
        text = clean_text(el.get_text())
        dish = clean_text(el.find("strong").get_text())
        description = text.replace(dish, "").strip(" -–—")

        # find the nearest price block
        parent = el.find_parent("div")
        price_tag = parent.find_next("div", class_="framer-uf3a4z") if parent else None

        # skip dishes without price
        if not price_tag:
            continue

        # store result
        dishes.append({
            "restaurant": "De Dikke van Dale",
            "city": "Leeuwarden",
            "menu_type": "Dinner",
            "category": current_category,
            "dish": dish,
            "price": clean_text(price_tag.get_text()),
            "description": clean_text(description) if description else None,
            "tags": None
        })

    # return cleaned results
    return pd.DataFrame(dishes).drop_duplicates().to_dict(orient="records")

# =========================
# FIER GRONINGEN (DINNER)
# =========================

# scrape dinner menu from fier groningen
def scrape_fier_groningen_dinner():
    restaurant_name = "Fier Groningen"
    city_name = "Groningen"
    menu_type_default = "Dinner"

    url = "https://fiergroningen.nl"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # store results
    menu_items = []

    # get all category headings from the food menu section
    sections = soup.select("#food-menu h3")

    for section in sections:
        category = clean_text(section.get_text(strip=True))

        # find the parent block that contains the dishes for this category
        parent = section.find_parent("div", class_="mb-16")
        if not parent:
            continue

        dishes = parent.select(".border-b")
        for dish in dishes:
            # get dish name, price and description
            name_tag = dish.find("h4")
            price_tag = dish.find("span")
            desc_tag = dish.find("p")

            dish_name = clean_text(name_tag.get_text(strip=True)) if name_tag else None
            description = clean_text(desc_tag.get_text(strip=True)) if desc_tag else None
            price_text = clean_text(price_tag.get_text(strip=True)) if price_tag else None

            # use regex to find a numeric price inside the text
            price = None
            if price_text:
                match = re.search(r"(\d+[.,]?\d*)", price_text)
                if match:
                    price = float(match.group(1).replace(",", "."))

            # add vegetarian tag if found in description
            tags = []
            if description and ("vega" in description.lower() or "vegetarisch" in description.lower()):
                tags.append("vegetarian")
            tags_str = ", ".join(tags) if tags else None

            # only keep valid dishes with a name and a price
            if dish_name and price is not None:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": category,
                    "dish": dish_name,
                    "price": price,
                    "description": description,
                    "tags": tags_str
                })

    # turn list into df and remove duplicates
    return pd.DataFrame(menu_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")

# =========================
# DOKJARD (DINNER)
# =========================

# scrape dinner menu from dokjard
def scrape_dokjard_dinner():
    restaurant_name = "Dokjard"
    city_name = "Groningen"
    menu_type_default = "Dinner"

    url = "https://dokjard.nl/menu/"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # store results
    menu_items = []

    # find the main menu section
    section = soup.find("section", id="bistro-menu")
    if not section:
        return []

    # get all menu articles
    articles = section.find_all("article", class_="menu-item")

    current_category = None

    for art in articles:
        classes = art.get("class", [])
        title_tag = art.find("h2", class_="entry-title")
        if not title_tag:
            continue

        # extract title, price text and description
        title = clean_text(title_tag.get_text(strip=True))
        price_tag = art.find("span", class_="menu-price")
        price_text = clean_text(price_tag.get_text(strip=True)) if price_tag else ""
        desc_div = art.find("div", class_="entry-content")
        description = clean_text(desc_div.get_text(" ", strip=True)) if desc_div else None

        # some articles are just category labels and not real dishes
        is_label = "tk_menu_item_label-kop" in classes
        is_empty_price = (not price_text)
        is_empty_description = (not description)

        if is_label or (is_empty_price and is_empty_description):
            current_category = title
            continue

        # split prices in case one dish has multiple prices
        prices = []
        if price_text:
            for part in re.split(r"[\/]", price_text):
                part = part.strip()
                if part:
                    m = re.search(r"(\d+[.,]?\d*)", part)
                    if m:
                        prices.append(float(m.group(1).replace(",", ".")))

        # detect vegetarian tags from description
        tags = []
        desc_lower = (description or "").lower()
        if any(word in desc_lower for word in ["vega", "vegetarisch", "vegan", "veganistisch"]):
            tags.append("vegetarian")
        tags_str = ", ".join(tags) if tags else None

        # if no prices are found still store the dish with price none
        if not prices:
            menu_items.append({
                "restaurant": restaurant_name,
                "city": city_name,
                "menu_type": menu_type_default,
                "category": current_category,
                "dish": title,
                "price": None,
                "description": description,
                "tags": tags_str
            })
        else:
            # make a separate row for each price
            for p in prices:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": current_category,
                    "dish": title,
                    "price": p,
                    "description": description,
                    "tags": tags_str
                })

    # turn list into df and remove duplicates
    return pd.DataFrame(menu_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")


# =========================
# DE DRIE GEZUSTERS (LUNCH + DINNER)
# =========================

# scrape menu data from multiple pages for de drie gezusters
def scrape_drie_gezusters():
    restaurant_name = "De Drie Gezusters"
    city_name = "Groningen"
    headers = {"User-Agent": "Mozilla/5.0"}

    # this restaurant spreads the menu over multiple urls
    menus = [
        {"url": "https://www.dedriegezusters.nl/nl/menu/diner/voorgerechten/voorgerechten", "type": "dinner"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/diner/hoofdgerechten", "type": "dinner"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/diner/nagerechten", "type": "dinner"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/borrel", "type": "borrel"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/ontbijt/gebak", "type": "borrel"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/ontbijt/stadshap", "type": "borrel"},
        {"url": "https://www.dedriegezusters.nl/nl/menu/lunch", "type": "lunch"}
    ]

    # store all menu items from all urls together
    all_items = []

    for menu in menus:
        url = menu["url"]
        menu_type = menu["type"]

        # download each page and parse html
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        sections = soup.select("div.menu")
        for section in sections:
            # get the category title
            title_tag = section.select_one(".menu--title h2")
            category = clean_text(title_tag.get_text(strip=True)) if title_tag else "Unknown"

            # rename this special label to a simpler category name
            if "en natuurlijk ook" in category.lower():
                category = "borrel"

            items_blocks = section.select(".menu--item")
            for block in items_blocks:
                cols = block.select("div.col-md-6")
                for col in cols:
                    h5_tags = col.find_all("h5")
                    for h5 in h5_tags:
                        # get dish name
                        dish_name = clean_text(h5.get_text(" ", strip=True))
                        if not dish_name:
                            continue

                        # collect all text after the h5 until the next h5
                        desc_segments = []
                        sib = h5.next_sibling
                        while sib and (sib.name not in ["h5"]):
                            if hasattr(sib, "get_text"):
                                txt = clean_text(sib.get_text(" ", strip=True))
                                if txt:
                                    desc_segments.append(txt)
                            sib = sib.next_sibling

                        # combine extra text into one string
                        combined_text = " ".join(desc_segments).strip()

                        # try to find a price inside the text
                        price_match = re.search(r"(\d+[.,]?\d*)", combined_text)
                        price = float(price_match.group(1).replace(",", ".")) if price_match else None

                        # remove the price from the description text
                        description = combined_text
                        if price_match:
                            description = description.replace(price_match.group(1), "").strip()

                        # detect vegetarian dishes
                        tags = []
                        if "vega" in description.lower() or "vegetarisch" in description.lower():
                            tags.append("vegetarian")
                        tags_str = ", ".join(tags) if tags else None

                        # only store dishes with a valid price
                        if price is not None:
                            all_items.append({
                                "restaurant": restaurant_name,
                                "city": city_name,
                                "menu_type": menu_type,
                                "category": category,
                                "dish": dish_name,
                                "price": price,
                                "description": description,
                                "tags": tags_str
                            })

    # turn list into df and remove duplicates
    return pd.DataFrame(all_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")


# =========================
# BRASSERIE FLAIR (DINNER)
# =========================

# ignore this warning because this page structure can trigger it during parsing
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

# scrape dinner menu from brasserie flair
def scrape_brasserie_flair():
    restaurant_name = "Brasserie Flair"
    city_name = "Groningen"
    menu_type_default = "Dinner"
    
    url = "https://www.brasserieflair.nl/menukaart"
    # download page and raise an error if request fails
    resp = requests.get(url)
    resp.raise_for_status()
    
    # parse html
    soup = BeautifulSoup(resp.text, "html.parser")
    section = soup.find("section", class_="sections minmargin content")
    p = section.find("p") if section else None
    
    # return empty list if menu paragraph is missing
    if not p:
        return []

    # convert the paragraph to raw html and split on br tags
    raw_html = str(p)
    parts = re.split(r'<br\s*/?>', raw_html, flags=re.IGNORECASE)
    
    # clean every line separately
    lines = []
    for part in parts:
        cleaned = BeautifulSoup(part, "html.parser").get_text(" ", strip=True)
        cleaned = re.sub(r'[<>*/•]', '', cleaned).strip()
        if cleaned and len(cleaned) > 1:
            lines.append(cleaned)
    
    # regex pattern to recognize prices like 12,50 or 12.50
    price_pattern = re.compile(r'€?\s*\d+[,.]\d{2}')
    menu_items = []
    current_category = "General"
    i = 0
    
    # go through the cleaned lines one by one
    while i < len(lines):
        line = clean_text(lines[i]).strip()
        
        # if line ends with : and has no price then treat it as a category
        if line.endswith(":") and not price_pattern.search(line):
            current_category = line[:-1].strip()
            i += 1
            continue
        
        # if line has a price then treat it as a dish line
        if price_pattern.search(line):
            matches = list(price_pattern.finditer(line))
            last_match = matches[-1]
            
            # split the line into dish name and price text
            dish_name = clean_text(line[:last_match.start()]).strip()
            price_text = line[last_match.start():].strip()
            
            # convert price to float
            price_match = re.search(r'(\d+)[,.](\d{2})', price_text)
            price_numeric = None
            if price_match:
                whole, decimal = price_match.groups()
                price_numeric = float(f"{whole}.{decimal}")
            
            # sometimes the next line is the description
            description = ""
            if i + 1 < len(lines):
                next_line = clean_text(lines[i + 1]).strip()
                if (not price_pattern.search(next_line) and 
                    not next_line.endswith(":") and 
                    len(next_line) > 10):
                    description = next_line
                    i += 1
            
            # detect vegetarian dishes
            tags = ""
            if "(V)" in dish_name or "vega" in description.lower() or "vegetarisch" in description.lower():
                tags = "vegetarian"
            
            # store result if price is valid
            if price_numeric:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": current_category,
                    "dish": dish_name,
                    "price": price_numeric,
                    "description": description,
                    "tags": tags
                })
        
        i += 1
    
    # return cleaned results
    return pd.DataFrame(menu_items).drop_duplicates().to_dict(orient="records")

# =========================
# JAVAANS EETCAFE GRONINGEN (DINNER)
# =========================

# scrape dinner menu from javaans eetcafe
def scrape_javaans_eetcafe():
    restaurant_name = "Javaans Eetcafe Groningen"
    city_name = "Groningen"
    menu_type_default = "Dinner"

    URL = "https://javaanseetcafegroningen.nl/menukaart/"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # store results
    menu_items = []

    # get all price list sections
    price_lists = soup.select("div.elementor-widget-price-list")

    for pl in price_lists:
        # find category heading for this price list
        section = pl.find_previous("h2")
        category = clean_text(section.get_text(strip=True)) if section else "Unknown"

        items = pl.select("li")

        for item in items:
            # get dish name
            title_tag = item.select_one(".elementor-price-list-title")
            dish_name = clean_text(title_tag.get_text(strip=True)) if title_tag else category

            # clean and convert price
            price_tag = item.select_one(".elementor-price-list-price")
            price_numeric = None
            if price_tag:
                price_text = clean_text(price_tag.get_text(strip=True))
                price_text_clean = price_text.replace("prijs p.p.", "").replace("€", "").replace(",", ".").strip()
                try:
                    price_numeric = float(price_text_clean)
                except:
                    price_numeric = None

            # get description
            desc_tag = item.select_one(".elementor-price-list-description")
            description = clean_text(desc_tag.get_text(strip=True)) if desc_tag else ""

            # detect vegetarian dishes
            tags = ""
            if "vega" in (description.lower() + dish_name.lower()) or "vegetarisch" in description.lower():
                tags = "vegetarian"

            # only store dishes with valid price
            if price_numeric is not None:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": category,
                    "dish": dish_name,
                    "price": price_numeric,
                    "description": description,
                    "tags": tags
                })

    # remove unwanted category rows
    df = pd.DataFrame(menu_items)
    df = df[~df["category"].str.contains("woordenboek", case=False, na=False)]

    # return cleaned results
    return df.drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")

# =========================
# MAHALO (LUNCH)
# =========================

# scrape lunch menu from mahalo
def scrape_mahalo():
    restaurant_name = "Mahalo"
    city_name = "Groningen"
    menu_type_default = "Lunch"

    URL = "https://mahalo.nu/menu/"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # store results
    menu_items = []

    # get all price list sections
    sections = soup.select("div.elementor-widget-price-list")

    for section in sections:
        # find category title above the section
        section_title = section.find_previous("div", class_="elementor-widget-text-editor")
        category = clean_text(section_title.get_text(strip=True)) if section_title else "Unknown"

        items = section.select("li.elementor-price-list-item")

        for item in items:
            # get dish name
            title_tag = item.select_one(".elementor-price-list-title")
            dish_name = clean_text(title_tag.get_text(strip=True)) if title_tag else category

            # clean and convert price
            price_tag = item.select_one(".elementor-price-list-price")
            price_numeric = None
            if price_tag:
                try:
                    price_numeric = float(clean_text(price_tag.get_text(strip=True)).replace(",", "."))
                except:
                    price_numeric = None

            # get description
            desc_tag = item.select_one(".elementor-price-list-description")
            description = clean_text(desc_tag.get_text(strip=True)) if desc_tag else ""

            # detect vegetarian dishes
            tags = ""
            if "vega" in (description.lower() + dish_name.lower()) or "vegetarisch" in description.lower():
                tags = "vegetarian"

            # only store dishes with valid price
            if price_numeric is not None:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": category,
                    "dish": dish_name,
                    "price": price_numeric,
                    "description": description,
                    "tags": tags
                })

    # return cleaned results
    return pd.DataFrame(menu_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")

# =========================
# MR DAM BANH MI (LUNCH)
# =========================

# scrape lunch menu from mr dam banh mi
def scrape_mr_dam_banh_mi():
    restaurant_name = "Mr. Dam Banh Mi"
    city_name = "Groningen"
    menu_type_default = "Lunch"

    URL = "http://mrdambanhmi.com/nl/"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and parse html
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # store results
    menu_items = []

    # get the main menu div
    menu_div = soup.find("div", id="menu")

    # categories are stored in h3 tags
    categories = menu_div.find_all("h3") if menu_div else []

    for cat in categories:
        category_name = clean_text(cat.get_text(strip=True))

        # get the next definition list for this category
        dl = cat.find_next("dl")
        if not dl:
            continue

        dts = dl.find_all("dt")
        dds = dl.find_all("dd")

        # pair dish names with their matching detail blocks
        for dt, dd in zip(dts, dds):
            dish_name = clean_text(dt.get_text(strip=True))

            if not dish_name:
                continue

            # extract and clean price
            price_tag = dd.find("strong")
            price_numeric = None

            if price_tag:
                price_text = clean_text(price_tag.get_text(strip=True))
                price_text_clean = price_text.replace("€", "").replace(",", ".").strip()
                price_text_clean = re.sub(r"[^\d\.]", "", price_text_clean)

                try:
                    price_numeric = float(price_text_clean)
                except:
                    price_numeric = None

            # no separate description here
            description = ""

            # detect vegetarian dishes from the dish name
            combined_text = dish_name.lower()
            tags = ""
            if any(word in combined_text for word in ["vega", "vegetarisch", "vegan"]):
                tags = "vegetarian"

            # only store dishes with valid price
            if price_numeric is not None:
                menu_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type_default,
                    "category": category_name,
                    "dish": dish_name,
                    "price": price_numeric,
                    "description": description,
                    "tags": tags
                })

    # return cleaned results
    return pd.DataFrame(menu_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")

# =========================
# UGLY DUCK (LUNCH + DINNER)
# =========================

# scrape both lunch and dinner menu from ugly duck
def scrape_ugly_duck():
    restaurant_name = "Ugly Duck"
    city_name = "Groningen"
    headers = {"User-Agent": "Mozilla/5.0"}

    URL = "https://www.uglyduck.nl/menukaart/"
    # download page and parse html
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # store results and current menu type
    menu_items = []
    current_menu_type = None

    # get headings and content blocks
    elements = soup.find_all(["h1", "h2", "div"])

    for el in elements:
        # h1 headings tell us if we are in lunch or dinner section
        if el.name == "h1":
            text = clean_text(el.get_text(strip=True)).lower()
            if "lunch" in text:
                current_menu_type = "lunch"
            elif "diner" in text or "nagerechten" in text:
                current_menu_type = "dinner"

        if el.name == "h2":
            # h2 is used as category name
            category = clean_text(el.get_text(strip=True))

            # find the next price list connected to this category
            next_pl = el.find_next("div", class_="elementor-widget-price-list")
            if not next_pl:
                continue

            items = next_pl.select("li")

            for item in items:
                # get dish name
                title_tag = item.select_one(".elementor-price-list-title")
                dish_name = clean_text(title_tag.get_text(strip=True)) if title_tag else category

                # clean and convert price
                price_tag = item.select_one(".elementor-price-list-price")
                price_numeric = None

                if price_tag:
                    price_text = clean_text(price_tag.get_text(strip=True))
                    price_text_clean = price_text.lower()
                    price_text_clean = price_text_clean.replace("€", "").replace(",", ".")
                    price_text_clean = re.sub(r"[^\d\.]", "", price_text_clean)

                    try:
                        price_numeric = float(price_text_clean)
                    except:
                        price_numeric = None

                # get description
                desc_tag = item.select_one(".elementor-price-list-description")
                description = clean_text(desc_tag.get_text(" ", strip=True)) if desc_tag else ""

                # detect vegetarian dishes
                combined_text = (dish_name + " " + description).lower()
                tags = ""
                if any(word in combined_text for word in ["vega", "vegetarisch", "vegan", " v"]):
                    tags = "vegetarian"

                # only store dishes with valid price and known menu type
                if price_numeric is not None and current_menu_type:
                    menu_items.append({
                        "restaurant": restaurant_name,
                        "city": city_name,
                        "menu_type": current_menu_type,
                        "category": category,
                        "dish": dish_name,
                        "price": price_numeric,
                        "description": description,
                        "tags": tags
                    })

    # remove rows without menu type and drop duplicates
    df = pd.DataFrame(menu_items)
    df = df.dropna(subset=["menu_type"])

    return df.drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")

# =========================
# XO GRONINGEN (LUNCH)
# =========================

# scrape lunch menu from xo groningen
def scrape_xo_groningen_lunch():
    restaurant_name = "XO Groningen"
    city_name = "Groningen"
    menu_type = "Lunch"

    url = "https://xo-groningen.nl/menu/#lunch"
    headers = {"User-Agent": "Mozilla/5.0"}

    # download page and raise an error if request fails
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    html_content = response.text

    # parse html
    soup = BeautifulSoup(html_content, "html.parser")

    # store results
    all_items = []

    # loop through every menu section
    for section in soup.select("div.menu-list"):
        category_tag = section.select_one("h2.menu-list__title")
        if not category_tag:
            continue
        category = clean_text(category_tag.get_text(strip=True))
        
        # loop through every dish in the section
        for li in section.select("ul.menu-list__items > li.menu-list__item"):
            dish_tag = li.select_one("h4.menu-list__item-title")
            desc_tag = li.select_one("p.menu-list__item-desc span.desc__content")
            
            # skip if dish name is missing
            if not dish_tag:
                continue
            
            dish_text = clean_text(dish_tag.get_text(strip=True))
            description = clean_text(desc_tag.get_text(strip=True)) if desc_tag else ""
            
            # first try to find a price inside the dish text
            price_match = None
            if dish_text:  
                price_match = re.search(r'€\s*\d+[,\.]?\d*', dish_text)
            
            # if not found there then look for separate price span
            if not price_match:
                price_span = li.select_one("span.menu-list__item-price")
                price = clean_text(price_span.get_text(strip=True)) if price_span else None
            else:
                price = price_match.group(0)
                dish_text = dish_text.replace(price, "").strip()
            
            # make sure dish and description are always safe strings
            safe_dish = dish_text or ""
            safe_desc = description or ""
            
            # detect vegetarian dishes
            veg_keywords = ["Vega", "vegetarisch", "geitenkaas"]
            tags = "Vegetarian" if any(k.lower() in safe_dish.lower() or k.lower() in safe_desc.lower() for k in veg_keywords) else ""
            
            # only store dishes with a price
            if price:
                all_items.append({
                    "restaurant": restaurant_name,
                    "city": city_name,
                    "menu_type": menu_type,
                    "category": category,
                    "dish": safe_dish,
                    "price": price,
                    "description": safe_desc,
                    "tags": tags
                })

    # turn list into df and remove duplicates
    return pd.DataFrame(all_items).drop_duplicates(
        subset=["restaurant","city","menu_type","category","dish","price"]
    ).to_dict(orient="records")

# =========================
# COLLECTOR 
# =========================

# run every scraper and combine all results into one dataframe
def scrape_all_menus():
    all_data = []

    # print how many rows each scraper found
    print("Jack and Jacky's:", len(scrape_jack_and_jackys()))
    print("Roast lunch:", len(scrape_roast_lunch()))
    print("Roast dinner:", len(scrape_roast_dinner()))
    print("Baylings:", len(scrape_baylings()))
    print("DVD lunch:", len(scrape_dikke_van_dale_lunch()))
    print("DVD dinner:", len(scrape_dikke_van_dale_dinner()))
    print("Fier Groningen:", len(scrape_fier_groningen_dinner()))
    print("Dokjard:", len(scrape_dokjard_dinner()))
    print("Drie Gezusters:", len(scrape_drie_gezusters()))
    print("Brasserie Flair:", len(scrape_brasserie_flair()))
    print("Javaans Eetcafe:", len(scrape_javaans_eetcafe()))
    print("Mahalo:", len(scrape_mahalo()))
    print("Mr Dam Banh Mi:", len(scrape_mr_dam_banh_mi()))
    print("Ugly Duck:", len(scrape_ugly_duck()))
    print("XO Groningen:", len(scrape_xo_groningen_lunch()))

    # add all scraped results to one big list
    all_data.extend(scrape_jack_and_jackys())
    all_data.extend(scrape_roast_lunch())
    all_data.extend(scrape_roast_dinner())
    all_data.extend(scrape_baylings())
    all_data.extend(scrape_dikke_van_dale_lunch())
    all_data.extend(scrape_dikke_van_dale_dinner())
    all_data.extend(scrape_fier_groningen_dinner())
    all_data.extend(scrape_dokjard_dinner())
    all_data.extend(scrape_drie_gezusters())
    all_data.extend(scrape_brasserie_flair())
    all_data.extend(scrape_javaans_eetcafe())
    all_data.extend(scrape_mahalo())
    all_data.extend(scrape_mr_dam_banh_mi())
    all_data.extend(scrape_ugly_duck())
    all_data.extend(scrape_xo_groningen_lunch())

    # turn everything into one dataframe
    return pd.DataFrame(all_data)

# running file manually
if __name__ == "__main__":
    df = scrape_all_menus()
    # print first rows to quickly check if scraping worked
    print(df.head())

# run all scrapers again and save the full raw dataset
df = scrape_all_menus()

# save dataframe as csv file
df.to_csv("data/menus_raw.csv", index=False, encoding="utf-8-sig")

print("Saved raw dataset")