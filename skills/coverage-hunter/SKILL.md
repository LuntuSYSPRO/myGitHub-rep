---
name: coverage-hunter
description: Use when analyzing code coverage reports to create test cases for uncovered COBOL code blocks - parses HTML coverage reports and systematically creates tests to maximize coverage
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, mcp__syspro-enet__*, mcp__mssql__execute_sql
---

# Coverage Hunter - Test Generation from Code Coverage Analysis

**Core principle:** Analyze code coverage HTML reports to identify uncovered code blocks, then create comprehensive test cases to maximize coverage by EXECUTING actual SYSPRO transactions and capturing real outputs.

## The Iron Laws

**1. NO OUTPUT FILES WITHOUT EXECUTING THE ACTUAL TRANSACTION**

Creating test file structures without executing via SYSPRO MCP results in fabricated outputs that fail on first run.

**2. ALL OUTPUT DATA MUST COME FROM SYSPRO MCP CALLS ONLY**

- SQL errors (e.g., "Key not found on table") are NOT valid test outputs - they are infrastructure errors
- System errors (e.g., "memory leak in RMATRL") are NOT valid test outputs - they are runtime errors
- Only business object validation responses (with `<ErrorNumber>`, `<ErrorDescription>`) are valid outputs
- If a test scenario produces a SQL or system error, REMOVE THAT TEST - do not write the error as output

**3. THE MCP TOOL RETURNS PARSED TEXT, NOT RAW XML**

The `syspro_transaction_post_ld` tool returns human-readable parsed output. You MUST reconstruct the XML using the correct SYSPRO format (see "Transaction Output XML Format" section below). The field names, values, error numbers, and descriptions from MCP are accurate - but the XML structure must follow SYSPRO's actual format.

## When to Use

- After nightly code coverage runs identify uncovered code blocks
- When coverage reports show red (uncovered) code that should be testable
- When systematically improving test coverage for a business object
- When setup options might enable additional code paths

## Input Requirements

User provides: **Business Object name** (e.g., INVQ9C)

The skill will:
1. Locate the coverage report at `K:\CodeCoverage\[Module]\[BusinessObject]\Syspro_[BusinessObject].htm`
2. Search across modules (Distribution, Financial, Manufacturing, Core, Emerging Technology) if needed
3. Parse the HTML to identify uncovered blocks

## Coverage Report Structure

The HTML coverage report uses this structure:

**Executed code (green):**
- `<tbody id="...">` (no `tcov-unexec` class)
- `<td class="tcov-count">` shows execution count (e.g., "14")
- Code displayed in green color

**Unexecuted code (red):**
- `<tbody class="tcov-unexec" id="...">`
- `<td class="tcov-count">` shows "-"
- Code displayed in red color

**Key elements:**
- `tcov-linenumber` - Line number in source file
- `tcov-statement` - The actual COBOL code in `<pre>` tags
- `tcov-count` - Execution count (number or "-")
- `tcov-nodenum` - Block identifier (B1, B2, B3, etc.)

## Mandatory Workflow

### Phase 1: Discovery and Analysis

```
1. Locate coverage report file:
   - Search K:\CodeCoverage\*\[BUSOBJ]\Syspro_[BUSOBJ].htm
   - Possible module folders: Distribution, Financial, Manufacturing, Core, Emerging Technology

2. Parse coverage report:
   - Extract ALL <tbody class="tcov-unexec"> blocks
   - Capture line numbers and COBOL statements
   - Group consecutive uncovered lines into logical scenarios
   - Create a summary of all uncovered code paths

3. Read source program:
   - Read C:\RND900\SOURCE\[BUSOBJ].CBL
   - Understand the context around uncovered blocks
   - Identify conditions that trigger uncovered code
   - Note any setup options (EVALUATE, IF conditions on setup flags)

4. Read existing tests:
   - Read all tests in C:\T900\[BUSOBJ]\
   - Identify what's already covered
   - Find the next test number (T00001, T00002, etc.)
   - Match exact file naming and XML structure patterns

5. **CRITICAL - Read a WORKING test's output files for format reference:**
   - Find a test that has REAL output (e.g., T00001 or any active test)
   - Read the *OUT.XML file to understand the EXACT XML format SYSPRO produces
   - Note: root element casing, quote style, error element structure, attribute names
   - Copy THIS format exactly when writing new output files
   - NEVER guess the XML format - always use a real example as template
```

