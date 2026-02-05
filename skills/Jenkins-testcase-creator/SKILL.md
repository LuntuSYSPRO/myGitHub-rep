---
name: Jenkins-testcase-creator
description: Use when creating test cases for SYSPRO Business Objects in the T900 test framework - guides through test creation with actual SYSPRO MCP execution to capture real outputs
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, mcp__syspro-enet__*, mcp__mssql__execute_sql
---

# SYSPRO Test Generator

**Core principle:** Create test files by EXECUTING actual SYSPRO transactions and capturing real outputs. Never fabricate XML.

## The Iron Law

**NO OUTPUT FILES WITHOUT EXECUTING THE ACTUAL TRANSACTION**

Creating test file structures without executing via SYSPRO MCP results in fabricated outputs that fail on first run.

## When to Use

- After modifying Business Object programs in C:\RND900\SOURCE\
- When code review identifies insufficient test coverage
- When new functionality needs test validation
- When bug fixes require additional test cases

## Mandatory Workflow

### Phase 1: Setup

```
1. Configure SYSPRO MCP connection (mcp__syspro-enet__syspro_configure)
2. Verify connection successful
3. Query SQL to find/verify test data exists
```

### Phase 2: Understand Existing Patterns (MANDATORY)

```
1. Read existing tests in C:\T900\[BUSOBJ]\
2. Identify next test number (T00001, T00002, etc.)
3. Match exact file naming and XML structure
4. **CRITICAL: Check how existing tests chain Pre_Tests**
   - Look at Pre_Test_*DOC.XML files
   - Note they use HARD-CODED values, NOT placeholders
   - Copy the exact patterns used
5. Get XML format from MCP: syspro_get_business_object_details
   - Use EXACT parameter/document structure from MCP
   - Do NOT invent elements or attributes
```

### Phase 3: Create Test with Execution

For EACH test file set:

| Step | Action | Tool |
|------|--------|------|
| **Pre-Test** | Execute COMFND query to capture baseline | `syspro_query` |
| **Base Test** | Execute the actual transaction | `syspro_query` or `syspro_transaction_post_ld` |
| **Post-Test** | Execute verification queries | `syspro_query` |

**CRITICAL: Capture the EXACT XML response and write it to output files**

### Phase 4: Verification

```
1. Query database to confirm data changes
2. Verify output XML matches SYSPRO format
3. Check all required files exist (including CFG files)
```

## Required Files Checklist

| File | Required | Purpose |
|------|----------|---------|
| `_TestInfo.XML` | Always | Test metadata (use `<Test>` root) |
| `Base_*.XML` | Always | Parameters |
| `Base_*DOC.XML` | If needed | Document input (xml-in) |
| `Base_*OUT.XML` | Always | Captured output |
| `Pre_Test_NN_*CFG.XML` | Per pre-test | **REQUIRED** - Configuration |
| `Post_Test_NN_*CFG.XML` | Per post-test | **REQUIRED** - Configuration |

## COMFND Pattern (Best Practice)

Use COMFND to verify data before/after transactions:

```
Pre_Test_01_COMFND.XML     → Query table (shows value BEFORE)
Pre_Test_01_COMFNDCFG.XML  → Config (EnetClass=query, EnetMethod=query)
Pre_Test_01_COMFNDOUT.XML  → Captured baseline

Base_WIPTMI.XML            → Transaction parameters
Base_WIPTMIDOC.XML         → Transaction document
Base_WIPTMIOUT.XML         → Captured transaction result

Post_Test_01_COMFND.XML    → Query same table (shows value AFTER)
Post_Test_01_COMFNDCFG.XML → Config
Post_Test_01_COMFNDOUT.XML → Captured result showing change
```

## COMFND XML Format (CRITICAL)

**NEVER use SQL-style WHERE clauses.** COMFND uses Expression blocks.

**WRONG - SQL syntax will fail:**
```xml
<Where>DispatchNote IN ('000000000000023', '000000000000024')</Where>
<Where>KeyInvoice = '000000000100536'</Where>
```

