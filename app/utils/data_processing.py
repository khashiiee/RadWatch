import pandas as pd
import numpy as np
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point

class DataProcessor:
    # Class-level constants
    SENSOR_ID = 'sensor_id'
    TIMESTAMP = 'timestamp'
    USER_ID = 'user_id'
    VALUE = 'value'
    UNITS = 'units'
    LATITUDE = 'latitude'
    LONGITUDE = 'longitude'
    
    # Data cleaning constants
    MIN_VALID_VALUE = 0.0  # Minimum valid radiation reading
    MAX_VALID_VALUE = 100.0  # Maximum valid radiation reading
    MAX_RATE_OF_CHANGE = 50.0  # Maximum allowed change between consecutive readings
    
    def __init__(self):
        self.static_sensors = None
        self.static_readings = None
        self.mobile_readings = None
        self.start_date = None
        self.end_date = None
        self.gdf = None
        
        try:
            self.gdf = gpd.read_file('../data/StHimarkNeighborhoodShapefile/StHimark.shp')
            if self.gdf.crs != 'EPSG:4326':
                self.gdf = self.gdf.to_crs('EPSG:4326')
        except Exception as e:
            print(f"Warning: Could not load neighborhood shapefile: {str(e)}")
            self.gdf = None

    def clean_radiation_data(self, df):
        """
        Clean radiation readings by removing anomalies and invalid values
        
        Args:
            df (pd.DataFrame): DataFrame containing radiation readings
            
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        if df is None or len(df) == 0:
            return df
            
        cleaned = df.copy()
        
        # Remove readings outside valid range
        mask = (cleaned[self.VALUE] >= self.MIN_VALID_VALUE) & \
               (cleaned[self.VALUE] <= self.MAX_VALID_VALUE)
        
        invalid_count = len(cleaned) - mask.sum()
        if invalid_count > 0:
            print(f"Removed {invalid_count} readings outside valid range ({self.MIN_VALID_VALUE}-{self.MAX_VALID_VALUE})")
        
        cleaned = cleaned[mask]
        
        # Sort by sensor and timestamp for rate-of-change calculation
        cleaned = cleaned.sort_values([self.SENSOR_ID, self.TIMESTAMP])
        
        # Calculate rate of change for each sensor
        cleaned['value_diff'] = cleaned.groupby(self.SENSOR_ID)[self.VALUE].diff()
        
        # Remove readings with excessive rate of change
        mask = abs(cleaned['value_diff']) <= self.MAX_RATE_OF_CHANGE
        
        spike_count = len(cleaned) - mask.sum()
        if spike_count > 0:
            print(f"Removed {spike_count} readings with excessive rate of change (>{self.MAX_RATE_OF_CHANGE})")
        
        cleaned = cleaned[mask]
        
        # Remove the temporary column
        cleaned = cleaned.drop('value_diff', axis=1)
        
        # Remove statistical outliers using IQR method
        Q1 = cleaned[self.VALUE].quantile(0.25)
        Q3 = cleaned[self.VALUE].quantile(0.75)
        IQR = Q3 - Q1
        outlier_mask = (cleaned[self.VALUE] >= Q1 - 1.5 * IQR) & \
                      (cleaned[self.VALUE] <= Q3 + 1.5 * IQR)
        
        outlier_count = len(cleaned) - outlier_mask.sum()
        if outlier_count > 0:
            print(f"Removed {outlier_count} statistical outliers")
        
        cleaned = cleaned[outlier_mask]
        
        print(f"Final clean dataset contains {len(cleaned)} readings")
        return cleaned

    def load_data(self):
        """Load and clean all data sources"""
        try:
            # Load raw data
            self.static_sensors = pd.read_csv('../data/StaticSensorLocations.csv')
            self.static_readings = pd.read_csv('../data/StaticSensorReadings.csv')
            self.mobile_readings = pd.read_csv('../data/MobileSensorReadings.csv')
            
            # Standardize column names
            self.standardize_column_names()
            
            # Convert timestamps
            self.static_readings[self.TIMESTAMP] = pd.to_datetime(self.static_readings[self.TIMESTAMP])
            self.mobile_readings[self.TIMESTAMP] = pd.to_datetime(self.mobile_readings[self.TIMESTAMP])
            
            # Clean the readings
            print("Cleaning static sensor readings...")
            self.static_readings = self.clean_radiation_data(self.static_readings)
            
            print("\nCleaning mobile sensor readings...")
            self.mobile_readings = self.clean_radiation_data(self.mobile_readings)
            
            # Set the time range from cleaned data
            self.start_date = min(
                self.static_readings[self.TIMESTAMP].min(),
                self.mobile_readings[self.TIMESTAMP].min()
            )
            self.end_date = max(
                self.static_readings[self.TIMESTAMP].max(),
                self.mobile_readings[self.TIMESTAMP].max()
            )
            
            print("\nData loaded and cleaned successfully")
            return True
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False

    def standardize_column_names(self):
        """Standardize column names across all datasets"""
        column_maps = {
            'Sensor-id': self.SENSOR_ID,
            'Timestamp': self.TIMESTAMP,
            ' User-id': self.USER_ID,
            'User-id': self.USER_ID,
            'Value': self.VALUE,
            'Units': self.UNITS,
            'Lat': self.LATITUDE,
            'Long': self.LONGITUDE,
            'Latitude': self.LATITUDE,
            'Longitude': self.LONGITUDE
        }
        
        for df in [self.static_sensors, self.static_readings, self.mobile_readings]:
            if df is not None:
                df.columns = df.columns.str.strip()
                df.rename(columns=column_maps, inplace=True)

    def filter_time_range(self, df, start_date, end_date):
        """Filter dataframe by time range"""
        if start_date and end_date:
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            mask = (df[self.TIMESTAMP] >= start_date) & (df[self.TIMESTAMP] <= end_date)
            return df[mask]
        return df

    def calculate_period_statistics(self, static_data, mobile_data):
        """Calculate statistics for the current time period"""
        try:
            stats = {
                'static_mean': static_data[self.VALUE].mean(),
                'static_max': static_data[self.VALUE].max(),
                'static_min': static_data[self.VALUE].min(),
                'static_std': static_data[self.VALUE].std(),
                'mobile_mean': mobile_data[self.VALUE].mean(),
                'mobile_max': mobile_data[self.VALUE].max(),
                'mobile_min': mobile_data[self.VALUE].min(),
                'mobile_std': mobile_data[self.VALUE].std(),
                'num_static_readings': len(static_data),
                'num_mobile_readings': len(mobile_data),
                'unique_mobile_sensors': mobile_data[self.SENSOR_ID].nunique()
            }
            
            # Handle NaN values
            for key, value in stats.items():
                if pd.isna(value):
                    stats[key] = 0
                    
            return stats
            
        except Exception as e:
            print(f"Error calculating statistics: {str(e)}")
            return {
                'static_mean': 0, 'static_max': 0, 'static_min': 0, 'static_std': 0,
                'mobile_mean': 0, 'mobile_max': 0, 'mobile_min': 0, 'mobile_std': 0,
                'num_static_readings': 0, 'num_mobile_readings': 0,
                'unique_mobile_sensors': 0
            }
    
    def get_sensor_stats(self):
        """Get basic statistics about the sensors"""
        if self.static_sensors is None or self.static_readings is None or self.mobile_readings is None:
            return {
                'static_sensor_count': 0,
                'mobile_sensor_count': 0,
                'unique_users': 0,
                'date_range': (None, None),
                'static_reading_count': 0,
                'mobile_reading_count': 0
            }
            
        return {
            'static_sensor_count': len(self.static_sensors[self.SENSOR_ID].unique()),
            'mobile_sensor_count': len(self.mobile_readings[self.SENSOR_ID].unique()),
            'unique_users': len(self.mobile_readings[self.USER_ID].unique()),
            'date_range': (self.start_date, self.end_date),
            'static_reading_count': len(self.static_readings),
            'mobile_reading_count': len(self.mobile_readings)
        }
    
    def get_hourly_averages(self, sensor_type='static'):
        """Calculate hourly radiation averages"""
        if sensor_type == 'static':
            df = self.static_readings
        else:
            df = self.mobile_readings
            
        return df.groupby([
            df[self.TIMESTAMP].dt.date,
            df[self.TIMESTAMP].dt.hour,
            self.SENSOR_ID
        ])[self.VALUE].mean().reset_index()
    
    def get_sensor_locations(self, timestamp=None):
        """Get sensor locations at a specific timestamp"""
        static_locs = self.static_sensors[[self.SENSOR_ID, self.LATITUDE, self.LONGITUDE]].copy()
        
        if timestamp:
            mobile_locs = self.mobile_readings[
                self.mobile_readings[self.TIMESTAMP] == timestamp
            ][[self.SENSOR_ID, self.LATITUDE, self.LONGITUDE, self.USER_ID]].copy()
        else:
            # Get latest locations for mobile sensors
            mobile_locs = self.mobile_readings.sort_values(self.TIMESTAMP).groupby(self.SENSOR_ID).last()
            mobile_locs = mobile_locs[[self.LATITUDE, self.LONGITUDE, self.USER_ID]].reset_index()
            
        return static_locs, mobile_locs
    
    def detect_anomalies(self, readings, window_size='1H', threshold=3):
        """Detect anomalous radiation readings using rolling statistics"""
        df = readings.copy()
        df['rolling_mean'] = df.groupby(self.SENSOR_ID)[self.VALUE].transform(
            lambda x: x.rolling(window=window_size).mean()
        )
        df['rolling_std'] = df.groupby(self.SENSOR_ID)[self.VALUE].transform(
            lambda x: x.rolling(window=window_size).std()
        )
        
        df['is_anomaly'] = abs(df[self.VALUE] - df['rolling_mean']) > (threshold * df['rolling_std'])
        return df[df['is_anomaly']]
    
    
    def calculate_coverage_stats(self, static_sensors, mobile_readings):
        """Calculate statistics about actual data coverage across neighborhoods"""
        try:
            if self.gdf is None:
                return {
                    'total_neighborhoods': 0,
                    'covered_neighborhoods': 0,
                    'uncovered_neighborhoods': 0,
                    'coverage_percentage': 0
                }
                
            total_neighborhoods = len(self.gdf)
            neighborhoods_with_data = set()
            
            # Check actual reading locations, not just sensor positions
            if static_sensors is not None:
                static_readings = pd.merge(
                    static_sensors,
                    self.static_readings,
                    on=self.SENSOR_ID
                )
                
                for _, reading in static_readings.iterrows():
                    point = Point(reading[self.LONGITUDE], reading[self.LATITUDE])
                    for idx, neighborhood in self.gdf.iterrows():
                        if point.within(neighborhood.geometry):
                            neighborhoods_with_data.add(neighborhood.get('Nbrhood', str(idx)))
            
            if mobile_readings is not None:
                for _, reading in mobile_readings.iterrows():
                    point = Point(reading[self.LONGITUDE], reading[self.LATITUDE])
                    for idx, neighborhood in self.gdf.iterrows():
                        if point.within(neighborhood.geometry):
                            neighborhoods_with_data.add(neighborhood.get('Nbrhood', str(idx)))
            
            num_covered = len(neighborhoods_with_data)
            coverage_pct = (num_covered / total_neighborhoods * 100) if total_neighborhoods > 0 else 0
            
            # Get list of neighborhoods without data
            all_neighborhoods = set(self.gdf['Nbrhood'].values)
            uncovered_neighborhoods = all_neighborhoods - neighborhoods_with_data
            
            return {
                'total_neighborhoods': total_neighborhoods,
                'covered_neighborhoods': num_covered,
                'uncovered_neighborhoods': total_neighborhoods - num_covered,
                'coverage_percentage': coverage_pct,
                'neighborhoods_without_data': sorted(list(uncovered_neighborhoods))
            }
            
        except Exception as e:
            print(f"Error calculating coverage statistics: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {
                'total_neighborhoods': 0,
                'covered_neighborhoods': 0,
                'uncovered_neighborhoods': 0,
                'coverage_percentage': 0,
                'neighborhoods_without_data': []
            }