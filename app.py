"""
Solar Power Generation Dashboard
=================================
An interactive dashboard for the BigML Solar Power Generation Dataset,
built with Streamlit and Plotly.

Run locally with:
    pip install -r requirements.txt
    streamlit run app.py
"""

import itertools
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------------
st.set_page_config(
    page_title="Solar Power Generation",
    page_icon="🔆",
    layout="wide",
    initial_sidebar_state="expanded",
)

ACCENT = "#2563EB"
ACCENT_SOFT = "#DBEAFE"
INK = "#1C1917"
MUTED = "#78716C"
TEMPLATE = "plotly_white"
BLUE_SCALE = ["#DBEAFE", "#93C5FD", "#3B82F6", "#2563EB", "#1E40AF"]

_id_counter = itertools.count()


def load_css(path: str) -> None:
    css = Path(path).read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


load_css("assets/style.css")


def style_fig(fig: go.Figure, height: int = 380) -> go.Figure:
    """Apply a consistent, minimal look to every chart."""
    fig.update_layout(
        template=TEMPLATE,
        font=dict(family="palatino", color=INK, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
        height=height,
        title_font=dict(size=15, color=INK),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="#EFEDEB", zeroline=False)
    fig.update_yaxes(gridcolor="#EFEDEB", zeroline=False)
    return fig


def animated_metric(label: str, value: float, decimals: int = 0, suffix: str = "", prefix: str = "") -> None:
    """A small count-up KPI card rendered as an isolated HTML component."""
    uid = next(_id_counter)
    html = f"""
    <div style="
        font-family: palatino, serif !important;
        background: #FFFFFF !important;
        border: 1px solid #E7E5E4 !important;
        border-radius: 14px !important;
        padding: 16px 18px !important;
        text-align: left !important;
        box-sizing: border-box !important;
        height: 125px !important;
        margin: 0 !important;
    ">
      <div id="kpi-{uid}" style="font-size:1.65rem;font-weight:700;color:{INK};line-height:1.1;">
        {prefix}0{suffix}
      </div>
      <div style="font-size:0.82rem;color:{MUTED};margin-top:4px;">{label}</div>
    </div>
    <script>
      (function() {{
        const target = {value};
        const el = document.getElementById("kpi-{uid}");
        const duration = 800;
        let start = null;
        function step(ts) {{
          if (!start) start = ts;
          const p = Math.min((ts - start) / duration, 1);
          const eased = 1 - Math.pow(1 - p, 3);
          const current = target * eased;
          el.textContent = "{prefix}" + current.toLocaleString(undefined, {{maximumFractionDigits: {decimals}}}) + "{suffix}";
          if (p < 1) requestAnimationFrame(step);
        }}
        requestAnimationFrame(step);
      }})();
    </script>
    """
    components.html(html, height=135)


# -----------------------------------------------------------------------
# DATA LOADING + CLEANING
# -----------------------------------------------------------------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Merge Year, Month, Day, First Hour of Period into real datetime fields
    df["Date"] = pd.to_datetime(dict(year=df["Year"], month=df["Month"], day=df["Day"]))
    df["DateTime"] = df["Date"] + pd.to_timedelta(df["First Hour of Period"], unit="h")

    df["Month Name"] = df["DateTime"].dt.strftime("%b")
    df["Is Daylight"] = df["Is Daylight"].astype(bool)

    sky_labels = {
        0: "0 · Clear",
        1: "1 · Few clouds",
        2: "2 · Scattered",
        3: "3 · Broken",
        4: "4 · Overcast",
    }
    df["Sky Cover Label"] = df["Sky Cover"].map(sky_labels)

    if df["Average Wind Speed (Period)"].isna().any():
        df["Average Wind Speed (Period)"] = df["Average Wind Speed (Period)"].fillna(
            df["Average Wind Speed (Period)"].median()
        )

    return df


DATA_PATH = "data/solar_data.csv"
df_raw = load_data(DATA_PATH)


# -----------------------------------------------------------------------
# SIDEBAR — FILTERS
# -----------------------------------------------------------------------
st.sidebar.markdown("### Filters")
st.sidebar.caption("Applied across every tab.")

years = sorted(df_raw["Year"].unique())
year_sel = st.sidebar.multiselect("Year", years, default=years)

month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
months_present = [m for m in month_order if m in df_raw["Month Name"].unique()]
month_sel = st.sidebar.multiselect("Month", months_present, default=months_present)

daylight_sel = st.sidebar.radio("Daylight", ["All", "Daylight only", "Night only"], index=1)

sky_opts = sorted(df_raw["Sky Cover Label"].dropna().unique())
sky_sel = st.sidebar.multiselect("Sky cover", sky_opts, default=sky_opts)

humidity_range = st.sidebar.slider(
    "Relative humidity (%)",
    int(df_raw["Relative Humidity"].min()),
    int(df_raw["Relative Humidity"].max()),
    (int(df_raw["Relative Humidity"].min()), int(df_raw["Relative Humidity"].max())),
)

if st.sidebar.button("Reset filters"):
    st.rerun()

df = df_raw[
    df_raw["Year"].isin(year_sel)
    & df_raw["Month Name"].isin(month_sel)
    & df_raw["Sky Cover Label"].isin(sky_sel)
    & df_raw["Relative Humidity"].between(*humidity_range)
].copy()

if daylight_sel == "Daylight only":
    df = df[df["Is Daylight"]]
elif daylight_sel == "Night only":
    df = df[~df["Is Daylight"]]

if df.empty:
    st.warning("No data matches the current filters — try widening your selection.")
    st.stop()

df_daylight = df[df["Is Daylight"]]


# -----------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------
st.title("Solar Power Generation")
st.markdown(
    f"<div class='subtitle'>BigML dataset · "
    f"{df['DateTime'].min():%d %b %Y} – {df['DateTime'].max():%d %b %Y} · "
    f"{len(df):,} of {len(df_raw):,} readings in view</div>",
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    animated_metric("Total power generated", df["Power Generated"].sum() / 1e6, decimals=2, suffix="M")
with k2:
    animated_metric("Average, all periods", df["Power Generated"].mean(), decimals=0)
with k3:
    animated_metric(
        "Average, daylight only",
        df_daylight["Power Generated"].mean() if len(df_daylight) else 0,
        decimals=0,
    )
with k4:
    animated_metric("Peak output", df["Power Generated"].max(), decimals=0)
with k5:
    animated_metric("Share of readings in daylight", df["Is Daylight"].mean() * 100, decimals=1, suffix="%")

st.write("")


# -----------------------------------------------------------------------
# TABS
# -----------------------------------------------------------------------
tab_overview, tab_time, tab_env, tab_sky, tab_3d, tab_explore = st.tabs(
    ["Overview", "Time trends", "Environmental factors", "Sky & humidity", "3D & motion", "Explorer"]
)

# =========================================================================
# TAB 1 — OVERVIEW
# =========================================================================
with tab_overview:
    c1, c2 = st.columns([1.3, 1])

    with c1:
        with st.container(border=True):
            fig = px.histogram(
                df,
                x="Power Generated",
                nbins=40,
                color="Is Daylight",
                color_discrete_map={True: ACCENT, False: "#D6D3D1"},
                title="Distribution of power output",
            )
            fig.update_layout(bargap=0.05)
            st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)
            st.caption(
                "Every night-time reading sits at zero, so the distribution splits into "
                "a spike at zero and a daylight curve stretching out to around 36,500."
            )

    with c2:
        with st.container(border=True):
            month_sum = df.groupby("Month Name")["Power Generated"].sum().reindex(months_present).reset_index()
            fig2 = px.bar(
                month_sum,
                x="Power Generated",
                y="Month Name",
                orientation="h",
                title="Total output by month",
                color="Power Generated",
                color_continuous_scale=BLUE_SCALE,
            )
            fig2.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="")
            st.plotly_chart(style_fig(fig2), use_container_width=True, theme=None)

    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            sky_count = df["Sky Cover Label"].value_counts().sort_index().reset_index()
            sky_count.columns = ["Sky Cover", "Count"]
            fig3 = px.pie(
                sky_count,
                names="Sky Cover",
                values="Count",
                title="Readings by sky cover",
                color_discrete_sequence=BLUE_SCALE,
                hole=0.55,
            )
            st.plotly_chart(style_fig(fig3, height=340), use_container_width=True, theme=None)
    with c4:
        with st.container(border=True):
            fig4 = px.box(
                df_daylight,
                x="Sky Cover Label",
                y="Power Generated",
                title="Output spread by sky cover (daylight only)",
                color="Sky Cover Label",
                color_discrete_sequence=BLUE_SCALE,
            )
            fig4.update_layout(showlegend=False, xaxis_title="")
            st.plotly_chart(style_fig(fig4, height=340), use_container_width=True, theme=None)

