# 🚀 Quick Setup Guide for New Testers

This guide will help you set up GitHub Copilot CLI with SYSPRO T900 testing capabilities, including the **coverage-hunter** and **Jenkins-testcase-creator** skills.

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.10+** installed and in PATH
- ✅ **Git** installed
- ✅ **GitHub Copilot CLI** installed ([install guide](https://docs.github.com/en/copilot/github-copilot-in-the-cli))
- ✅ **SYSPRO 8** with e.net Solutions enabled
- ✅ Access to **SYSPRO WCF REST Service**
- ✅ Valid **SYSPRO operator credentials** with e.net license
- ✅ **SQL Server** with ODBC Driver 17 for SQL Server
- ✅ **Windows PowerShell** or **Command Prompt**

---

## 🎯 Installation Steps

### Step 1: Clone the Repository

Open PowerShell or Command Prompt and run:

```powershell
# Navigate to where you want to store the plugin
cd C:\

# Clone the repository
git clone https://github.com/LuntuSYSPRO/myGitHub-rep.git Jenkins_Senior

# Navigate into the repository
cd Jenkins_Senior
```

### Step 2: Run the Automated Installer

The `install.bat` script will install all Python dependencies automatically:

```cmd
install.bat
```

This will:
- ✅ Install SYSPRO MCP server dependencies
- ✅ Install MSSQL MCP server
- ✅ Check for required environment variables

### Step 3: Configure Environment Variables

**IMPORTANT:** You must set these environment variables for the MCP servers to work.

#### Option A: Set User-Level Variables (Recommended)

Open **PowerShell** and run these commands (update values for your environment):

```powershell
# SYSPRO Connection Settings
[Environment]::SetEnvironmentVariable("SYSPRO_BASE_URL", "http://localhost:40001/SYSPROWCFService/Rest", "User")
[Environment]::SetEnvironmentVariable("SYSPRO_OPERATOR", "ADMIN", "User")
[Environment]::SetEnvironmentVariable("SYSPRO_PASSWORD", "your-password-here", "User")
[Environment]::SetEnvironmentVariable("SYSPRO_COMPANY_ID", "EDU1", "User")
[Environment]::SetEnvironmentVariable("SYSPRO_COMPANY_PASSWORD", "", "User")

# SQL Server Settings
[Environment]::SetEnvironmentVariable("MSSQL_HOST", "localhost", "User")
[Environment]::SetEnvironmentVariable("MSSQL_DATABASE", "DS001_CMP_EDU1_900", "User")
[Environment]::SetEnvironmentVariable("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server", "User")
[Environment]::SetEnvironmentVariable("MSSQL_TRUSTED_CONNECTION", "yes", "User")
```

#### Option B: Set System-Level Variables (Requires Admin)

1. Press `Win + X` → Select **System**
2. Click **Advanced system settings**
3. Click **Environment Variables**
4. Under **User variables**, click **New** and add each variable:

| Variable Name | Example Value |
|--------------|---------------|
| `SYSPRO_BASE_URL` | `http://localhost:40001/SYSPROWCFService/Rest` |
| `SYSPRO_OPERATOR` | `ADMIN` |
| `SYSPRO_PASSWORD` | `your-password` |
| `SYSPRO_COMPANY_ID` | `EDU1` |
| `SYSPRO_COMPANY_PASSWORD` | (leave empty if not required) |
| `MSSQL_HOST` | `localhost` |
| `MSSQL_DATABASE` | `DS001_CMP_EDU1_900` |
| `MSSQL_DRIVER` | `ODBC Driver 17 for SQL Server` |
| `MSSQL_TRUSTED_CONNECTION` | `yes` |

**After setting variables, restart your terminal/PowerShell for changes to take effect!**

### Step 4: (Optional) Enable Entity Search by Name

This improves the ability to search for stock codes, customers, suppliers, etc., by name instead of just code.

1. Open SQL Server Management Studio
2. Connect to your SYSPRO database server
3. Open the file: `C:\Jenkins_Senior\scripts\SetupSearchEntity.sql`
4. Execute the script against your **SysproDb** database

### Step 5: Install the Plugin in GitHub Copilot CLI

Now install the plugin so GitHub Copilot CLI can use it:

```powershell
# Make sure you're in the repository directory
cd "C:\GitHub rep\Jenkins_Senior"

# Install the plugin for your user account
claude plugin install . --scope user
```

You should see a success message like:
```
✓ Plugin installed: syspro-t900-testing
```

### Step 6: Restart Your Terminal

**CRITICAL:** Close and reopen your terminal (PowerShell/Command Prompt) for all changes to take effect.

---

## ✅ Verify Installation

After restarting your terminal, verify everything is working:

### 1. Check Plugin Installation

```powershell
claude plugin list
```

You should see:
- ✅ `syspro-t900-testing` in the list (enabled)

### 2. Check Skills Are Available

Start GitHub Copilot CLI:

```powershell
claude
```

Inside Copilot, type:
```
What skills do I have available?
```

You should see:
- ✅ **coverage-hunter** - Analyzes code coverage and creates tests for uncovered blocks
- ✅ **Jenkins-testcase-creator** - Creates test cases for SYSPRO Business Objects

### 3. Test SYSPRO Connection

Inside GitHub Copilot CLI, ask:
```
List available SYSPRO business objects
```

If the connection works, you'll see a list of business objects like INVQRY, SORQRY, etc.

### 4. Test SQL Connection

Inside GitHub Copilot CLI, ask:
```
Query the SQL database to show me the top 5 stock codes from InvMaster
```

If successful, you'll see stock codes from your database.

---

## 🎓 How to Use the Skills

### Using the Coverage Hunter Skill

The **coverage-hunter** skill analyzes HTML code coverage reports and systematically creates tests to maximize coverage.

```
/coverage-hunter
```

Or simply ask:
```
Analyze coverage for INVQ9C and create tests for uncovered blocks
```

The skill will:
1. Parse the coverage HTML report at `K:\CodeCoverage\[Module]\[BO]\Syspro_[BO].htm`
2. Identify uncovered code blocks
3. Analyze trigger conditions
4. Execute real SYSPRO transactions via MCP
5. Create a single test folder with chained tests

### Using the Jenkins Test Case Creator Skill

The **Jenkins-testcase-creator** skill guides you through creating test cases with actual SYSPRO MCP execution.

```
/Jenkins-testcase-creator
```

Or simply ask:
```
Create a test case for INVQRY to query stock item A100
```

The skill will:
1. Guide you through the test creation process
2. Execute the actual transaction via SYSPRO e.net MCP
3. Capture real output XML
4. Create the test folder with input.xml and output.xml

---

## 🔧 Troubleshooting

### Problem: "Python is not installed or not in PATH"

**Solution:**
1. Download Python 3.10+ from [python.org](https://www.python.org/downloads/)
2. During installation, **check** "Add Python to PATH"
3. Restart your terminal and try again

### Problem: "MCP server not starting"

**Solution:**
1. Check the log file: `servers\syspro-enet\syspro_mcp_startup.log`
2. Verify Python dependencies are installed:
   ```powershell
   cd servers\syspro-enet
   pip install -r requirements.txt
   ```
3. Restart your terminal

### Problem: "SYSPRO connection failed"

**Solution:**
1. Verify SYSPRO WCF Service is running
2. Open in browser: `http://localhost:40001/SYSPROWCFService/Rest/Logon`
3. Check environment variables are set correctly:
   ```powershell
   echo $env:SYSPRO_BASE_URL
   echo $env:SYSPRO_OPERATOR
   ```
4. Verify your operator has an e.net license in SYSPRO

### Problem: "SQL connection failed"

**Solution:**
1. Verify ODBC Driver 17 is installed:
   - Download from [Microsoft](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
2. Check database name matches your SYSPRO company database
3. Test connection with SQL Server Management Studio
4. If using `MSSQL_TRUSTED_CONNECTION=yes`, ensure Windows authentication works

### Problem: "Plugin not found"

**Solution:**
1. Verify you ran `claude plugin install . --scope user` from inside the `Jenkins_Senior` directory
2. Check plugin list:
   ```powershell
   claude plugin list
   ```
3. If not listed, reinstall:
   ```powershell
   cd "C:\GitHub rep\Jenkins_Senior"
   claude plugin install . --scope user
   ```

### Problem: "Environment variables not working"

**Solution:**
1. After setting environment variables, **restart your terminal**
2. Verify they are set:
   ```powershell
   Get-ChildItem Env: | Where-Object { $_.Name -like "SYSPRO*" -or $_.Name -like "MSSQL*" }
   ```
3. If empty, re-run the SetEnvironmentVariable commands from Step 3

---

## 📚 Additional Resources

- **Plugin Documentation:** See [README.md](README.md) for detailed information
- **Skills Documentation:**
  - Coverage Hunter: `skills/coverage-hunter/SKILL.md`
  - Jenkins Test Creator: `skills/Jenkins-testcase-creator/SKILL.md`
- **GitHub Copilot CLI Docs:** [https://docs.github.com/en/copilot/github-copilot-in-the-cli](https://docs.github.com/en/copilot/github-copilot-in-the-cli)

---

## 🔒 Security Notes

- ⚠️ Never commit credentials to the repository
- ✅ Store credentials in environment variables only
- ✅ Use a dedicated SYSPRO operator with minimal permissions
- ✅ Enable SYSPRO audit logging for e.net operations
- ✅ Always test in a development environment first

---

## 🆘 Getting Help

If you encounter issues not covered in this guide:

1. Check the logs in `servers/syspro-enet/syspro_mcp_startup.log`
2. Review the main README.md for detailed troubleshooting
3. Contact the repository maintainer

---

## ✨ You're Ready!

Once installation is complete and verified, you can start creating test cases with:

```
claude
```

Then inside Copilot CLI:
```
Create a test case for INVQRY to query stock item A100
```

or

```
Analyze coverage for PORQ9C and create tests for uncovered blocks
```

Happy testing! 🎉
