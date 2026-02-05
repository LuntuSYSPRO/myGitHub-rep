"""
SYSPRO e.net Solutions MCP Server (Updated for REST API with Business Objects Catalog)
A Model Context Protocol server for interacting with SYSPRO ERP system via WCF REST API
Based on actual SYSPRO WCF REST API structure from Postman collection
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import xml.etree.ElementTree as ET

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

# For SYSPRO WCF/REST communication
import httpx
# Get the directory where THIS script is located
SCRIPT_DIR = Path(__file__).parent
script_path = SCRIPT_DIR / "discover_business_objects.py"
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("syspro-mcp-server")


class SysproClient:
    """Client for interacting with SYSPRO WCF REST API"""
    
    def __init__(self, base_url: str, operator: str, password: str, company_id: str = "", company_password: str = ""):
        """
        Initialize SYSPRO client
        
        Args:
            base_url: WCF REST service base address (e.g., http://server:port/SYSPROWCFService/Rest)
            operator: SYSPRO operator code
            password: Operator password
            company_id: Company ID (optional)
            company_password: Company password (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.operator = operator
        self.password = password
        self.company_id = company_id
        self.company_password = company_password
        self.session_id = None
        
    async def logon(self) -> bool:
        """Authenticate with SYSPRO and establish session"""
        try:
            async with httpx.AsyncClient() as client:
                # Logon is a GET request with query parameters
                params = {
                    "Operator": self.operator,
                    "OperatorPassword": self.password,
                    "CompanyId": self.company_id,
                    "CompanyPassword": self.company_password
                }
                response = await client.get(
                    f"{self.base_url}/Logon",
                    params=params
                )
                
                if response.status_code == 200:
                    # Check if response contains an error message
                    response_text = response.text.strip()
                    if response_text.startswith("ERROR:"):
                        logger.error(f"Logon failed: {response_text}")
                        return False
                    
                    # SYSPRO returns the session ID as plain text
                    if response_text and len(response_text) > 10:
                        self.session_id = response_text
                        logger.info(f"Successfully logged on to SYSPRO. Session: {self.session_id}")
                        return True
                    else:
                        logger.error(f"Logon failed: Unexpected response format: {response_text}")
                        return False
                else:
                    logger.error(f"Logon failed: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error during logon: {str(e)}")
            return False
    
    async def query(
        self,
        business_object: str,
        xml_in: str
    ) -> Dict[str, Any]:
        """
        Execute a Query operation
        
        Args:
            business_object: Business object name (e.g., "INVQRY")
            xml_in: XML input data
            
        Returns:
            Dictionary containing response data and status
        """
        if not self.session_id:
            await self.logon()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "UserId": self.session_id,
                    "BusinessObject": business_object,
                    "XmlIn": xml_in
                }
                
                response = await client.get(
                    f"{self.base_url}/Query/Query",
                    params=params
                )
                
                return self._process_response(response)
        except Exception as e:
            logger.error(f"Error in query: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def setup_add(
        self,
        business_object: str,
        xml_in: str,
        xml_parameters: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a Setup/Add operation"""
        return await self._setup_operation("Add", business_object, xml_in, xml_parameters)
    
    async def setup_update(
        self,
        business_object: str,
        xml_in: str,
        xml_parameters: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a Setup/Update operation"""
        return await self._setup_operation("Update", business_object, xml_in, xml_parameters)
    
    async def setup_delete(
        self,
        business_object: str,
        xml_in: str,
        xml_parameters: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a Setup/Delete operation"""
        return await self._setup_operation("Delete", business_object, xml_in, xml_parameters)
    
    async def _setup_operation(
        self,
        method: str,
        business_object: str,
        xml_in: str,
        xml_parameters: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a Setup operation (Add/Update/Delete)"""
        if not self.session_id:
            await self.logon()
        
        if xml_parameters is None:
            xml_parameters = "<Parameters />"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "UserId": self.session_id,
                    "BusinessObject": business_object,
                    "XmlIn": xml_in,
                    "XmlParameters": xml_parameters
                }
                
                response = await client.get(
                    f"{self.base_url}/Setup/{method}",
                    params=params
                )
                
                return self._process_response(response)
        except Exception as e:
            logger.error(f"Error in setup {method}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _strip_cdata(self, xml_str: str) -> str:
        """Strip CDATA wrapper from XML string if present"""
        if xml_str is None:
            return xml_str
        xml_str = xml_str.strip()
        if xml_str.startswith("<![CDATA[") and xml_str.endswith("]]>"):
            xml_str = xml_str[9:-3]
        return xml_str

    async def transaction_post_ld(
        self,
        business_object: str,
        xml_in: str,
        xml_parameters: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a Transaction/Post operation (GET method for small requests)

        Args:
            business_object: Business object name
            xml_in: XML input data
            xml_parameters: Optional XML parameters

        Returns:
            Dictionary containing response data and status
        """
        if not self.session_id:
            await self.logon()
        logger.info(f"transaction_post - Session ID: {self.session_id}")
        if xml_parameters is None:
            xml_parameters = "<Parameters />"

        # Strip any existing CDATA wrappers to avoid double wrapping
        xml_in = self._strip_cdata(xml_in)
        xml_parameters = self._strip_cdata(xml_parameters)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "UserId": self.session_id,
                    "BusinessObject": business_object,
                    "XmlIn": xml_in,
                    "XmlParameters": xml_parameters
                }

                xml_body = f"""<TransactionPostLD xmlns="http://SYSPROWcfService">
                    <UserId>{self.session_id}</UserId>
                    <BusinessObject>{business_object}</BusinessObject>
                    <XmlParameters><![CDATA[{xml_parameters}]]></XmlParameters>
                    <XmlIn><![CDATA[{xml_in}]]></XmlIn>
                </TransactionPostLD>"""
                logger.info(f"transaction_post - Calling transaction post with {xml_body}")
                response = await client.post(
                    f"{self.base_url}/Transaction/PostLD",
                    content=xml_body,
                    headers={"Content-Type": "application/xml"}
                )
                logger.info(f"transaction_post - transaction post output {response.text.strip()}")
                return self._process_response(response)
        except Exception as e:
            logger.error(f"Error in transaction post: {str(e)}")
            return {"success": False, "error": str(e)}
   
    
    def _process_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Process HTTP response from SYSPRO"""
        try:
            if response.status_code == 200:
                response_text = response.text.strip()
                
                # Check for SYSPRO error messages
                if response_text.startswith("ERROR:"):
                    return {
                        "success": False,
                        "error": response_text,
                        "raw_response": response_text
                    }
                
                # Try to parse as XML
                try:
                    root = ET.fromstring(response_text)
                    parsed_data = self._xml_to_dict(root)
                    
                    return {
                        "success": True,
                        "raw_response": response_text,
                        "parsed_data": parsed_data
                    }
                except ET.ParseError:
                    # If not XML, return as plain text
                    return {
                        "success": True,
                        "raw_response": response_text,
                        "parsed_data": {"text": response_text}
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "raw_response": response.text
                }
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _xml_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            for key, value in element.attrib.items():
                result[f"@{key}"] = value
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result["#text"] = element.text.strip()
        
        # Add child elements
        children = {}
        for child in element:
            child_data = self._xml_to_dict(child)
            
            if child.tag in children:
                # Multiple children with same tag - convert to list
                if not isinstance(children[child.tag], list):
                    children[child.tag] = [children[child.tag]]
                children[child.tag].append(child_data)
            else:
                children[child.tag] = child_data
        
        result.update(children)
        
        # If only text content, return it directly
        if len(result) == 1 and "#text" in result:
            return result["#text"]
        
        return result


    async def search_entity(
        self,
        search_term: str,
        tile_name: str = "USR004_SQL",
        max_results: int = 1000000
    ) -> Dict[str, Any]:
        """
        Search for entities (customers, suppliers, stock codes, etc.) by name using SYSPRO tiles
        
        This uses the COMQTM business object with tile queries to perform fuzzy searches.
        The response is a hex-encoded string that needs to be decoded.
        
        Args:
            search_term: The text to search for (e.g., "bayside bikes")
            tile_name: The tile to query (default: "USR004_SQL" for general search)
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating if search succeeded
            - results: List of tuples (entity_type, entity_code)
            - raw_response: The original response
            - decoded_data: The decoded hex data
        """
        # Build the query XML
        xml_in = f"""<?xml version="1.0" encoding="Windows-1252"?>
<Tile>
    <Name>{tile_name}</Name>
    <Level>D</Level>
    <KeyInfo>
        <KeyTyp>Insights</KeyTyp>
        <KeyVal>1</KeyVal>
    </KeyInfo>
    <SearchStr>{search_term}</SearchStr>
    <TopX>{max_results}</TopX>
</Tile>"""
        
        # Execute the query
        result = await self.query("COMQTM", xml_in)
        
        if not result["success"]:
            return result
        
        try:
            # Extract the hex data from the response
            raw_text = result["raw_response"]
            logger.info(f"search_entity - Raw response from COMQTM call {raw_text}")
            # The response format is like:
            # <TileDetail>...</TileDetail>:TileId:006:USR004:Title:003:SQL:Lview:00000052:HEX_DATA
            # We need to extract the last part after the last colon
            
            parts = raw_text.split(':')
            if len(parts) < 2:
                return {
                    "success": False,
                    "error": "Unexpected response format - no hex data found",
                    "raw_response": raw_text
                }
            
            hex_data = parts[-1].strip()
            logger.info(f"search_entity - Hex Data Found response from COMQTM call {hex_data}")
            
            # Convert hex to ASCII/Latin-1
            # Use latin-1 encoding which accepts all bytes 0-255, including xFF (chr 255)
            try:
                decoded_bytes = bytes.fromhex(hex_data)
                # Use latin-1 instead of ascii to preserve xFF characters
                decoded_text = decoded_bytes.decode('latin-1')
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Failed to decode hex data: {str(e)}",
                    "raw_response": raw_text,
                    "hex_data": hex_data
                }
            logger.info(f"search_entity - Decoded Text {repr(decoded_text)}")
            
            # Parse the decoded data
            # Format: ColumnCount:002\r\nEntityType\x01\x01\x01\x01\xFF000000000000001\x01\x01\x01\x01\xFF\r\n
            # Note: \x01 bytes are padding, \xFF (chr 255) is the field separator
            results = []
            
            # Split by \r\n (carriage return + line feed)
            lines = decoded_text.split('\r\n')
            
            for line in lines:
                logger.info(f"search_entity - Checking line {repr(line)}")
                if not line or line.startswith('ColumnCount'):
                    continue
                
                # Remove \x01 padding characters (they appear around the xFF delimiter)
                line_clean = line.replace('\x01', '')
                logger.info(f"search_entity - Cleaned line {repr(line_clean)}")
                
                # Split by chr(255) which is \xFF or ÿ in latin-1
                parts = line_clean.split('\xFF')
                logger.info(f"search_entity - Split into {len(parts)} parts: {parts}")
                
                if len(parts) >= 2:
                    entity_type = parts[0].strip()
                    entity_code = parts[1].strip()
                    
                    if entity_type and entity_code:
                        # Remove leading zeros for cleaner display
                        entity_code_clean = entity_code.lstrip('0') or '0'
                        logger.info(f"search_entity - Found: {entity_type} = {entity_code} (clean: {entity_code_clean})")
                        results.append({
                            "type": entity_type,
                            "code": entity_code,
                            "code_clean": entity_code_clean
                        })
            
            return {
                "success": True,
                "results": results,
                "raw_response": raw_text,
                "hex_data": hex_data,
                "decoded_data": decoded_text,
                "search_term": search_term
            }
            
        except Exception as e:
            logger.error(f"Error parsing search results: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to parse search results: {str(e)}",
                "raw_response": result.get("raw_response", "")
            }


class SysproMCPServer:
    """MCP Server for SYSPRO integration"""
    
    def __init__(self):
        self.server = Server("syspro-mcp-server")
        self.syspro_client: Optional[SysproClient] = None
        self.business_objects_catalog: Dict[str, Any] = {}
        self._setup_handlers()
        
    def _load_business_objects_catalog(self) -> bool:
        """Load the business objects catalog from JSON file"""
        try:
            # Optionally run discovery script to refresh catalog
            if script_path.exists():
                logger.info(f"Found discovery script at: {script_path}")
                catalog_file = SCRIPT_DIR / "business_objects_catalog.json"
                
                # Only run if catalog doesn't exist
                if not catalog_file.exists():
                    logger.info("Catalog file doesn't exist, running discovery script...")
                    try:
                        result = subprocess.run(
                            [sys.executable, str(script_path)],
                            cwd=str(SCRIPT_DIR),
                            capture_output=True,
                            encoding='utf-8',
                            errors='ignore',  # CRITICAL: Ignore decode errors
                            timeout=60
                        )
                        if result.returncode == 0:
                            logger.info("✓ Discovery script completed successfully")
                        else:
                            logger.warning(f"⚠ Discovery script returned code {result.returncode}")
                            if result.stderr:
                                logger.warning(f"Script errors: {result.stderr[:500]}")
                    except subprocess.TimeoutExpired:
                        logger.warning("⚠ Discovery script timed out after 60 seconds")
                    except Exception as e:
                        logger.warning(f"⚠ Could not run discovery script: {str(e)}")
                else:
                    logger.info("Catalog file exists, skipping discovery script")
            
            # Try multiple possible locations for the catalog file
            possible_paths = [
                SCRIPT_DIR / "business_objects_catalog.json",
                Path(__file__).parent / "business_objects_catalog.json",
                Path.cwd() / "business_objects_catalog.json",
                Path(os.getenv("SYSPRO_CATALOG_PATH", "")) / "business_objects_catalog.json" if os.getenv("SYSPRO_CATALOG_PATH") else None,
            ]
            
            # Filter out None values
            possible_paths = [p for p in possible_paths if p]
            
            for catalog_path in possible_paths:
                if catalog_path.exists():
                    logger.info(f"Loading business objects catalog from: {catalog_path}")
                    with open(catalog_path, 'r', encoding='utf-8') as f:
                        self.business_objects_catalog = json.load(f)
                    logger.info(f"✓ Loaded {len(self.business_objects_catalog)} business objects")
                    return True
            
            logger.warning("⚠ Business objects catalog not found. Checked paths:")
            for path in possible_paths:
                logger.warning(f"  - {path}")
            logger.info("The server will work without the catalog, but won't have business object documentation.")
            logger.info("Run discover_business_objects.py manually to generate the catalog.")
            return False
            
        except Exception as e:
            logger.error(f"Error loading business objects catalog: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def auto_configure(self) -> bool:
        """Attempt to configure SYSPRO from environment variables"""
        base_url = os.getenv("SYSPRO_BASE_URL")
        operator = os.getenv("SYSPRO_OPERATOR")
        password = os.getenv("SYSPRO_PASSWORD")
        company_id = os.getenv("SYSPRO_COMPANY_ID", "")
        company_password = os.getenv("SYSPRO_COMPANY_PASSWORD", "")
        
        logger.info("Attempting auto-configuration from environment variables...")
        logger.info(f"  SYSPRO_BASE_URL: {'✓ Set' if base_url else '✗ Not set'}")
        logger.info(f"  SYSPRO_OPERATOR: {'✓ Set' if operator else '✗ Not set'}")
        logger.info(f"  SYSPRO_PASSWORD: {'✓ Set' if password else '✗ Not set'}")
        logger.info(f"  SYSPRO_COMPANY_ID: {company_id if company_id else '(empty)'}")
        
        if base_url and operator and password:
            self.syspro_client = SysproClient(
                base_url=base_url,
                operator=operator,
                password=password,
                company_id=company_id,
                company_password=company_password
            )
            
            # Attempt to log on and establish session
            success = await self.syspro_client.logon()
            if success:
                logger.info("✓ Auto-configuration successful - SYSPRO connection established")
                return True
            else:
                logger.error("✗ Auto-configuration failed - Could not authenticate with SYSPRO")
                self.syspro_client = None
                return False
        else:
            missing = []
            if not base_url:
                missing.append("SYSPRO_BASE_URL")
            if not operator:
                missing.append("SYSPRO_OPERATOR")
            if not password:
                missing.append("SYSPRO_PASSWORD")
            
            logger.warning(f"Auto-configuration skipped - Missing environment variables: {', '.join(missing)}")
            logger.info("SYSPRO will need to be configured manually using syspro_configure tool")
            return False
    
    def _setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources"""
            resources = []
            
            if self.business_objects_catalog:
                resources.append(
                    Resource(
                        uri="syspro://catalog/business_objects",
                        name="SYSPRO Business Objects Catalog",
                        mimeType="application/json",
                        description=f"Complete catalog of {len(self.business_objects_catalog)} SYSPRO business objects with XML examples"
                    )
                )
            
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            if uri == "syspro://catalog/business_objects":
                if self.business_objects_catalog:
                    # Return formatted catalog information
                    return json.dumps(self.business_objects_catalog, indent=2)
                else:
                    return json.dumps({"error": "Business objects catalog not loaded"})
            else:
                raise ValueError(f"Unknown resource: {uri}")
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available SYSPRO tools"""
            return [
                Tool(
                    name="syspro_list_business_objects",
                    description="List and search SYSPRO business objects from the catalog. Use this to find available business objects by module, type, or search term.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "module": {
                                "type": "string",
                                "description": "Filter by module code (e.g., INV, SOR, POR, ARS, APS). Leave empty for all modules.",
                                "default": ""
                            },
                            "type": {
                                "type": "string",
                                "description": "Filter by type (Query, Setup, Transaction, Build, Browse). Leave empty for all types.",
                                "default": ""
                            },
                            "search": {
                                "type": "string",
                                "description": "Search term to filter business objects by code. Leave empty to list all.",
                                "default": ""
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 50)",
                                "default": 50
                            }
                        }
                    }
                ),
                Tool(
                    name="syspro_get_business_object_details",
                    description="Get detailed information about a specific SYSPRO business object, including sample XML.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_object": {
                                "type": "string",
                                "description": "Business object code (e.g., INVQRY, SORTOI, PORQRY)"
                            }
                        },
                        "required": ["business_object"]
                    }
                ),
                Tool(
                    name="syspro_search_entity",
                    description="Search for SYSPRO entities (customers, suppliers, stock codes, etc.) by name. Use this when you have a name but need to find the code. For example, searching 'bayside bikes' will return the customer code.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "The name or partial name to search for (e.g., 'bayside bikes', 'john smith')"
                            },
                            "tile_name": {
                                "type": "string",
                                "description": "The SYSPRO tile to query (default: USR004_SQL for general search)",
                                "default": "USR004_SQL"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 1000000)",
                                "default": 1000000
                            }
                        },
                        "required": ["search_term"]
                    }
                ),
                Tool(
                    name="syspro_query_setup_options",
                    description="Query SYSPRO setup options for a specific module or area. Use this when asked about configuration settings, setup options, or system parameters. This tool automatically finds the appropriate QSO (Query Setup Options) business object and returns the current settings. Examples: 'What are the inventory setup options?', 'Show me AR configuration', 'What are the sales order settings?'",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "module_or_area": {
                                "type": "string",
                                "description": "The module or area to query setup options for (e.g., 'inventory', 'sales order', 'purchase order', 'accounts receivable', 'AR', 'INV', 'SOR', 'POR', 'APS', 'GLD', 'WIP', 'BOM')"
                            },
                            "company": {
                                "type": "string",
                                "description": "Company code to query (optional, uses logged-in company if not specified)",
                                "default": ""
                            }
                        },
                        "required": ["module_or_area"]
                    }
                ),
                Tool(
                    name="syspro_configure",
                    description="Configure SYSPRO connection settings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "base_url": {
                                "type": "string",
                                "description": "SYSPRO WCF REST base URL (e.g., http://server:port/SYSPROWCFService/Rest)"
                            },
                            "operator": {
                                "type": "string",
                                "description": "SYSPRO operator code"
                            },
                            "password": {
                                "type": "string",
                                "description": "Operator password"
                            },
                            "company_id": {
                                "type": "string",
                                "description": "Company ID (optional)",
                                "default": ""
                            },
                            "company_password": {
                                "type": "string",
                                "description": "Company password (optional)",
                                "default": ""
                            }
                        },
                        "required": ["base_url", "operator", "password"]
                    }
                ),
                Tool(
                    name="syspro_query",
                    description="Query data from SYSPRO using any business object. Use the business_objects catalog resource to find available business objects and XML examples.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_object": {
                                "type": "string",
                                "description": "Business object name (e.g., INVQRY, SORQRY, ARSCUS)"
                            },
                            "xml_in": {
                                "type": "string",
                                "description": "XML input for the query"
                            }
                        },
                        "required": ["business_object", "xml_in"]
                    }
                ),
                Tool(
                    name="syspro_setup_add",
                    description="Add a new record using Setup business objects. Use the business_objects catalog resource to find available business objects and XML examples.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_object": {
                                "type": "string",
                                "description": "Business object name (e.g., INVMST, ARSTOR)"
                            },
                            "xml_in": {
                                "type": "string",
                                "description": "XML input data"
                            },
                            "xml_parameters": {
                                "type": "string",
                                "description": "Optional XML parameters",
                                "default": ""
                            }
                        },
                        "required": ["business_object", "xml_in"]
                    }
                ),
                Tool(
                    name="syspro_setup_update",
                    description="Update an existing record using Setup business objects. Use the business_objects catalog resource to find available business objects and XML examples.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_object": {
                                "type": "string",
                                "description": "Business object name"
                            },
                            "xml_in": {
                                "type": "string",
                                "description": "XML input data"
                            },
                            "xml_parameters": {
                                "type": "string",
                                "description": "Optional XML parameters",
                                "default": ""
                            }
                        },
                        "required": ["business_object", "xml_in"]
                    }
                ),
                Tool(
                    name="syspro_setup_delete",
                    description="Delete a record using Setup business objects. Use the business_objects catalog resource to find available business objects and XML examples.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_object": {
                                "type": "string",
                                "description": "Business object name"
                            },
                            "xml_in": {
                                "type": "string",
                                "description": "XML input data"
                            },
                            "xml_parameters": {
                                "type": "string",
                                "description": "Optional XML parameters",
                                "default": ""
                            }
                        },
                        "required": ["business_object", "xml_in"]
                    }
                ),
                Tool(
                    name="syspro_transaction_post_ld",
                    description="Post a large transaction (preferred for big posts, avoids URL length limits). Use the business_objects catalog resource to find available business objects and XML examples.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "business_object": {
                                "type": "string",
                                "description": "Business object name"
                            },
                            "xml_in": {
                                "type": "string",
                                "description": "XML input data"
                            },
                            "xml_parameters": {
                                "type": "string",
                                "description": "Optional XML parameters",
                                "default": ""
                            }
                        },
                        "required": ["business_object", "xml_in"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls"""
            
            try:
                # Handle catalog tools (don't require SYSPRO connection)
                if name == "syspro_list_business_objects":
                    return await self._list_business_objects(arguments)
                elif name == "syspro_get_business_object_details":
                    return await self._get_business_object_details(arguments)
                elif name == "syspro_configure":
                    return await self._configure_connection(arguments)
                
                # Auto-configure from environment if not already configured
                if not self.syspro_client:
                    logger.info("No client configured, attempting auto-configuration")
                    success = await self.auto_configure()
                    if not success:
                        return [TextContent(
                            type="text",
                            text="Error: SYSPRO not configured. Please set environment variables in claude_desktop_config.json or use syspro_configure tool."
                        )]
                
                if name == "syspro_query":
                    return await self._query(arguments)
                elif name == "syspro_query_setup_options":
                    return await self._query_setup_options(arguments)
                elif name == "syspro_search_entity":
                    return await self._search_entity(arguments)
                elif name == "syspro_setup_add":
                    return await self._setup_add(arguments)
                elif name == "syspro_setup_update":
                    return await self._setup_update(arguments)
                elif name == "syspro_setup_delete":
                    return await self._setup_delete(arguments)
                elif name == "syspro_transaction_post_ld":
                    return await self._transaction_post_ld(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return [TextContent(
                    type="text",
                    text=f"Error executing tool: {str(e)}"
                )]

    async def _list_business_objects(self, args: Dict[str, Any]) -> list[TextContent]:
        """List business objects from catalog"""
        if not self.business_objects_catalog:
            return [TextContent(
                type="text",
                text="❌ Business objects catalog not loaded. Please ensure business_objects_catalog.json is in the server directory."
            )]
        
        module_filter = args.get("module", "").upper()
        type_filter = args.get("type", "")
        search_term = args.get("search", "").upper()
        limit = args.get("limit", 50)
        
        # Filter business objects
        filtered = []
        for code, data in self.business_objects_catalog.items():
            # Apply filters
            if module_filter and data.get("module", "") != module_filter:
                continue
            if type_filter and data.get("type", "") != type_filter:
                continue
            if search_term and search_term not in code.upper():
                if search_term and search_term not in data.get("description", ""):
                    continue
            
            filtered.append((code, data))
        
        # Sort by code
        filtered.sort(key=lambda x: x[0])
        
        # Limit results
        filtered = filtered[:limit]
        
        if not filtered:
            return [TextContent(
                type="text",
                text=f"No business objects found matching the criteria.\n"
                     f"Module: {module_filter or 'all'}, Type: {type_filter or 'all'}, Search: {search_term or 'none'}"
            )]
        
        # Format output
        result_lines = [
            f"📚 Found {len(filtered)} SYSPRO Business Objects",
            f"Filters: Module={module_filter or 'all'}, Type={type_filter or 'all'}, Search={search_term or 'none'}",
            ""
        ]
        
        # Group by module for better readability
        by_module = {}
        for code, data in filtered:
            module = data.get("module", "Unknown")
            if module not in by_module:
                by_module[module] = []
            by_module[module].append((code, data))
        
        for module in sorted(by_module.keys()):
            result_lines.append(f"\n📦 {module} Module:")
            for code, data in by_module[module]:
                obj_type = data.get("type", "Unknown")
                xml_root = data.get("xml_root", "N/A")
                result_lines.append(f"  • {code:10} [{obj_type:12}] - Root: {xml_root}")
        
        result_lines.append(f"\n💡 Use syspro_get_business_object_details to see XML examples for any object.")
        
        return [TextContent(
            type="text",
            text="\n".join(result_lines)
        )]
    
    async def _get_business_object_details(self, args: Dict[str, Any]) -> list[TextContent]:
        """Get detailed information about a business object"""
        if not self.business_objects_catalog:
            return [TextContent(
                type="text",
                text="❌ Business objects catalog not loaded."
            )]
        
        bo_code = args["business_object"].upper()
        
        if bo_code not in self.business_objects_catalog:
            return [TextContent(
                type="text",
                text=f"❌ Business object '{bo_code}' not found in catalog.\n"
                     f"Use syspro_list_business_objects to see available objects."
            )]
        
        bo_data = self.business_objects_catalog[bo_code]
        
        # Format detailed information
        result_lines = [
            f"📋 Business Object: {bo_code}",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"Module:      {bo_data.get('module', 'N/A')}",
            f"Type:        {bo_data.get('type', 'N/A')}",
            f"XML Root:    {bo_data.get('xml_root', 'N/A')}",
            f"Description: {bo_data.get('description', 'No description available')}",
            f""
        ]
        
        # Show what XML is required
        if bo_data.get("has_parameters"):
            result_lines.append("📝 Requires: Parameters XML")
        if bo_data.get("has_document"):
            result_lines.append("📝 Requires: Document XML")
        
        result_lines.append("")
        
        # Show sample XML if available
        sample_xml = bo_data.get("sample_input_xml", "")
        if sample_xml:
            result_lines.append("📄 Sample Input XML:")
            result_lines.append("```xml")
            # Truncate if too long
            if len(sample_xml) > 2000:
                result_lines.append(sample_xml[:2000] + "\n... (truncated)")
            else:
                result_lines.append(sample_xml)
            result_lines.append("```")
        else:
            result_lines.append("⚠️  No sample XML available for this business object.")
        
        if bo_data.get("has_parameters"):
            # Show sample XML if available
            param_xml = bo_data.get("sample_doc_xml", "")
            if param_xml:
                result_lines.append("📄 Sample Parameter XML:")
                result_lines.append("```xml")
                # Truncate if too long
                if len(param_xml) > 2000:
                    result_lines.append(param_xml[:2000] + "\n... (truncated)")
                else:
                    result_lines.append(param_xml)
                result_lines.append("```")
            else:
                result_lines.append("⚠️  No sample XML Parameters available for this business object.")
        else:
                result_lines.append("⚠️  No sample XML Parameters required for this business object.")
        
        result_lines.append("")
        result_lines.append("💡 Use this XML as a template with the appropriate syspro_query, syspro_setup_*, or syspro_transaction_* tool.")

        return [TextContent(
            type="text",
            text="\n".join(result_lines)
        )]

    def _find_qso_business_objects(self, module_or_area: str) -> list[tuple[str, Dict[str, Any]]]:
        """
        Find QSO (Query Setup Options) business objects matching the given module or area.

        Args:
            module_or_area: Module code or descriptive area name

        Returns:
            List of tuples (bo_code, bo_data) for matching QSO business objects
        """
        # Normalize the input
        search_term = module_or_area.upper().strip()

        # Map common names to module codes
        module_mappings = {
            # Inventory
            "INVENTORY": "INV",
            "STOCK": "INV",
            "WAREHOUSE": "INV",
            # Sales
            "SALES ORDER": "SOR",
            "SALES ORDERS": "SOR",
            "SALES": "SOR",
            "SO": "SOR",
            # Purchase
            "PURCHASE ORDER": "POR",
            "PURCHASE ORDERS": "POR",
            "PURCHASE": "POR",
            "PURCHASING": "POR",
            "PO": "POR",
            # Accounts Receivable
            "ACCOUNTS RECEIVABLE": "ARS",
            "AR": "ARS",
            "RECEIVABLES": "ARS",
            "DEBTORS": "ARS",
            "CUSTOMER": "ARS",
            "CUSTOMERS": "ARS",
            # Accounts Payable
            "ACCOUNTS PAYABLE": "APS",
            "AP": "APS",
            "PAYABLES": "APS",
            "CREDITORS": "APS",
            "SUPPLIER": "APS",
            "SUPPLIERS": "APS",
            "VENDOR": "APS",
            "VENDORS": "APS",
            # General Ledger
            "GENERAL LEDGER": "GLD",
            "GL": "GLD",
            "LEDGER": "GLD",
            # Work in Progress
            "WORK IN PROGRESS": "WIP",
            "WIP": "WIP",
            "MANUFACTURING": "WIP",
            "PRODUCTION": "WIP",
            # Bill of Materials
            "BILL OF MATERIALS": "BOM",
            "BOM": "BOM",
            "STRUCTURES": "BOM",
            # Cash Book
            "CASH BOOK": "CBS",
            "CASH": "CBS",
            "BANK": "CBS",
            # Assets
            "ASSETS": "ASS",
            "FIXED ASSETS": "ASS",
            # Contact Management
            "CONTACT": "CRM",
            "CONTACTS": "CRM",
            "CRM": "CRM",
            # Lot Traceability
            "LOT": "LOT",
            "LOTS": "LOT",
            "TRACEABILITY": "LOT",
            # Serial Tracking
            "SERIAL": "SER",
            "SERIALS": "SER",
            # Quotations
            "QUOTATION": "QOT",
            "QUOTATIONS": "QOT",
            "QUOTE": "QOT",
            "QUOTES": "QOT",
            # Return Merchandise
            "RMA": "RMA",
            "RETURN": "RMA",
            "RETURNS": "RMA",
            # Requisitions
            "REQUISITION": "REQ",
            "REQUISITIONS": "REQ",
            # Global Tax
            "TAX": "GTX",
            "GLOBAL TAX": "GTX",
            # Company
            "COMPANY": "COM",
            "SYSTEM": "COM",
            "COMMON": "COM",
        }

        # Determine module code(s) to search for
        target_modules = []

        # Check if input is a known mapping
        if search_term in module_mappings:
            target_modules.append(module_mappings[search_term])
        # Check if it's already a 3-letter module code
        elif len(search_term) == 3 and search_term.isalpha():
            target_modules.append(search_term)
        # Otherwise, search for partial matches in mappings
        else:
            for name, code in module_mappings.items():
                if search_term in name or name in search_term:
                    if code not in target_modules:
                        target_modules.append(code)

        # If no matches found, try direct search in catalog
        if not target_modules:
            target_modules = [search_term[:3]]  # Use first 3 chars as module guess

        # Find all QSO business objects for the target modules
        qso_objects = []

        if self.business_objects_catalog:
            for bo_code, bo_data in self.business_objects_catalog.items():
                # QSO business objects end with "QSO" (Query Setup Options)
                if bo_code.endswith("QSO"):
                    bo_module = bo_data.get("module", "")
                    # Match against target modules
                    if bo_module in target_modules:
                        qso_objects.append((bo_code, bo_data))
                    # Also include if the search term appears in the BO code
                    elif any(tm in bo_code for tm in target_modules):
                        qso_objects.append((bo_code, bo_data))

        # Sort by code
        qso_objects.sort(key=lambda x: x[0])

        return qso_objects

    async def _query_setup_options(self, args: Dict[str, Any]) -> list[TextContent]:
        """
        Query setup options for a specific module or area.
        Automatically finds and queries the appropriate QSO business object.
        """
        module_or_area = args.get("module_or_area", "")
        company = args.get("company", "")

        if not module_or_area:
            return [TextContent(
                type="text",
                text="❌ Please specify a module or area to query setup options for.\n\nExamples:\n- 'inventory' or 'INV'\n- 'sales order' or 'SOR'\n- 'accounts receivable' or 'ARS'"
            )]

        # Find matching QSO business objects
        qso_objects = self._find_qso_business_objects(module_or_area)

        if not qso_objects:
            # No QSO found - search for any business objects ending in QSO
            all_qso = []
            if self.business_objects_catalog:
                for bo_code, bo_data in self.business_objects_catalog.items():
                    if bo_code.endswith("QSO"):
                        all_qso.append((bo_code, bo_data.get("module", "Unknown")))

            result_lines = [
                f"❌ No Query Setup Options (QSO) business objects found for '{module_or_area}'.",
                "",
                "Available QSO business objects in the catalog:"
            ]

            if all_qso:
                # Group by module
                by_module = {}
                for code, module in all_qso:
                    if module not in by_module:
                        by_module[module] = []
                    by_module[module].append(code)

                for module in sorted(by_module.keys()):
                    result_lines.append(f"\n📦 {module} Module:")
                    for code in by_module[module]:
                        result_lines.append(f"  • {code}")
            else:
                result_lines.append("  (No QSO business objects found in catalog)")

            result_lines.append("")
            result_lines.append("💡 Try using one of the module codes listed above, or use syspro_list_business_objects with search='QSO' to see all available options.")

            return [TextContent(
                type="text",
                text="\n".join(result_lines)
            )]

        # Found QSO objects - query each one
        result_lines = [
            f"⚙️ Setup Options for '{module_or_area}'",
            f"{'=' * 60}",
            f"\nFound {len(qso_objects)} Query Setup Options (QSO) business object(s):\n"
        ]

        for bo_code, bo_data in qso_objects:
            result_lines.append(f"📋 {bo_code} - {bo_data.get('module', 'Unknown')} Module")
            result_lines.append("-" * 40)

            # Build a basic query XML for the QSO
            # Use the company from args, or fall back to the client's configured company_id
            effective_company = company if company else self.syspro_client.company_id

            # Most QSO objects accept a simple Query with Company in the Key
            if effective_company:
                xml_in = f"""<?xml version="1.0" encoding="UTF-8"?>
<Query>
    <Key>
        <Company>{effective_company}</Company>
    </Key>
</Query>"""
            else:
                xml_in = """<?xml version="1.0" encoding="UTF-8"?>
<Query>
    <Option>
        <XslStylesheet/>
    </Option>
</Query>"""

            # Try to query the setup options
            try:
                query_result = await self.syspro_client.query(
                    business_object=bo_code,
                    xml_in=xml_in
                )

                if query_result["success"]:
                    result_lines.append("✓ Query successful")
                    result_lines.append("")
                    # Format the result
                    parsed = query_result.get("parsed_data", {})
                    formatted = self._format_result(parsed)
                    result_lines.append(formatted)
                else:
                    error = query_result.get("error", "Unknown error")
                    result_lines.append(f"⚠️ Query returned error: {error}")

                    # Try with alternative XML format
                    xml_in_alt = f"""<?xml version="1.0" encoding="UTF-8"?>
<Query/>"""
                    query_result_alt = await self.syspro_client.query(
                        business_object=bo_code,
                        xml_in=xml_in_alt
                    )

                    if query_result_alt["success"]:
                        result_lines.append("✓ Retry with simple query successful")
                        result_lines.append("")
                        parsed = query_result_alt.get("parsed_data", {})
                        formatted = self._format_result(parsed)
                        result_lines.append(formatted)

            except Exception as e:
                result_lines.append(f"❌ Error querying {bo_code}: {str(e)}")

            result_lines.append("")

        result_lines.append("💡 To see the XML schema for any QSO business object, use:")
        result_lines.append(f"   syspro_get_business_object_details with business_object='{qso_objects[0][0]}'")

        return [TextContent(
            type="text",
            text="\n".join(result_lines)
        )]

    async def _configure_connection(self, args: Dict[str, Any]) -> list[TextContent]:
        """Configure SYSPRO connection"""
        self.syspro_client = SysproClient(
            base_url=args["base_url"],
            operator=args["operator"],
            password=args["password"],
            company_id=args.get("company_id", ""),
            company_password=args.get("company_password", "")
        )

        success = await self.syspro_client.logon()

        if success:
            return [TextContent(
                type="text",
                text="✓ Successfully connected to SYSPRO and authenticated."
            )]
        else:
            return [TextContent(
                type="text",
                text="✗ Failed to connect to SYSPRO. Please check your credentials."
            )]

    async def _query(self, args: Dict[str, Any]) -> list[TextContent]:
        """Execute query"""
        result = await self.syspro_client.query(
            business_object=args["business_object"],
            xml_in=args["xml_in"]
        )
        
        if result["success"]:
            return [TextContent(
                type="text",
                text=f"Query Results:\n\n{self._format_result(result['parsed_data'])}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Error in query: {result.get('error', 'Unknown error')}"
            )]
    
    async def _search_entity(self, args: Dict[str, Any]) -> list[TextContent]:
        """Execute entity search"""
        search_term = args["search_term"]
        tile_name = args.get("tile_name", "USR004_SQL")
        max_results = args.get("max_results", 1000000)
        
        result = await self.syspro_client.search_entity(
            search_term=search_term,
            tile_name=tile_name,
            max_results=max_results
        )
        
        if result["success"]:
            results = result.get("results", [])
            
            if not results:
                return [TextContent(
                    type="text",
                    text=f"No results found for '{search_term}'.\n\nThe search returned no matches. Try:\n- Checking spelling\n- Using fewer or different keywords\n- Being less specific"
                )]
            
            # Format the results nicely
            lines = [
                f"🔍 Search Results for '{search_term}'",
                f"=" * 60,
                f"\nFound {len(results)} result(s):\n"
            ]
            
            for i, item in enumerate(results, 1):
                entity_type = item["type"]
                entity_code = item["code"]
                entity_code_clean = item["code_clean"]
                
                lines.append(f"{i}. {entity_type}")
                lines.append(f"   Code: {entity_code_clean} (Full: {entity_code})")
                lines.append("")
            
            lines.append("💡 You can now use these codes in other SYSPRO operations.")
            lines.append(f"   Example: Query customer {results[0]['code_clean']} details")
            
            return [TextContent(
                type="text",
                text="\n".join(lines)
            )]
        else:
            error_msg = result.get("error", "Unknown error")
            return [TextContent(
                type="text",
                text=f"Error searching for '{search_term}': {error_msg}\n\nRaw response:\n{result.get('raw_response', 'N/A')}"
            )]
    
    async def _setup_add(self, args: Dict[str, Any]) -> list[TextContent]:
        """Execute setup add"""
        result = await self.syspro_client.setup_add(
            business_object=args["business_object"],
            xml_in=args["xml_in"],
            xml_parameters=args.get("xml_parameters")
        )
        
        return self._format_operation_result("Add", result)
    
    async def _setup_update(self, args: Dict[str, Any]) -> list[TextContent]:
        """Execute setup update"""
        result = await self.syspro_client.setup_update(
            business_object=args["business_object"],
            xml_in=args["xml_in"],
            xml_parameters=args.get("xml_parameters")
        )
        
        return self._format_operation_result("Update", result)
    
    async def _setup_delete(self, args: Dict[str, Any]) -> list[TextContent]:
        """Execute setup delete"""
        result = await self.syspro_client.setup_delete(
            business_object=args["business_object"],
            xml_in=args["xml_in"],
            xml_parameters=args.get("xml_parameters")
        )
        
        return self._format_operation_result("Delete", result)
   
    
    async def _transaction_post_ld(self, args: Dict[str, Any]) -> list[TextContent]:
        """Execute transaction post LD (large data)"""
        result = await self.syspro_client.transaction_post_ld(
            business_object=args["business_object"],
            xml_in=args["xml_in"],
            xml_parameters=args.get("xml_parameters")
        )
        
        return self._format_operation_result("Transaction PostLd", result)
    
    def _format_operation_result(self, operation: str, result: Dict[str, Any]) -> list[TextContent]:
        """Format operation result"""
        if result["success"]:
            return [TextContent(
                type="text",
                text=f"{operation} completed successfully.\n\n{self._format_result(result['parsed_data'])}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Error in {operation}: {result.get('error', 'Unknown error')}"
            )]
    
    def _format_result(self, data: Any, indent: int = 0) -> str:
        """Format result data for display"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if key.startswith("@") or key.startswith("#"):
                    continue
                prefix = "  " * indent
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.append(self._format_result(value, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            lines = []
            for i, item in enumerate(data):
                prefix = "  " * indent
                lines.append(f"{prefix}[{i}]:")
                lines.append(self._format_result(item, indent + 1))
            return "\n".join(lines)
        else:
            return str(data)
    
    async def run(self):
        """Run the MCP server"""
        # Load business objects catalog
        logger.info("Loading SYSPRO business objects catalog...")
        self._load_business_objects_catalog()
        
        # Attempt auto-configuration on startup
        logger.info("Starting SYSPRO MCP Server...")
        await self.auto_configure()
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    server = SysproMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())