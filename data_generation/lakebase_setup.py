"""
Create the fhlb_app database inside the fhlb-lakebase instance and print a
Prisma-ready DATABASE_URL (OAuth token as password, ~1h validity) for migration.
"""
import sys
import uuid

import psycopg
from databricks.sdk import WorkspaceClient

PROFILE = "fevm-serverless-stable-blj52t"
INSTANCE = "fhlb-lakebase"
APP_DB = "fhlb_app"

w = WorkspaceClient(profile=PROFILE)
inst = w.database.get_database_instance(name=INSTANCE)
cred = w.database.generate_database_credential(
    request_id=str(uuid.uuid4()), instance_names=[INSTANCE]
)
user = w.current_user.me().user_name
host = inst.read_write_dns
token = cred.token

# Connect to the default database to create fhlb_app
admin_conn = (
    f"host={host} dbname=databricks_postgres user={user} "
    f"password={token} sslmode=require"
)
with psycopg.connect(admin_conn, autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (APP_DB,))
        if cur.fetchone():
            print(f"database {APP_DB} already exists")
        else:
            cur.execute(f'CREATE DATABASE "{APP_DB}"')
            print(f"created database {APP_DB}")

if "--print-url" in sys.argv:
    from urllib.parse import quote
    url = (
        f"postgresql://{quote(user)}:{quote(token)}@{host}:5432/{APP_DB}"
        f"?sslmode=require"
    )
    print("DATABASE_URL=" + url)
