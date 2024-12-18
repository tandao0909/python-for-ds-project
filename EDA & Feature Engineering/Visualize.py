import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# for creating a map
import folium 

 # for reading shapefiles
import fiona

from haversine import haversine
from sklearn.cluster import KMeans

# for creating a color map
from branca.colormap import LinearColormap

# for checking if a point is within a polygon, Point is a class to represent a point, shape is a function to create a polygon from a GeoJSON object
from shapely.geometry import Point, shape
from folium.plugins import HeatMap

def check_coordinates_in_vietnam(shapefile_path: str, housing_df: pd.DataFrame) -> pd.DataFrame:
    """
    Check if the coordinates in the housing DataFrame are within Vietnam's territory.

    Parameters:
        shapefile_path (str): The path to the shapefile containing the territory of Vietnam.
        housing_df (pd.DataFrame): The DataFrame containing the housing data.

    Returns:
        pd.DataFrame: The DataFrame containing the housing data with coordinates within Vietnam's territory.
    """
    # List of coordinates to check
    coordinates_list = [
        (longitude, latitude)
        for longitude, latitude
        in zip(housing_df['longitude'], housing_df['latitude'])
    ]

    # Open the shapefile and get the polygon representing Vietnam's territory
    with fiona.open(shapefile_path) as shp:
        geometries = [shape(feature['geometry']) for feature in shp]
        vietnam_shape = geometries[0]  # Vietnam shape is the first feature in the shapefile

    # Filter out coordinates within Vietnam's territory
    coordinates_in_vietnam = [
        coordinate
        for coordinate in coordinates_list
        if Point(coordinate).within(vietnam_shape)
    ]

    # Indices of coordinates within Vietnam's territory
    indices_in_vietnam = housing_df[['longitude', 'latitude']].apply(tuple, axis=1).isin(coordinates_in_vietnam)

    # Return the housing data with coordinates within Vietnam's territory
    return housing_df[indices_in_vietnam]

class RealEstateVisualizerPrice:
    """
    A class to visualize real estate data on a map based on price.
    
    Attributes:
        housing (pd.DataFrame): The DataFrame containing the real estate data.
        colormap (LinearColormap): The color map for the real estate prices.

    Methods:
        add_markers: Add markers for each real estate with color based on price.
        create_map: Create a folium map with real estate data.
    """
    def __init__(self, housing_df: pd.DataFrame) -> None:
        """
        Initialize the RealEstateVisualizer object.

        Parameters:
            housing_df (pd.DataFrame): The DataFrame containing the real estate data.
        """
        self.housing = housing_df
        self.colormap = LinearColormap(
            ['green', 'blue', 'orange', 'red', 'purple', 'brown', 'black'],
            vmin=self.housing['price'].min(),
            vmax=self.housing['price'].max()
        )

    def add_markers(self, gmap: folium.Map) -> None:
        """
        Add markers for each real estate with color based on price.

        Parameters:
            gmap (folium.Map): The folium map object.
        """
        for _, row in self.housing.iterrows():
            marker_color = self.colormap(row['price'])
            popup_content = f"Giá: {row['price']}"
            folium.CircleMarker(
                location=(row['latitude'], row['longitude']),
                radius=5,
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                popup=popup_content 
            ).add_to(gmap)

    def create_map(self) -> folium.Map:
        """
        Create a folium map with real estate data.

        Returns:
            folium.Map: The generated folium map.
        """
        gmap = folium.Map(location=[21.028511, 105.804817], zoom_start=6)
        self.colormap.add_to(gmap)
        self.add_markers(gmap)
        return gmap
    