**CORRECT - Use Expression blocks:**
```xml
<Query xmlns:xsd="http://www.w3.org/2001/XMLSchema-instance" xsd:noNamespaceSchemaLocation="COMFND.XSD">
  <TableName>MdnDetailLpn</TableName>
  <ReturnRows>10</ReturnRows>
  <Columns>
    <Column>DispatchNote</Column>
    <Column>LicensePlateNumber</Column>
  </Columns>
  <Where>
    <Expression>
      <OpenBracket>(</OpenBracket>
      <Column>DispatchNote</Column>
      <Condition>EQ</Condition>
      <Value>000000000000023</Value>
      <CloseBracket>)</CloseBracket>
    </Expression>
    <Expression>
      <AndOr>Or</AndOr>
      <OpenBracket>(</OpenBracket>
      <Column>DispatchNote</Column>
      <Condition>EQ</Condition>
      <Value>000000000000024</Value>
      <CloseBracket>)</CloseBracket>
    </Expression>
  </Where>
</Query>
```

**ALWAYS check existing COMFND tests** in `C:\T900\**\*COMFND.XML` for correct format.

## Output XML Format

**WRONG - Do not fabricate:**
```xml
<QueryResults>
  <Row>...</Row>
</QueryResults>
```

**CORRECT - Use actual SYSPRO format:**
```xml
<WhmLpnDetail Language='05' Language2='EN' CssStyle='' DecFormat='1' ...>
  <HeaderDetails>
    <TableName>WhmLpnDetail</TableName>
    ...
  </HeaderDetails>
  <Row>...</Row>
  <RowsReturned>       1</RowsReturned>
</WhmLpnDetail>
```

Root element = Table name (with Language attributes)

## CFG File Format

Every Pre_Test/Post_Test MUST have a CFG file:

```xml
<?xml version="1.0" encoding="Windows-1252"?>
<!-- Copyright 1994-2026 SYSPRO Ltd.-->
<Test xmlns:xsd="http://www.w3.org/2001/XMLSchema-instance" xsd:noNamespaceSchemaLocation="Pre_Test.XSD">
  <BusObj>COMFND</BusObj>
  <EnetClass>query</EnetClass>
  <EnetMethod>query</EnetMethod>
  <XmlInput>Pre_Test_01_COMFND.XML</XmlInput>
  <XmlDocumentInput></XmlDocumentInput>
  <XmlOutput>Pre_Test_01_COMFNDOUT.XML</XmlOutput>
  <Operator>ADMIN</Operator>
  <Company>EDU1</Company>
  <LogonXmlInput></LogonXmlInput>
</Test>
```

## EnetClass/EnetMethod Reference

| BO Type | EnetClass | EnetMethod |
|---------|-----------|------------|
| Query (INVQRY, COMFND) | query | query |
| Setup Add | setup | add |
| Setup Update | setup | update |
| Transaction Post | transaction | post |

## Dataset Isolation

Each test runs on freshly restored dataset:
- NEVER assume data from previous test exists
- ALWAYS use Pre_Test to create required data
- PREFER existing data from base dataset

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| **Using @placeholder@ syntax** | **T900 DOES NOT support placeholders. Use hard-coded values from MCP execution.** |
| Missing `<Bins>` element | Check error response, add required elements |
| Lot number too long | DB stores 15 chars, BO accepts 10 - verify format |
| Job number format | Zero-pad to full length (000000000000165) |
| Fabricated output XML | Execute transaction, capture REAL response |
| Missing CFG files | Every Pre/Post test needs a CFG file |
| TransmissionReference too long | Max 14 characters - keep it short (e.g., "LPN-T35-01") |
| Memory leak warnings | Transaction may still process - verify with SQL query |
| Invalid status transition | Check error message for valid transitions (e.g., 3→5→7, not 3→7) |
| Inventing XML structure | **ALWAYS get XML format from MCP** using `syspro_get_business_object_details` |
| Wrong Customer/SalesOrder format | Check MCP sample - use exact format shown (e.g., `000010` not `000000000000010`) |
| **SQL-style WHERE in COMFND** | **WRONG:** `<Where>Column = 'value'</Where>` **CORRECT:** Use `<Expression>` blocks |
| Not checking existing tests | **ALWAYS** look at existing tests for the same BO pattern before creating new ones |

