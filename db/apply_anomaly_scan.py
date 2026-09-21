"""Apply the anomaly_scan migration to the Lakebase fhlb_app database (idempotent)."""
import pathlib
import socket
import time
import uuid

import psycopg
from databricks.sdk import WorkspaceClient

PROFILE = "fevm-serverless-stable-blj52t"
INSTANCE = "fhlb-lakebase"
APP_DB = "fhlb_app"

sql = pathlib.Path(__file__).parent.joinpath("prisma/migrations/002_anomaly_scan.sql").read_text()

w = WorkspaceClient(profile=PROFILE)
inst = w.database.get_database_instance(name=INSTANCE)
cred = w.database.generate_database_credential(
    request_id=str(uuid.uuid4()), instance_names=[INSTANCE]
)
host = inst.read_write_dns
hostaddr = None
for _ in range(5):
    try:
        hostaddr = socket.gethostbyname(host)
        break
    except socket.gaierror:
        time.sleep(2)
conn_str = (
    f"host={host} {('hostaddr=' + hostaddr) if hostaddr else ''} dbname={APP_DB} "
    f"user={w.current_user.me().user_name} password={cred.token} sslmode=require"
)
with psycopg.connect(conn_str, autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='anomaly_scan' ORDER BY ordinal_position"
        )
        cols = [r[0] for r in cur.fetchall()]
print("anomaly_scan columns:", cols)
