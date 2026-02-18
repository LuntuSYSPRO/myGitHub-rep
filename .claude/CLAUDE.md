# SYSPRO T900 Testing Plugin

This plugin provides tools for creating automated test cases for SYSPRO Business Objects in the T900 test framework.

## Core Principle

**Create test files by EXECUTING actual SYSPRO transactions and capturing real outputs. Never fabricate XML.**

## Available Tools

### SYSPRO e.net MCP Tools
- `mcp__syspro-enet__syspro_configure` - Configure SYSPRO connection
- `mcp__syspro-enet__syspro_list_business_objects` - List available business objects
- `mcp__syspro-enet__syspro_get_business_object_details` - Get XML format for a business object
- `mcp__syspro-enet__syspro_query` - Execute query business objects
- `mcp__syspro-enet__syspro_transaction_post_ld` - Post transactions
- `mcp__syspro-enet__syspro_setup_add/update/delete` - Setup operations
- `mcp__syspro-enet__syspro_search_entity` - Search for customers, suppliers, stock codes by name

### MSSQL MCP Tools
- `mcp__mssql__execute_sql` - Execute SQL queries to verify data

## Skills

### /Jenkins-testcase-creator
Use this skill when creating test cases for SYSPRO Business Objects. It guides you through:
1. Configuring SYSPRO MCP connection
2. Understanding existing test patterns
3. Executing transactions and capturing outputs
4. Creating properly formatted test files

### /coverage-hunter
Use this skill when analyzing code coverage HTML reports to create tests for uncovered COBOL blocks. It guides you through:
1. Locating and parsing coverage reports at `K:\CodeCoverage\[Module]\[BO]\Syspro_[BO].htm`
2. Identifying uncovered code blocks and their trigger conditions
3. Distinguishing parameter-driven vs data-driven code paths
4. Executing real SYSPRO transactions and capturing valid outputs
5. Creating a single test folder with chained pre/base/post tests to maximize coverage

## Environment Variables Required

Users must set these environment variables before using:

| Variable | Description | Example |
|----------|-------------|---------|
| `SYSPRO_BASE_URL` | SYSPRO WCF REST endpoint | `http://server:port/SYSPROWCFService/Rest` |
| `SYSPRO_OPERATOR` | SYSPRO operator code | `ADMIN` |
| `SYSPRO_PASSWORD` | Operator password | |
| `SYSPRO_COMPANY_ID` | Company to log into | `EDU1` |
| `MSSQL_HOST` | SQL Server hostname | `localhost` |
| `MSSQL_DATABASE` | SYSPRO company database | `DS001_CMP_EDU1_900` |

## T900 Test Structure Reference

Each test case requires these files:
- `_TestInfo.XML` - Test metadata (use `<Test>` root element)
- `Base_*.XML` - Parameters
- `Base_*DOC.XML` - Document input (xml-in)
- `Base_*OUT.XML` - Captured output from execution
- `Pre_Test_NN_*CFG.XML` - **REQUIRED** for each pre-test
- `Post_Test_NN_*CFG.XML` - **REQUIRED** for each post-test

## Critical Rules

1. **Never fabricate output XML** - Always execute via MCP and capture real response
2. **No placeholder syntax** - T900 does not support `@variable@` - use hard-coded values
3. **Every Pre/Post test needs a CFG file** - Defines how to run the test
4. **Check existing tests first** - Match patterns from existing tests in same business object folder
