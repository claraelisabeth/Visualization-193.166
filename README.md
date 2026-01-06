# Edge Path Bundeling
Repository for the TU Vienna Course 193.166 Visualization

Graph visualizations often face the problem of *edge clutter*: when you draw many edges between nodes, the drawing becomes messy, overlapping edges, and visual clutter. One popular remedy is **edge bundling**, which groups (or “bundles”) edges that are spatially or directionally similar, making the drawing cleaner.

However, conventional edge bundling techniques (force-directed bundling, geometry-based bundling, confluent drawings) introduce **ambiguities**: by bundling edges, you lose clarity about which individual edge goes where, and intersections or overlaps can mislead the viewer.

The paper *“Edge-Path Bundling: A Less Ambiguous Edge Bundling Approach”* by Wallinger et al. (2021) (https://arxiv.org/pdf/2108.05467) proposes a new bundling method, **Edge-Path Bundling (EPB)**, which aims to reduce such ambiguities while still cleaning up the visual clutter. The key idea: rather than arbitrarily deforming edges into bundles, each edge is guided along a *weighted shortest path* in a constructed graph (overlay) so that deviations from the straight line are minimized and interpretability is preserved.  
They show EPB can be tuned (degree of bundling) and even handle directed edges naturally. Through quantitative metrics and visual examples, they compare EPB to previous bundling approaches and argue its superiority in reducing ambiguity while maintaining bundling benefits.


## Our Contribution

In this project, we reimplemented the core Edge-Path Bundling (EPB) algorithm proposed by Wallinger et al. in Python. The main motivation was to fully understand the method by rebuilding it from scratch and to verify that our implementation behaves similarly to the reference approach. To do this, we first applied our implementation to the same two-dimensional datasets used in the original paper, which allows for a direct comparison and helps validate correctness.

Beyond reimplementation, we extended EPB to work with additional data types and higher-dimensional data. In particular, we introduce a new dataset based on human brain connectomes, which naturally live in three-dimensional space. Working with 3D data posed new challenges and offered interesting insights into how the algorithm behaves outside of a planar setting. We also adapted the distance computation depending on the dataset: while Euclidean distance is used for the 3D brain data, we rely on the haversine distance for geospatial datasets to properly account for the curvature of the Earth.

To make the results easier to explore, we built an interactive Dash application that visualizes the bundled graphs. The interface allows users to select a dataset and interactively adjust key EPB parameters such as the maximum distortion threshold k and the edge weight factor. This makes it possible to explore the effect of different parameter choices in real time and compare how edge-path bundling behaves across datasets. Finally, we provide a dedicated section describing all datasets used in the project to make the workflow and data sources transparent.




## Data

### Airtraffic

The **Air Traffic** dataset consists of global flight routes between airports. It includes $|V| = 1533$ vertices (airports) and $|E| = 14825$ directed edges (routes), forming one connected component. The dataset is publicly available as part of the \textit{OpenFlights} project (https://openflights.org/data.php).


### Migration

The **Migration Flows** dataset represents directed migration flows between US counties. The version used in the original paper has approximately $|V| = 1702$ vertices and $|E| = 9726$ directed edges. The dataset is publicly available from the US Census Bureau https://www.census.gov/data/tables/2000/demo/geographic-mobility/county-to-county-migration-flows.html.


### Brain Connectivity

**Human Connectome Project (HCP)**(https://www.humanconnectome.org/study/hcp-young-adult/data-releases):   
The connectomes were generated from MRI scans obtained from the Human Connectome Project. Undirected and directed versions of the brain graphs are available. The direction of these graphs was defined using edge frequency analysis. Graphs with up to 1058 nodes. This can be downloaded at https://braingraph.org/download-pit-group-connectomes/.

We consider one graph from Scale2: *sub-OAS31172_ses-d1717_atlas-L2018_res-scale2_conndata-network_connectivity.graphml*
- sub-OAS31172 = subject ID
- ses-d1717 = session ID
- atlas-L2018 = the brain atlas used (Lausanne 2018)
- res-scale2 = resolution = 2 (≈ 83–100 regions)
- network_connectivity.graphml = GraphML file containing the connectome

Each node is a brain region and edges represent structural connections between brain regions.




## How to Run

The needed libraries are all included in the requirements.txt file. One can install everything through
```
pip install -r requirements.txt
```

To run the Dash application you can either use. 
```
python src/dashboard/app.py
```  
or   
```
python run_dashboard.py
```  
then you just go to http://127.0.0.1:8050/ where you can see the following UI.

--insert image--

On the right side one can see a graph which can be changed throughthe _Parameter Control_ on the left side. You can choose one out of three datasets, the maximum detour ratio _k_ and the edge weight factor _d_. 




## Discussion and Future Work

We managed building an interactive application with multiple parameters to control as well as switching between datasets. We consider 2D as well as 3D data. However the rendering time is sadly a bit too long. this we tried to fight however we think it is still possible to make it more efficient.





## References
- dataset links
- original paper link
- source code github repository
- code documentation













---

# add somewhere where it fits

- Overall, Edge-Path bundling has a worst case time complexity of $O(|E|^2log|V|)$ as the Dijkstra algorithm (priority queue heap implementation) runs $O(|E|)$ times. However, the distortion threshold $k$ can be used to stop Dijkstra’s algorithm once this threshold is exceeded, reducing the chance that this worst case complexity is observed.
- 







