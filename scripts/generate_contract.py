#!/usr/bin/env python3
"""
API Contract Generator

Generates TypeScript types and API client from FastAPI OpenAPI specification.
Creates type-safe interfaces for frontend applications.

Usage:
    python scripts/generate_contract.py [--output-file api-contract.ts] [--client-name ApiClient]
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Set
import argparse
from datetime import datetime

try:
    import httpx
except ImportError:
    print("Missing required dependency: httpx")
    print("Install with: pip install httpx")
    sys.exit(1)

# Add app to Python path
sys.path.append(str(Path(__file__).parent.parent))


class TypeScriptContractGenerator:
    """Generates TypeScript types and API client from OpenAPI specification."""
    
    def __init__(self, api_url: str = "http://localhost:8000", output_file: str = "api-contract.ts"):
        self.api_url = api_url.rstrip('/')
        self.output_file = Path(output_file)
        self.generated_types: Set[str] = set()
        
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
    
    def generate_contract(self, openapi_spec: Dict[str, Any], client_name: str = "ApiClient") -> None:
        """Generate complete TypeScript contract file."""
        info = openapi_spec.get('info', {})
        components = openapi_spec.get('components', {}).get('schemas', {})
        paths = openapi_spec.get('paths', {})
        
        contract_content = f"""/**
 * {info.get('title', 'API')} TypeScript Contract
 * 
 * Generated automatically from OpenAPI specification
 * Version: {info.get('version', '1.0.0')}
 * Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * 
 * 🚨 DO NOT EDIT MANUALLY - This file is auto-generated
 */

// Base types
type ApiResponse<T> = {{
  data?: T;
  error?: string;
  message?: string;
  status: number;
}};

type PaginatedResponse<T> = {{
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}};

type RequestConfig = {{
  headers?: Record<string, string>;
  params?: Record<string, any>;
}};

