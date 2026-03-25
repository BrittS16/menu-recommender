import pandas as pd

# recommend dishes based on optional filters
def recommend_dishes(df, max_price=None, keyword=None, dietary=None, menu_type=None, city=None):
    # make a copy so the original dataframe stays unchanged
    results = df.copy()

    # only keep dishes that are at or below the chosen max price
    if max_price is not None:
        results = results[results["price"] <= max_price]

    # only keep dishes from the selected menu type
    if menu_type:
        results = results[results["menu_type"].str.lower() == menu_type.lower()]

    # only keep dishes that match the selected dietary tag
    if dietary:
        results = results[results["tags"].str.contains(dietary, na=False)]

    # only keep dishes where keyword appears in dish name or description
    if keyword:
        keyword = keyword.lower()
        results = results[
            results["dish"].str.contains(keyword, na=False) |
            results["description"].str.contains(keyword, na=False)
        ]

    # only keep dishes from the selected city
    if city:
        results = results[results["city"].str.lower() == city.lower()]

    # return filtered results sorted by price from low to high
    return results.sort_values(by="price")