import os
import inspect
from datetime import datetime

class log:
    """provides colored logging for different levels (error, warning, debug, info)."""
    def __init__(self):
        self.red = "\033[0;31m"
        self.green = "\033[0;32m"
        self.blue = "\033[0;34m"
        self.yellow = "\033[1;33m"
        self.end = "\033[0m"

    def _get_info(self):
        """internal method to get timestamp, line number, and filename of the caller."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        stack = inspect.stack()[2]

        lineNumber = stack.lineno

        fileName = os.path.basename(stack.filename)

        return timestamp, lineNumber, fileName

    def error(self, message):
        timestamp, lineNumber, fileName = self._get_info()
        print(f"{self.red}[{lineNumber}][error][{fileName}][{timestamp}]: {message}{self.end}")

    def warning(self, message):
        timestamp, lineNumber, fileName = self._get_info()
        print(f"{self.yellow}[{lineNumber}][warning][{fileName}][{timestamp}]: {message}{self.end}")

    def debug(self, message):
        timestamp, lineNumber, fileName = self._get_info()
        print(f"{self.green}[{lineNumber}][debug][{fileName}][{timestamp}]: {message}{self.end}")

    def info(self, message):
        timestamp, lineNumber, fileName = self._get_info()
        print(f"{self.blue}[{lineNumber}][info][{fileName}][{timestamp}]: {message}{self.end}")