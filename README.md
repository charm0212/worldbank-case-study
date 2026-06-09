# World Bank Data Pipeline & Analysis

### Project Purpose
This project is an automated, configuration-driven Python pipeline designed to extract, reshape, and analyze macroeconomic data from the World Bank API. By tracking 17 major economies from 2000 to 2025, the project evaluates real GDP, total industry, and manufacturing value-added to identify structural economic shifts—specifically, signs of global de-industrialization.

### Explanation of the TOML Configuration
The pipeline is strictly governed by `config.toml`, ensuring zero hardcoded variables within the core Python scripts.
* **`[countries]`**: A customizable list of target country names
* **`[time]`**: Defines the historical extraction horizon (`start_year` and `end_year`)
* **`[series]`**: Maps World Bank API Indicator Codes to human-readable keys. The pipeline explicitly tracks three core macroeconomic metrics:
  * `NY.GDP.MKTP.KD`: Real GDP (constant USD)
  * `NV.IND.TOTL.KD`: Total Industry Value-Added (constant USD)
  * `NV.IND.MANF.KD`: Manufacturing Value-Added (constant USD)

---

### Instructions to Run
**Prerequisites:** Python 3.11+ (for native `tomllib` support), `pandas`, and `requests`.

1. **Clone the repository and install dependencies:**
   ```bash
   git clone [https://github.com/charm0212/worldbank-case-study.git](https://github.com/charm0212/worldbank-case-study.git)
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

During the implementation of the automation pipeline, several upstream repository anomalies within the World Bank database were observed and defensive-engineered:

* **API Optimizations & Source Control (`source=2`):** 
    - *Issue:* Querying indicators like `NV.IND.MANF.KD` without an explicit database source caused severe data silences (excessive `NaN` gaps) for critical economies, including the USA and China, due to multi-source mixing by the API.
    - *Solution:* Enforced `&source=2` strictly within the ingestion URL to isolate queries to the core **World Development Indicators (WDI)** database, resolving the omissions.

* **Data Quality & Schema Mapping (Türkiye):** 
    - *Issue:* A string mismatch occurred as the live World Bank API registers Turkey under the specific string `"Turkiye"` (without the standard diacritic `ü` or traditional English spelling `Turkey`).
    - *Solution:* Updated `config.toml` to `"Turkiye"` to keep adjustments configuration-driven. Additionally, introduced defensive string normalization (`.lower().strip()`) and alias mappings in `main.py` to ensure long-term pipeline resilience against naming evolutions.

* **Severe Institutional Data Omissions (USA & China):** 
    - *Issue:* Constant USD tracking for Manufacturing Value-Added in both the United States and China contains zero active time-series records except for a single isolated base-year entry in **2015**.
    - *Solution:* The pipeline cleanly isolates these empty spans into explicit `NaN` values to prevent skewed historical CAGR comparisons and population bias during aggregate statistical calculations.

* **Upstream Reporting Lags (Japan):** 
    - *Issue:* While Japan's real GDP is fully reported up to 2024, its industrial and manufacturing indices suffer from an upstream lag and only populate until **2023**.
    - *Solution:* Built a backward-scanning fallback function that seamlessly tracks this delta, calculating Japan's structural shifts using a truncated 2000–2023 horizon (matching numerator and denominator strictly to the same year) to preserve mathematical validity.


