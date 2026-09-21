"""Grant the Databricks App service principal privileges on the fhlb_app tables.

The app SP connects to Lakebase as its own Postgres role (named by its client_id).
The tables were created under the developer's role during migration, so the SP
needs explicit grants plus default privileges for anything created later.
"""
import socket
import time
import uuid

import psycopg
from databricks.sdk import WorkspaceClient

PROFILE = "fevm-serverless-stable-blj52t"
INSTANCE = "fhlb-lakebase"
APP_DB = "fhlb_app"
SP_CLIENT_ID = "79bc1f41-4f71-4f13-b70a-06675cea69d4"

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
me = w.current_user.me().user_name
conn_str = (
    f"host={host} {('hostaddr=' + hostaddr) if hostaddr else ''} dbname={APP_DB} "
    f"user={me} password={cred.token} sslmode=require"
)

with psycopg.connect(conn_str, autocommit=True) as conn, conn.cursor() as cur:
    cur.execute("SELECT rolname FROM pg_roles WHERE rolname = %s", (SP_CLIENT_ID,))
    role_exists = cur.fetchone() is not None
    print("SP role present:", role_exists, SP_CLIENT_ID)

    role = f'"{SP_CLIENT_ID}"'
    stmts = [
        f"GRANT USAGE ON SCHEMA public TO {role}",
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {role}",
        f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {role}",
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {role}",
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {role}",
    ]
    for s in stmts:
        try:
            cur.execute(s)
            print("OK:", s)
        except Exception as e:  # noqa: BLE001
            print("ERR:", s, "->", e)