### Phase 2: Setup Options Analysis (CRITICAL)

Many uncovered blocks are only reachable when specific setup options are enabled.

```
1. Search uncovered code for setup option checks:
   - EVALUATE statements on IM40-*, AR40-*, SO40-*, etc.
   - IF conditions checking setup flags
   - Company configuration options

2. Query current setup options:
   - Use mcp__syspro-enet__syspro_query_setup_options
   - Document which options affect uncovered code

3. Identify which setup options could enable coverage:
   - List options that would trigger uncovered paths
   - Determine if options can be set via Pre_Test or require manual setup
   - If setup change needed, document it clearly
```

### Phase 2B: Distinguish Parameter-Driven vs Data-Driven Code Paths (CRITICAL)

**IMPORTANT LEARNING: Many uncovered blocks in Query BOs are triggered by PARAMETERS, not by data setup.**

Before creating Pre_Tests, analyze whether uncovered code is:

**Parameter-Driven Code (use Post_Tests, NOT Pre_Tests):**
```cobol
IF INVQ9C-S-LOC = "R" OR "S"     ← Triggered by FilterType parameter in XML
   PERFORM STORE-LOCATION

IF INVQ9C-PRIMARY = "C"          ← Triggered by PrimarySeq parameter in XML
   MOVE "Customer" TO SEQ-DESC

IF INVQ9C-RETYPE = "2"           ← Triggered by ReportType parameter in XML
   PERFORM FORMAT-2LINE-SUMMARY
```
**Solution:** Create Post_Tests with different parameter values. No data setup needed.

**Data-Driven Code (requires Pre_Tests for data setup):**
```cobol
IF INVSTH-CUS NOT = SPACES       ← Requires serial assigned to customer
   MOVE INVSTH-CUS TO OUTPUT

IF INVSTH-VER NOT = INVQ9C-REV   ← Requires serial with Version/Release
   GO TO PRT-TMP-NXT

IF INVSTD-CLS = INVQ9C-TTS       ← Requires specific transaction types exist
   PERFORM PROCESS-TRANSACTION
```
**Solution:** Create Pre_Tests to set up serial items with required attributes (customer, version, dates, service flags).

**Key Insight for Query Business Objects:**
- WHERE clause building code executes even if the filter returns zero results
- Option flags (ItemsInServiceOnly, PrintBatchSerials, etc.) execute their code paths even without matching data
- Most uncovered blocks in query BOs can be covered with parameter variations alone

**When Pre_Tests ARE needed:**
1. Testing query results with specific data attributes (e.g., serials with ExpiryDate, Customer, Version)
2. Verifying output contains expected values (not just empty results)
3. Testing business logic that depends on data relationships
4. Covering code paths that skip processing when data doesn't match criteria

### Phase 3: Create Systematic Coverage Plan

**CRITICAL: Create a task plan before writing any files.**

```
1. Analyze all uncovered blocks and group by:
   - Error handling paths (may be hard to trigger - document but deprioritize)
   - Setup-dependent paths (note required setup options)
   - Business logic paths (primary targets for new tests)
   - Edge cases and boundary conditions

2. Prioritize coverage targets:
   - Main business logic paths (highest priority)
   - Setup-enabled paths (medium priority)
   - Error/exception paths (lower priority - often require invalid data)

3. Design test scenarios:
   - **Start with Post_Tests for parameter variations** (most query BO coverage comes from this)
   - Each scenario should cover multiple uncovered blocks where possible
   - Only create Pre_Tests when data setup is truly required
   - Use COMFND for data verification when Pre_Tests modify data

4. Create ONE test folder with chained tests:
   - Pre_Tests: ONLY if data setup is required (customer assignment, dates, ECC attributes)
   - Base test: One parameter configuration for the main BO
   - **Post_Tests: Multiple parameter variations** (PrimarySeq, FilterType, ReportType, options)
   - Focus on Post_Tests as the primary coverage mechanism for query BOs
```