# =========================================================================
# TAB 2 — TIME TRENDS
# =========================================================================
with tab_time:
    with st.container(border=True):
        daily = df.groupby("Date").agg(
            Power=("Power Generated", "sum"),
            Temp=("Average Temperature (Day)", "mean"),
        ).reset_index()

        fig5 = make_subplots(specs=[[{"secondary_y": True}]])
        fig5.add_trace(
            go.Scatter(x=daily["Date"], y=daily["Power"], name="Total power", line=dict(color=ACCENT, width=2)),
            secondary_y=False,
        )
        fig5.add_trace(
            go.Scatter(
                x=daily["Date"], y=daily["Temp"], name="Avg temperature (°F)",
                line=dict(color="#EF4444", width=2, dash="dot"),
            ),
            secondary_y=True,
        )
        fig5.update_layout(title="Daily output alongside average temperature")
        fig5.update_yaxes(title_text="Total power", secondary_y=False)
        fig5.update_yaxes(title_text="Avg temperature (°F)", secondary_y=True, showgrid=False)
        st.plotly_chart(style_fig(fig5, height=380), use_container_width=True, theme=None)
        st.caption(
            "Output follows the seasonal temperature curve, but loosely — day length "
            "and sun angle move together with temperature, so this reads more like a "
            "shared season than a direct cause."
        )

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            hourly = df.groupby("First Hour of Period")["Power Generated"].mean().reset_index()
            fig6 = px.line(hourly, x="First Hour of Period", y="Power Generated", markers=True,
                            title="Average output by time of day")
            fig6.update_traces(line=dict(color=ACCENT, width=3), marker=dict(size=7))
            st.plotly_chart(style_fig(fig6), use_container_width=True, theme=None)
            st.caption("A clean midday peak, as you'd expect from solar output.")

    with c2:
        with st.container(border=True):
            month_avg = df.groupby("Month Name")["Power Generated"].mean().reindex(months_present).reset_index()
            fig7 = px.line(month_avg, x="Month Name", y="Power Generated", markers=True,
                            title="Average output by month")
            fig7.update_traces(line=dict(color=ACCENT, width=3), marker=dict(size=7, color=ACCENT))
            st.plotly_chart(style_fig(fig7), use_container_width=True, theme=None)