// Generated Types
"""
        
        # Generate component types
        contract_content += self._generate_component_types(components)
        
        # Generate API methods
        contract_content += f"\n// API Client\nclass {client_name} {{\n"
        contract_content += "  private baseURL: string;\n"
        contract_content += "  private defaultHeaders: Record<string, string>;\n\n"
        
        contract_content += f"  constructor(baseURL: string = '{self.api_url}', defaultHeaders: Record<string, string> = {{}}) {{\n"
        contract_content += "    this.baseURL = baseURL.replace(/\/$/, '');\n"
        contract_content += "    this.defaultHeaders = { 'Content-Type': 'application/json', ...defaultHeaders };\n"
        contract_content += "  }\n\n"
        
        # Helper methods
        contract_content += self._generate_helper_methods()
        
        # API endpoint methods
        contract_content += self._generate_api_methods(paths, components)
        
        contract_content += "}\n\n"
        
        # Export default instance
        contract_content += f"// Default API client instance\n"
        contract_content += f"export const api = new {client_name}();\n"
        contract_content += f"export default api;\n"
        contract_content += f"export {{ {client_name} }};\n"
        
        # Write contract file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(contract_content)
        
        print(f"✅ TypeScript contract generated: {self.output_file}")
    
    def _generate_component_types(self, components: Dict[str, Any]) -> str:
        """Generate TypeScript types from OpenAPI components."""
        types_content = ""
        
        for type_name, schema in components.items():
            if type_name not in self.generated_types:
                types_content += self._generate_type_definition(type_name, schema, components)
                types_content += "\n\n"
                self.generated_types.add(type_name)
        
        return types_content
    
    def _generate_type_definition(self, type_name: str, schema: Dict[str, Any], components: Dict[str, Any]) -> str:
        """Generate a single TypeScript type definition."""
        if schema.get('type') == 'object' or 'properties' in schema:
            return self._generate_interface(type_name, schema, components)
        elif schema.get('enum'):
            return self._generate_enum(type_name, schema)
        else:
            return f"export type {type_name} = {self._convert_type(schema, components)};"
    
    def _generate_interface(self, type_name: str, schema: Dict[str, Any], components: Dict[str, Any]) -> str:
        """Generate TypeScript interface."""
        properties = schema.get('properties', {})
        required = set(schema.get('required', []))
        
        interface_content = f"export interface {type_name} {{\n"
        
        for prop_name, prop_schema in properties.items():
            optional = "" if prop_name in required else "?"
            prop_type = self._convert_type(prop_schema, components)
            description = prop_schema.get('description', '')
            
            if description:
                interface_content += f"  /** {description} */\n"
            
            interface_content += f"  {prop_name}{optional}: {prop_type};\n"
        
        interface_content += "}"
        return interface_content
    
    def _generate_enum(self, type_name: str, schema: Dict[str, Any]) -> str:
        """Generate TypeScript enum."""
        enum_values = schema.get('enum', [])
        
        if all(isinstance(v, str) for v in enum_values):
            enum_content = f"export enum {type_name} {{\n"
            for value in enum_values:
                enum_key = value.upper().replace(' ', '_').replace('-', '_')
                enum_content += f"  {enum_key} = '{value}',\n"
            enum_content += "}"
        else:
            # Use union type for mixed types
            union_values = ' | '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in enum_values])
            enum_content = f"export type {type_name} = {union_values};"
        
        return enum_content
    
    def _convert_type(self, schema: Dict[str, Any], components: Dict[str, Any]) -> str:
        """Convert OpenAPI type to TypeScript type."""
        if '$ref' in schema:
            # Handle component references
            ref_path = schema['$ref'].split('/')[-1]
            return ref_path
        
        schema_type = schema.get('type', 'any')
        
        if schema_type == 'string':
            if schema.get('enum'):
                return ' | '.join([f"'{v}'" for v in schema['enum']])
            return 'string'
        
        elif schema_type == 'integer' or schema_type == 'number':
            return 'number'
        
        elif schema_type == 'boolean':
            return 'boolean'
        
        elif schema_type == 'array':
            items = schema.get('items', {})
            item_type = self._convert_type(items, components)
            return f"{item_type}[]"
        
        elif schema_type == 'object':
            if 'properties' in schema:
                # Generate inline interface
                properties = schema['properties']
                required = set(schema.get('required', []))
                props = []
                
                for prop_name, prop_schema in properties.items():
                    optional = "" if prop_name in required else "?"
                    prop_type = self._convert_type(prop_schema, components)
                    props.append(f"{prop_name}{optional}: {prop_type}")
                
                return "{ " + "; ".join(props) + " }"
            else:
                return 'Record<string, any>'
        
        else:
            return 'any'
    
    def _generate_helper_methods(self) -> str:
        """Generate helper methods for the API client."""
        return """  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
    endpoint: string,
    data?: any,
    config?: RequestConfig
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const headers = { ...this.defaultHeaders, ...config?.headers };
    
    try {
      const options: RequestInit = {
        method,
        headers,
        ...config,
      };
      
      if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
      }
      
      if (method === 'GET' && config?.params) {
        const searchParams = new URLSearchParams(config.params);
        url += `?${searchParams.toString()}`;
      }
      
      const response = await fetch(url, options);
      const responseData = await response.json().catch(() => ({}));
      
      return {
        data: response.ok ? responseData : undefined,
        error: response.ok ? undefined : responseData.message || 'Request failed',
        message: responseData.message,
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  }

  setDefaultHeader(key: string, value: string): void {
    this.defaultHeaders[key] = value;
  }

  removeDefaultHeader(key: string): void {
    delete this.defaultHeaders[key];
  }

  setAuthToken(token: string): void {
    this.setDefaultHeader('Authorization', `Bearer ${token}`);
  }

