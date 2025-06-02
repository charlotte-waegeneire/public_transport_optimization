import pickle
import os
from datetime import datetime, timedelta
import pandas as pd
from public_transport_watcher.logging_config import get_logger

logger = get_logger()


class CacheManager:
    """Manages caching operations for API data"""

    def __init__(self, cache_file="api_alerts_cache.pkl", duration_minutes=60):
        self.cache_file = cache_file
        self.duration_minutes = duration_minutes

    def get_cache_info(self):
        """Returns cache information (timestamp and validity)"""
        if not os.path.exists(self.cache_file):
            return None, False

        try:
            with open(self.cache_file, "rb") as f:
                cached_data = pickle.load(f)

            cache_time = cached_data["timestamp"]
            is_valid = (datetime.now() - cache_time) < timedelta(minutes=self.duration_minutes)

            return cache_time, is_valid
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None, False

    def is_cache_valid(self):
        """Checks if cache is still valid"""
        _, is_valid = self.get_cache_info()
        return is_valid

    def load_from_cache(self):
        """Loads data from cache"""
        try:
            with open(self.cache_file, "rb") as f:
                cached_data = pickle.load(f)
            logger.info(f"Data loaded from cache (created at {cached_data['timestamp'].strftime('%H:%M:%S')})")
            return cached_data["data"]
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return pd.DataFrame()

    def save_to_cache(self, data):
        """Saves data to cache"""
        try:
            cache_data = {"timestamp": datetime.now(), "data": data}
            with open(self.cache_file, "wb") as f:
                pickle.dump(cache_data, f)
            logger.info(f"Data saved to cache ({len(data)} records)")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def clear_cache(self):
        """Removes cache file"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                logger.info("Cache deleted")
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")


default_cache = CacheManager()


def get_cache_info():
    """Returns cache information (timestamp and validity)"""
    return default_cache.get_cache_info()


def is_cache_valid():
    """Checks if cache is still valid"""
    return default_cache.is_cache_valid()


def load_from_cache():
    """Loads data from cache"""
    return default_cache.load_from_cache()


def save_to_cache(data):
    """Saves data to cache"""
    return default_cache.save_to_cache(data)


def clear_cache():
    """Removes cache file"""
    return default_cache.clear_cache()