# =========================================================================
# TAB 3 — ENVIRONMENTAL FACTORS
# =========================================================================
with tab_env:
    st.caption("Scatter plots below use daylight periods only — every night reading is zero and would flatten the trend.")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            fig8 = px.scatter(
                df_daylight, x="Average Temperature (Day)", y="Power Generated",
                color="Sky Cover Label", opacity=0.6,
                color_discrete_sequence=BLUE_SCALE,
                title="Temperature vs power output",
            )
            st.plotly_chart(style_fig(fig8), use_container_width=True, theme=None)

    with c2:
        with st.container(border=True):
            fig9 = px.scatter(
                df_daylight, x="Relative Humidity", y="Power Generated",
                color="Sky Cover Label", opacity=0.6,
                color_discrete_sequence=BLUE_SCALE,
                title="Humidity vs power output",
            )
            st.plotly_chart(style_fig(fig9), use_container_width=True, theme=None)
            st.caption("Output peaks around 40–60% humidity and falls away above ~80% — "
                       "high humidity is mostly standing in for cloud cover here.")

    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            fig10 = px.scatter(
                df_daylight, x="Average Wind Speed (Period)", y="Power Generated",
                trendline="ols", opacity=0.5, color_discrete_sequence=[ACCENT],
                title="Wind speed vs power output",
            )
            fig10.data[1].line.color = "#1E40AF"
            st.plotly_chart(style_fig(fig10), use_container_width=True, theme=None)
    with c4:
        with st.container(border=True):
            fig11 = px.scatter(
                df_daylight, x="Distance to Solar Noon", y="Power Generated",
                opacity=0.5, color_discrete_sequence=[ACCENT],
                title="Distance to solar noon vs power output",
            )
            st.plotly_chart(style_fig(fig11), use_container_width=True, theme=None)
            st.caption("The strongest single relationship in the dataset.")

