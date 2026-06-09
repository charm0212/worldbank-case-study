import tomllib
import requests
import pandas as pd


def load_config(path="config.toml"):
    with open(path, "rb") as f:
        return tomllib.load(f)


def build_country_code_map():
    # Fetch country metadata from World Bank API to map names to ISO codes
    url = "https://api.worldbank.org/v2/country?format=json&per_page=400"
    response = requests.get(url)
    response.raise_for_status()
    payload = response.json()[1]

    name_to_code = {}
    for item in payload:
        name = item.get("name")
        code = item.get("id")
        region = item.get("region", {}).get("value", "")

        if name and code and region != "Aggregates":
            name_to_code[name] = code

    # Alias mapping to ensure robustness against country name updates
    if "Turkiye" in name_to_code:
        name_to_code["Turkey"] = name_to_code["Turkiye"]

    return name_to_code


def fetch_indicator(country_code, indicator_code, start_year, end_year):
    base_url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}"
    page = 1
    rows = []

    while True:
        url = f"{base_url}?format=json&per_page=100&page={page}&source=2"
        response = requests.get(url)
        response.raise_for_status()
        payload = response.json()

        if not payload or len(payload) < 2 or payload[1] is None:
            break

        meta = payload[0]
        data = payload[1]

        for item in data:
            year = item.get("date")
            value = item.get("value")

            if year is None:
                continue

            year = int(year)
            if start_year <= year <= end_year:
                rows.append(
                    {
                        "country": country_code,
                        "indicator": indicator_code,
                        "year": year,
                        "value": value,
                    }
                )

        if page >= meta.get("pages", 1):
            break

        page += 1

    return pd.DataFrame(rows)


def main():
    config = load_config()
    country_map = build_country_code_map()

    countries = config["countries"]["list"]
    start_year = config["time"]["start_year"]
    end_year = config["time"]["end_year"]
    series = config["series"]

    all_frames = []

    for country_name in countries:
        country_code = country_map.get(country_name)
        if not country_code:
            print(f"Skipping unmapped country: {country_name}")
            continue

        for indicator_key, indicator_code in series.items():
            df = fetch_indicator(country_code, indicator_code, start_year, end_year)
            all_frames.append(df)

    # Combine all structural data chunks into a single long-format DataFrame
    result = pd.concat(all_frames, ignore_index=True)

    # Convert the dataset from long format to wide format
    df_wide = result.pivot(
        index=["country", "indicator"], 
        columns="year", 
        values="value"
    ).reset_index()

    # Reformat columns to append year_ prefix schema
    df_wide.columns = [
        f"year_{col}" if isinstance(col, int) else col 
        for col in df_wide.columns
    ]
    print(df_wide.head())
    
    # Export the dataset to CSV
    df_wide.to_csv("output_wide.csv", index=False)
    print("Successfully generated output_wide.csv")
    
if __name__ == "__main__":
    main()