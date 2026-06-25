# Buffalo Box Tools - ArcGIS Pro Python Toolbox

A custom ArcGIS Pro Python Toolbox (`.pyt`) designed to automate the spatial placement and attribute updating of water service buffalo boxes (b-boxes). 

This tool calculates the exact geographic location of a buffalo box based on physical tie-card measurements from a house corner and the street curb, streamlining utility data updates and editing workflows.

## Features
* **Coordinate Geometry Calculation:** Automatically calculates the new X/Y location based on offset distances from specified corner and curb coordinates.
* **Batch Processing:** Allows a GIS technician or analyst to move and update up to 10 buffalo boxes in a single tool execution.
* **Attribute Management:** Simultaneously updates key feature attributes, including `DIAMETER`, `MATERIAL`, and `NOTES`, mapping them to your schema.
* **Coordinate Parsing:** Cleans and parses standard coordinate strings copied directly from the ArcGIS Pro map display.

## Coordinate System Note
This script was originally developed with the **City of Elgin, IL** and **Illinois State Plane (US Feet)** in mind. However, because it relies on the spatial reference of the input feature layer, it will dynamically adapt to the coordinate system of your active map and data.

## Requirements
* ArcGIS Pro
* Basic, Standard, or Advanced License
* A point feature class representing buffalo boxes/water valves with editable geometry

## Installation
1. Clone or download this repository to your local machine.
2. Open your ArcGIS Pro project.
3. In the **Catalog** pane, right-click **Toolboxes** > **Add Toolbox**.
4. Navigate to the downloaded folder and select `BuffaloBox.pyt`.

## How to Use
1. **Select Features:** Using the Select tool in ArcGIS Pro, select the buffalo box point(s) you want to move. You must select the exact number of boxes you plan to fill out in the tool (up to 10).
2. **Open the Tool:** Double-click **Move Buffalo Boxes (1 to 10)** in the Catalog pane.
3. **Select Layer:** Choose your buffalo box feature layer from the drop-down.
4. **Input Measurements:** For each box you are moving:
   * **Corner Coordinates:** Right-click the house corner on the map, copy the coordinates, and paste them into the tool.
   * **Corner ID:** Select which corner it is (e.g., SE Corner).
   * **Distance:** Enter the measured distance from the corner in feet.
   * **Curb Coordinates:** Right-click the curb perpendicular to the box, copy the coordinates, and paste them into the tool.
   * **Curb Direction & Distance:** Enter the distance from the curb and the direction toward the house.
   * **Attributes:** Select the material, enter the diameter, and add any notes.
5. **Run:** Click Run. The tool will calculate the exact intersection of these offsets, snap the point to the new location, and update the table.

## Acknowledgments
* Initial script logic and structure generated with the assistance of Claude (Anthropic).