### Phase 4: Execute and Create Tests

For EACH test file set:

| Step | Action | Tool |
|------|--------|------|
| **Pre-Test** | Execute setup transactions | `syspro_query` or `syspro_transaction_post_ld` |
| **Base Test** | Execute the actual BO under test | `syspro_query` or `syspro_transaction_post_ld` |
| **Post-Test** | Execute verification queries | `syspro_query` |

**CRITICAL: Capture the EXACT XML response and write it to output files**

### Phase 5: Verification

```
1. Query database to confirm data changes
2. Verify output XML matches SYSPRO format
3. Check all required files exist (including CFG files)
4. Review which uncovered blocks should now be covered
```

## Output: Single Test Folder with Chained Tests

**DO NOT create multiple test folders per uncovered block.**

Create ONE test folder (e.g., T00005) containing:

```
T00005/
├── _TestInfo.XML                    # Test metadata
├── Pre_Test_01_SETUP.XML            # Setup option or data preparation
├── Pre_Test_01_SETUPDOC.XML
├── Pre_Test_01_SETUPCFG.XML
├── Pre_Test_01_SETUPOUT.XML
├── Pre_Test_02_COMFND.XML           # Baseline verification
├── Pre_Test_02_COMFNDCFG.XML
├── Pre_Test_02_COMFNDOUT.XML
├── ...                              # More pre-tests as needed
├── Base_[BUSOBJ].XML                # Main test parameters
├── Base_[BUSOBJ]DOC.XML             # Main test document
├── Base_[BUSOBJ]OUT.XML             # Captured output
├── Post_Test_01_COMFND.XML          # Verification query 1
├── Post_Test_01_COMFNDCFG.XML
├── Post_Test_01_COMFNDOUT.XML
├── Post_Test_02_[BUSOBJ].XML        # Additional test with different params
├── Post_Test_02_[BUSOBJ]DOC.XML
├── Post_Test_02_[BUSOBJ]CFG.XML
├── Post_Test_02_[BUSOBJ]OUT.XML
└── ...                              # More post-tests for coverage
```

## Coverage Analysis Report Format

After analyzing coverage, present findings as:

```
## Coverage Analysis for [BUSOBJ]

### Summary
- Total uncovered blocks: N
- Likely coverable: X (with test changes)
- Setup-dependent: Y (require configuration changes)
- Error paths: Z (may not be practically testable)

### Uncovered Blocks Detail

#### Block B23 (Lines 1234-1240) - COVERABLE
```cobol
IF INVQ9C-S-LOC = "R" OR "S"
   PERFORM STORE-LOCATION
```
**Trigger condition:** Query with StoreLocation parameter set to "R" or "S"
**Test approach:** Add Pre_Test to set StoreLocation, execute query

#### Block B45 (Lines 2345-2350) - SETUP DEPENDENT
```cobol
IF IM40-ECC-STK-LVL = "L" OR "R"
   MOVE RAW-NAME TO KEYVAL-RAW-ELEMENT
   ...
```
**Trigger condition:** Setup option ECC Stock Level must be "L" or "R"
**Test approach:** Requires setup change or different company/dataset

#### Block B67 (Lines 3456-3460) - ERROR PATH
```cobol
MOVE COM-MSG-UNKNOWN-METHOD TO LINK-COM-MSG
GO TO ENDJOB
```
**Trigger condition:** Invalid method name passed to BO
**Test approach:** Low priority - tests error handling
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

Base_INVQ9C.XML            → Query parameters with specific filters
Base_INVQ9CDOC.XML         → Query document (if needed)
Base_INVQ9COUT.XML         → Captured query result

Post_Test_01_COMFND.XML    → Query same table (verify state)
Post_Test_01_COMFNDCFG.XML → Config
Post_Test_01_COMFNDOUT.XML → Captured result
```

