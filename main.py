import tomllib
import requests
import pandas as pd
import time
from urllib.parse import quote


# Updated using try, exception handling to ensure production safety
def load_config(path="config.toml"):
    try:
        with open(path, "rb") as f:     # try: Open file that might fail if path is missing
            return tomllib.load(f)
    except FileNotFoundError:           # except: Handle file absence safely without crashing
        print(f"Error: Configuration file not found at {path}.")
        return {}


# Updated using try, exception handling
def build_country_code_map():
    # Fetch country metadata from World Bank API to map names to ISO codes
    url = "https://api.worldbank.org/v2/country?format=json&per_page=400"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        payload = response.json()[1]
    except (requests.RequestException, IndexError) as e:
        print(f"Failed to fetch country metadata: {e}")
        return {}
    else:
        name_to_code = {}
        for item in payload:
            name = item.get("name")
            code = item.get("id")
            region = item.get("region", {}).get("value", "")

            if name and code and region != "Aggregates":
                name_to_code[name] = code

        if "Turkiye" in name_to_code:
            name_to_code["Turkey"] = name_to_code["Turkiye"]

        return name_to_code


# Updated using flexible *args to accept dynamic target indicator codes
def fetch_indicator(country_code, start_year, end_year, *indicator_codes, **kwargs):
    """
    *args (*indicator_codes): Dynamically handles multiple API metrics passed as positional arguments.
    **kwargs: Flexibly captures runtime parameters (e.g.custom_per_page=100, custom_source=2).
    """
    all_indicator_frames = []
    
    # Extract query overrides from kwargs with defensive fallback defaults
    per_page = kwargs.get("custom_per_page", 100)
    source_catalog = kwargs.get("custom_source", 2)

    # Production parameter configs
    max_retries = 3  # Maximum alignment attempts, before gracefully skipping
    backoff_factor = 2  # Seconds to wait between retries

    for indicator_code in indicator_codes:
        # TELEMETRY LOG: Instantly notify the engineer which node is currently processing
        print(f"-> Processing Pipeline: Country [{country_code}] | Metric [{indicator_code}] ... ", end="", flush=True)

        safe_indicator_code = quote(indicator_code)
        base_url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{safe_indicator_code}"
        page = 1
        rows = []
        indicator_failed = False

        while True:
            url = f"{base_url}?format=json&per_page={per_page}&page={page}&source={source_catalog}"
            payload = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    # Optimized to timeout=5 to prevent long terminal hangs during development
                    response = requests.get(url, timeout=5)
                    response.raise_for_status()
                    payload = response.json()
                    break  # Success! Break the retry loop and proceed
                except requests.RequestException as e:
                    if attempt < max_retries:
                        print(f"Warning: Attempt {attempt} failed for {country_code} ({indicator_code}). Retrying in {backoff_factor}s... Error: {e}")
                        time.sleep(backoff_factor)
                    else:
                        # Executed only if all retries are completely exhausted
                        print(f"API Error: All {max_retries} attempts exhausted for {country_code} - {indicator_code} on page {page}: {e}")
                        indicator_failed = True
                        payload = None

            # If the retry loop failed to get payload, safely break out of the pagination loop
            if payload is None or indicator_failed:
                break

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
                    
                
        if rows:
            all_indicator_frames.append(pd.DataFrame(rows))
            print("DONE")  # TELEMETRY LOG: Success confirmation on the same line
        else:
            print("SKIPPED (No data)")
            
    if all_indicator_frames:
        return pd.concat(all_indicator_frames, ignore_index=True)
    return pd.DataFrame()


def main():
    config = load_config()
    if not config:
        return
        
    country_map = build_country_code_map()
    if not country_map:
        return

    countries = config["countries"]["list"]
    start_year = config["time"]["start_year"]
    end_year = config["time"]["end_year"]
    # Extract indicator codes into a flat list to feed into *args unpacker
    indicator_list = list(config["series"].values())

    all_frames = []

    for country_name in countries:
        country_code = country_map.get(country_name)
        if not country_code:
            print(f"Skipping unmapped country: {country_name}")
            continue

        # *indicator_list unpacks list into multiple *args arguments
        # custom_per_page and custom_source feed into **kwargs flexibly
        df = fetch_indicator(
            country_code, 
            start_year, 
            end_year, 
            *indicator_list, 
            custom_per_page=100, 
            custom_source=2
        )
        if not df.empty:
            all_frames.append(df)

    if not all_frames:
        print("No data collected. Output CSV aborted.")
        return

    result = pd.concat(all_frames, ignore_index=True)

    df_wide = result.pivot(
        index=["country", "indicator"], 
        columns="year", 
        values="value"
    ).reset_index()

    df_wide.columns = [
        f"year_{col}" if isinstance(col, int) else col 
        for col in df_wide.columns
    ]

    try:
        df_wide.to_csv("output_wide.csv", index=False)
    except IOError as e:
        print(f"File System Error: Could not write output file. {e}")
    else:
        print("Successfully generated output_wide.csv")
        
        
if __name__ == "__main__":
    main()