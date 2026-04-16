#!/bin/bash
# ==============================================================================
# Diagnostic script: check why call_records data is not showing
# Run on server: bash scripts/check_db.sh
# ==============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "=============================================="
echo "  AVA Database Diagnostic"
echo "=============================================="
echo ""

# ------ 1. Docker containers ------
echo -e "${CYAN}[1/7] Docker containers status${NC}"
echo "----------------------------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "postgres|admin_ui|customer_portal|ai_engine" || echo -e "${RED}No relevant containers found!${NC}"
echo ""

# ------ 2. PostgreSQL connectivity ------
echo -e "${CYAN}[2/7] PostgreSQL connectivity${NC}"
echo "----------------------------------------------"
if docker exec postgres pg_isready -U ava_user -d ava_db 2>/dev/null; then
    echo -e "${GREEN}OK - PostgreSQL is accepting connections${NC}"
else
    echo -e "${RED}FAIL - PostgreSQL is NOT reachable${NC}"
    exit 1
fi
echo ""

# ------ 3. Table existence & schema ------
echo -e "${CYAN}[3/7] Table schema check${NC}"
echo "----------------------------------------------"
echo "--- Tables in database ---"
docker exec postgres psql -U ava_user -d ava_db -c "\dt" 2>&1
echo ""
echo "--- call_records columns ---"
docker exec postgres psql -U ava_user -d ava_db -c "\d call_records" 2>&1
echo ""

# ------ 4. Row counts ------
echo -e "${CYAN}[4/7] Row counts${NC}"
echo "----------------------------------------------"
docker exec postgres psql -U ava_user -d ava_db -c "
SELECT 'call_records' as table_name, COUNT(*) as rows FROM call_records
UNION ALL
SELECT 'outbound_campaigns', COUNT(*) FROM outbound_campaigns
UNION ALL
SELECT 'outbound_leads', COUNT(*) FROM outbound_leads
UNION ALL
SELECT 'outbound_attempts', COUNT(*) FROM outbound_attempts;
" 2>&1
echo ""

# ------ 5. Sample data ------
echo -e "${CYAN}[5/7] Sample data (first 3 call_records)${NC}"
echo "----------------------------------------------"
docker exec postgres psql -U ava_user -d ava_db -c "
SELECT id, call_id, caller_number, outcome, start_time, tenant_id, is_outbound
FROM call_records
ORDER BY start_time DESC
LIMIT 3;
" 2>&1
echo ""

# ------ 6. Check critical columns ------
echo -e "${CYAN}[6/7] Critical column check${NC}"
echo "----------------------------------------------"

# Check is_outbound
HAS_OUTBOUND=$(docker exec postgres psql -U ava_user -d ava_db -tAc "
SELECT COUNT(*) FROM information_schema.columns
WHERE table_name='call_records' AND column_name='is_outbound';
" 2>&1)
if [ "$HAS_OUTBOUND" = "1" ]; then
    echo -e "${GREEN}OK - is_outbound column EXISTS${NC}"
else
    echo -e "${RED}MISSING - is_outbound column NOT FOUND${NC}"
    echo "  Fix: docker exec postgres psql -U ava_user -d ava_db -c \"ALTER TABLE call_records ADD COLUMN is_outbound INTEGER DEFAULT 0;\""
fi

# Check tenant_id
HAS_TENANT=$(docker exec postgres psql -U ava_user -d ava_db -tAc "
SELECT COUNT(*) FROM information_schema.columns
WHERE table_name='call_records' AND column_name='tenant_id';
" 2>&1)
if [ "$HAS_TENANT" = "1" ]; then
    echo -e "${GREEN}OK - tenant_id column EXISTS${NC}"
else
    echo -e "${RED}MISSING - tenant_id column NOT FOUND${NC}"
    echo "  Fix: docker exec postgres psql -U ava_user -d ava_db -c \"ALTER TABLE call_records ADD COLUMN tenant_id TEXT;\""
fi

# Check tenant_id values
if [ "$HAS_TENANT" = "1" ]; then
    TENANT_NULL=$(docker exec postgres psql -U ava_user -d ava_db -tAc "
    SELECT COUNT(*) FROM call_records WHERE tenant_id IS NULL;
    " 2>&1)
    TENANT_SET=$(docker exec postgres psql -U ava_user -d ava_db -tAc "
    SELECT COUNT(*) FROM call_records WHERE tenant_id IS NOT NULL;
    " 2>&1)
    echo ""
    echo "  tenant_id IS NULL : $TENANT_NULL rows"
    echo "  tenant_id IS SET  : $TENANT_SET rows"
    if [ "$TENANT_NULL" != "0" ] && [ "$TENANT_SET" = "0" ]; then
        echo -e "  ${YELLOW}WARNING - All rows have NULL tenant_id!${NC}"
        echo "  Customer Portal uses tenantQuery() which filters by tenant_id."
        echo "  If tenant_id is NULL, NO rows will be returned."
        echo ""
        echo "  Fix: docker exec postgres psql -U ava_user -d ava_db -c \"UPDATE call_records SET tenant_id = 'tenant-uuid-abc-123' WHERE tenant_id IS NULL;\""
    fi
fi
echo ""

# ------ 7. .env check ------
echo -e "${CYAN}[7/7] Environment variable check (from .env)${NC}"
echo "----------------------------------------------"

ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    ENV_FILE="$(dirname "$0")/../.env"
fi

if [ -f "$ENV_FILE" ]; then
    CH_ENABLED=$(grep -E "^CALL_HISTORY_ENABLED=" "$ENV_FILE" | cut -d= -f2 | tr -d '[:space:]')
    DB_URL=$(grep -E "^DATABASE_URL=" "$ENV_FILE" | cut -d= -f2- | tr -d '[:space:]')

    if [ "$CH_ENABLED" = "true" ] || [ "$CH_ENABLED" = "1" ]; then
        echo -e "${GREEN}OK - CALL_HISTORY_ENABLED=$CH_ENABLED${NC}"
    else
        echo -e "${RED}PROBLEM - CALL_HISTORY_ENABLED=$CH_ENABLED (should be 'true')${NC}"
        echo "  Fix: sed -i 's/CALL_HISTORY_ENABLED=.*/CALL_HISTORY_ENABLED=true/' .env"
    fi

    if echo "$DB_URL" | grep -q "^postgresql://"; then
        echo -e "${GREEN}OK - DATABASE_URL starts with postgresql://${NC}"
    else
        echo -e "${RED}PROBLEM - DATABASE_URL='$DB_URL' (should start with postgresql://)${NC}"
    fi
else
    echo -e "${YELLOW}WARNING - .env file not found${NC}"
fi

echo ""

# ------ 8. Container logs (last errors) ------
echo -e "${CYAN}[BONUS] Recent errors from admin_ui & customer_portal${NC}"
echo "----------------------------------------------"
echo "--- admin_ui (last 10 error lines) ---"
docker logs admin_ui 2>&1 | grep -iE "error|exception|traceback|fail" | tail -10 || echo "(no errors found)"
echo ""
echo "--- customer_portal (last 10 error lines) ---"
docker logs customer_portal 2>&1 | grep -iE "error|exception|fail|column" | tail -10 || echo "(no errors found)"
echo ""

echo "=============================================="
echo "  Diagnostic complete!"
echo "=============================================="
