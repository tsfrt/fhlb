from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, TypeAlias

from fastapi import Depends, Request

from ._defaults import ConfigDependency, ClientDependency, UserWorkspaceClientDependency
from ._headers import HeadersDependency

if TYPE_CHECKING:
    from ..services.lakebase import LakebasePool


def _get_lakebase(request: Request) -> "LakebasePool":
    """Lazily build and cache a Lakebase connection pool on app.state."""
    app = request.app
    pool = getattr(app.state, "lakebase_pool", None)
    if pool is None:
        from ..services.lakebase import LakebasePool

        cfg = app.state.config
        pool = LakebasePool(
            app.state.workspace_client, cfg.lakebase_instance, cfg.lakebase_database
        )
        app.state.lakebase_pool = pool
    return pool


class Dependencies:
    """FastAPI dependency injection shorthand for route handler parameters."""

    Client: TypeAlias = ClientDependency
    """Databricks WorkspaceClient using app-level service principal credentials.
    Recommended usage: `ws: Dependencies.Client`"""

    UserClient: TypeAlias = UserWorkspaceClientDependency
    """WorkspaceClient authenticated on behalf of the current user via OBO token.
    Requires the X-Forwarded-Access-Token header.
    Recommended usage: `user_ws: Dependencies.UserClient`"""

    Config: TypeAlias = ConfigDependency
    """Application configuration loaded from environment variables.
    Recommended usage: `config: Dependencies.Config`"""

    Headers: TypeAlias = HeadersDependency
    """Databricks Apps HTTP headers for the current request.
    Recommended usage: `headers: Dependencies.Headers`"""

    Lakebase: TypeAlias = Annotated["LakebasePool", Depends(_get_lakebase)]
    """Lakebase (Postgres) connection pool for app OLTP state.
    Recommended usage: `db: Dependencies.Lakebase`"""