class RealEstateVisualizerCluster:
    """
    A class to visualize real estate data on a map.

    Attributes:
        housing (pd.DataFrame): The DataFrame containing the real estate data.
        num_clusters (int): The number of clusters for KMeans clustering.
        colormap (LinearColormap): The color map for the real estate prices.
        cluster_centers (np.ndarray): The coordinates of the cluster centers.
        cluster_radius (List[float]): The radius of the clusters.

    Methods:
        fit_kmeans: Fit a KMeans model to the real estate data and add cluster labels to the DataFrame.
        calculate_cluster_radius: Calculate the radius of the clusters.
        add_cluster_visualization: Add cluster visualization to the map.
        add_markers: Add markers for each real estate with color based on price.
        create_map: Create a folium map with real estate data and cluster visualization.
    """
    def __init__(self, housing_df:pd.DataFrame, num_clusters:int=5) -> None:
        """
        Initialize the RealEstateVisualizer object.

        Parameters:
            housing_df (pd.DataFrame): The DataFrame containing the real estate data.
            num_clusters (int): The number of clusters for KMeans clustering, default is 5.

        Returns:
            RealEstateVisualizer: The RealEstateVisualizer object.
        """
        self.housing = housing_df
        self.num_clusters = num_clusters
        self.cluster_colormap = LinearColormap(
            ['green', 'blue', 'orange', 'red', 'purple', 'brown', 'black'],
            vmin=0,
            vmax=num_clusters - 1
        )
        self.cluster_centers = None
        self.cluster_radius = None

    def fit_kmeans(self) -> None:
        """
        Fit a KMeans model to the real estate data and add cluster labels to the DataFrame.
        """
        clustering_features = self.housing[['latitude', 'longitude']] # Choose the clustering features
        self.num_clusters = self.elbow_method(clustering_features)
        kmeans = KMeans(n_clusters=self.num_clusters, random_state=0).fit(clustering_features)
        self.cluster_centers = kmeans.cluster_centers_ # Get the cluster centers
        self.housing['Cluster'] = kmeans.labels_ # Add the cluster labels to the housing DataFrame
        self.distance_to_center(self.housing)
        self.calculate_cluster_radius()

    def elbow_method(self, clustering_features:pd.DataFrame) -> np.ndarray:
        """
        Find the optimal number of clusters using the elbow method.

        Parameters:
            clustering_features (pd.DataFrame): The features used for clustering.

        Returns:
            np.ndarray: The coordinates of the cluster centers.
        """
        distortions = []
        K = range(1, 11)
        for k in K:
            kmeans = KMeans(n_clusters=k, random_state=0).fit(clustering_features)
            distortions.append(kmeans.inertia_)
            
        # plt.figure(figsize=(16,8))
        plt.plot(K, distortions, 'bx-')
        plt.xlabel('k')
        plt.ylabel('Distortion')
        plt.title(f'The Elbow Method showing the optimal $k$')
        plt.show()

        diff = np.diff(distortions)
        return abs(diff).argmax() + 2
    
    def distance_to_center(self, housing:pd.DataFrame) -> None:
        """
        Calculate the distance of each real estate to the cluster center.

        Parameters:
            housing (pd.DataFrame): The DataFrame containing the real estate data.
        """
        for idx, center in enumerate(self.cluster_centers):
            housing[f'Distance to center {idx}'] = housing.apply(
                lambda row: haversine(center, (row['latitude'], row['longitude'])),
                axis=1
            )

    def calculate_cluster_radius(self) -> None:
        """
        Calculate the radius of the clusters, which is the distance from the cluster center to the farthest point in the cluster.
        """
        self.cluster_radius = [
            max(
                haversine(center, (point.latitude, point.longitude))
                for point in self.housing[self.housing['Cluster'] == idx].itertuples() # itertuples is a function to iterate through the DataFrame as tuples
            )
            for idx, center in enumerate(self.cluster_centers)
        ]
    
    def add_markers(self, gmap: folium.Map) -> None:
        """
        Add markers for each real estate with color based on price.

        Parameters:
            gmap (folium.Map): The folium map object.
        """
        for _, row in self.housing.iterrows():
            cluster_label = row['Cluster']
            marker_color = self.cluster_colormap(cluster_label)
            popup_content = f"Giá: {row['price']}, Cụm: {cluster_label}"
            folium.CircleMarker(
                location=(row['latitude'], row['longitude']),
                radius=5,
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                # popup is the text that appears when you click on the marker
                popup=popup_content 
            ).add_to(gmap)

    def create_map(self) -> folium.Map:
        gmap = folium.Map(location=[21.028511, 105.804817], zoom_start=6)
        self.cluster_colormap.add_to(gmap)
        self.add_markers(gmap)
        return gmap

class RealEstateVisualizerHeatmap:
    """
    A class to visualize real estate data on a heatmap based on price.
    
    Attributes:
        housing (pd.DataFrame): The DataFrame containing the real estate data.

    Methods:
        add_heatmap: Add heatmap for the real estate data.
        create_map: Create a folium map with real estate data.
    """
    def __init__(self, housing_df: pd.DataFrame) -> None:
        """
        Initialize the RealEstateVisualizerHeatmap object.

        Parameters:
            housing_df (pd.DataFrame): The DataFrame containing the real estate data.
        """
        self.housing = housing_df

    def add_heatmap(self, gmap: folium.Map) -> None:
        """
        Add a heatmap layer for the real estate data.

        Parameters:
            gmap (folium.Map): The folium map object.
        """
        # Prepare the data for the heatmap (latitude, longitude, price)
        heat_data = [
            [row['latitude'], row['longitude'], row['price']] for _, row in self.housing.iterrows()
        ]
        HeatMap(
            heat_data, 
            min_opacity=0.5,  
            max_val=self.housing['price'].max(),
            radius=20,  
            blur=10,
        ).add_to(gmap)

    def create_map(self) -> folium.Map:
        """
        Create a folium map with real estate data.

        Returns:
            folium.Map: The generated folium map with heatmap.
        """
        gmap = folium.Map(location=[21.028511, 105.804817], zoom_start=6)
        self.add_heatmap(gmap)
        return gmap

def visualize_real_estate_price(housing_df: pd.DataFrame) -> folium.Map:
    """
    Visualize real estate data on a map based on price.

    Parameters:
        housing_df (pd.DataFrame): The DataFrame containing the real estate data.

    Returns:
        folium.Map: The generated folium map.
    """
    visualizer = RealEstateVisualizerPrice(housing_df)
    return visualizer.create_map()  # Create a folium map

def visualize_real_estate_clusters(housing_df:pd.DataFrame, num_clusters:int=5) -> folium.Map:
    visualizer = RealEstateVisualizerCluster(housing_df, num_clusters) 
    visualizer.fit_kmeans() # Fit KMeans model and add cluster labels to the dataframe
    return visualizer.create_map() # Create a folium map

def visualize_real_estate_price_heatmap(housing_df: pd.DataFrame) -> folium.Map:
    """
    Visualize real estate data on a heatmap based on price.

    Parameters:
        housing_df (pd.DataFrame): The DataFrame containing the real estate data.

    Returns:
        folium.Map: The generated folium map with heatmap.
    """
    visualizer = RealEstateVisualizerHeatmap(housing_df)
    return visualizer.create_map()