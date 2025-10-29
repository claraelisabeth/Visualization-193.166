# Visualization-193.166
Repository for the TU Vienna Course Visualization

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

---

## Summary

A summary of the paper *“Edge-Path Bundling: A Less Ambiguous Edge Bundling Approach”* by Wallinger et al. (2021) https://arxiv.org/pdf/2108.05467 

### Short Summary

Graph visualizations often face the problem of *edge clutter*: when you draw many edges between nodes, the drawing becomes messy, overlapping edges, and visual clutter. One popular remedy is **edge bundling**, which groups (or “bundles”) edges that are spatially or directionally similar, making the drawing cleaner.

However, conventional edge bundling techniques (force-directed bundling, geometry-based bundling, confluent drawings) introduce **ambiguities**: by bundling edges, you lose clarity about which individual edge goes where, and intersections or overlaps can mislead the viewer.

This paper proposes a new bundling method, **Edge-Path Bundling (EPB)**, which aims to reduce such ambiguities while still cleaning up the visual clutter. The key idea: rather than arbitrarily deforming edges into bundles, each edge is guided along a *weighted shortest path* in a constructed graph (overlay) so that deviations from the straight line are minimized and interpretability is preserved.  
They show EPB can be tuned (degree of bundling) and even handle directed edges naturally. Through quantitative metrics and visual examples, they compare EPB to previous bundling approaches and argue its superiority in reducing ambiguity while maintaining bundling benefits.


### EPB Method

* Take an existing layout (positions of nodes + straight-line edges) as input (so EPB is a *post-processing* bundling method).
* Overlay a *routing graph* (a geometric graph) over the layout, with nodes and edges (the overlay nodes are like “junctions” through which edges can pass).
* For each original edge (from node A to B), compute a **weighted shortest path** in this routing graph from A to B. The weight formulation combines *Euclidean distance* and *geodesic (overlay) distance* so edges prefer to stick near straight line, but can deviate if bundling is beneficial.
* By clustering edges to shared overlay segments, bundling emerges. However, because edges are guided by shortest path, the ambiguity (like edge crossing overlap or unclear mapping) is minimized.
* They provide control parameters to adjust *how strongly* edges are pulled into bundles (how much deviation is allowed), e.g. weights, thresholds.
* For *directed edges*, the shortest path approach naturally supports directionality (you can prefer directed flows in the overlay).

Some deeper insights:

**Routing Graph / Overlay Construction**
To allow edges to bend and bundle, EPB overlays a graph over the plane. The nodes of this overlay graph may be grid points, strategically placed junctions, or other geometric points. Edges of the overlay link these junctions. The original graph’s nodes are connected to the nearest overlay nodes (or inserted into the overlay). So every original edge becomes a path through this overlay.

**Weighting / Cost Function**  
  The cost for traversing overlay edges is not uniform. It is defined as a combination:

  $$
  c(e) = \alpha \cdot d_{\text{Euclidean}} + \beta \cdot d_{\text{overlay}}
  $$

  where $(d_{\text{Euclidean}})$ is (roughly) how far from the straight-line path the overlay edge deviates, and $(d_{\text{overlay}})$ is the intrinsic overlay distance. The parameters $\alpha$, $\beta$ (or equivalent) allow you to adjust how strictly the edge stays straight vs how much it gets pulled into a bundle.

**Shortest Path for Each Edge**  
  For each original edge, compute a shortest path in the overlay graph from its source to its target, with the above cost metric. Because many edges may share parts of the overlay, bundling arises naturally: common subpaths are reused.

**Ambiguity Avoidance**  
  Because each edge has a “preferred route” (the shortest path), there is a clearer mapping from original edge to visual route — you avoid arbitrary bending that hides which edge is which. Also, by limiting the deviation cost, edges that diverge too much are disfavored, so overlap is controlled.

**Directed Edges**  
  If edges have direction, they can influence the shortest path search (e.g. only allow overlay traversal consistent with direction, or weight forward vs backward differently). So EPB can handle directionality in bundling.

**Parameter Tuning / Bundling Strength**  
  The user can adjust how strongly bundling is enforced (i.e. how willing edges are to deviate). If bundling strength is low, edges remain close to their original straight-line. If stronger, more edges will share overlay subpaths. It’s a trade-off between clutter reduction and preserving interpretability.

**Ambiguity and Metrics**  
*Ambiguity*:   e.g. where two edges cross or overlap in a way that the viewer can’t tell which one is which
*Ambiguity Metrics*:   




### Cheat Sheet Summary 

| Aspect            | Description                                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------------- |
| Problem addressed | Edge clutter + ambiguity in graph drawings                                                                    |
| Proposed method   | **Edge-Path Bundling (EPB)**                                                                                  |
| Core idea         | Overlay a routing graph; for each edge, compute a weighted shortest path (balancing straightness vs bundling) |
| Key benefit       | Reduces ambiguity (overlaps, confusion) compared to many existing bundling methods                            |
| Control           | Parameters allow tuning bundling strength vs deviation                                                        |
| Directed edges    | Naturally supported                                                                                           |
| Evaluation        | Visual examples + ambiguity metrics show EPB outperforms baseline bundling methods in many cases              |
| Limitations       | Computational cost, parameter sensitivity, overlay design, scalability                                        |
| Best use cases    | Graphs where edge traceability matters but clutter needs mitigation                                           |