## COMFND XML Format (CRITICAL)

**NEVER use SQL-style WHERE clauses.** COMFND uses Expression blocks.

**WRONG - SQL syntax will fail:**
```xml
<Where>DispatchNote IN ('000000000000023', '000000000000024')</Where>
```

**CORRECT - Use Expression blocks:**
```xml
<Query xmlns:xsd="http://www.w3.org/2001/XMLSchema-instance" xsd:noNamespaceSchemaLocation="COMFND.XSD">
  <TableName>InvMaster</TableName>
  <ReturnRows>10</ReturnRows>
  <Columns>
    <Column>StockCode</Column>
    <Column>Description</Column>
  </Columns>
  <Where>
    <Expression>
      <OpenBracket>(</OpenBracket>
      <Column>StockCode</Column>
      <Condition>EQ</Condition>
      <Value>A100</Value>
      <CloseBracket>)</CloseBracket>
    </Expression>
  </Where>
</Query>
```

## Transaction Output XML Format (CRITICAL - LEARNED THE HARD WAY)

The SYSPRO MCP tool (`syspro_transaction_post_ld`) returns **parsed text**, NOT raw XML.
You MUST reconstruct the XML using the correct format below. **ALWAYS read an existing working test's OUT file first to confirm the format.**

### Error Response Format (validation failures)

```xml
<?xml version="1.0" encoding="Windows-1252"?>
<rmaline Language='05' Language2='EN' CssStyle='' DecFormat='1' DateFormat='01' Role='01' Version='8.0.021' OperatorPrimaryRole='   '>
<Item>
<StockCode>
<Value/>
<ErrorNumber>100030</ErrorNumber>
<ErrorDescription>XML element '{Item}{StockCode}' cannot be spaces</ErrorDescription>
</StockCode>
<PurchaseDate>
<Value>04095999</Value>
<ErrorNumber>100028</ErrorNumber>
<ErrorDescription>Date '0409-59-99' is invalid for XML element 'PurchaseDate' it must be CCYY-MM-DD format</ErrorDescription>
</PurchaseDate>
<ItemNumber>00001</ItemNumber>
</Item>
<StatusOfItems>
<ItemsProcessed>00000</ItemsProcessed>
<ItemsInvalid>00001</ItemsInvalid>
</StatusOfItems>
</rmaline>
```

### Format Rules - NEVER VIOLATE

| Rule | WRONG | RIGHT |
|------|-------|-------|
| Root element | `<RmaLine>` | `<rmaline>` (lowercase) |
| Attribute quotes | `Language="05"` | `Language='05'` (single quotes) |
| Error fields | `<StockCode ErrorNumber="100030"/>` (attributes) | `<StockCode><Value/><ErrorNumber>100030</ErrorNumber>...</StockCode>` (child elements) |
| Empty value | `Value=""` or omitted | `<Value/>` (self-closing element) |
| Non-empty value | `Value="ABC"` | `<Value>ABC</Value>` (child element) |
| ItemNumber | `<Item ItemNumber="00001">` (attribute) | `<ItemNumber>00001</ItemNumber>` (child element inside Item) |
| StatusOfItems | `<StatusOfItems ItemsProcessed="00000"/>` (attributes) | `<StatusOfItems><ItemsProcessed>00000</ItemsProcessed>...</StatusOfItems>` (child elements) |
| StatusOfItems position | Before Item | **AFTER** `</Item>` |
| OperatorPrimaryRole | `OperatorPrimaryRole=' '` (1 space) | `OperatorPrimaryRole='   '` (3 spaces) |

