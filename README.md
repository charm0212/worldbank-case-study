# World Bank Data Pipeline & Analysis

### Project Purpose
This project is an automated, configuration-driven Python pipeline designed to extract, reshape, and analyze macroeconomic data from the World Bank API. By tracking 17 major economies from 2000 to 2025, the project evaluates real GDP, total industry, and manufacturing value-added to identify structural economic shifts, specifically indicators of global de-industrialization.

---

### Explanation of the TOML Configuration
The core data collection process is governed by config.toml, ensuring that countries, indicators, and time horizons can be modified without changing the ingestion logic.
* **`[countries]`**: A customizable list of target country names
* **`[time]`**: Defines the historical extraction horizon (`start_year` and `end_year`)
* **`[series]`**: Maps World Bank API Indicator Codes to human-readable keys. The pipeline explicitly tracks three core macroeconomic metrics:
  * `NY.GDP.MKTP.KD`: Real GDP (constant USD)
  * `NV.IND.TOTL.KD`: Total Industry Value-Added (constant USD)
  * `NV.IND.MANF.KD`: Manufacturing Value-Added (constant USD)

---

### Instructions to Run the Project
**Prerequisites:** Python 3.11+ (for native `tomllib` support), `pandas`, and `requests`.

1. **Clone the repository and install dependencies:**
   ```bash
   git clone https://github.com/charm0212/worldbank-case-study.git
   pip install pandas requests
   ```

2. **Execute Data Ingestion:**
   Fetches and reshapes World Bank API data based on the TOML configuration.
   ```bash
   python main.py
   ```

3. **Execute Analytical Engine:**
   Computes metrics and outputs the descriptive interpretation to the terminal.
   ```bash
   python analysis.py
   ```
   *(Note: For a detailed visual report with markdown narratives, you can also view `analysis.ipynb`)*

---

### Description of Output Files
* **`output_wide.csv`**: The raw time-series dataset reshaped into a wide format, featuring one consolidated column per fiscal year (e.g., `country`, `indicator`, `year_2000`, `year_2001`, ..., `year_2025`)
* **`summary_table.csv`**: The finalized analytical table containing one row per country, detailing computed start year shares, end year shares (dynamically matched latest available data), and Compound Annual Growth Rates (CAGR) for GDP, Industry, and Manufacturing.

---

### Brief Discussion of Analytical Findings
1. **De-industrialization Landscape:** 9 out of 17 tracked countries exhibit a structural decline in their manufacturing share, which concurrently dragged down their broader total industry shares. Within this cohort, **Canada** and **Italy** experienced *Absolute De-industrialization* (a physical contraction in manufacturing output, showing negative CAGRs of -0.37% and -0.05%). Conversely, nations like **Brazil, Australia, and France** experienced *Relative De-industrialization*. Their manufacturing output grew in absolute terms, but was structurally diluted by the faster expansion of other domestic sectors (such as services).

2. **Manufacturing vs. Total Industry:** A comparison between manufacturing and broader industrial growth verifies the depth of this structural shift. Globally, the average manufacturing growth rate (1.21% CAGR) lags behind total industry (1.57%). Within the isolated de-industrializing cohort from the cohort identified above, this underperformance becomes even more acute (Industry CAGR: 0.82% vs. Manufacturing CAGR: 0.45%). This mathematically confirms that the erosion of the manufacturing base is the primary anchor pulling down overall industrial weight.

3. **Advanced vs. Emerging Economies:** Grouping the data reveals the underlying macroeconomic shift driving these trends. Emerging economies are actively industrializing, posting robust growth across all aggregate metrics (GDP CAGR: 3.78%, Manufacturing CAGR: 1.96%). In contrast, advanced economies exhibit post-industrial consolidation (GDP CAGR: 1.41%, Manufacturing CAGR: 0.81%). Based strictly on these figures, the de-industrialization observed in advanced nations reflects a mature transition toward service-driven economic growth, while emerging markets strongly sustain global manufacturing momentum.

---

### Engineering Assumptions, Limitations & Data Quality

During implementation, several data-quality and metadata issues were identified and handled explicitly within the pipeline.

* **API Source Selection (`source=2`):** 
All API requests explicitly specify `source=2` (World Development Indicators, WDI) to ensure that indicators are retrieved from a consistent data source and to reduce potential discrepancies arising from source ambiguity.

* **Country Name Mapping (Turkiye):** 
The World Bank API registers Turkey under the official country name `Turkiye`, while the assignment configuration originally used `Turkey`. To maintain consistency with the World Bank metadata, the configuration was updated to use `Turkiye`. In addition, an alias mapping was implemented within the pipeline to ensure that both `Turkey` and `Turkiye` resolve to the same ISO country code, improving robustness against naming variations.

* **Data Coverage Gaps (USA & China):** 
The manufacturing value-added indicator (`NV.IND.MANF.KD`) contains substantial missing observations for some country-year combinations, particularly for the United States and China. Missing observations were preserved as `NaN` values and were not imputed.

* **Incomplete Recent-Year Coverage (Japan):** 
Some Japanese industrial indicators are only available through 2023, while GDP data extends through 2024. The analysis therefore uses the latest available observation for each indicator when calculating shares and growth rates.

* **General Missing-Data Handling**
Missing observations were retained as `NaN` values throughout the pipeline. Growth rates and share calculations were only computed when sufficient valid observations were available.


---

### Enhancements (12.06.2026)

The core data pipeline has been refactored to make the data collection process more robust and flexible. The implementation now includes the following Python patterns and improvements:

1. **Exception Handling (`try-except-else`):**
Added structured exception handling around:

* Configuration loading
* World Bank API requests
* Output file generation

This prevents unexpected interruptions caused by missing files, network issues, or write failures and ensures that downstream operations only proceed when previous steps complete successfully.

2. **Flexible Function Parameters (`*args` & `**kwargs`):**
Refactored `fetch_indicator` to support more flexible inputs:
* **`*indicator_codes` (`*args`)** allow multiple indicator codes to be passed dynamically without changing the function signature.
* **`**kwargs`** enables optional runtime parameters such as custom pagination settings or source configuration.

This makes the pipeline easier to extend when adding new indicators or modifying API behavior.

3. **Improved API Resilience:**
Added several safeguards to improve stability when interacting with the World Bank API:
* URL encoding via `urllib.parse.quote()` for indicator identifiers.
* Retry mechanism `(max_retries=3)` for temporary request failures.
* Request timeouts and graceful skipping of failed requests.

These changes help maintain pipeline continuity even when individual API calls encounter temporary issues.
