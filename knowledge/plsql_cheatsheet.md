# PL/SQL — practical cheat sheet

Original notes (not copied from Oracle docs).

## Where PL/SQL fits with Fusion and OIC
- Oracle Fusion SaaS does not let you deploy custom PL/SQL into the Fusion database. In BIP you write read-only SQL.
- PL/SQL is used in your own Oracle DB / Autonomous DB (ATP/ADW): staging tables, validation, transformation, stored procedures called from OIC with the **Database adapter**, ORDS REST endpoints, scheduler jobs.

## Block structure
```sql
DECLARE
  v_count NUMBER := 0;
BEGIN
  SELECT COUNT(*) INTO v_count FROM stg_invoices WHERE status = 'NEW';
  DBMS_OUTPUT.PUT_LINE('Rows: ' || v_count);
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE(SQLERRM);
    RAISE;
END;
/
```
- Types: `VARCHAR2`, `NUMBER`, `DATE`, `TIMESTAMP`, `BOOLEAN` (PL/SQL only), `CLOB`, `%TYPE` and `%ROWTYPE` to follow table definitions.

## Cursors
- Implicit cursor attributes after DML: `SQL%ROWCOUNT`, `SQL%FOUND`.
- Cursor FOR loop (simplest and efficient):
```sql
FOR r IN (SELECT id, amount FROM stg_invoices WHERE status = 'NEW') LOOP
  -- process r.id, r.amount
END LOOP;
```
- Explicit cursor: `OPEN` / `FETCH ... INTO` / `CLOSE`, with `%NOTFOUND`.
- `SYS_REFCURSOR` to return result sets from procedures/functions.

## Exceptions
- Predefined: `NO_DATA_FOUND` (ORA-01403), `TOO_MANY_ROWS` (ORA-01422), `DUP_VAL_ON_INDEX` (ORA-00001), `VALUE_ERROR` (ORA-06502), `ZERO_DIVIDE`, `INVALID_NUMBER` (ORA-01722), `CURSOR_ALREADY_OPEN`.
- Custom: declare an exception, or `RAISE_APPLICATION_ERROR(-20001, 'message')` (codes -20000 to -20999).
- Map an Oracle error to a name: `PRAGMA EXCEPTION_INIT(e_deadlock, -60);`
- Log both `SQLERRM` and `DBMS_UTILITY.FORMAT_ERROR_BACKTRACE` (line numbers) — `WHEN OTHERS` without logging or re-raising hides bugs.
- Handle errors per row inside loops if one bad row should not stop the batch.

## Procedures, functions, packages
```sql
CREATE OR REPLACE PACKAGE inv_pkg AS
  PROCEDURE load_batch(p_batch_id IN NUMBER, p_status OUT VARCHAR2);
  FUNCTION  is_valid(p_amount IN NUMBER) RETURN BOOLEAN;
END inv_pkg;
/
CREATE OR REPLACE PACKAGE BODY inv_pkg AS
  FUNCTION is_valid(p_amount IN NUMBER) RETURN BOOLEAN IS
  BEGIN
    RETURN p_amount IS NOT NULL AND p_amount > 0;
  END;

  PROCEDURE load_batch(p_batch_id IN NUMBER, p_status OUT VARCHAR2) IS
  BEGIN
    UPDATE stg_invoices SET status = 'LOADED' WHERE batch_id = p_batch_id;
    p_status := 'OK: ' || SQL%ROWCOUNT;
    COMMIT;
  EXCEPTION
    WHEN OTHERS THEN
      ROLLBACK;
      p_status := 'ERR: ' || SQLERRM;
  END;
END inv_pkg;
/
```
- Use packages to group related code, hide helpers (only in body), and keep state/constants.
- Parameter modes: `IN`, `OUT`, `IN OUT`; use `NOCOPY` for large collections when safe.

## Collections and bulk processing
- Types: associative array (`INDEX BY`), nested table, VARRAY.
- Avoid row-by-row loops with DML inside; use **BULK COLLECT** and **FORALL** to cut context switches:
```sql
DECLARE
  TYPE t_ids IS TABLE OF stg_invoices.id%TYPE;
  l_ids t_ids;
  CURSOR c IS SELECT id FROM stg_invoices WHERE status = 'NEW';
BEGIN
  OPEN c;
  LOOP
    FETCH c BULK COLLECT INTO l_ids LIMIT 1000;
    EXIT WHEN l_ids.COUNT = 0;
    FORALL i IN 1 .. l_ids.COUNT
      UPDATE stg_invoices SET status = 'PROCESSED' WHERE id = l_ids(i);
  END LOOP;
  CLOSE c;
  COMMIT;
END;
/
```
- `FORALL ... SAVE EXCEPTIONS` continues after errors; inspect `SQL%BULK_EXCEPTIONS`.
- Always use `LIMIT` with BULK COLLECT on big tables to protect memory.

## Dynamic SQL
- `EXECUTE IMMEDIATE 'UPDATE ' || DBMS_ASSERT.SIMPLE_SQL_NAME(p_table) || ' SET x = :1' USING p_val;`
- Always bind values (`USING`) — never concatenate user values (SQL injection, plus bad performance).
- `DBMS_SQL` when the number of columns/binds is unknown at compile time.

## Transactions
- `COMMIT`, `ROLLBACK`, `SAVEPOINT`. Decide who commits (usually the caller, not utility procedures).
- `PRAGMA AUTONOMOUS_TRANSACTION` for logging that must survive a rollback; the autonomous block must commit/rollback itself.

## Triggers
- Row-level (`FOR EACH ROW`) vs statement-level; `BEFORE`/`AFTER`/`INSTEAD OF`; compound triggers avoid mutating-table errors (ORA-04091). Keep triggers small.

## JSON / XML / files
- JSON: `JSON_OBJECT`, `JSON_ARRAYAGG`, `JSON_TABLE` (shred JSON into rows), `JSON_VALUE`, `JSON_QUERY`.
- XML: `XMLTYPE`, `XMLTABLE`, `XMLELEMENT`/`XMLAGG`.
- CSV/files: `UTL_FILE` (server directory objects), or external tables; in ADB use `DBMS_CLOUD`.
- `DBMS_SCHEDULER` for jobs; `DBMS_LOCK.SLEEP`/`DBMS_SESSION` for utilities (check privileges).

## Performance checklist
1. Prefer one set-based SQL statement over a loop.
2. Bulk collect + FORALL when you must loop.
3. Use bind variables.
4. Check the plan: `EXPLAIN PLAN FOR ...; SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);`
5. Index the columns used in joins/filters; avoid functions on indexed columns in `WHERE` (or use a function-based index).
6. Gather statistics (`DBMS_STATS`) after big loads.
7. Avoid `SELECT *` and unnecessary `DISTINCT`.
8. Keep transactions short; commit in sensible batches.

## Common errors cheat list
- ORA-01403 no data found — SELECT INTO returned nothing.
- ORA-01422 exact fetch returns more than requested number of rows.
- ORA-06502 character string buffer too small / numeric conversion.
- ORA-00001 unique constraint violated.
- ORA-01722 invalid number (bad string-to-number conversion).
- ORA-01843 / ORA-01861 date format problems — always use `TO_DATE(x, 'YYYY-MM-DD')` with an explicit mask.
- ORA-04091 mutating table.
- ORA-06512 is just the stack trace line reference.
- PLS-00201 identifier must be declared (often missing grant/synonym).
- ORA-00054 resource busy (locked row/table).
