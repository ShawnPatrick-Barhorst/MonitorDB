from monitordb.config import DB_PATH
from monitordb.db.schema import init_tables

init_tables(DB_PATH)