## Critical: Read Source Code First

Before creating tests, **read the business object source code** in `C:\RND900\SOURCE\[BUSOBJ].CBL`:

```
grep -n "Status" C:\RND900\SOURCE\SORTCD.CBL
```

Example discovery: SORTCD line 2268 shows `(a.DispatchNoteStatus = '7')` - dispatch notes MUST be status 7.

## Status Transition Reference (Sales Order/Dispatch)

| From Status | Valid Transitions | Business Object |
|-------------|-------------------|-----------------|
| 3 (Ready for invoicing) | 5, S, H | SORTDS |
| 5 | 7 (Ready for consolidation) | SORTDS |
| 7 | 8 (Consolidated) | SORTCD (automatic) |

**Flow for consolidation tests:** Create dispatch → SORTDS (3→5) → SORTDS (5→7) → SORTCD

## Complex Test Pattern (Multi-step Pre-tests)

Some tests require many chained pre-tests. Example SORTCD LPN consolidation:

```
Pre_Test_01: SORTOI  → Create sales order 1
Pre_Test_02: SORTOI  → Create sales order 2
Pre_Test_03: SORTDN  → Create dispatch note 1 with LPN
Pre_Test_04: SORTDN  → Create dispatch note 2 with LPN
Pre_Test_05: SORTDS  → Change DN1 status 3→5
Pre_Test_06: SORTDS  → Change DN1 status 5→7
Pre_Test_07: SORTDS  → Change DN2 status 3→5
Pre_Test_08: SORTDS  → Change DN2 status 5→7
Pre_Test_09: COMFND  → Verify MdnDetailLpn populated
Base:        SORTCD  → Run consolidation
Post_Test_01: COMFND → Verify MdnDetailLpnCons populated
```

## CRITICAL: NO PLACEHOLDER SYNTAX - USE HARD-CODED VALUES

**THE T900 FRAMEWORK DOES NOT SUPPORT VARIABLE PLACEHOLDERS.**

**NEVER use syntax like:**
- `@Pre_Test_01_SalesOrder@`
- `@Pre_Test_03_DispatchNoteNumber@`
- `@Base_Invoice@`

**This placeholder syntax DOES NOT EXIST in T900.** It will be treated as a literal string and the test will fail.

### The Correct Pattern: Hard-Coded Values

When Pre_Test files need to reference values from earlier pre-tests, use the **actual values that will be generated** on a fresh dataset restore.

**WRONG - Placeholder syntax doesn't exist:**
```xml
<SalesOrder>@Pre_Test_01_SalesOrder@</SalesOrder>
<DispatchNote>@Pre_Test_03_DispatchNoteNumber@</DispatchNote>
```

**CORRECT - Use hard-coded values from MCP execution:**
```xml
<SalesOrder>000895</SalesOrder>
<DispatchNote>000000000000023</DispatchNote>
```

### How to Get the Correct Values

1. Execute Pre_Test_01 via MCP → Note the generated SalesOrder (e.g., 000895)
2. Execute Pre_Test_02 via MCP → Note the generated SalesOrder (e.g., 000896)
3. Use these EXACT values in subsequent Pre_Test DOC files
4. Dataset restores are deterministic - same baseline = same generated numbers

### Verification: Check Existing Tests

Before creating chained pre-tests, **ALWAYS check existing T900 tests** for the same business object pattern:

```
C:\T900\[BUSOBJ]\T00001\Pre_Test_*DOC.XML
```

Existing tests will show hard-coded values, NOT placeholders.

### Example from Real T900 Test (SORTCD\T00001):