"""
    
    def _generate_api_methods(self, paths: Dict[str, Any], components: Dict[str, Any]) -> str:
        """Generate API endpoint methods."""
        methods_content = ""
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    methods_content += self._generate_api_method(path, method, details, components)
                    methods_content += "\n\n"
        
        return methods_content
    
    def _generate_api_method(self, path: str, method: str, details: Dict[str, Any], components: Dict[str, Any]) -> str:
        """Generate a single API method."""
        operation_id = details.get('operationId', '')
        summary = details.get('summary', '')
        description = details.get('description', '')
        
        # Generate method name
        if operation_id:
            method_name = self._camel_case(operation_id)
        else:
            # Generate from path and method
            path_parts = [part for part in path.split('/') if part and not part.startswith('{')]
            method_name = f"{method.lower()}{''.join([self._pascal_case(part) for part in path_parts])}"
        
        # Analyze parameters
        parameters = details.get('parameters', [])
        path_params = [p for p in parameters if p.get('in') == 'path']
        query_params = [p for p in parameters if p.get('in') == 'query']
        
        # Analyze request body
        request_body = details.get('requestBody')
        request_type = None
        if request_body:
            content = request_body.get('content', {})
            json_content = content.get('application/json', {})
            if json_content.get('schema'):
                request_type = self._convert_type(json_content['schema'], components)
        
        # Analyze response
        responses = details.get('responses', {})
        success_response = responses.get('200') or responses.get('201') or responses.get('204')
        response_type = 'any'
        
        if success_response:
            content = success_response.get('content', {})
            json_content = content.get('application/json', {})
            if json_content.get('schema'):
                response_type = self._convert_type(json_content['schema'], components)
        
        # Build method signature
        params = []
        
        # Add path parameters
        for param in path_params:
            param_type = self._convert_type(param.get('schema', {}), components)
            params.append(f"{param['name']}: {param_type}")
        
        # Add request body parameter
        if request_type:
            params.append(f"data: {request_type}")
        
        # Add query parameters as optional object
        if query_params:
            query_props = []
            for param in query_params:
                param_type = self._convert_type(param.get('schema', {}), components)
                optional = "?" if not param.get('required') else ""
                query_props.append(f"{param['name']}{optional}: {param_type}")
            
            params.append(f"params?: {{ {'; '.join(query_props)} }}")
        
        # Add config parameter
        params.append("config?: RequestConfig")
        
        # Generate method documentation
        doc_lines = []
        if summary:
            doc_lines.append(f"   * {summary}")
        if description and description != summary:
            doc_lines.append(f"   * {description}")
        if path_params:
            doc_lines.append("   * @param path parameters")
        if request_type:
            doc_lines.append("   * @param data request body")
        if query_params:
            doc_lines.append("   * @param params query parameters")
        
        method_content = ""
        if doc_lines:
            method_content += "  /**\n"
            method_content += "\n".join(doc_lines)
            method_content += "\n   */\n"
        
        # Generate method
        params_str = ", ".join(params) if params else "config?: RequestConfig"
        method_content += f"  async {method_name}({params_str}): Promise<ApiResponse<{response_type}>> {{\n"
        
        # Build endpoint URL with path parameters
        endpoint_url = path
        for param in path_params:
            endpoint_url = endpoint_url.replace(f"{{{param['name']}}}", f"${{{param['name']}}}")
        
        method_content += f"    const endpoint = `{endpoint_url}`;\n"
        
        # Prepare request config
        if query_params:
            method_content += "    const requestConfig = { ...config, params };\n"
        else:
            method_content += "    const requestConfig = config;\n"
        
        # Make request
        if request_type:
            method_content += f"    return this.request<{response_type}>('{method.upper()}', endpoint, data, requestConfig);\n"
        else:
            method_content += f"    return this.request<{response_type}>('{method.upper()}', endpoint, undefined, requestConfig);\n"
        
        method_content += "  }"
        
        return method_content
    
    def _camel_case(self, text: str) -> str:
        """Convert text to camelCase."""
        words = text.replace('-', '_').split('_')
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    
    def _pascal_case(self, text: str) -> str:
        """Convert text to PascalCase."""
        return ''.join(word.capitalize() for word in text.replace('-', '_').split('_'))


async def main():
    parser = argparse.ArgumentParser(description='Generate TypeScript API contract')
    parser.add_argument('--api-url', default='http://localhost:8000', help='API server URL')
    parser.add_argument('--output-file', default='api-contract.ts', help='Output TypeScript file')
    parser.add_argument('--client-name', default='ApiClient', help='Generated client class name')
    
    args = parser.parse_args()
    
    print("🚀 Generating TypeScript API contract...")
    print(f"   API URL: {args.api_url}")
    print(f"   Output: {args.output_file}")
    print(f"   Client: {args.client_name}")
    print()
    
    generator = TypeScriptContractGenerator(args.api_url, args.output_file)
    
    # Fetch OpenAPI specification
    openapi_spec = await generator.fetch_openapi_spec()
    print(f"✅ Fetched OpenAPI spec for {openapi_spec['info']['title']}")
    
    # Generate TypeScript contract
    generator.generate_contract(openapi_spec, args.client_name)
    
    print("\n🎉 TypeScript contract generation complete!")
    print(f"   Import in your frontend: import {{ api }} from './{args.output_file.replace('.ts', '')}';")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())