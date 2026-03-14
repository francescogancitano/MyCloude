from lib.database import DatabaseManager 
from schemas import Device 
from lib import logger

import psutil as p 
import os

log = logger.log()
megabyte = 1024 * 1024

class ResourceManager:
    def __init__(self):
        """initializes the resource manager, setting procfs path for containers."""
        log.info("initializing resource manager")
        procfs_path = os.getenv("PROCFS_PATH")
        if procfs_path and hasattr(p, "PROCFS_PATH"):
            p.PROCFS_PATH = procfs_path

        self.metrics_root_path = os.getenv("METRICS_ROOT_PATH", "/")
        self.db = DatabaseManager()
        
    def getCpuUsage(self):
        return p.cpu_percent(interval=1)

    def getCpuTemperature(self):
        temps = p.sensors_temperatures()
        if not temps:
            return 0.0

        for entries in temps.values():
            if entries:
                return float(entries[0].current)
        return 0.0
    
    def getRamUsed(self):
        return p.virtual_memory().used / megabyte

    def getRamTotal(self):
        return p.virtual_memory().total / megabyte

    def getDiskUsed(self):
        return p.disk_usage(self.metrics_root_path).used / megabyte

    def getDiskTotal(self):
        return p.disk_usage(self.metrics_root_path).total / megabyte

    def getNetworkIn(self):
        return p.net_io_counters().bytes_recv / 1024

    def getNetworkOut(self):
        return p.net_io_counters().bytes_sent / 1024

    def InsertDataIntoDatabase(self):
        """collects all system metrics and inserts them into the database."""
        try:
            device = Device(
                cpuUsedPct     = self.getCpuUsage(),
                cpuTemperature = self.getCpuTemperature(),
                ramUsedInMb  = self.getRamUsed(),
                ramTotalInMb = self.getRamTotal(),
                diskUsedInMb  = self.getDiskUsed(),
                diskTotalInMb = self.getDiskTotal(),
                networkTrafficIn  = self.getNetworkIn(),
                networkTrafficOut = self.getNetworkOut()
            )
            
            log.info("calling database function")
            
            result = self.db.insertSystemMetrics(device)
            
            if not result:
                log.error("the database encountered issues during data insertion")
                return False

            log.info("the data has been sent correctly")
            return True

        except Exception as e:
            log.error(e)
            return False

    def close(self):
        self.db.close()

    
if __name__ == "__main__":
    # for testing purposes
    rs = ResourceManager()
    print("resource function: ", rs.InsertDataIntoDatabase())