```xml
<!-- Pre_Test_01_SORTOIDOC.XML -->
<SalesOrder>221124</SalesOrder>  <!-- Hard-coded, not a placeholder -->

<!-- Pre_Test_02_SORTDNDOC.XML -->
<SalesOrder>889</SalesOrder>     <!-- Hard-coded, references existing data -->
```

## CRITICAL: Output Files Must Contain Generated Keys

**THE #1 MISTAKE: Writing output files with empty elements instead of actual values.**

Output files MUST contain the actual generated values from MCP execution.

### WRONG - Empty elements:
```xml
<Order>
  <SalesOrder/>           <!-- WRONG: Empty! -->
  <DispatchNoteNumber/>   <!-- WRONG: Empty! -->
</Order>
```

### CORRECT - Actual captured values:
```xml
<Order>
  <SalesOrder>000895</SalesOrder>
  <DispatchNoteNumber>000000000000023</DispatchNoteNumber>
</Order>
```

### Key Fields That MUST Be Captured (Never Empty):

| Business Object | Field | Example Value |
|-----------------|-------|---------------|
| SORTOI | `<SalesOrder>` | 000895 |
| SORTDN | `<DispatchNoteNumber>` | 000000000000023 |
| SORTCD | `<Invoice>` | 100536 |
| PORTOR | `<PurchaseOrder>` | 000000000000001 |
| WIPTJI | `<Job>` | 000000000000165 |
| INVTMR | `<Receipt>` | 000000000000001 |

### Validation Checklist for Output Files:

Before finalizing any test case, verify EVERY output file:

1. ☐ Execute the transaction via SYSPRO MCP
2. ☐ Copy the EXACT response into the output file
3. ☐ Verify generated keys have VALUES not empty elements
4. ☐ Verify with SQL that the generated value exists in database
5. ☐ Use the same hard-coded values in subsequent Pre_Test DOC files

## Red Flags - STOP

- Creating output files without executing transaction
- Guessing XML element names
- Output XML with `<QueryResults>` root
- Missing CFG files for Pre/Post tests
- Assuming data exists without querying
- **Empty elements for generated keys** (e.g., `<SalesOrder/>` instead of `<SalesOrder>000895</SalesOrder>`)
- Output files that don't match the actual SYSPRO response
- **Using @placeholder@ syntax** (e.g., `@Pre_Test_01_SalesOrder@`) - THIS DOES NOT EXIST IN T900
- **Inventing syntax not seen in existing tests** - ALWAYS check existing tests first

**All mean: Execute via SYSPRO MCP first, then copy the EXACT response. Use hard-coded values, not placeholders.**

## Quick Start Template

```
1. syspro_configure → Connect
2. Read C:\RND900\SOURCE\[BUSOBJ].CBL → Understand requirements (status checks, validations)
3. execute_sql → Find/verify test data exists
4. syspro_get_business_object_details → Get XML format
5. Plan pre-test chain → Identify all setup steps needed (may need 5-10 pre-tests)
6. For EACH pre-test:
   a. Execute transaction via MCP
   b. Write output file with EXACT response (including generated keys!)
   c. Verify generated key in database via SQL
   d. Confirm output file has actual value, NOT empty element
7. syspro_transaction_post_ld → Execute main transaction
8. Write Base output file with EXACT response (capture Invoice, etc.)
9. syspro_query (COMFND) → Verify changes in target table
10. Write Post_Test output files with actual data
11. FINAL CHECK: Review ALL output files - no empty elements for keys!
```

## Investigating Errors

When a transaction fails or returns empty:

1. **Check error message** - Often reveals valid options (e.g., "status can only be '5 / S / H'")
2. **Query the source table** - Verify data exists and has correct status
3. **Read source code** - Search for WHERE clauses to find hidden requirements
4. **Check related tables** - Some BOs require data in multiple tables

Example SQL investigation:
```sql
-- Check dispatch note status
SELECT DispatchNote, DispatchNoteStatus, Invoice FROM MdnMaster WHERE DispatchNote = '000000000000023'

-- Check if LPN data exists
SELECT * FROM MdnDetailLpn WHERE DispatchNote = '000000000000023'
```
