# Solar Power Generation — Interactive Python Dashboard

An interactive, multi-tab dashboard built with **Streamlit** and **Plotly**, using the
BigML Solar Power Generation Dataset. This is a Python companion to the Power BI
dashboard, built for the same assignment.

The look is a light, warm, minimalist theme (soft white background, amber accent),
with animated count-up KPI cards, bordered "card" panels for every chart, a rotatable
3D scatter plot, and a play-through animation of how the solar-noon relationship
shifts across the seasons.

## Folder structure

```
solar_dashboard/
├── app.py                 # main Streamlit app
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml        # theme colors (light, amber accent)
├── assets/
│   └── style.css           # fonts, card hover effects, tab styling
├── data/
│   └── solar_data.csv     # the BigML dataset
└── README.md
```

## Setup

1. Make sure you have Python 3.9+ installed.
2. Open a terminal in this folder and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Run the dashboard

```bash
streamlit run app.py
```

This opens the dashboard in your browser (usually at `http://localhost:8501`).

## What's inside

**Sidebar (slicers):** Year, Month, Daylight/Night, Sky Cover, Relative Humidity range —
all filters apply live to every tab.

**KPI cards:** Total Power Generated, Average Power (all periods), Average Power
(daylight only), Max Power, Daylight Share.

**Tabs:**
1. **Overview** — distribution of Power Generated, monthly totals, sky cover mix,
   box plot of power by sky cover.
2. **Time Trends** — daily power vs temperature (dual-axis), average power by
   time of day, seasonality by month.
3. **Environmental Factors** — scatter plots of temperature, humidity, wind
   speed, and distance to solar noon against Power Generated.
4. **Sky & Humidity** — average power by sky cover and humidity band,
   daylight vs night share of total generation.
5. **3D & Motion** — a rotatable 3D scatter (temperature × humidity × power) and
   an animated scatter plot with a play button that steps through each month.
6. **Explorer** — full correlation heatmap plus a build-your-own scatter plot
   tool with feature/color selectors and a raw data table.

## Design notes

- Theme colors live in `.streamlit/config.toml` — change `primaryColor`,
  `backgroundColor` etc. there to retheme without touching `app.py`.
- `assets/style.css` handles the Inter font, card hover-lift animation, tab
  underline styling, and hides the default Streamlit menu/footer for a
  cleaner look.
- KPI cards use a small embedded HTML/JS snippet (`animated_metric()` in
  `app.py`) to count up from zero on load rather than Streamlit's default
  static `st.metric`.
- Chart panels use `st.container(border=True)`, Streamlit's built-in bordered
  container, so each chart sits in its own card without extra CSS hacking.

## Data preparation notes

- `Year`, `Month`, `Day`, and `First Hour of Period` are merged into a real
  `DateTime` column (`pd.to_datetime` + `pd.to_timedelta`), and a `Date` column
  for daily aggregation — matching the Power BI date modelling.
- The single missing `Average Wind Speed (Period)` value is filled with the
  column median.
- `Sky Cover` (0–4) is mapped to readable labels for chart legends.
- Scatter plots default to daylight-only periods, since every night-time
  record has `Power Generated = 0` and would otherwise dominate the trend line.

## Key findings baked into the dashboard

- **Distance to Solar Noon** is the strongest driver of output (r ≈ -0.75).
- **Relative Humidity** has a non-linear relationship — power peaks at
  moderate humidity (40–60%) and collapses above ~80%, likely because high
  humidity co-occurs with heavy cloud cover.
- **Sky Cover** confirms the same story: overcast conditions (cover = 4)
  produce roughly 4–5x less power than clear/lightly-clouded periods.
- **Wind Speed** and **Temperature** are secondary, weaker positive factors.
- **Barometric Pressure** shows almost no relationship with output.
