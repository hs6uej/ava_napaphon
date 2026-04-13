import logging
from typing import Optional, Dict, Any
from .db_connection import get_db_connection, is_postgres

logger = logging.getLogger(__name__)

class TenantManager:
    """Manages multi-tenant resolution and configuration lookup."""

    def __init__(self):
        self._cache_dids: Dict[str, Dict[str, Any]] = {}  # phone -> tenant_info
        self._cache_settings: Dict[str, Dict[str, Any]] = {}  # tenant_id -> settings
        self._cache_azure: Dict[str, str] = {}  # azure_oid -> tenant_id

    async def resolve_tenant_by_did(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Look up which tenant owns a specific dialed number (DID).
        
        Returns:
            Dict with tenant_id and context_name, or None if not found.
        """
        if not phone_number:
            return None
        
        # Quick cache check
        if phone_number in self._cache_dids:
            return self._cache_dids[phone_number]

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            placeholder = '%s' if is_postgres() else '?'
            query = f"SELECT tenant_id, context_name FROM tenant_dids WHERE phone_number = {placeholder} AND is_active = 1"
            
            cursor.execute(query, (phone_number,))
            row = cursor.fetchone()
            
            if row:
                res = {
                    "tenant_id": row["tenant_id"],
                    "context_name": row["context_name"]
                }
                self._cache_dids[phone_number] = res
                return res
            
            return None
        except Exception as e:
            logger.error(f"Error resolving tenant for DID {phone_number}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    async def resolve_tenant_by_azure_oid(self, azure_oid: str) -> Optional[str]:
        """Find the local tenant_id associated with an Azure Object ID."""
        if not azure_oid:
            return None
        
        if azure_oid in self._cache_azure:
            return self._cache_azure[azure_oid]

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            placeholder = '%s' if is_postgres() else '?'
            query = f"SELECT id FROM tenants WHERE azure_oid = {placeholder}"
            
            cursor.execute(query, (azure_oid,))
            row = cursor.fetchone()
            
            if row:
                t_id = row["id"]
                self._cache_azure[azure_oid] = t_id
                return t_id
            
            return None
        except Exception as e:
            logger.error(f"Error resolving tenant for Azure OID {azure_oid}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    async def get_tenant_settings(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Fetch custom settings (prompt, greeting, etc.) for a tenant."""
        if not tenant_id:
            return None

        if tenant_id in self._cache_settings:
            return self._cache_settings[tenant_id]

        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            placeholder = '%s' if is_postgres() else '?'
            query = f"SELECT greeting_message, system_prompt, transfer_number, working_hours_json FROM tenant_settings WHERE tenant_id = {placeholder}"
            
            cursor.execute(query, (tenant_id,))
            row = cursor.fetchone()
            
            if row:
                res = {
                    "greeting": row["greeting_message"],
                    "prompt": row["system_prompt"],
                    "transfer_number": row["transfer_number"],
                    "working_hours": row["working_hours_json"]
                }
                self._cache_settings[tenant_id] = res
                return res
            
            return None
        except Exception as e:
            logger.error(f"Error fetching settings for tenant {tenant_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def clear_cache(self):
        """Clear the resolution caches (use when DB updates occur)."""
        self._cache_dids.clear()
        self._cache_settings.clear()

# Global instance
tenant_manager = TenantManager()
