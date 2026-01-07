# Edge Path Bundling  
**An Interactive Dash Application**

**Authors:** Clara Pichler, Paul Schmitt  
**Course:** 193.166 Visualization, TU Vienna  
**Year:** 2026  

---

## Project Overview

Graph visualizations often suffer from **edge clutter**: when many edges overlap, the structure of the graph becomes hard to understand.

A common solution is **edge bundling**, where similar edges are grouped together to reduce visual clutter. However, many existing edge bundling techniques distort edges so strongly that it becomes unclear where connections start and end.

This project is based on the paper  
**_“Edge-Path Bundling: A Less Ambiguous Edge Bundling Approach”_** by Wallinger et al. (2021).

Instead of arbitrarily deforming edges, **Edge-Path Bundling (EPB)** routes each edge along a **weighted shortest path** in an overlay graph. This preserves interpretability while still achieving effective bundling.

---

## Our Contribution

- Reimplementation of the **Edge-Path Bundling (EPB)** algorithm in **Python**
- Validation using the same (or very similar) 2D datasets as the original paper
- Extension of EPB to **higher-dimensional data**
- Introduction of a **3D brain connectivity dataset**
- Adaptation of distance metrics:
  - **Haversine distance** for geospatial datasets
  - **Euclidean distance** for 3D brain data
- Development of an **interactive Dash application** allowing:
  - Dataset selection
  - Interactive parameter tuning
  - Real-time visualization updates
  - Bezier curve smoothing to control bundling strength

---

## Datasets

### Air Traffic
- Global flight routes between airports
- **1,533 nodes**, **14,825 directed edges**
- One connected component
- Source: OpenFlights
- Distance metric: **Haversine**

### Migration Flows
- Migration outflows between U.S. counties
- Based on U.S. Census Bureau data
- Similar to the dataset used in the original paper
- Distance metric: **Haversine**

### Brain Connectivity
- MRI-derived connectomes from the Human Connectome Project
- Nodes represent brain regions
- Edges represent structural connections
- One Scale 2 connectome (~80–100 regions)
- Distance metric: **Euclidean**

---

## How to Run

### Install dependencies

```bash
pip install -r requirements.txt
```
Run either

```bash
python run_dashboard.py
```

or
```bash
python src/dashboard/app.py
```