### Success Response Format (items processed)

```xml
<?xml version="1.0" encoding="Windows-1252"?>
<rmaline Language='05' Language2='EN' CssStyle='' DecFormat='1' DateFormat='01' Role='01' Version='7.0.009' OperatorPrimaryRole='   '>
  <Item>
    <Key>
      <RmaLineNumberAdded>0001</RmaLineNumberAdded>
      <Status>Successful</Status>
    </Key>
    <ItemNumber>00001</ItemNumber>
  </Item>
  <StatusOfItems>
    <ItemsProcessed>00003</ItemsProcessed>
    <ItemsInvalid>00000</ItemsInvalid>
  </StatusOfItems>
</rmaline>
```

### How to Handle MCP Parsed Output

The MCP returns text like:
```
Item:
  StockCode:
    Value:
    ErrorNumber: 100030
    ErrorDescription: XML element '{Item}{StockCode}' cannot be spaces
  ItemNumber: 00001
StatusOfItems:
  ItemsProcessed: 00000
  ItemsInvalid: 00001
```

Map this to XML as:
- Each field name becomes a **parent element** (e.g., `<StockCode>`)
- `Value`, `ErrorNumber`, `ErrorDescription` become **child elements**
- Empty `Value:` becomes `<Value/>`
- `ItemNumber: 00001` becomes `<ItemNumber>00001</ItemNumber>` (child of `<Item>`, NOT attribute)

## Query Output XML Format

**WRONG - Do not fabricate:**
```xml
<QueryResults>
  <Row>...</Row>
</QueryResults>
```

**CORRECT - Use actual SYSPRO format:**
```xml
<InvMaster Language='05' Language2='EN' CssStyle='' DecFormat='1' ...>
  <HeaderDetails>
    <TableName>InvMaster</TableName>
    ...
  </HeaderDetails>
  <Row>...</Row>
  <RowsReturned>       1</RowsReturned>
</InvMaster>
```

Root element = Table name (with Language attributes, single quotes)

## CFG File Format

Every Pre_Test/Post_Test MUST have a CFG file. **MUST include `<XmlException>` tag** (even if empty):

```xml
<?xml version="1.0" encoding="Windows-1252"?>
<!-- Copyright 1994-2026 SYSPRO Ltd.-->
<!--
     Test case for Post-test configuration definition
     Note this file defines how to run Post-test business object
-->
<Test xmlns:xsd="http://www.w3.org/2001/XMLSchema-instance" xsd:noNamespaceSchemaLocation="Post_Test.XSD">
  <BusObj>COMFND</BusObj>
  <EnetClass>query</EnetClass>
  <EnetMethod>query</EnetMethod>
  <XmlInput>Pre_Test_01_COMFND.XML</XmlInput>
  <XmlDocumentInput></XmlDocumentInput>
  <XmlException></XmlException>
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

## Analyzing Uncovered Code Patterns

### Pattern 1: EVALUATE Branches
```cobol
EVALUATE LINK-COM-METHOD
   WHEN "query"
      GO TO BEGIN           # Covered (executed)
   WHEN OTHER
      MOVE COM-MSG...       # Uncovered (error path)
      GO TO ENDJOB          # Uncovered
END-EVALUATE
```
**Analysis:** "OTHER" branch is error handling - only triggered by invalid method

### Pattern 2: Setup-Dependent Code
```cobol
IF IM40-ECC-STK-LVL = "L" OR "R"
   MOVE RAW-NAME TO KEYVAL-RAW-ELEMENT
   ...
```
**Analysis:** Requires ECC Stock Level setup option to be "L" or "R"

### Pattern 3: Filter Options
```cobol
IF INVQ9C-S-LOC = "R" OR "S"
   PERFORM STORE-LOCATION
```
**Analysis:** Requires specific filter parameter in query XML

### Pattern 4: Date Range Filters
```cobol
IF INVQ9C-F-EDS NOT = ZEROES
   PERFORM SQL-CON-NEXT
   MOVE "a.ExpiryDate >= %11 AND" TO SQL-CON(SQL-CX1:)
