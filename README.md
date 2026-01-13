# Edge Path Bundling  
*An Interactive Dash Application*

*Authors:* Clara Pichler, Paul Schmitt  
*Course:* 193.166 Visualization, TU Vienna  
*Year:* 2025  

---

## Project Overview

Graph visualizations often suffer from *edge clutter*: when many edges overlap, the structure of the graph becomes hard to understand.

A common solution is *edge bundling*, where similar edges are grouped together to reduce visual clutter. However, many existing edge bundling techniques distort edges so strongly that it becomes unclear where connections start and end.

This project is based on the paper  
*"Edge-Path Bundling: A Less Ambiguous Edge Bundling Approach"* by Wallinger et al. (2022).

Instead of arbitrarily deforming edges, *Edge-Path Bundling (EPB)* routes each edge along a *weighted shortest path* in an overlay graph. This preserves interpretability while still achieving effective bundling.

---

## Our Contribution

- Reimplementation of the *Edge-Path Bundling (EPB)* algorithm in *Python*
- Validation using the same (or very similar) 2D datasets as the original paper
- Extension of EPB to *higher-dimensional data*
- Introduction of a *3D brain connectivity dataset*
- Adaptation of distance metrics:
  - *Haversine distance* for geospatial datasets
  - *Euclidean distance* for 3D brain data
- Development of an *interactive Dash application* allowing:
  - Dataset selection
  - Interactive parameter tuning
  - Real-time visualization updates
  - Bézier curve smoothing to control bundling strength

---

## Datasets

### Air Traffic
- Global flight routes between airports
- *1,533 nodes, 14,825 directed edges*
- One connected component
- Source: OpenFlights
- Distance metric: *Haversine*

### Migration Flows
- Migration outflows between U.S. counties
- Based on U.S. Census Bureau data
- Similar to the dataset used in the original paper
- Distance metric: *Haversine*

### Brain Connectivity
- MRI-derived connectomes from the Human Connectome Project
- Nodes represent brain regions
- Edges represent structural connections
- One Scale 2 connectome (~80–100 regions)
- Distance metric: *Euclidean*

---

## How to Run

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the application

Either run:

```bash
python run_dashboard.py
```

or:

```bash
python src/dashboard/app.py
```

Then open your browser and navigate to `http://localhost:8050` to view the interactive dashboard.

---

## Project Structure

```
├── src/
│   ├── core/
│   │   └── bundling.py          # Core edge bundling algorithm
│   ├── data_loader/
│   │   ├── air_traffic.py       # Airport and route data loader
│   │   ├── brain_connectivity.py # Brain connectivity data loader
│   │   └── migration.py         # Migration flow data loader
│   ├── dashboard/
│   │   └── app.py              # Interactive Dash application
│   └── visualization/
│       ├── curves.py           # Bézier curve generation
│       └── plotly_renderer.py  # Visualization rendering
├── data/                       # Dataset files
├── documentation/              # Project documentation
├── requirements.txt            # Python dependencies
└── README.md                  # This file
```

---

## Algorithm Parameters

- **k (Distortion Threshold)**: Controls the maximum allowed detour ratio (1.0 - 10.0)
  - Higher values allow more bundling but increase path distortion
- **d (Edge Weight Factor)**: Exponent for edge length weighting (0.5 - 3.0)  
  - Higher values prioritize longer edges for bundling
- **Smoothing Level**: Controls Bézier curve smoothness (1 - 4)
  - Higher values create smoother curves but increase computation time

---

## HTML Page

For detailed code documentation and a demo, see https://claraelisabeth.github.io/Visualization-193.166/documentation/code_documentation.html.

---

## References

Wallinger, M., Archambault, D., Auber, D., Beck, F., Dwyer, T., Günther, W., ... & Hurter, C. (2022). Edge-path bundling: A less ambiguous edge bundling approach. *IEEE Transactions on Visualization and Computer Graphics*.