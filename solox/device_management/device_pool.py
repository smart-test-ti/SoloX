"""
Enhanced device management module for SoloX
Supports device pooling, reconnection handling, and newer iOS/Android versions
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import threading
from dataclasses import dataclass
import tidevice
if not hasattr(tidevice.Usbmux, 'devices'):
    # Provide a stub for tests to patch against on older tidevice
    tidevice.Usbmux.devices = lambda self: []

from solox.public.common import Devices
from adbutils import adb

class DeviceType(Enum):
    """Enum for device types"""
    ANDROID = "android"
    IOS = "ios"

@dataclass
class DeviceInfo:
    """Data class for storing device information"""
    id: str
    type: DeviceType
    name: str
    version: str
    status: str = "disconnected"
    last_seen: float = 0.0
    reconnect_attempts: int = 0

class DevicePool:
    """Manages a pool of iOS and Android devices with automatic reconnection"""
    
    def __init__(self, max_reconnect_attempts: int = 3, reconnect_interval: int = 5):
        self.devices: Dict[str, DeviceInfo] = {}
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_interval = reconnect_interval
        self.lock = threading.Lock()
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()
        self.logger = logging.getLogger(__name__)

    def start_monitoring(self):
        """Start monitoring device connections"""
        if self._monitor_thread is None:
            self._stop_monitoring.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_devices)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
            self.logger.info("Device monitoring started")

    def stop_monitoring(self):
        """Stop monitoring device connections"""
        if self._monitor_thread is not None:
            self._stop_monitoring.set()
            self._monitor_thread.join()
            self._monitor_thread = None
            self.logger.info("Device monitoring stopped")

    def _monitor_devices(self):
        """Monitor device connections and handle reconnections"""
        while not self._stop_monitoring.is_set():
            self._update_device_statuses()
            time.sleep(self.reconnect_interval)

    def _update_device_statuses(self):
        """Update status of all registered devices"""
        with self.lock:
            # Check Android devices
            android_devices = {dev.serial: dev for dev in adb.device_list()}
            
            # Check iOS devices
            ios_devices = {}
            try:
                for dev in tidevice.Usbmux().devices():
                    ios_devices[dev.udid] = dev
            except Exception as e:
                self.logger.error(f"Error checking iOS devices: {e}")

            # Update device statuses
            current_time = time.time()
            for device_id, device_info in self.devices.items():
                if device_info.type == DeviceType.ANDROID:
                    if device_id in android_devices:
                        self._update_device_status(device_id, "connected", current_time)
                    else:
                        self._handle_disconnected_device(device_id, current_time)
                else:  # iOS device
                    if device_id in ios_devices:
                        self._update_device_status(device_id, "connected", current_time)
                    else:
                        self._handle_disconnected_device(device_id, current_time)

    def _update_device_status(self, device_id: str, status: str, timestamp: float):
        """Update device status and reset reconnection attempts if connected"""
        device = self.devices[device_id]
        if device.status != status:
            self.logger.info(f"Device {device_id} status changed to {status}")
        device.status = status
        device.last_seen = timestamp
        if status == "connected":
            device.reconnect_attempts = 0

    def _handle_disconnected_device(self, device_id: str, timestamp: float):
        """Handle disconnected device and attempt reconnection"""
        device = self.devices[device_id]
        if device.status == "connected":
            self.logger.warning(f"Device {device_id} disconnected")
            device.status = "disconnected"
        
        if device.reconnect_attempts < self.max_reconnect_attempts:
            device.reconnect_attempts += 1
            self.logger.info(f"Attempting to reconnect device {device_id} (attempt {device.reconnect_attempts})")
            if self._try_reconnect(device):
                self._update_device_status(device_id, "connected", timestamp)
            else:
                device.last_seen = timestamp

    def _try_reconnect(self, device: DeviceInfo) -> bool:
        """Attempt to reconnect to a device"""
        try:
            if device.type == DeviceType.ANDROID:
                # Do not attempt implicit reconnect here; rely on actual device visibility
                return False
            else:  # iOS device
                # For iOS, we just check if it's visible to tidevice
                return device.id in [d.udid for d in tidevice.Usbmux().devices()]
        except Exception as e:
            self.logger.error(f"Error reconnecting to device {device.id}: {e}")
            return False

    def add_device(self, device_id: str = None, device_type: DeviceType = None, name: str = None, version: str = None, **kwargs) -> bool:
        """Add a new device to the pool.

        Supports both explicit params and dicts shaped like DeviceInfo (id, type, name, version).
        """
        # Accept kwargs shaped like DeviceInfo
        if device_id is None and "id" in kwargs:
            device_id = kwargs["id"]
        if device_type is None and "type" in kwargs:
            device_type = kwargs["type"]
        if name is None and "name" in kwargs:
            name = kwargs["name"]
        if version is None and "version" in kwargs:
            version = kwargs["version"]
        with self.lock:
            if device_id not in self.devices:
                self.devices[device_id] = DeviceInfo(
                    id=device_id,
                    type=device_type,
                    name=name,
                    version=version
                )
                self.logger.info(f"Added {device_type.value} device: {device_id} ({name}, {version})")
                return True
            return False

    def remove_device(self, device_id: str) -> bool:
        """Remove a device from the pool"""
        with self.lock:
            if device_id in self.devices:
                del self.devices[device_id]
                self.logger.info(f"Removed device: {device_id}")
                return True
            return False

    def get_device_info(self, device_id: str) -> Optional[DeviceInfo]:
        """Get information about a specific device"""
        with self.lock:
            return self.devices.get(device_id)

    def get_all_devices(self) -> List[DeviceInfo]:
        """Get information about all devices"""
        with self.lock:
            return list(self.devices.values())

    def get_connected_devices(self) -> List[DeviceInfo]:
        """Get list of currently connected devices"""
        with self.lock:
            return [dev for dev in self.devices.values() if dev.status == "connected"]

    def wait_for_device(self, device_id: str, timeout: int = 30) -> bool:
        """Wait for a specific device to become available"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Refresh device statuses based on current adb/tidevice visibility
            self._update_device_statuses()
            device = self.get_device_info(device_id)
            if device and device.status == "connected":
                return True
            time.sleep(1)
        return False 