# =========================================================================
# TAB 4 — SKY & HUMIDITY
# =========================================================================
with tab_sky:
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            sky_avg = df_daylight.groupby("Sky Cover Label")["Power Generated"].mean().reset_index()
            fig12 = px.bar(
                sky_avg, x="Sky Cover Label", y="Power Generated",
                title="Average output by sky cover (daylight only)",
                color="Power Generated", color_continuous_scale=BLUE_SCALE,
            )
            fig12.update_layout(coloraxis_showscale=False, xaxis_title="")
            st.plotly_chart(style_fig(fig12), use_container_width=True, theme=None)

    with c2:
        with st.container(border=True):
            bins = [0, 20, 40, 60, 80, 100]
            labels = ["0-20", "20-40", "40-60", "60-80", "80-100"]
            tmp = df_daylight.copy()
            tmp["Humidity Band"] = pd.cut(tmp["Relative Humidity"], bins=bins, labels=labels, include_lowest=True)
            hum_avg = tmp.groupby("Humidity Band", observed=True)["Power Generated"].mean().reset_index()
            fig13 = px.bar(
                hum_avg, x="Humidity Band", y="Power Generated",
                title="Average output by humidity band (daylight only)",
                color="Power Generated", color_continuous_scale=BLUE_SCALE,
            )
            fig13.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_fig(fig13), use_container_width=True, theme=None)

    with st.container(border=True):
        daylight_sum = df.groupby("Is Daylight")["Power Generated"].sum().reset_index()
        daylight_sum["Is Daylight"] = daylight_sum["Is Daylight"].map({True: "Daylight", False: "Night"})
        fig14 = px.pie(
            daylight_sum, names="Is Daylight", values="Power Generated",
            title="Share of total output: daylight vs night",
            color_discrete_sequence=[ACCENT, "#E7E5E4"], hole=0.55,
        )
        st.plotly_chart(style_fig(fig14, height=340), use_container_width=True, theme=None)

