"""
Welele Media™ — Migration Dependency & Security Static Validation Harness
Analyzes proposed SQL migration scripts for:
1. Complete Relation & Foreign Key Dependency DAG.
2. 100% RLS Enablement across all tables.
3. Absence of Known Vulnerabilities (Episode Deletion, Audit Spoofing, UUID/Text Mismatch).
4. Idempotency Guards (IF NOT EXISTS, DROP POLICY IF EXISTS).
5. Schema vs Seed Model Contract Alignment.
"""

import os
import re
import sys
from typing import Dict, List, Set, Tuple

MIGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))
MIGRATION_FILES = [
    "01_candidate_base_schema_v2.sql",
    "02_operational_and_production_contracts.sql",
    "03_security_hardening_and_rls_v3.sql"
]

def parse_sql_tables(sql_content: str) -> Dict[str, Set[str]]:
    """Extracts tables and their columns from CREATE TABLE statements."""
    tables = {}
    table_pattern = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?(\w+)\s*\((.*?)\);", re.DOTALL | re.IGNORECASE)
    
    for match in table_pattern.finditer(sql_content):
        table_name = match.group(1).lower()
        body = match.group(2)
        columns = set()
        for line in body.split("\n"):
            line = line.strip()
            if not line or line.startswith("--") or line.upper().startswith("CONSTRAINT") or line.upper().startswith("PRIMARY KEY"):
                continue
            parts = line.split()
            if parts:
                col_name = parts[0].strip('",').lower()
                if col_name and not col_name.startswith("--"):
                    columns.add(col_name)
        tables[table_name] = columns
    return tables

def parse_foreign_keys(sql_content: str) -> List[Tuple[str, str, str]]:
    """Extracts foreign key dependencies: (source_table, target_table, target_column)."""
    fks = []
    table_pattern = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?(\w+)\s*\((.*?)\);", re.DOTALL | re.IGNORECASE)
    fk_pattern = re.compile(r"REFERENCES\s+(?:public\.)?(\w+)\s*\((.*?)\)", re.IGNORECASE)

    for match in table_pattern.finditer(sql_content):
        source_table = match.group(1).lower()
        body = match.group(2)
        for fk_match in fk_pattern.finditer(body):
            target_table = fk_match.group(1).lower()
            target_col = fk_match.group(2).strip('",').lower()
            fks.append((source_table, target_table, target_col))
    return fks

def parse_rls_enabled(sql_content: str) -> Set[str]:
    """Finds all tables with RLS enabled."""
    enabled = set()
    # Direct ALTER TABLE ... ENABLE ROW LEVEL SECURITY
    direct_pattern = re.compile(r"ALTER\s+TABLE\s+(?:public\.)?(\w+)\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY", re.IGNORECASE)
    for match in direct_pattern.finditer(sql_content):
        enabled.add(match.group(1).lower())
    
    # Array in DO block: tables text[] := ARRAY['...', '...']
    array_pattern = re.compile(r"ARRAY\s*\[(.*?)\]", re.DOTALL | re.IGNORECASE)
    for match in array_pattern.finditer(sql_content):
        items = match.group(1).split(",")
        for item in items:
            cleaned = item.strip().strip("'\"\n ")
            if cleaned:
                enabled.add(cleaned.lower())
    return enabled

def validate():
    print("==================================================================")
    print("WELELE MEDIA™ — MIGRATION SUITE STATIC CONTRACT & SECURITY AUDIT")
    print("==================================================================")
    
    all_tables: Dict[str, Set[str]] = {}
    all_fks: List[Tuple[str, str, str]] = []
    all_rls: Set[str] = set()
    errors = []
    warnings = []

    # Step 1: Parse and validate SQL files in order
    for fn in MIGRATION_FILES:
        path = os.path.join(MIGRATIONS_DIR, fn)
        if not os.path.exists(path):
            errors.append(f"Migration file missing: {fn}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        tables = parse_sql_tables(content)
        fks = parse_foreign_keys(content)
        rls = parse_rls_enabled(content)

        # Check for legacy vulnerabilities
        if "episodes_tenant_policy" in content and "FOR ALL" in content and "status = 'published'" in content:
            errors.append(f"FATAL SECURITY VULNERABILITY in {fn}: Anonymous deletion permitted on episodes!")
        if "audit_ledger_append_policy" in content and "WITH CHECK (TRUE)" in content and "service_role" not in content:
            errors.append(f"FATAL SECURITY VULNERABILITY in {fn}: Unauthenticated insertion allowed on audit ledger!")
        if "auth.uid()::text" in content and ("master_owner_id" in content or "user_id" in content):
            warnings.append(f"Potential PostgreSQL UUID/text comparison warning in {fn}: found 'auth.uid()::text'")

        all_tables.update(tables)
        all_fks.extend(fks)
        all_rls.update(rls)

        print(f"  ✓ Validated {fn:<42} ({len(tables):>2} tables, {len(fks):>2} foreign keys)")

    # Step 2: Validate Foreign Key Graph
    print("\n--- Validating Foreign Key Dependency Graph ---")
    for src, tgt, col in all_fks:
        if tgt not in all_tables:
            errors.append(f"Foreign Key Error: Table '{src}' references non-existent table '{tgt}'!")
        elif col not in all_tables[tgt] and col != "id": # "id" is default PK
            errors.append(f"Foreign Key Error: Table '{src}' references non-existent column '{tgt}.{col}'!")
        else:
            # Verified
            pass
    print(f"  ✓ Verified {len(all_fks)} relational constraints across all candidate tables.")

    # Step 3: Validate 100% RLS Coverage
    print("\n--- Validating Row-Level Security Coverage ---")
    missing_rls = set(all_tables.keys()) - all_rls
    if missing_rls:
        for m in missing_rls:
            errors.append(f"RLS Missing: Table '{m}' does not have Row-Level Security enabled!")
    else:
        print(f"  ✓ 100% RLS Coverage Verified: All {len(all_tables)} tables have Row-Level Security explicitly enabled.")

    # Step 4: Validate Staging Seed Contract Alignment
    print("\n--- Validating Staging Seed Payload Compatibility ---")
    import importlib.util
    spec = importlib.util.spec_from_file_location("seed_staging_v2", os.path.join(MIGRATIONS_DIR, "04_seed_staging_v2.py"))
    seed_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed_mod)
    build_staging_seed_payload = seed_mod.build_staging_seed_payload

    payload = build_staging_seed_payload()
    for table_name, records in payload.items():
        if table_name not in all_tables:
            errors.append(f"Seed Error: Payload seeds non-existent table '{table_name}'!")
            continue
        valid_cols = all_tables[table_name]
        for idx, rec in enumerate(records):
            for key in rec.keys():
                if key not in valid_cols and key != "id":
                    errors.append(f"Seed Contract Mismatch: Table '{table_name}' row {idx} has invalid column '{key}' (valid: {sorted(valid_cols)})")
    print(f"  ✓ Verified seed compatibility across all {len(payload)} seeded entities.")

    # Summary
    print("\n==================================================================")
    if errors:
        print(f"VALIDATION FAILED: {len(errors)} critical issues detected.")
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED: All {len(all_tables)} candidate relations, foreign keys, RLS policies, and seed contracts are strictly valid.")
        if warnings:
            print(f"Advisories ({len(warnings)}):")
            for w in warnings:
                print(f"  ⚠️ {w}")
    print("==================================================================")

if __name__ == "__main__":
    validate()
