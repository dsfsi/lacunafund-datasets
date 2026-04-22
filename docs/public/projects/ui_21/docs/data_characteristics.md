For access and use, see Zenodo link to the left.

The dataset was developed through an integrative data collection and validation approach:

Wall-to-Wall Labeling:
Training data was created through opportunistic sampling across 6x6 km grids overlapping known oil palm regions. Labels were digitized in QGIS and refined through multi-spectral analysis of Planet NICFI imagery from corresponding months. The land cover classification followed a two-tiered typology covering estate crops (e.g., oil palm, rubber, coconut), annual crops, forests, shrubland, wetlands, and other land uses.

Satellite Imagery Pairing:
Each labeled grid is paired with PlanetScope monthly composite images clipped to grid extent. These cloud-minimized mosaics are consistent with the date of interpretation to support supervised machine learning training.

Validation Dataset (CEO):
A stratified random sampling method was applied to generate verification points across diverse land cover classes. Interpreters labeled points in CEO using a standardized survey form and high-resolution imagery. Twenty percent of samples were cross-verified by multiple interpreters to calculate agreement scores as part of QA/QC procedures. Select ambiguous classes were also validated through targeted field checks.

Metadata and Format:
All spatial layers are delivered in GeoJSON format, accompanied by metadata following ISO 19115 standards. Image tiles are delivered as GeoTIFFs, pre-aligned to vector boundaries.

Data Type:

Vector spatial dataset (Polygons, WKT), tabular metadata (.csv/.geojson), JSON-compatible attributes, raster images (GeoTIFF)