#!/usr/bin/env python3
"""
RemotelyPy - Configuration Manager

This module provides functionality to save, load, and manage configuration profiles
for both client and controller modes of RemotelyPy.
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration profiles for RemotelyPy."""
    
    def __init__(self, config_dir=None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir (str, optional): Directory to store configuration files.
                                       Defaults to ~/.remotelypy/
        """
        if config_dir is None:
            self.config_dir = os.path.expanduser("~/.remotelypy")
        else:
            self.config_dir = config_dir
            
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Separate directories for client and controller profiles
        self.client_config_dir = os.path.join(self.config_dir, "client_profiles")
        self.controller_config_dir = os.path.join(self.config_dir, "controller_profiles")
        
        os.makedirs(self.client_config_dir, exist_ok=True)
        os.makedirs(self.controller_config_dir, exist_ok=True)
        
    def _get_profile_path(self, profile_name, mode):
        """
        Get the file path for a specific profile.
        
        Args:
            profile_name (str): Name of the profile
            mode (str): Either 'client' or 'controller'
            
        Returns:
            str: Path to the profile file
        """
        if mode == 'client':
            return os.path.join(self.client_config_dir, f"{profile_name}.json")
        elif mode == 'controller':
            return os.path.join(self.controller_config_dir, f"{profile_name}.json")
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'client' or 'controller'")
    
    def save_profile(self, profile_name, config, mode):
        """
        Save a configuration profile.
        
        Args:
            profile_name (str): Name of the profile
            config (dict): Configuration settings to save
            mode (str): Either 'client' or 'controller'
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            profile_path = self._get_profile_path(profile_name, mode)
            with open(profile_path, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Saved {mode} profile '{profile_name}' to {profile_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save {mode} profile '{profile_name}': {str(e)}")
            return False
    
    def load_profile(self, profile_name, mode):
        """
        Load a configuration profile.
        
        Args:
            profile_name (str): Name of the profile
            mode (str): Either 'client' or 'controller'
            
        Returns:
            dict: Configuration settings or None if profile doesn't exist
        """
        try:
            profile_path = self._get_profile_path(profile_name, mode)
            if not os.path.exists(profile_path):
                logger.warning(f"{mode.capitalize()} profile '{profile_name}' does not exist")
                return None
                
            with open(profile_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded {mode} profile '{profile_name}' from {profile_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load {mode} profile '{profile_name}': {str(e)}")
            return None
    
    def delete_profile(self, profile_name, mode):
        """
        Delete a configuration profile.
        
        Args:
            profile_name (str): Name of the profile
            mode (str): Either 'client' or 'controller'
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            profile_path = self._get_profile_path(profile_name, mode)
            if not os.path.exists(profile_path):
                logger.warning(f"{mode.capitalize()} profile '{profile_name}' does not exist")
                return False
                
            os.remove(profile_path)
            logger.info(f"Deleted {mode} profile '{profile_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {mode} profile '{profile_name}': {str(e)}")
            return False
    
    def list_profiles(self, mode):
        """
        List all available profiles for a specific mode.
        
        Args:
            mode (str): Either 'client' or 'controller'
            
        Returns:
            list: List of profile names
        """
        try:
            if mode == 'client':
                config_dir = self.client_config_dir
            elif mode == 'controller':
                config_dir = self.controller_config_dir
            else:
                raise ValueError(f"Invalid mode: {mode}. Must be 'client' or 'controller'")
                
            profiles = []
            for file in os.listdir(config_dir):
                if file.endswith('.json'):
                    profiles.append(os.path.splitext(file)[0])
            return profiles
        except Exception as e:
            logger.error(f"Failed to list {mode} profiles: {str(e)}")
            return []
    
    def args_to_config(self, args, mode):
        """
        Convert command line arguments to a configuration dictionary.
        
        Args:
            args (Namespace): Command line arguments
            mode (str): Either 'client' or 'controller'
            
        Returns:
            dict: Configuration dictionary
        """
        config = vars(args).copy()
        
        # Remove command and profile-related arguments
        if 'command' in config:
            del config['command']
        if 'profile' in config:
            del config['profile']
        if 'save_profile' in config:
            del config['save_profile']
        if 'list_profiles' in config:
            del config['list_profiles']
        if 'delete_profile' in config:
            del config['delete_profile']
        
        return config
    
    def config_to_args(self, config, args):
        """
        Apply configuration settings to command line arguments.
        
        Args:
            config (dict): Configuration settings
            args (Namespace): Command line arguments to update
            
        Returns:
            Namespace: Updated arguments
        """
        # Only update args that aren't explicitly set on the command line
        for key, value in config.items():
            if not hasattr(args, key) or getattr(args, key) is None:
                setattr(args, key, value)
        
        return args