```
**Analysis:** Requires FromExpiryDate filter to be set (non-zero)

## Common Pitfalls

| Issue | Solution |
|-------|----------|
| Creating multiple test folders | ONE folder with chained pre/base/post tests |
| Ignoring setup options | Analyze IM40-*, AR40-*, SO40-* checks in code |
| Trying to cover all error paths | Prioritize business logic over error handling |
| Fabricated output XML | Execute transaction, capture REAL response |
| Missing CFG files | Every Pre/Post test needs a CFG file |
| Not understanding coverage context | Read surrounding code to understand trigger conditions |
| SQL error in output (e.g., "Key not found on table") | REMOVE the test - SQL errors are infrastructure, not valid test outputs |
| System error in output (e.g., "memory leak in BUSOBJ") | REMOVE the test - system errors are not valid test outputs |
| Output XML uses attributes for errors | Use child elements: `<Value/>`, `<ErrorNumber>`, `<ErrorDescription>` |
| Same DOC comment across multiple Post_Tests | Each DOC file MUST have a unique comment describing its specific test scenario |
| XML element at wrong DOC level | Check source COBOL to confirm element nesting (e.g., EstimatedRepairDate goes inside OutOfWarranty, not at Item level) |
| Not reading existing working output first | ALWAYS read a real OUT.XML before writing any - confirms root element, quotes, error structure |
| CFG file missing XmlException tag | Every CFG file MUST include `<XmlException></XmlException>` even if empty |

## Red Flags - STOP

- Creating output files without executing transaction
- Creating multiple test folders per uncovered block
- Guessing XML element names
- Output XML with `<QueryResults>` root
- Missing CFG files for Pre/Post tests
- Assuming data exists without querying
- Not analyzing setup options that could enable coverage
- Using @placeholder@ syntax (DOES NOT EXIST IN T900)
- SQL errors (e.g., "Key not found", "file error") in any OUT.XML file
- System errors (e.g., "memory leak", "stack overflow") in any OUT.XML file
- Error fields as XML attributes (`ErrorNumber="100030"`) instead of child elements
- Identical comments across multiple DOC files (copy-paste without updating)
- `<Value>` or `<ErrorNumber>` as XML attributes instead of child elements
- Root element in PascalCase (`<RmaLine>`) instead of lowercase (`<rmaline>`)
- Double quotes on root element attributes (`Language="05"`) instead of single quotes (`Language='05'`)
- CFG files without `<XmlException>` tag

**All mean: Analyze thoroughly, plan systematically, execute via SYSPRO MCP, then copy the EXACT response.**

## Quick Start Template

```
1. syspro_configure → Connect
2. Glob K:\CodeCoverage\*\[BUSOBJ]\Syspro_[BUSOBJ].htm → Find coverage report
3. Read and parse coverage HTML → List all tcov-unexec blocks
4. Read C:\RND900\SOURCE\[BUSOBJ].CBL → Understand trigger conditions
5. Read C:\T900\[BUSOBJ]\ → Check existing tests, find next test number
6. syspro_query_setup_options → Check setup options that might enable coverage
7. Create coverage analysis report → Document each uncovered block
8. Design ONE test with chained pre/base/post → Plan which blocks to cover
9. For EACH pre/base/post test:
   a. Execute transaction via MCP
   b. Write output file with EXACT response
   c. Verify in database if needed
10. Create _TestInfo.XML and all CFG files
11. Document which blocks should now be covered
```

## Limitations to Document

Not all code can be covered. Document these honestly:

1. **Deprecated code paths** - May never be reachable
2. **External system integration** - May require live system not in test environment
3. **Edge cases requiring specific data states** - May not exist in test datasets

The goal is maximum practical coverage, not 100% coverage. Focus on business logic paths that provide real validation value.
