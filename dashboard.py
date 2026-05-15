import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Indian Railway Delay Genome",
    page_icon="🚆",
    layout="wide"
)

conn = sqlite3.connect(r"C:\Users\HP\delays.db")
@st.cache_data
def load_data():
    conn = sqlite3.connect("delays.db")
    vuln     = pd.read_sql("SELECT * FROM junction_vulnerability",  conn)
    depth    = pd.read_sql("SELECT * FROM cascade_depth",           conn)
    pairs    = pd.read_sql("SELECT * FROM high_risk_pairs",         conn)
    contagion= pd.read_sql("SELECT * FROM contagion_index",         conn)
    schedule = pd.read_sql("SELECT * FROM schedule",                conn)
    trains   = pd.read_sql("SELECT * FROM trains",                  conn)
    conn.close()
    return vuln, depth, pairs, contagion, schedule, trains

vuln, depth, pairs, contagion, schedule, trains = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🚆 Indian Railway Delay Genome")
st.markdown(
    "Mapping failure propagation across the Indian railway network — "
    "which junctions, when delayed, infect the most other trains?"
)
st.divider()

# ── KPI cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Trains",        f"{len(trains):,}")
k2.metric("Unique Junctions",    f"{len(vuln):,}")
k3.metric("High-Risk Train Pairs", f"{len(pairs[pairs['risk']=='HIGH']):,}")
k4.metric("Most Dangerous Junction", "Itarsi Jn")
st.divider()

# ── Tab layout ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Contagion Index",
    "🕸️ Cascade Depth",
    "⚠️ High-Risk Pairs",
    "🔍 Train Explorer"
])

