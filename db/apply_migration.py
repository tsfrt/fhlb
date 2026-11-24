"""Apply the Prisma-generated migration SQL to the Lakebase fhlb_app database."""
import os
import pathlib
import uuid

import psycopg
from databricks.sdk import WorkspaceClient

PROFILE = os.environ.get("FHLB_PROFILE", "fevm-serverless-stable-blj52t")
INSTANCE = os.environ.get("FHLB_LAKEBASE_INSTANCE", "fhlb-lakebase")
APP_DB = os.environ.get("FHLB_LAKEBASE_DB", "fhlb_app")

sql = pathlib.Path(__file__).parent.joinpath("prisma/migrations/init.sql").read_text()

w = WorkspaceClient(profile=PROFILE)
inst = w.database.get_database_instance(name=INSTANCE)
cred = w.database.generate_database_credential(
    request_id=str(uuid.uuid4()), instance_names=[INSTANCE]
)
import socket
host = inst.read_write_dns
hostaddr = None
for _ in range(5):
    try:
        hostaddr = socket.gethostbyname(host)
        break
    except socket.gaierror:
        import time
        time.sleep(2)
conn_str = (
    f"host={host} {('hostaddr=' + hostaddr) if hostaddr else ''} dbname={APP_DB} "
    f"user={w.current_user.me().user_name} password={cred.token} sslmode=require"
)
with psycopg.connect(conn_str, autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name"
        )
        tables = [r[0] for r in cur.fetchall()]
print("tables in fhlb_app.public:", tables)
