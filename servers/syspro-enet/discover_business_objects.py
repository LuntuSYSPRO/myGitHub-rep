"""
SYSPRO Business Object Discovery Tool
Scans the SYSPRO Schemas folder and builds a comprehensive database of all business objects
"""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

config_file_path = "syspro_config.json"

class SysproBusinessObjectDiscovery:
    """Discovers and catalogs SYSPRO business objects from schema files"""
    
    def __init__(self, schemas_path: str = r"C:\RND900\Base\Schemas"):
        r"""
        Initialize the discovery tool
        
        Args:
            schemas_path: Path to SYSPRO Base\Schemas folder
        """
        self.schemas_path = Path(schemas_path)
        self.business_objects = {}
        self.categories = defaultdict(list)
        
    def discover_all(self):
        """Scan the schemas folder and discover all business objects"""
        print(f"Scanning: {self.schemas_path}")
        print("=" * 60)
        
        if not self.schemas_path.exists():
            print(f"ERROR: Path does not exist: {self.schemas_path}")
            print(f"   Please check if SYSPRO is installed at this location.")
            return
        
        # Find all XML files (case-insensitive)
        all_files = list(self.schemas_path.glob("*"))
        xml_files = [f for f in all_files if f.suffix.upper() == '.XML']
        xsd_files = [f for f in all_files if f.suffix.upper() == '.XSD']
        
        print(f"Found {len(xml_files)} XML files")
        print(f"Found {len(xsd_files)} XSD files")
        print()
        
        # Process each business object
        business_object_codes = set()
        
        # Extract business object codes from filenames
        for xml_file in xml_files:
            filename = xml_file.stem.upper()
            
            # Skip output and document files
            if filename.endswith("OUT") or filename.endswith("DOC"):
                continue
                
            # Business object codes are typically 6 characters
            if len(filename) == 6 and filename.isalnum():
                business_object_codes.add(filename)
        
        print(f"Discovered {len(business_object_codes)} business objects")
        print()
        
        # Process each business object
        for bo_code in sorted(business_object_codes):
            self._process_business_object(bo_code)
        
        # Categorize business objects
        self._categorize_business_objects()
        
        return self.business_objects
    
    def _process_business_object(self, bo_code: str):
        """Process a single business object"""
        bo_info = {
            "code": bo_code,
            "module": bo_code[:3],
            "type": self._get_bo_type(bo_code[3]),
            "type_code": bo_code[3],
            "files": {},
            "description": "",
            "xml_root": None,
            "sample_input_xml": None,
            "sample_doc_xml": None,
            "sample_output_xml": None,
            "has_parameters": False,
            "has_document": False
        }
        
        # Determine file naming based on business object type
        type_char = bo_code[3]
        
        if type_char in ['T', 'S']:  # Transaction or Setup
            # Transaction/Setup pattern:
            # - Parameters: {BO}.XML
            # - Document: {BO}DOC.XML
            # - Output: {BO}OUT.XML
            param_file = self.schemas_path / f"{bo_code}.XML"
            doc_file = self.schemas_path / f"{bo_code}DOC.XML"
            out_file = self.schemas_path / f"{bo_code}OUT.XML"
            
            param_schema = self.schemas_path / f"{bo_code}.XSD"
            doc_schema = self.schemas_path / f"{bo_code}DOC.XSD"
            out_schema = self.schemas_path / f"{bo_code}OUT.XSD"
            
            if param_file.exists():
                bo_info["files"]["parameters"] = str(param_file)
                bo_info["sample_doc_xml"] = self._read_sample_xml(param_file)
                bo_info["has_parameters"] = True
                # If no description from params, try doc
                if not bo_info["description"]:
                    bo_info["description"] = self._extract_description_from_xml(param_file)
                
            if doc_file.exists():
                bo_info["files"]["document"] = str(doc_file)
                bo_info["sample_input_xml"] = self._read_sample_xml(doc_file)
                bo_info["xml_root"] = self._get_xml_root(doc_file)
                bo_info["description"] = self._extract_description_from_xml(doc_file)
                bo_info["has_document"] = True
                
            if out_file.exists():
                bo_info["files"]["output"] = str(out_file)
                bo_info["sample_output_xml"] = self._read_sample_xml(out_file)
                
            if param_schema.exists():
                bo_info["files"]["parameters_schema"] = str(param_schema)
                
            if doc_schema.exists():
                bo_info["files"]["document_schema"] = str(doc_schema)
                
            if out_schema.exists():
                bo_info["files"]["output_schema"] = str(out_schema)
                
        else:  # Query or other types
            # Query pattern:
            # - Input: {BO}.XML
            # - Output: {BO}OUT.XML
            input_file = self.schemas_path / f"{bo_code}.XML"
            out_file = self.schemas_path / f"{bo_code}OUT.XML"
            
            input_schema = self.schemas_path / f"{bo_code}.XSD"
            out_schema = self.schemas_path / f"{bo_code}OUT.XSD"
            
            if input_file.exists():
                bo_info["files"]["input"] = str(input_file)
                bo_info["sample_input_xml"] = self._read_sample_xml(input_file)
                bo_info["xml_root"] = self._get_xml_root(input_file)
                bo_info["description"] = self._extract_description_from_xml(input_file)
                
            if out_file.exists():
                bo_info["files"]["output"] = str(out_file)
                bo_info["sample_output_xml"] = self._read_sample_xml(out_file)
                
            if input_schema.exists():
                bo_info["files"]["input_schema"] = str(input_schema)
                
            if out_schema.exists():
                bo_info["files"]["output_schema"] = str(out_schema)
        
        self.business_objects[bo_code] = bo_info
    
    def _get_bo_type(self, type_char: str) -> str:
        """Get business object type from character"""
        type_map = {
            'Q': 'Query',
            'S': 'Setup',
            'T': 'Transaction',
            'R': 'Build',
            'B': 'Browse'
        }
        return type_map.get(type_char, 'Unknown')
    
    def _read_sample_xml(self, xml_file: Path) -> str:
        """Read sample XML content"""
        try:
            # Try UTF-8 first, then fall back to other encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(xml_file, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                        # Limit to first 1000 characters for sample
                        return content[:1000] if len(content) > 1000 else content
                except (UnicodeDecodeError, LookupError):
                    continue
            
            # If all encodings fail, read as binary and decode with errors='replace'
            with open(xml_file, 'rb') as f:
                content = f.read().decode('utf-8', errors='replace')
                return content[:1000] if len(content) > 1000 else content
                
        except Exception as e:
            return None
    
    def _get_xml_root(self, xml_file: Path) -> str:
        """Get root element name from XML file"""
        try:
            # Try multiple encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(xml_file, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                    root = ET.fromstring(content)
                    return root.tag
                except (ET.ParseError, UnicodeDecodeError):
                    continue
            
            return None
        except Exception as e:
            return None
    
    def _extract_description_from_xml(self, xml_file: Path) -> str:
        """Extract description from XML file comments"""
        try:
            # Try multiple encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(xml_file, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                        # Look for description in comments
                        # Pattern: <!-- Description text -->
                        import re
                        comments = re.findall(r'<!--\s*(.*?)\s*-->', content, re.DOTALL)
                        for comment in comments:
                            # Skip copyright and empty comments
                            if 'copyright' in comment.lower() or len(comment.strip()) < 10:
                                continue
                            # Return first meaningful comment
                            clean_comment = ' '.join(comment.split())  # Normalize whitespace
                            if len(clean_comment) > 10:
                                return clean_comment[:200]  # Limit length
                        return ""
                except (UnicodeDecodeError, LookupError):
                    continue
            
            return ""
        except Exception as e:
            return ""
    
    def _extract_description(self, schema_file: Path) -> str:
        """Extract description from XSD schema file"""
        try:
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(schema_file, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                        # Look for description in comments
                        if "Copyright" in content:
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if 'Copyright' in line and i + 1 < len(lines):
                                    next_line = lines[i + 1].strip()
                                    if next_line.startswith('<!--'):
                                        desc = next_line.replace('<!--', '').replace('-->', '').strip()
                                        return desc
                    return ""
                except (UnicodeDecodeError, LookupError):
                    continue
            
            return ""
        except Exception as e:
            return ""
    
    def _categorize_business_objects(self):
        """Categorize business objects by module and type"""
        for bo_code, bo_info in self.business_objects.items():
            module = bo_info["module"]
            bo_type = bo_info["type"]
            
            self.categories[module].append(bo_code)
            self.categories[bo_type].append(bo_code)
    
    def generate_report(self, output_file: str = "business_objects_catalog.md"):
        """Generate a markdown report of all business objects"""
        report = []
        
        report.append("# SYSPRO Business Objects Catalog")
        report.append(f"\nGenerated from: `{self.schemas_path}`")
        report.append(f"\nTotal Business Objects: **{len(self.business_objects)}**\n")
        
        # Summary by type
        report.append("## Summary by Type\n")
        type_counts = defaultdict(int)
        for bo in self.business_objects.values():
            type_counts[bo["type"]] += 1
        
        for bo_type, count in sorted(type_counts.items()):
            report.append(f"- **{bo_type}**: {count} objects")
        
        report.append("\n## Summary by Module\n")
        module_counts = defaultdict(int)
        for bo in self.business_objects.values():
            module_counts[bo["module"]] += 1
        
        for module, count in sorted(module_counts.items()):
            report.append(f"- **{module}**: {count} objects")
        
        # Detailed listing by type
        for bo_type in ["Query", "Setup", "Transaction", "Build", "Browse", "Unknown"]:
            objects = [bo for bo in self.business_objects.values() if bo["type"] == bo_type]
            if not objects:
                continue
                
            report.append(f"\n## {bo_type} Business Objects ({len(objects)})\n")
            
            for bo in sorted(objects, key=lambda x: x["code"]):
                report.append(f"### {bo['code']} - {bo['module']} Module\n")
                
                if bo["description"]:
                    report.append(f"**Description**: {bo['description']}\n")
                
                if bo["xml_root"]:
                    report.append(f"**XML Root Element**: `{bo['xml_root']}`\n")
                
                report.append("**Required XML**:")
                if bo["type_code"] in ['T', 'S']:
                    report.append("- **XmlIn**: Document data (see `DOC.XML` example)")
                    report.append("- **XmlParameters**: Processing parameters (see `.XML` example)")
                else:
                    report.append("- **XmlIn**: Query input (see `.XML` example)")
                
                report.append("\n**Files Available**:")
                for file_type, file_path in bo["files"].items():
                    report.append(f"- {file_type}: `{Path(file_path).name}`")
                
                # Show sample input XML
                if bo["sample_input_xml"]:
                    if bo["type_code"] in ['T', 'S']:
                        report.append("\n**Sample Parameters XML**:")
                    else:
                        report.append("\n**Sample Input XML**:")
                    report.append("```xml")
                    # Limit to 30 lines
                    lines = bo["sample_input_xml"].split('\n')[:30]
                    report.append('\n'.join(lines))
                    if len(bo["sample_input_xml"].split('\n')) > 30:
                        report.append("... (truncated)")
                    report.append("```")
                
                # Show sample document XML for Transaction/Setup
                if bo["sample_doc_xml"] and bo["type_code"] in ['T', 'S']:
                    report.append("\n**Sample Document XML**:")
                    report.append("```xml")
                    lines = bo["sample_doc_xml"].split('\n')[:30]
                    report.append('\n'.join(lines))
                    if len(bo["sample_doc_xml"].split('\n')) > 30:
                        report.append("... (truncated)")
                    report.append("```")
                
                report.append("\n---\n")
        
        # Write report
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"[OK] Report generated: {output_path}")
        return output_path
    
    def generate_json(self, output_file: str = "business_objects_catalog.json"):
        """Generate JSON database of all business objects"""
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.business_objects, f, indent=2)
        
        print(f"[OK] JSON database generated: {output_path}")
        return output_path
    
    def generate_python_reference(self, output_file: str = "syspro_business_objects.py"):
        """Generate Python module with business object constants"""
        lines = []
        
        lines.append('"""')
        lines.append('SYSPRO Business Objects Reference')
        lines.append(f'Auto-generated from: {self.schemas_path}')
        lines.append('"""')
        lines.append('')
        lines.append('class BusinessObjects:')
        lines.append('    """SYSPRO Business Object codes"""')
        lines.append('')
        
        # Group by type
        for bo_type in ["Query", "Setup", "Transaction", "Build", "Browse"]:
            objects = [bo for bo in self.business_objects.values() if bo["type"] == bo_type]
            if not objects:
                continue
            
            lines.append(f'    # {bo_type} Objects')
            for bo in sorted(objects, key=lambda x: x["code"]):
                desc = bo.get("description", bo["code"])
                lines.append(f'    {bo["code"]} = "{bo["code"]}"  # {desc}')
            lines.append('')
        
        # Add helper dictionaries
        lines.append('    # Helper Dictionaries')
        lines.append('    BY_MODULE = {')
        for module in sorted(set(bo["module"] for bo in self.business_objects.values())):
            objects = [bo["code"] for bo in self.business_objects.values() if bo["module"] == module]
            lines.append(f'        "{module}": {objects},')
        lines.append('    }')
        lines.append('')
        
        lines.append('    BY_TYPE = {')
        for bo_type in ["Query", "Setup", "Transaction", "Build", "Browse"]:
            objects = [bo["code"] for bo in self.business_objects.values() if bo["type"] == bo_type]
            if objects:
                lines.append(f'        "{bo_type}": {objects},')
        lines.append('    }')
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"[OK] Python reference generated: {output_path}")
        return output_path
    
    def print_summary(self):
        """Print summary to console"""
        print("\n" + "=" * 60)
        print("BUSINESS OBJECTS SUMMARY")
        print("=" * 60)
        
        print(f"\nTotal: {len(self.business_objects)} business objects")
        
        print("\nBy Type:")
        type_counts = defaultdict(int)
        for bo in self.business_objects.values():
            type_counts[bo["type"]] += 1
        for bo_type, count in sorted(type_counts.items()):
            print(f"  {bo_type:15} {count:3} objects")
        
        print("\nBy Module:")
        module_counts = defaultdict(int)
        for bo in self.business_objects.values():
            module_counts[bo["module"]] += 1
        for module, count in sorted(module_counts.items())[:10]:  # Top 10
            print(f"  {module:15} {count:3} objects")
        if len(module_counts) > 10:
            print(f"  ... and {len(module_counts) - 10} more modules")
        
        print("\nSample Business Objects:")
        samples = list(self.business_objects.values())[:5]
        for bo in samples:
            print(f"  {bo['code']:8} {bo['type']:12} {bo['module']} Module")


