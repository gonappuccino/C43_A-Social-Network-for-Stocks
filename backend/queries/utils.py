import decimal
delete_all_tables = '''
    DO $$ DECLARE
        r RECORD;
    BEGIN
        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
        END LOOP;
    END $$;
    '''


def decimal_to_float(value):
    """Convert Decimal or numeric types to float safely."""
    if value is None:
        return None
    if isinstance(value, decimal.Decimal):
        return float(value)
    return value