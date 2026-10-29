<p align="center"><img src="docs/assets/header.svg" alt="GridSite: where can an electric truck depot actually get power?" width="100%"></p>

<p align="center">
  <a href="https://github.com/aryaMehta26/gridsite/actions/workflows/ci.yml"><img src="https://github.com/aryaMehta26/gridsite/actions/workflows/ci.yml/badge.svg" alt="tests"></a>
  <a href="https://github.com/aryaMehta26/gridsite/actions/workflows/refresh.yml"><img src="https://github.com/aryaMehta26/gridsite/actions/workflows/refresh.yml/badge.svg" alt="weekly refresh"></a>
  <img src="https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/data-OpenStreetMap%20(ODbL)-7ebc6f?logo=openstreetmap&logoColor=white" alt="OpenStreetMap data">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="Apache 2.0"></a>
</p>

**GridSite scores every sizeable industrial site in the San Francisco Bay Area and the Stockton / Central Valley freight corridor on one question: if you wanted to charge a fleet of electric trucks here, how close is the power?** It pulls public grid data every week, ranks 1,390 sites, and publishes the result as a map anyone can click through.

[🗺️ Open the live map](https://aryamehta26.github.io/gridsite/) · [📄 Download the scores (CSV)](data/processed/sites_scored.csv) · [Run it yourself](#run-it) · [How a site is scored](#how-a-site-is-scored)

<p align="center">
  <a href="https://aryamehta26.github.io/gridsite/"><img src="docs/img/interactive_map.png" alt="GridSite interactive map of the Bay Area and Stockton" width="100%"></a>
  <br><sub>Green dots are the best sites, dark-blue diamonds are high-voltage substations. Click the image for the live map.</sub>
</p>

## The 30-second version

An electric truck depot isn't limited by chargers. It's limited by **power**. Charging dozens of trucks overnight takes megawatts, about as much as a small neighborhood, and the cheapest, fastest way to get that much power is to build **right next to the high-voltage grid**. Build far from it and you can wait years and pay millions for new lines.

So the first question in picking a depot site is a map question: **which empty industrial lots sit close to a big substation *and* close to the freeway the trucks already drive?**

GridSite answers that for two regions, using only public data, and refreshes the answer every Monday:

| | |
|---|---|
| 🏭 Industrial sites scored | **1,390** (≥ ~2 acres; power plants and hazardous uses excluded) |
| ⚡ Substations mapped | **536**, of which **184** are high-voltage (≥ 115 kV) |
| 🛣️ Freeway exits checked | **1,591** |
| 📏 Typical distance from a site to the high-voltage grid | **2.05 km** (median) |
| ✅ Automated tests | **28**, run on every change |
| 🔄 Data refresh | **weekly**, automatically |

<sub>From the run on 2026-10-28. Every refresh rewrites [`summary.json`](data/processed/summary.json).</sub>

## What it found

**The Bay Area is grid-rich and Stockton looks grid-poor.** That's the headline:

| Region | Sites | High-voltage substations | Typical distance to one | Median score | Top-tier sites |
|---|---:|---:|---:|---:|---:|
| 🌉 Bay Area | 912 | 168 | **1.67 km** | 77.0 | **136** |
| 🚚 Stockton / Central Valley | 478 | 16 | **3.49 km** | 65.5 | **5** |

Stockton is one of the most important freight hubs in California, exactly where fleets will electrify, yet the public map shows **10× fewer high-voltage substations** and **twice the distance** to reach one. Either that's a real constraint on electrifying Central Valley freight, or OpenStreetMap is missing substations there. Either way, it's the first thing to check against the utility's own maps.

**The best sites cluster along the transmission backbone:**

| Rank | Score | Next to | Voltage | To the substation | To a freeway exit |
|---:|---:|---|---:|---:|---:|
| 1 | 93.9 | Metcalf Substation, south San José | 500 kV | 0.41 km | 0.76 km |
| 2 | 93.8 | Las Positas Substation, Livermore | 230 kV | 0.25 km | 0.20 km |
| 3 | 93.1 | Contra Costa Substation | 230 kV | 0.09 km | 0.51 km |
| 4 | 92.6 | Northern Receiving Station, Santa Clara | 230 kV | 0.09 km | 0.45 km |
| 5 | 92.2 | Contra Costa Power Plant Substation | 230 kV | 0.80 km | 0.13 km |

Every one of the top five is **within a kilometer of a 230–500 kV substation *and* under a kilometer from a freeway exit.**

<p align="center">
  <img src="docs/img/grid_vs_access.png" width="49%" alt="Grid distance vs truck access, colored by tier">
  <img src="docs/img/score_distribution.png" width="49%" alt="Distribution of site scores">
</p>
<p align="center">
  <img src="docs/img/substations_by_voltage.png" width="60%" alt="Substations by highest voltage">
</p>
