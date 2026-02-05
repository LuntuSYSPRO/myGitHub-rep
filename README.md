# SYSPRO T900 Testing Plugin

A Claude Code plugin for creating automated test cases for SYSPRO Business Objects in the T900 test framework.

## What This Plugin Does

This plugin enables Claude to:
- **Execute live SYSPRO transactions** via the SYSPRO e.net MCP server
- **Query SQL Server databases** to verify test data
- **Create T900 test cases** with properly captured output XML
- **Follow the Jenkins-testcase-creator skill** for consistent test creation

## Prerequisites

- Python 3.10+
- SYSPRO 8 with e.net Solutions enabled
- Access to SYSPRO WCF REST Service
- Valid SYSPRO operator credentials with e.net license
- SQL Server with ODBC Driver 17
- Claude Code CLI

## Installation

### 1. Clone/Copy the Plugin

```bash
# Option A: Clone from repository
git clone https://github.com/your-org/syspro-t900-testing.git

# Option B: Copy the folder to your desired location
```

### 2. Install Python Dependencies

```bash
cd syspro-t900-testing/servers/syspro-enet
pip install -r requirements.txt
```

### 3. Install MSSQL MCP Server

```bash
pip install mssql-mcp-server
```

### 4. Set Up Entity Search (Optional but Recommended)

Run the `scripts/SetupSearchEntity.sql` script in your SYSPRO system database (SysproDb) to enable entity search by name.

### 5. Configure Environment Variables

Set these environment variables on your system:

**Windows (PowerShell - User level):**
```powershell
[Environment]::SetEnvironmentVariable("SYSPRO_BASE_URL", "http://your-server:port/SYSPROWCFService/Rest", "User")
[Environment]::SetEnvironmentVariable("SYSPRO_OPERATOR", "ADMIN", "User")
[Environment]::SetEnvironmentVariable("SYSPRO_PASSWORD", "your-password", "User")
[Environment]::SetEnvironmentVariable("SYSPRO_COMPANY_ID", "EDU1", "User")
[Environment]::SetEnvironmentVariable("MSSQL_HOST", "localhost", "User")
[Environment]::SetEnvironmentVariable("MSSQL_DATABASE", "DS001_CMP_EDU1_900", "User")
```

**Or create a `.env` file** in your project and source it before running Claude Code.

### 6. Install the Plugin

```bash
# Add the plugin to Claude Code
claude plugin install /path/to/syspro-t900-testing --scope user

# Or for project-specific installation
claude plugin install /path/to/syspro-t900-testing --scope project
```

### 7. Restart Claude Code

Restart Claude Code to load the MCP servers.

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SYSPRO_BASE_URL` | Yes | SYSPRO WCF REST endpoint | `http://server:40001/SYSPROWCFService/Rest` |
| `SYSPRO_OPERATOR` | Yes | SYSPRO operator code | `ADMIN` |
| `SYSPRO_PASSWORD` | Yes | Operator password | |
| `SYSPRO_COMPANY_ID` | Yes | Company to log into | `EDU1` |
| `SYSPRO_COMPANY_PASSWORD` | No | Company password (if required) | |
| `MSSQL_HOST` | Yes | SQL Server hostname | `localhost` |
| `MSSQL_DATABASE` | Yes | SYSPRO company database | `DS001_CMP_EDU1_900` |
| `MSSQL_DRIVER` | No | ODBC driver name | `ODBC Driver 17 for SQL Server` |
| `Trusted_Connection` | No | Use Windows auth | `yes` |

## Usage

### Creating Test Cases

Invoke the skill in Claude Code:

```
/Jenkins-testcase-creator
```

Or simply ask Claude to create a test case:

```
Create a test case for the INVQRY business object to query stock item A100
```

### Available MCP Tools

After installation, these tools are available:

**SYSPRO e.net:**
- `syspro_configure` - Configure connection settings
- `syspro_list_business_objects` - List available business objects
- `syspro_get_business_object_details` - Get XML format for a BO
- `syspro_query` - Execute query business objects
- `syspro_transaction_post_ld` - Post transactions
- `syspro_setup_add/update/delete` - Setup operations
- `syspro_search_entity` - Search entities by name

**MSSQL:**
- `execute_sql` - Run SQL queries

## Plugin Structure

```
syspro-t900-testing/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── .mcp.json                 # MCP server configurations
├── .claude/
│   └── CLAUDE.md             # Plugin documentation for Claude
├── skills/
│   └── Jenkins-testcase-creator/
│       └── SKILL.md          # Test creation workflow
├── servers/
│   └── syspro-enet/
│       ├── syspro_mcp_wrapper.py
│       ├── syspro_mcp_server.py
│       ├── syspro_business_objects.py
│       ├── business_objects_catalog.json
│       └── requirements.txt
├── scripts/
│   └── SetupSearchEntity.sql # SQL setup for entity search
├── install.bat               # Windows installation script
└── README.md                 # This file
```

## Troubleshooting

### MCP Server Not Starting

1. Check Python is in your PATH
2. Verify all dependencies are installed: `pip install -r servers/syspro-enet/requirements.txt`
3. Check the log file: `servers/syspro-enet/syspro_mcp_startup.log`

### Connection Failed

1. Verify SYSPRO WCF Service is running
2. Test connectivity: Open `http://your-server:port/SYSPROWCFService/Rest/Logon` in a browser
3. Check environment variables are set correctly

### SQL Connection Failed

1. Verify ODBC Driver 17 is installed
2. Check database name matches your SYSPRO company database
3. Ensure Windows authentication is working (if using Trusted_Connection)

## Security Notes

- Store credentials in environment variables, not in code
- Use HTTPS in production environments
- Create a dedicated SYSPRO operator with minimal required permissions
- Enable SYSPRO audit logging for e.net operations

## License

MIT License

## Disclaimer

This is an independent implementation and is not officially supported by SYSPRO. Always test thoroughly in a development environment before using in production.
