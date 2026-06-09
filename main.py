import tomllib
import requests
import pandas as pd

# 讀取 config
with open("config.toml", "rb") as f:
    config = tomllib.load(f)

print(config)

# 先測 Germany GDP
country_code = "DEU"
indicator = config["series"]["gdp_usd_real"]

url = (
    f"https://api.worldbank.org/v2/country/"
    f"{country_code}/indicator/{indicator}"
    f"?format=json&per_page=100"
)

response = requests.get(url)

print("Status:", response.status_code)

data = response.json()

print(data[1][:3])