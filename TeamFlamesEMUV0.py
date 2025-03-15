import socket
import threading
import time
import random
import json
import os
import hashlib
from typing import Dict, List, Any, Optional

class MegaConnectorEmulator:
    """
    Emulates the Nintendo Mega-Connector technology from Super Mario 64 cartridges.
    This module creates a virtual connection to an emulated server that simulates
    the storage capabilities of the original Nintendo HQ servers.
    """
    
    def __init__(self, rom_path: str = None):
        self.connected = False
        self.rom_path = rom_path
        self.rom_hash = None
        self.server_thread = None
        self.stop_event = threading.Event()
        self.virtual_storage: Dict[str, Any] = {}
        self.session_id = None
        self.connection_latency = random.uniform(0.05, 0.2)  # Simulated network latency
        self.bandwidth = random.randint(500, 2000)  # KB/s
        self.storage_capacity = 1024 * 1024 * 1024  # 1GB virtual storage
        self.used_storage = 0
        self.connection_quality = random.uniform(0.8, 1.0)  # Connection quality factor
        
        # Mega-Connector protocol version
        self.protocol_version = "MCv2.5"
        
        # Initialize virtual storage with default values
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize the virtual storage with default system data"""
        self.virtual_storage = {
            "system": {
                "protocol_version": self.protocol_version,
                "last_connection": time.time(),
                "total_connections": 0,
                "uptime": 0,
                "error_count": 0
            },
            "game_data": {},
            "save_data": {},
            "user_settings": {
                "controller_config": {
                    "rumble_enabled": True,
                    "sensitivity": 0.75
                },
                "display_settings": {
                    "anti_aliasing": True,
                    "texture_filtering": "bilinear"
                },
                "audio_settings": {
                    "stereo": True,
                    "volume": 0.8
                }
            },
            "extended_levels": {}
        }
    
    def connect(self) -> bool:
        """
        Establish a virtual connection to the Nintendo server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.connected:
            return True
            
        # Generate ROM hash if ROM path is provided
        if self.rom_path and os.path.exists(self.rom_path):
            self.rom_hash = self._hash_rom(self.rom_path)
        else:
            # Use a fake hash for testing
            self.rom_hash = hashlib.md5(f"SuperMario64_{random.randint(1000, 9999)}".encode()).hexdigest()
        
        # Simulate connection process
        print(f"[Mega-Connector] Establishing connection to Nintendo HQ servers...")
        time.sleep(self.connection_latency * 2)
        
        # Randomly fail connection sometimes to simulate real-world conditions
        if random.random() < 0.05:  # 5% chance of failure
            print(f"[Mega-Connector] Connection failed: Network error")
            return False
            
        # Generate a session ID
        self.session_id = f"MC_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Update connection stats
        self.virtual_storage["system"]["last_connection"] = time.time()
        self.virtual_storage["system"]["total_connections"] += 1
        
        # Initialize game-specific data if not present
        if self.rom_hash not in self.virtual_storage["game_data"]:
            self.virtual_storage["game_data"][self.rom_hash] = {
                "name": f"Game_{self.rom_hash[:8]}",
                "first_played": time.time(),
                "play_time": 0,
                "custom_data": {}
            }
            
        # Start the background server simulation thread
        self.stop_event.clear()
        self.server_thread = threading.Thread(target=self._server_simulation, daemon=True)
        self.server_thread.start()
        
        self.connected = True
        print(f"[Mega-Connector] Connected successfully (Session ID: {self.session_id})")
        print(f"[Mega-Connector] Protocol version: {self.protocol_version}")
        return True
    
    def disconnect(self):
        """Disconnect from the virtual Nintendo server"""
        if not self.connected:
            return
            
        print(f"[Mega-Connector] Disconnecting from Nintendo HQ servers...")
        
        # Stop the server simulation thread
        self.stop_event.set()
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)
            
        # Update stats before disconnecting
        if self.rom_hash in self.virtual_storage["game_data"]:
            game_data = self.virtual_storage["game_data"][self.rom_hash]
            game_data["last_played"] = time.time()
            
        self.connected = False
        self.session_id = None
        print(f"[Mega-Connector] Disconnected successfully")
    
    def store_data(self, key: str, data: Any) -> bool:
        """
        Store data on the virtual Nintendo server
        
        Args:
            key: Data key/path
            data: Data to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            print(f"[Mega-Connector] Error: Not connected to server")
            return False
            
        # Simulate network latency
        time.sleep(self.connection_latency)
        
        # Simulate data size
        data_size = len(json.dumps(data).encode())
        
        # Check if we have enough storage
        if self.used_storage + data_size > self.storage_capacity:
            print(f"[Mega-Connector] Error: Insufficient storage space")
            return False
            
        # Calculate transfer time based on data size and bandwidth
        transfer_time = data_size / (self.bandwidth * 1024)
        
        # Adjust for connection quality
        transfer_time /= self.connection_quality
        
        # Simulate transfer time
        time.sleep(min(transfer_time, 2.0))  # Cap at 2 seconds for usability
        
        # Store the data
        parts = key.split('/')
        current = self.virtual_storage
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
                
        current[parts[-1]] = data
        
        # Update used storage
        self.used_storage += data_size
        
        print(f"[Mega-Connector] Data stored successfully ({data_size} bytes)")
        return True
    
    def retrieve_data(self, key: str) -> Optional[Any]:
        """
        Retrieve data from the virtual Nintendo server
        
        Args:
            key: Data key/path
            
        Returns:
            Any: Retrieved data or None if not found
        """
        if not self.connected:
            print(f"[Mega-Connector] Error: Not connected to server")
            return None
            
        # Simulate network latency
        time.sleep(self.connection_latency)
        
        # Navigate to the requested data
        parts = key.split('/')
        current = self.virtual_storage
        
        try:
            for part in parts:
                current = current[part]
                
            # Simulate data size for retrieval time calculation
            data_size = len(json.dumps(current).encode())
            
            # Calculate transfer time based on data size and bandwidth
            transfer_time = data_size / (self.bandwidth * 1024)
            
            # Adjust for connection quality
            transfer_time /= self.connection_quality
            
            # Simulate transfer time
            time.sleep(min(transfer_time, 2.0))  # Cap at 2 seconds for usability
            
            print(f"[Mega-Connector] Data retrieved successfully ({data_size} bytes)")
            return current
        except (KeyError, TypeError):
            print(f"[Mega-Connector] Error: Data not found for key '{key}'")
            return None
    
    def delete_data(self, key: str) -> bool:
        """
        Delete data from the virtual Nintendo server
        
        Args:
            key: Data key/path
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            print(f"[Mega-Connector] Error: Not connected to server")
            return False
            
        # Simulate network latency
        time.sleep(self.connection_latency)
        
        # Navigate to the requested data
        parts = key.split('/')
        current = self.virtual_storage
        
        try:
            for i, part in enumerate(parts[:-1]):
                current = current[part]
                
            # Calculate data size for updating used storage
            data_size = len(json.dumps(current[parts[-1]]).encode())
            
            # Delete the data
            del current[parts[-1]]
            
            # Update used storage
            self.used_storage -= data_size
            
            print(f"[Mega-Connector] Data deleted successfully")
            return True
        except (KeyError, TypeError):
            print(f"[Mega-Connector] Error: Data not found for key '{key}'")
            return False
    
    def store_custom_level(self, level_id: str, level_data: Dict[str, Any]) -> bool:
        """
        Store a custom level on the virtual Nintendo server
        
        Args:
            level_id: Unique level identifier
            level_data: Level data dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            print(f"[Mega-Connector] Error: Not connected to server")
            return False
            
        # Make sure extended_levels exists
        if "extended_levels" not in self.virtual_storage:
            self.virtual_storage["extended_levels"] = {}
            
        # Add metadata
        level_data["created_at"] = time.time()
        level_data["created_by"] = self.session_id
        level_data["last_modified"] = time.time()
        
        return self.store_data(f"extended_levels/{level_id}", level_data)
    
    def get_custom_level(self, level_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a custom level from the virtual Nintendo server
        
        Args:
            level_id: Unique level identifier
            
        Returns:
            Dict[str, Any]: Level data or None if not found
        """
        return self.retrieve_data(f"extended_levels/{level_id}")
    
    def list_custom_levels(self) -> List[str]:
        """
        List all custom levels on the virtual Nintendo server
        
        Returns:
            List[str]: List of level IDs
        """
        if not self.connected:
            print(f"[Mega-Connector] Error: Not connected to server")
            return []
            
        extended_levels = self.retrieve_data("extended_levels")
        if extended_levels is None:
            return []
            
        return list(extended_levels.keys())
    
    def save_game_state(self, save_id: str, state_data: Dict[str, Any]) -> bool:
        """
        Save game state to the virtual Nintendo server
        
        Args:
            save_id: Save identifier
            state_data: Game state data
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            print(f"[Mega-Connector] Error: Not connected to server")
            return False
            
        # Make sure the ROM hash exists in the save_data
        if self.rom_hash not in self.virtual_storage["save_data"]:
            self.virtual_storage["save_data"][self.rom_hash] = {}
            
        # Add metadata
        state_data["saved_at"] = time.time()
        state_data["session_id"] = self.session_id
        
        return self.store_data(f"save_data/{self.rom_hash}/{save_id}", state_data)
    
    def load_game_state(self, save_id: str) -> Optional[Dict[str, Any]]:
        """
        Load game state from the virtual Nintendo server
        
        Args:
            save_id: Save identifier
            
        Returns:
            Dict[str, Any]: Game state data or None if not found
        """
        if not self.connected:
            print(f"[Mega-Connector] Error: Not connected to server")
            return None
            
        return self.retrieve_data(f"save_data/{self.rom_hash}/{save_id}")
    
    def list_game_saves(self) -> List[str]:
        """
        List all game saves for the current ROM
        
        Returns:
            List[str]: List of save IDs
        """
        if not self.connected:
            print(f"[Mega-Connector] Error: Not connected to server")
            return []
            
        save_data = self.retrieve_data(f"save_data/{self.rom_hash}")
        if save_data is None:
            return []
            
        return list(save_data.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection and server statistics
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        stats = {
            "connected": self.connected,
            "session_id": self.session_id,
            "rom_hash": self.rom_hash,
            "connection_latency_ms": self.connection_latency * 1000,
            "bandwidth_kbps": self.bandwidth,
            "storage": {
                "total_bytes": self.storage_capacity,
                "used_bytes": self.used_storage,
                "free_bytes": self.storage_capacity - self.used_storage,
                "used_percentage": (self.used_storage / self.storage_capacity) * 100
            },
            "connection_quality": self.connection_quality,
            "protocol_version": self.protocol_version
        }
        
        return stats
    
    def _server_simulation(self):
        """Background thread to simulate server behavior"""
        while not self.stop_event.is_set():
            # Simulate occasional network instability
            if random.random() < 0.01:  # 1% chance per iteration
                self.connection_latency = min(2.0, self.connection_latency * random.uniform(1.0, 3.0))
                self.connection_quality = max(0.3, self.connection_quality * random.uniform(0.7, 1.0))
                print(f"[Mega-Connector] Network condition changed: Latency {self.connection_latency*1000:.1f}ms, Quality {self.connection_quality:.2f}")
            else:
                # Gradually return to normal
                self.connection_latency = max(0.05, self.connection_latency * 0.95)
                self.connection_quality = min(1.0, self.connection_quality * 1.01)
            
            # Update system uptime
            if self.virtual_storage and "system" in self.virtual_storage:
                self.virtual_storage["system"]["uptime"] += 5
                
            # Periodically auto-save
            if self.rom_hash and random.random() < 0.1:  # 10% chance per iteration
                try:
                    # Create an auto-save with basic info
                    auto_save = {
                        "auto_save": True,
                        "saved_at": time.time(),
                        "session_id": self.session_id,
                        "basic_state": {
                            "random_seed": random.randint(1, 1000000),
                            "game_flags": random.randint(1, 65535)
                        }
                    }
                    
                    # Store without calling the public method to avoid latency simulation
                    if "save_data" not in self.virtual_storage:
                        self.virtual_storage["save_data"] = {}
                    if self.rom_hash not in self.virtual_storage["save_data"]:
                        self.virtual_storage["save_data"][self.rom_hash] = {}
                        
                    self.virtual_storage["save_data"][self.rom_hash]["auto_save"] = auto_save
                except Exception as e:
                    print(f"[Mega-Connector] Auto-save error: {str(e)}")
                    
            time.sleep(5)  # Update every 5 seconds
    
    def _hash_rom(self, rom_path: str) -> str:
        """
        Generate a hash for the ROM file
        
        Args:
            rom_path: Path to the ROM file
            
        Returns:
            str: MD5 hash of the ROM
        """
        try:
            # For large ROMs, just hash the first 1MB for speed
            with open(rom_path, 'rb') as f:
                return hashlib.md5(f.read(1024 * 1024)).hexdigest()
        except Exception as e:
            print(f"[Mega-Connector] Error hashing ROM: {str(e)}")
            return hashlib.md5(f"error_{time.time()}".encode()).hexdigest()


# Integration with the N64 emulator
class MegaConnectorPlugin:
    """
    Plugin to integrate the Mega-Connector with the N64 emulator.
    This connects the emulator to the virtual Nintendo server.
    """
    
    def __init__(self, emulator):
        self.emulator = emulator
        self.mega_connector = None
        self.enabled = False
        
    def initialize(self):
        """Initialize the Mega-Connector plugin"""
        print("Initializing Nintendo Mega-Connector Plugin...")
        self.mega_connector = MegaConnectorEmulator()
        self.enabled = True
        print("Mega-Connector Plugin initialized successfully")
        
    def shutdown(self):
        """Shutdown the Mega-Connector plugin"""
        if self.mega_connector and self.mega_connector.connected:
            self.mega_connector.disconnect()
        self.enabled = False
        print("Mega-Connector Plugin shutdown")
        
    def connect(self):
        """Connect to the virtual Nintendo server"""
        if not self.enabled or not self.mega_connector:
            print("Mega-Connector Plugin not enabled")
            return False
            
        if self.emulator.current_rom:
            self.mega_connector.rom_path = self.emulator.current_rom
            return self.mega_connector.connect()
        else:
            print("No ROM loaded, cannot connect to Mega-Connector")
            return False
            
    def save_extended_data(self, key, data):
        """Save extended data to the server"""
        if not self.enabled or not self.mega_connector or not self.mega_connector.connected:
            return False
            
        return self.mega_connector.store_data(f"game_data/{self.mega_connector.rom_hash}/extended/{key}", data)
        
    def load_extended_data(self, key):
        """Load extended data from the server"""
        if not self.enabled or not self.mega_connector or not self.mega_connector.connected:
            return None
            
        return self.mega_connector.retrieve_data(f"game_data/{self.mega_connector.rom_hash}/extended/{key}")
        
    def save_custom_level(self, level_id, level_data):
        """Save a custom level to the server"""
        if not self.enabled or not self.mega_connector or not self.mega_connector.connected:
            return False
            
        return self.mega_connector.store_custom_level(level_id, level_data)
        
    def load_custom_level(self, level_id):
        """Load a custom level from the server"""
        if not self.enabled or not self.mega_connector or not self.mega_connector.connected:
            return None
            
        return self.mega_connector.get_custom_level(level_id)
        
    def list_custom_levels(self):
        """List all available custom levels"""
        if not self.enabled or not self.mega_connector or not self.mega_connector.connected:
            return []
            
        return self.mega_connector.list_custom_levels()
        
    def get_connection_stats(self):
        """Get connection statistics"""
        if not self.enabled or not self.mega_connector:
            return {"enabled": False, "connected": False}
            
        stats = self.mega_connector.get_stats()
        stats["plugin_enabled"] = self.enabled
        return stats


# Example usage
if __name__ == "__main__":
    # Test the Mega-Connector functionality
    connector = MegaConnectorEmulator()
    
    print("Testing Mega-Connector functionality...")
    
    # Connect
    connected = connector.connect()
    if not connected:
        print("Failed to connect to virtual Nintendo server")
        exit(1)
        
    # Store some data
    test_data = {
        "player": "Mario",
        "stars": 120,
        "coins": 999,
        "lives": 99,
        "levels_completed": ["Bob-omb Battlefield", "Whomp's Fortress", "Jolly Roger Bay"]
    }
    
    store_success = connector.store_data("test_save", test_data)
    print(f"Store data success: {store_success}")
    
    # Retrieve the data
    retrieved_data = connector.retrieve_data("test_save")
    print(f"Retrieved data: {retrieved_data}")
    
    # Store a custom level
    custom_level = {
        "name": "Cloudy Heights",
        "difficulty": "Hard",
        "coins": 150,
        "stars": 7,
        "enemies": 25,
        "layout": {
            "start_position": [100, 50, 200],
            "exit_position": [800, 600, 100],
            "platforms": [
                {"x": 100, "y": 50, "z": 200, "width": 100, "height": 20},
                {"x": 300, "y": 150, "z": 300, "width": 200, "height": 30},
                {"x": 600, "y": 350, "z": 100, "width": 150, "height": 25}
            ]
        }
    }
    
    level_success = connector.store_custom_level("cloudy_heights", custom_level)
    print(f"Store custom level success: {level_success}")
    
    # List custom levels
    levels = connector.list_custom_levels()
    print(f"Available custom levels: {levels}")
    
    # Get connection stats
    stats = connector.get_stats()
    print("Connection stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
        
    # Disconnect
    connector.disconnect()
    print("Test completed")
