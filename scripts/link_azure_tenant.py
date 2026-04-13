import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.db_connection import get_db_connection, is_postgres

def link_tenant_to_azure(tenant_name_or_id: str, azure_oid: str):
    """Links a local tenant account to an Azure AD user."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Find the tenant
        placeholder = '%s' if is_postgres() else '?'
        cursor.execute(f"SELECT id, name FROM tenants WHERE id = {placeholder} OR name = {placeholder}", 
                       (tenant_name_or_id, tenant_name_or_id))
        row = cursor.fetchone()
        
        if not row:
            print(f"❌ Error: Tenant '{tenant_name_or_id}' not found.")
            return

        tenant_id = row["id"]
        tenant_name = row["name"]

        # 2. Update the azure_oid
        cursor.execute(f"UPDATE tenants SET azure_oid = {placeholder} WHERE id = {placeholder}", 
                       (azure_oid, tenant_id))
        conn.commit()
        
        print(f"✅ Success: Linked Tenant '{tenant_name}' ({tenant_id}) to Azure OID: '{azure_oid}'")
        print(f"Now this user can login to the Customer Portal using their Microsoft account.")

    except Exception as e:
        print(f"❌ Error linking tenant: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python link_azure_tenant.py <tenant_name_or_id> <azure_oid>")
        sys.exit(1)
    
    link_tenant_to_azure(sys.argv[1], sys.argv[2])
