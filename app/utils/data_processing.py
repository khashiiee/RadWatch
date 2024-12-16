# app/utils/data_processing.py
import pandas as pd
import numpy as np
from datetime import datetime

class DataProcessor:
    # Class-level constants for standardized column names
    SENSOR_ID = 'sensor_id'
    TIMESTAMP = 'timestamp'
    USER_ID = 'user_id'
    VALUE = 'value'
    UNITS = 'units'
    LATITUDE = 'latitude'
    LONGITUDE = 'longitude'
    
    def __init__(self):
        self.static_sensors = None
        self.static_readings = None
        self.mobile_readings = None
        self.start_date = None
        self.end_date = None
        
    def load_data(self):
        """Load all data sources"""
        try:
            # Load data with relative paths
            self.static_sensors = pd.read_csv('../data/StaticSensorLocations.csv')
            self.static_readings = pd.read_csv('../data/StaticSensorReadings.csv')
            self.mobile_readings = pd.read_csv('../data/MobileSensorReadings.csv')
            
            # Print original column names for debugging
            print("Static sensors columns:", self.static_sensors.columns)
            print("Static readings columns:", self.static_readings.columns)
            print("Mobile readings columns:", self.mobile_readings.columns)
            
            # Standardize column names
            self.standardize_column_names()
            
            print("\nStandardized column names:")
            print("Static sensors:", self.static_sensors.columns)
            print("Static readings:", self.static_readings.columns)
            print("Mobile readings:", self.mobile_readings.columns)
            
            # Convert timestamp columns to datetime
            self.static_readings[self.TIMESTAMP] = pd.to_datetime(self.static_readings[self.TIMESTAMP])
            self.mobile_readings[self.TIMESTAMP] = pd.to_datetime(self.mobile_readings[self.TIMESTAMP])
            
            # Set the time range
            self.start_date = self.static_readings[self.TIMESTAMP].min()
            self.end_date = self.static_readings[self.TIMESTAMP].max()
            
            print("Data loaded successfully")
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