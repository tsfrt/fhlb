"""Lakebase (Postgres) access for app OLTP state, with OAuth token refresh.

Tokens issued by ``generate_database_credential`` expire after ~1h, so we cache
and refresh on an interval. DNS on some hosts is flaky, so we resolve to an IP and
pass ``hostaddr`` to psycopg (keeping ``host`` for TLS SNI/cert validation).
"""
from __future__ import annotations

import socket
import threading
import time
import uuid
from contextlib import contextmanager

import psycopg
from databricks.sdk import WorkspaceClient

from ..core import logger

_TOKEN_TTL = 50 * 60  # refresh well before the 1h expiry


class LakebasePool:
    def __init__(self, ws: WorkspaceClient, instance: str, database: str):
        self._ws = ws
        self._instance = instance
        self._database = database
        self._lock = threading.Lock()
        self._token: str | None = None
        self._token_ts: float = 0.0
        self._host: str | None = None
        self._hostaddr: str | None = None
        self._user: str | None = None

    def _refresh(self) -> None:
        inst = self._ws.database.get_database_instance(name=self._instance)
        cred = self._ws.database.generate_database_credential(
            request_id=str(uuid.uuid4()), instance_names=[self._instance]
        )
        self._host = inst.read_write_dns
        try:
            self._hostaddr = socket.gethostbyname(self._host) if self._host else None
        except socket.gaierror:
            self._hostaddr = None
        self._user = self._ws.current_user.me().user_name
        self._token = cred.token
        self._token_ts = time.time()
        logger.info("Refreshed Lakebase credential for %s", self._instance)

    def _conn_str(self) -> str:
        with self._lock:
            if not self._token or (time.time() - self._token_ts) > _TOKEN_TTL:
                self._refresh()
            hostaddr = f"hostaddr={self._hostaddr} " if self._hostaddr else ""
            return (
                f"host={self._host} {hostaddr}dbname={self._database} "
                f"user={self._user} password={self._token} sslmode=require"
            )

    @contextmanager
    def connection(self):
        conn = psycopg.connect(self._conn_str(), autocommit=True)
        try:
            yield conn
        finally:
            conn.close()

    def query(self, sql: str, params: tuple | None = None) -> list[dict]:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(sql, params or ())
            if cur.description is None:
                return []
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def execute(self, sql: str, params: tuple | None = None) -> None:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(sql, params or ())