# ── TAB 1: Contagion Index ────────────────────────────────────────────────────
with tab1:
    st.subheader("Junction Contagion Index")
    st.markdown(
        "The **Contagion Index** measures how much damage a junction causes when delayed. "
        "It combines the number of trains passing through, the number of at-risk train pairs, "
        "and how many downstream stations the delay ripples to."
    )

    top_n = st.slider("Show top N junctions", 5, 30, 10)
    df = contagion.head(top_n).sort_values("contagion_index")

    fig = go.Figure(go.Bar(
        x=df["contagion_index"],
        y=df["station"],
        orientation="h",
        marker=dict(
            color=df["contagion_index"],
            colorscale="Reds",
            showscale=False
        ),
        text=df["contagion_index"].apply(lambda x: f"{x:,.0f}"),
        textposition="outside"
    ))
    fig.update_layout(
        height=420,
        xaxis_title="Contagion Index",
        yaxis_title="",
        margin=dict(l=10, r=80, t=20, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### What this means")
    top = contagion.iloc[0]
    st.info(
        f"**{top['station']}** is the most dangerous junction in the network. "
        f"**{int(top['total_trains'])}** trains pass through it, creating "
        f"**{int(top['shared_pairs']):,}** at-risk train pairs. "
        f"A delay there can ripple across **{int(top['reachable_stations']):,}** downstream stations — "
        f"nearly **{int(top['reachable_stations']/7333*100)}%** of all stations in India."
    )

    st.dataframe(
        contagion[["station","total_trains","shared_pairs","reachable_stations","contagion_index"]]
        .rename(columns={
            "station":            "Junction",
            "total_trains":       "Trains Through",
            "shared_pairs":       "At-Risk Pairs",
            "reachable_stations": "Downstream Stations",
            "contagion_index":    "Contagion Index"
        }),
        use_container_width=True,
        hide_index=True
    )

# ── TAB 2: Cascade Depth ──────────────────────────────────────────────────────
with tab2:
    st.subheader("Cascade Depth — How Far Does a Delay Travel?")
    st.markdown(
        "For each top junction, how many other stations are reachable through trains "
        "that pass through it? A delay at the junction travels with every train that was there."
    )

    fig2 = px.scatter(
        depth,
        x="carrier_trains",
        y="reachable_stations",
        text="junction",
        size="reachable_stations",
        color="reachable_stations",
        color_continuous_scale="Oranges",
        labels={
            "carrier_trains":     "Trains Passing Through",
            "reachable_stations": "Downstream Stations Affected"
        }
    )
    fig2.update_traces(textposition="top center")
    fig2.update_layout(
        height=460,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig2, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Key insight:** Ghaziabad has fewer trains than Itarsi but reaches almost as many "
                    "downstream stations — it punches above its weight because it sits on multiple "
                    "high-density corridors simultaneously.")
    with c2:
        st.metric("Max downstream reach",
                  f"{depth['reachable_stations'].max():,} stations",
                  f"via {depth.loc[depth['reachable_stations'].idxmax(), 'junction']}")

# ── TAB 3: High-Risk Pairs ────────────────────────────────────────────────────
with tab3:
    st.subheader("High-Risk Train Pairs")
    st.markdown(
        "These are trains scheduled to arrive at the **same junction within 60 minutes** of each other. "
        "When one is delayed, it directly blocks the other's path."
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        risk_filter = st.radio("Risk level", ["ALL", "HIGH (≤20 min)", "MEDIUM (21–60 min)"])
        junction_filter = st.selectbox(
            "Filter by junction",
            ["All"] + sorted(pairs["junction"].unique().tolist())
        )

    filtered = pairs.copy()
    if risk_filter == "HIGH (≤20 min)":
        filtered = filtered[filtered["risk"] == "HIGH"]
    elif risk_filter == "MEDIUM (21–60 min)":
        filtered = filtered[filtered["risk"] == "MEDIUM"]
    if junction_filter != "All":
        filtered = filtered[filtered["junction"] == junction_filter]

    with col2:
        r1, r2 = st.columns(2)
        r1.metric("HIGH risk pairs",   len(pairs[pairs["risk"]=="HIGH"]))
        r2.metric("MEDIUM risk pairs", len(pairs[pairs["risk"]=="MEDIUM"]))

    st.dataframe(
        filtered[["junction","name1","arr1","name2","arr2","gap_min","risk"]]
        .rename(columns={
            "junction": "Junction",
            "name1":    "Train 1",
            "arr1":     "Arr 1",
            "name2":    "Train 2",
            "arr2":     "Arr 2",
            "gap_min":  "Gap (min)",
            "risk":     "Risk"
        })
        .sort_values("Gap (min)"),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("**Note:** Pairs with 0-minute gap are structurally problematic — "
                "they are scheduled to arrive simultaneously, meaning one always waits.")

# ── TAB 4: Train Explorer ─────────────────────────────────────────────────────
with tab4:
    st.subheader("Train Route Explorer")
    st.markdown("Look up any train's full route and see which high-risk junctions it passes through.")

    search = st.text_input("Search by train name or number", placeholder="e.g. Rajdhani or 12951")

    if search:
        mask = (
            trains["train_name"].str.contains(search, case=False, na=False) |
            trains["train_no"].astype(str).str.contains(search, na=False)
        )
        results = trains[mask]

        if results.empty:
            st.warning("No trains found.")
        else:
            selected = st.selectbox(
                "Select train",
                results["train_no"].tolist(),
                format_func=lambda x: f"{x} — {trains[trains['train_no']==x]['train_name'].iloc[0]}"
            )

            route = schedule[schedule["train_no"] == selected].sort_values("stop_sequence")
            top_junction_names = contagion["station"].head(20).tolist()
            route["is_hotspot"] = route["station_name"].isin(top_junction_names)

            st.markdown(f"**{len(route)} stops** | "
                        f"**{route['is_hotspot'].sum()} high-risk junctions** on this route")

            def highlight_hotspot(row):
                if row["is_hotspot"]:
                    return ["background-color: #fff3cd"] * len(row)
                return [""] * len(row)

            display = route[["stop_sequence","station_name","arrival_time","departure_time","is_hotspot"]].rename(columns={
                "stop_sequence":  "Stop #",
                "station_name":   "Station",
                "arrival_time":   "Arrival",
                "departure_time": "Departure",
                "is_hotspot":     "High-Risk Junction"
            })

            st.dataframe(
                display.style.apply(highlight_hotspot, axis=1),
                use_container_width=True,
                hide_index=True,
                height=400
            )
    else:
        st.info("Type a train name or number above to explore its route.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Indian Railway Delay Genome | Data: Indian Railways timetable (Kaggle) | "
    "Graph analysis: Neo4j AuraDB | Built with Streamlit + Plotly"
)
