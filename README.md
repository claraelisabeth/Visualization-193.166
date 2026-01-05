# Visualization-193.166
Repository for the TU Vienna Course Visualization

Graph visualizations often face the problem of *edge clutter*: when you draw many edges between nodes, the drawing becomes messy, overlapping edges, and visual clutter. One popular remedy is **edge bundling**, which groups (or “bundles”) edges that are spatially or directionally similar, making the drawing cleaner.

However, conventional edge bundling techniques (force-directed bundling, geometry-based bundling, confluent drawings) introduce **ambiguities**: by bundling edges, you lose clarity about which individual edge goes where, and intersections or overlaps can mislead the viewer.

The paper *“Edge-Path Bundling: A Less Ambiguous Edge Bundling Approach”* by Wallinger et al. (2021) (https://arxiv.org/pdf/2108.05467) proposes a new bundling method, **Edge-Path Bundling (EPB)**, which aims to reduce such ambiguities while still cleaning up the visual clutter. The key idea: rather than arbitrarily deforming edges into bundles, each edge is guided along a *weighted shortest path* in a constructed graph (overlay) so that deviations from the straight line are minimized and interpretability is preserved.  
They show EPB can be tuned (degree of bundling) and even handle directed edges naturally. Through quantitative metrics and visual examples, they compare EPB to previous bundling approaches and argue its superiority in reducing ambiguity while maintaining bundling benefits.


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

For the EPB we need a list of 3D coordinates for each node, edges as pairs of node indices and a weight for each connection.
As for the weight we chose `number_of_fibers`. It reflects the strength of the connection, and it’s positive, simple, and standard.



## How to Run

To run the dash application you can either use
```
python src/dashboard/app.py
```
or 
```
python run_dashboard.py
```



## TODO

- 












---

# Notes for us
Important dates:  
29.10.24 - Topic Presentation Submission  
30.10.24 - Topic Presentation  
5.11.24 - Project proposal submission (summary of implementation idea)  
3.12.24 -	Intermediate submission (voluntary)  
7.01.25 -	Final submission: presentation & program   
8.01.25 & 15.01.25 - Presentation  
22.01.25 - Submission Talks (date picker/schedule to be announced)

## Task Description
The task is to implement a state-of-the-art interactive visualization technique in a group of two (you can use the group finder to find a partner!). There are three principle approaches how to address the project: 

- Select an article describing a state-of-the-art visualization algorithm (e.g., from our paper list). Implement the technique in a different programming language (e.g., using WebGPU instead of d3) or in a different environment (e.g., in virtual or augmented reality) than the reference solution from the paper. The focus lies on the quality (e.g., performance, visual result, usability) of the implemented algorithm compared to the reference paper. 
- Select a state-of-the-art visualization technique for which an open source implementation exists and **adapt or extend** it. Examples could be a generalization of the technique to other data types, increasing the scalability of the system, or **adding new interaction techniques**. The focus lies on the technical quality (e.g., performance, robustness against different data characteristics) and / or creativity of the implemented extension.  
- Select a challenging data set (e.g., large or complex) and visualize it using a state-of-the-art visualization technique (e.g., re-implementing one of our provided papers). The focus lies on a creative (interactive) solution and a robust system. 
It is up to you how you implement this exercise, no requirements on the programming language, libraries, or development environment are given. This could be an opportunity to try new technology!

Original Paper: https://arxiv.org/pdf/2108.05467   
2024: https://github.com/eliasfuericht/Atmospheric-Edge-Path-Bundling  
2023: https://immersive-edge-path.emanum.dev/   
2022: https://www.cg.tuwien.ac.at/courses/Vis2/HallOfFame/2022S/Hoefler/index.html  
Survey by TU Graz Students: https://courses.isds.tugraz.at/ivis/surveys/ss2017/ivis-ss2017-g4-survey-edge-bundling.pdf   
GGRAPH: https://ggraph.data-imaginist.com/reference/geom_edge_bundle_path.html   

## Further Information
Each project must include a README.md file in the submission repository. The README should explain:
- The goal of your project and which visualization technique you implemented.
- A summary of the re-implemented / extended algorithm / technique. 
- How to install and run your code (dependencies, setup instructions).
- A short usage guide (e.g., which parameters can be adjusted, how to interact with the system).
- References to the original paper(s) and other resources you used.
You may also include screenshots, small demo videos, or example data sets to showcase your results.

Link for useful possible tools: https://www.cg.tuwien.ac.at/courses/Vis2/resources

References to previous work:
- https://www.cg.tuwien.ac.at/courses/Vis2/HallOfFame/
- https://gan-disentanglement.vercel.app/
- https://www.cg.tuwien.ac.at/courses/Vis2/HallOfFame/2022S/KimmersdorferAndHuerbe/index.html
- https://www.cg.tuwien.ac.at/courses/Vis2/HallOfFame/2024/Other%20Topic%201/html/index.html

### Grading
Grading criteria of the final implementation: 
- Quality of the algorithm as implemented in the reference paper
- Visual result
- Feature-richness / interactivity (very basic implementation vs. many parameters to tune) 
- Generalizability (supports just one trivial data set vs. supports multiple data sets) 
- Performance
- Creativity concerning extensions of the selected technique
- Usability
The weighting of these aspects depends on the scope of the chosen project. 

Point deductions: 
- Exceptionally poor code quality (max. 5 points deduction) 
- Late submissions (-10% for every delayed day)