def main():
    """Main entry point"""
    print("""
===============================================================
     SYSPRO Business Object Discovery Tool                 
===============================================================
    """)
    
    try:
        with open(config_file_path, 'r') as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file_path}' not found.")
        config = {} # Provide a default empty config or handle the error appropriately
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{config_file_path}'. Check file format.")
        config = {}
    
    # Default path
    default_path = config.get("syspro_installation", {}).get("schemas_path")
    
    schemas_path = default_path
    
    # Create discovery tool
    discovery = SysproBusinessObjectDiscovery(schemas_path)
    
    # Discover all business objects
    print("\nStarting discovery...")
    discovery.discover_all()
    
    # Print summary
    discovery.print_summary()
    
    # Generate outputs
    print("\nGenerating outputs...")
    discovery.generate_report("business_objects_catalog.md")
    discovery.generate_json("business_objects_catalog.json")
    discovery.generate_python_reference("syspro_business_objects.py")
    
    print("\n[SUCCESS] Discovery complete!")
    print("\nGenerated files:")
    print("  1. business_objects_catalog.md   - Human-readable reference")
    print("  2. business_objects_catalog.json - Machine-readable database")
    print("  3. syspro_business_objects.py    - Python constants module")
    print("\nYou can now:")
    print("  - Review the markdown catalog")
    print("  - Import the Python module in your code")
    print("  - Use the JSON for other integrations")


if __name__ == "__main__":
    main()