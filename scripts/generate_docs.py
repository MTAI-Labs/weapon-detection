#!/usr/bin/env python3
"""
API Documentation Generator

Generates comprehensive API documentation from FastAPI OpenAPI specification.
Creates both static HTML documentation and markdown files for version control.

Usage:
    python scripts/generate_docs.py [--output-dir docs] [--format html,markdown]
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import argparse
from datetime import datetime

try:
    import httpx
    from jinja2 import Environment, FileSystemLoader, Template
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Install with: pip install httpx jinja2")
    sys.exit(1)

# Add app to Python path
sys.path.append(str(Path(__file__).parent.parent))


class APIDocumentationGenerator:
    """Generates API documentation from OpenAPI specification."""
    
    def __init__(self, api_url: str = "http://localhost:8000", output_dir: str = "docs"):
        self.api_url = api_url.rstrip('/')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    async def fetch_openapi_spec(self) -> Dict[str, Any]:
        """Fetch OpenAPI specification from running API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/openapi.json")
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError:
            print(f"❌ Cannot connect to API at {self.api_url}")
            print("   Make sure the API is running: uvicorn app.main:app --reload")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error fetching OpenAPI spec: {e}")
            sys.exit(1)
    
    def generate_html_docs(self, openapi_spec: Dict[str, Any]) -> None:
        """Generate static HTML documentation."""
        html_template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ info.title }} - API Documentation</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { border-bottom: 2px solid #e1e5e9; padding-bottom: 20px; margin-bottom: 30px; }
        .endpoint { margin: 20px 0; padding: 20px; border: 1px solid #e1e5e9; border-radius: 8px; }
        .method { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; color: white; }
        .get { background-color: #28a745; }
        .post { background-color: #007bff; }
        .put { background-color: #ffc107; color: black; }
        .delete { background-color: #dc3545; }
        .path { font-family: Monaco, 'Courier New', monospace; font-size: 16px; margin-left: 10px; }
        .description { margin: 15px 0; color: #666; }
        .parameters { margin-top: 15px; }
        .parameter { margin: 10px 0; padding: 10px; background-color: #f8f9fa; border-radius: 4px; }
        .schema { font-family: Monaco, 'Courier New', monospace; background-color: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }
        .tag-section { margin: 30px 0; }
        .tag-title { font-size: 24px; font-weight: bold; color: #333; border-bottom: 1px solid #e1e5e9; padding-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ info.title }}</h1>
            <p>{{ info.description }}</p>
            <p><strong>Version:</strong> {{ info.version }}</p>
            <p><strong>Generated:</strong> {{ generated_at }}</p>
        </div>
        
        {% for tag, endpoints in endpoints_by_tag.items() %}
        <div class="tag-section">
            <h2 class="tag-title">{{ tag.title() }}</h2>
            {% for endpoint in endpoints %}
            <div class="endpoint">
                <div>
                    <span class="method {{ endpoint.method }}">{{ endpoint.method.upper() }}</span>
                    <span class="path">{{ endpoint.path }}</span>
                </div>
                <div class="description">{{ endpoint.summary or endpoint.description or 'No description available' }}</div>
                
                {% if endpoint.parameters %}
                <div class="parameters">
                    <h4>Parameters:</h4>
                    {% for param in endpoint.parameters %}
                    <div class="parameter">
                        <strong>{{ param.name }}</strong> ({{ param.in }}) - {{ param.schema.type if param.schema else 'any' }}
                        {% if param.required %}<em> (required)</em>{% endif %}
                        {% if param.description %}<br>{{ param.description }}{% endif %}
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                {% if endpoint.request_body %}
                <div class="parameters">
                    <h4>Request Body:</h4>
                    <div class="schema">{{ endpoint.request_body_example }}</div>
                </div>
                {% endif %}
                
                {% if endpoint.responses %}
                <div class="parameters">
                    <h4>Responses:</h4>
                    {% for status_code, response in endpoint.responses.items() %}
                    <div class="parameter">
                        <strong>{{ status_code }}</strong> - {{ response.description or 'No description' }}
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </div>
</body>
</html>
        """)
        
        # Parse endpoints by tag
        endpoints_by_tag = self._parse_endpoints_by_tag(openapi_spec)
        
        # Render HTML
        html_content = html_template.render(
            info=openapi_spec.get('info', {}),
            endpoints_by_tag=endpoints_by_tag,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Write HTML file
        html_file = self.output_dir / "api-documentation.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML documentation generated: {html_file}")
    
    def generate_markdown_docs(self, openapi_spec: Dict[str, Any]) -> None:
        """Generate markdown documentation for version control."""
        info = openapi_spec.get('info', {})
        endpoints_by_tag = self._parse_endpoints_by_tag(openapi_spec)
        
        md_content = f"""# {info.get('title', 'API')} Documentation

{info.get('description', '')}

**Version:** {info.get('version', '1.0.0')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Table of Contents

"""
        
        # Generate table of contents
        for tag in endpoints_by_tag.keys():
            md_content += f"- [{tag.title()}](#{tag.lower().replace(' ', '-')})\n"
        
        md_content += "\n---\n\n"
        
        # Generate endpoint documentation
        for tag, endpoints in endpoints_by_tag.items():
            md_content += f"## {tag.title()}\n\n"
            
            for endpoint in endpoints:
                md_content += f"### {endpoint['method'].upper()} {endpoint['path']}\n\n"
                md_content += f"{endpoint.get('summary', endpoint.get('description', 'No description available'))}\n\n"
                
                # Parameters
                if endpoint.get('parameters'):
                    md_content += "**Parameters:**\n\n"
                    md_content += "| Name | Type | Location | Required | Description |\n"
                    md_content += "|------|------|----------|----------|-------------|\n"
                    
                    for param in endpoint['parameters']:
                        param_type = param.get('schema', {}).get('type', 'any')
                        required = '✓' if param.get('required') else ''
                        description = param.get('description', '')
                        md_content += f"| {param['name']} | {param_type} | {param['in']} | {required} | {description} |\n"
                    
                    md_content += "\n"
                
                # Request body
                if endpoint.get('requestBody'):
                    md_content += "**Request Body:**\n\n"
                    md_content += "```json\n"
                    md_content += endpoint.get('request_body_example', '{}')
                    md_content += "\n```\n\n"
                
                # Responses
                if endpoint.get('responses'):
                    md_content += "**Responses:**\n\n"
                    for status_code, response in endpoint['responses'].items():
                        md_content += f"- **{status_code}**: {response.get('description', 'No description')}\n"
                    md_content += "\n"
                
                md_content += "---\n\n"
        
        # Write markdown file
        md_file = self.output_dir / "API.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"✅ Markdown documentation generated: {md_file}")
    
    def _parse_endpoints_by_tag(self, openapi_spec: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Parse endpoints grouped by tags."""
        endpoints_by_tag = {}
        paths = openapi_spec.get('paths', {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    tags = details.get('tags', ['default'])
                    tag = tags[0] if tags else 'default'
                    
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    
                    # Process request body example
                    request_body_example = '{}'
                    if details.get('requestBody'):
                        content = details['requestBody'].get('content', {})
                        json_content = content.get('application/json', {})
                        if json_content.get('schema'):
                            request_body_example = self._generate_example_from_schema(
                                json_content['schema'], openapi_spec.get('components', {}).get('schemas', {})
                            )
                    
                    endpoint = {
                        'method': method,
                        'path': path,
                        'summary': details.get('summary', ''),
                        'description': details.get('description', ''),
                        'parameters': details.get('parameters', []),
                        'requestBody': details.get('requestBody'),
                        'request_body_example': request_body_example,
                        'responses': details.get('responses', {})
                    }
                    
                    endpoints_by_tag[tag].append(endpoint)
        
        return endpoints_by_tag
    
    def _generate_example_from_schema(self, schema: Dict[str, Any], components: Dict[str, Any]) -> str:
        """Generate example JSON from schema."""
        try:
            example = self._create_example_object(schema, components)
            return json.dumps(example, indent=2)
        except Exception:
            return '{}'
    
    def _create_example_object(self, schema: Dict[str, Any], components: Dict[str, Any]) -> Any:
        """Recursively create example object from schema."""
        if '$ref' in schema:
            # Handle component references
            ref_path = schema['$ref'].split('/')[-1]
            if ref_path in components:
                return self._create_example_object(components[ref_path], components)
            return {}
        
        schema_type = schema.get('type', 'object')
        
        if schema_type == 'object':
            properties = schema.get('properties', {})
            example = {}
            for prop_name, prop_schema in properties.items():
                example[prop_name] = self._create_example_object(prop_schema, components)
            return example
        
        elif schema_type == 'array':
            items = schema.get('items', {})
            return [self._create_example_object(items, components)]
        
        elif schema_type == 'string':
            return schema.get('example', 'string')
        
        elif schema_type == 'integer':
            return schema.get('example', 0)
        
        elif schema_type == 'number':
            return schema.get('example', 0.0)
        
        elif schema_type == 'boolean':
            return schema.get('example', True)
        
        else:
            return schema.get('example', None)


async def main():
    parser = argparse.ArgumentParser(description='Generate API documentation')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API server URL')
    parser.add_argument('--output-dir', default='docs', help='Output directory for documentation')
    parser.add_argument('--format', default='html,markdown', help='Output formats (comma-separated)')
    
    args = parser.parse_args()
    
    print("🚀 Generating API documentation...")
    print(f"   API URL: {args.api_url}")
    print(f"   Output: {args.output_dir}")
    print(f"   Formats: {args.format}")
    print()
    
    generator = APIDocumentationGenerator(args.api_url, args.output_dir)
    
    # Fetch OpenAPI specification
    openapi_spec = await generator.fetch_openapi_spec()
    print(f"✅ Fetched OpenAPI spec for {openapi_spec['info']['title']}")
    
    # Generate documentation in requested formats
    formats = [f.strip() for f in args.format.split(',')]
    
    if 'html' in formats:
        generator.generate_html_docs(openapi_spec)
    
    if 'markdown' in formats:
        generator.generate_markdown_docs(openapi_spec)
    
    print("\n🎉 Documentation generation complete!")
    print(f"   Check the {args.output_dir}/ directory for generated files")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())