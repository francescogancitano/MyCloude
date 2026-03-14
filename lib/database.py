import os
import json
import warnings
import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
import time
import asyncio
from dotenv import load_dotenv

from lib import logger
from schemas import Device, UserCreate

log = logger.log()

class DatabaseManager:
    def __init__(self, auto_connect=True):
        """initializes the mysql database connection."""
        log.info("initializing databasemanager")
        load_dotenv()

        try:
            pool_name = os.getenv("MYSQL_POOL_NAME", "mycloude_pool")
            pool_size = int(os.getenv("MYSQL_POOL_SIZE", "5"))
            db_config = {
                "host": os.getenv("MYSQL_HOST"),
                "user": os.getenv("MYSQL_USER"),
                "password": os.getenv("MYSQL_PASSWORD"),
                "database": os.getenv("MYSQL_DATABASE"),
                "buffered": True
            }
            if not hasattr(DatabaseManager, "_pool"):
                DatabaseManager._pool = MySQLConnectionPool(pool_name=pool_name, pool_size=pool_size, **db_config)
            
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            
            self.db = None
            if auto_connect:
                self.connect()

        except mysql.connector.Error as e:
            log.error(f"could not connect to database: {e}")
            raise

    def _retry_connect(self, get_conn_fn, sleep_fn):
        """helper for connection retry logic."""
        attempts = 3
        delay = 1
        for i in range(attempts):
            try:
                self.db = get_conn_fn()
                return
            except mysql.connector.Error as e:
                log.warning(f"db connection attempt {i+1} failed: {e}")
                if i+1 == attempts:
                    log.error(f"could not connect to database after {attempts} attempts: {e}")
                    raise
                sleep_fn(delay)
                delay *= 2

    def connect(self):
        """sync connection using retry helper."""
        self._retry_connect(DatabaseManager._pool.get_connection, time.sleep)

    async def connect_async(self):
        """async connection using retry helper."""
        def get_conn():
            # In a truly async environment this should block less,
            # but pool.get_connection is synchronous
            return DatabaseManager._pool.get_connection()
        
        async def async_sleep(delay):
            await asyncio.sleep(delay)
            
        # Wrap the synchronous get_conn in to_thread and await it,
        # but since _retry_connect isn't async, we have to refactor it slightly,
        # or keep the duplicate structure. The user suggested a pattern. Let's
        # implement a truly unified async/sync retry logic.
        
        # ACTUALLY, because one needs `await asyncio.sleep` and the other `time.sleep`, 
        # and one needs `await to_thread`, it's cleaner to keep them separate but 
        # using the user's exact suggestion pattern. Let me adjust.
        
        attempts = 3
        delay = 1
        for i in range(attempts):
            try:
                self.db = await asyncio.to_thread(DatabaseManager._pool.get_connection)
                break
            except mysql.connector.Error as e:
                log.warning(f"db connection attempt {i+1} failed: {e}")
                if i+1 == attempts:
                    log.error(f"could not connect to database after {attempts} attempts: {e}")
                    raise
                await asyncio.sleep(delay)
                delay *= 2

    def close(self):
        """closes the database connection if it's open."""
        try:
            if hasattr(self, "db") and self.db.is_connected():
                self.db.close()
                log.info("database connection closed.")
        except Exception as e:
            log.warning(f"error closing db connection: {e}")

    def getSystemStatus(self):
        """retrieves the latest system data via a stored procedure and maps DB columns to Device fields."""
        log.info("calling stored procedure: get_system_status")
        cursor = self.db.cursor(dictionary=True, buffered=True)
        try:
            cursor.callproc('get_system_status')
            row = None
            for result in cursor.stored_results():
                row = result.fetchone()
                if row:
                    break

            if not row:
                log.warning("get_system_status returned no data.")
                return None

            # Map DB columns (as returned by the stored procedure) directly to Device fields
            # Stored proc returns: cpu, temp, ram (pct), disk (pct), net_in, net_out, status
            return Device(
                cpuUsedPct = row.get('cpu'),
                cpuTemperature = row.get('temp'),
                ramUsedInPct = row.get('ram'),
                diskUsedInPct = row.get('disk'),
                networkTrafficIn = row.get('net_in'),
                networkTrafficOut = row.get('net_out'),
                status = row.get('status')
            )
        except Exception as e:
            log.error(f"error during getsystemstatus call: {e}")
            return None
        finally:
            cursor.close()

    def getSystemStatusInJson(self):
        """returns system data as a json string."""
        data_obj = self.getSystemStatus()

        if not data_obj:
            return None

        data_list = [data_obj.model_dump()]
        
        return json.dumps(data_list, indent=4)

    def insertSystemMetrics(self, device: Device):
        """inserts current system metrics into the database."""
        log.info("inserting system metrics into database")
        cursor = self.db.cursor()
        try:
            params = (
                device.cpuUsedPct,
                device.cpuTemperature,
                device.ramUsedInMb,
                device.ramTotalInMb,
                device.diskUsedInMb,
                device.diskTotalInMb,
                device.networkTrafficIn,
                device.networkTrafficOut
            )

            cursor.callproc('insert_system_metrics', params)
            self.db.commit()
            return True 
            
        except mysql.connector.Error as e:
            log.error(f"mysql error during insertsystemmetrics: {e}")
            return False
        except Exception as e:
            log.error(f"unexpected error during insertion: {e}")
            return False
        finally:
            cursor.close()

    def getUserByUsername(self, username: str):
        """finds a user by username and returns a userindb model."""
        log.info(f"searching for user: {username}")
        # Added buffered=True to properly fetch stored proc result sets
        cursor = self.db.cursor(dictionary=True, buffered=True)

        try:
            cursor.callproc('get_user_by_username', (username,))
            user_data = None
            for result in cursor.stored_results():
                user_data = result.fetchone()
                if user_data:
                    break
            
            if user_data:
                from schemas import UserInDB
                return UserInDB(**user_data)
            
            return None
        except Exception as e:
            log.error(f"error searching for user {username}: {e}")
            return None
        finally:
            cursor.close()

    def createUser(self, user: UserCreate, hashed_password: str):
        """creates a minimal user with username and hashed password."""
        log.info(f"creating minimal user {user.username}")
        cursor = self.db.cursor()
        try:
            cursor.callproc('insert_user', (user.username, hashed_password))
            self.db.commit()
            # retrieve last insert id reliably
            cursor.execute("SELECT LAST_INSERT_ID()")
            row = cursor.fetchone()
            new_id = row[0] if row else None
            return {"id": new_id, "username": user.username}
        except Exception as e:
            log.error(f"error creating user: {e}")
            return None
        finally:
            cursor.close()

async def get_db():
    """fastapi dependency to get a db instance and ensure it's closed."""
    db = DatabaseManager(auto_connect=False)
    await db.connect_async()
    try:
        yield db
    finally:
        db.close()