# =========================================================================
# TAB 5 — 3D & MOTION
# =========================================================================
with tab_3d:
    with st.container(border=True):
        fig15 = go.Figure(
            data=[
                go.Scatter3d(
                    x=df_daylight["Average Temperature (Day)"],
                    y=df_daylight["Relative Humidity"],
                    z=df_daylight["Power Generated"],
                    mode="markers",
                    marker=dict(
                        size=3.5,
                        color=df_daylight["Power Generated"],
                        colorscale=[[0, "#DBEAFE"], [0.5, "#3B82F6"], [1, "#1E40AF"]],
                        opacity=0.75,
                        colorbar=dict(title="Power", thickness=14),
                    ),
                    text=df_daylight["Sky Cover Label"],
                    hovertemplate="Temp %{x}°F · Humidity %{y}% · Power %{z:,.0f}<br>%{text}<extra></extra>",
                )
            ]
        )
        fig15.update_layout(
            title="Temperature, humidity and power — rotate to explore",
            scene=dict(
                xaxis_title="Avg temperature (°F)",
                yaxis_title="Relative humidity (%)",
                zaxis_title="Power generated",
                xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="#EFEDEB"),
                yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="#EFEDEB"),
                zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="#EFEDEB"),
            ),
            height=620,
            font=dict(family="palatino", color=INK, size=12),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=50, b=0),
        )
        st.plotly_chart(fig15, use_container_width=True, theme=None)
        st.caption(
            "Drag to rotate. The darkest, highest points cluster at moderate temperature "
            "and lower humidity — the same story the 2D charts tell, seen from another angle."
        )

    with st.container(border=True):
        anim_df = df_daylight.copy()
        anim_df["Month Name"] = pd.Categorical(anim_df["Month Name"], categories=months_present, ordered=True)
        anim_df = anim_df.sort_values("Month Name")

        fig16 = px.scatter(
            anim_df,
            x="Distance to Solar Noon",
            y="Power Generated",
            color="Sky Cover Label",
            animation_frame="Month Name",
            category_orders={"Month Name": months_present},
            range_y=[0, df["Power Generated"].max() * 1.05],
            color_discrete_sequence=BLUE_SCALE,
            title="Press play — how the solar-noon relationship shifts through the year",
        )
        fig16.update_traces(marker=dict(size=7, opacity=0.7))
        st.plotly_chart(style_fig(fig16, height=460), use_container_width=True, theme=None)
        st.caption("Watch how tightly the curve hugs the top in summer months, and how it flattens in winter.")

# =========================================================================
# TAB 6 — EXPLORER & CORRELATION
# =========================================================================
with tab_explore:
    with st.container(border=True):
        numeric_cols = [
            "Distance to Solar Noon", "Average Temperature (Day)", "Average Wind Direction (Day)",
            "Average Wind Speed (Day)", "Sky Cover", "Visibility", "Relative Humidity",
            "Average Wind Speed (Period)", "Average Barometric Pressure (Period)", "Power Generated",
        ]
        corr = df[numeric_cols].corr()
        fig17 = px.imshow(
            corr, text_auto=".2f", zmin=-1, zmax=1, aspect="auto",
            color_continuous_scale=["#57534E", "#FAFAF8", ACCENT],
            title="Correlation matrix",
        )
        st.plotly_chart(style_fig(fig17, height=460), use_container_width=True, theme=None)

    with st.container(border=True):
        st.markdown("**Build your own view**")
        feature_options = [c for c in numeric_cols if c != "Power Generated"]
        c1, c2, c3 = st.columns(3)
        with c1:
            x_feat = st.selectbox("X-axis", feature_options, index=feature_options.index("Distance to Solar Noon"))
        with c2:
            color_feat = st.selectbox("Color by", ["Sky Cover Label", "Is Daylight", "Month Name", "None"], index=0)
        with c3:
            daylight_only = st.checkbox("Daylight periods only", value=True)

        plot_df = df_daylight if daylight_only else df
        fig18 = px.scatter(
            plot_df, x=x_feat, y="Power Generated",
            color=None if color_feat == "None" else color_feat,
            opacity=0.6, color_discrete_sequence=BLUE_SCALE,
            title=f"{x_feat} vs power generated",
        )
        st.plotly_chart(style_fig(fig18), use_container_width=True, theme=None)

        with st.expander("View filtered data"):
            st.dataframe(
                df[[
                    "DateTime", "Is Daylight", "Distance to Solar Noon", "Average Temperature (Day)",
                    "Relative Humidity", "Sky Cover Label", "Average Wind Speed (Period)",
                    "Average Barometric Pressure (Period)", "Power Generated",
                ]].sort_values("DateTime"),
                use_container_width=True,
                height=340,
            )

st.write("")
st.caption("Built with Streamlit and Plotly · BigML Solar Power Generation Dataset")
