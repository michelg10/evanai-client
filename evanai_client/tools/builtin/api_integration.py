"""
Anthropic Built-in Tools API Integration

This module provides the integration layer between EvanAI and Anthropic's built-in tools.
It handles:
- Configuring API requests with proper headers and tool definitions
- Processing server-side tool results (web fetch, web search)
- Managing client-side tool interactions (text editor)
"""

from typing import Dict, Any, List, Optional
from .text_editor import TextEditorTool
from .web_fetch import WebFetchTool
from .web_search import WebSearchTool


class BuiltinToolsIntegration:
    """
    Integration layer for Anthropic's built-in tools.
    
    This class manages the configuration and execution of both server-side
    and client-side built-in tools.
    """
    
    # Tool type strings for different models
    TOOL_TYPES = {
        'web_fetch': 'web_fetch_20250910',
        'web_search': 'web_search_20250305',
        'text_editor': {
            'claude-4': 'text_editor_20250728',
            'claude-3-7': 'text_editor_20250124',
            'claude-3-5': 'text_editor_20241022'
        }
    }
    
    # Beta headers required for certain tools
    BETA_HEADERS = {
        'web_fetch': 'web-fetch-2025-09-10',
        'computer_use': 'computer-use-2024-10-22'  # For older Claude 3.5 with text editor
    }
    
    def __init__(self, workspace_dir: Optional[str] = None):
        """
        Initialize the built-in tools integration.
        
        Args:
            workspace_dir: Directory for text editor operations
        """
        # Initialize client-side tool handlers
        self.text_editor = TextEditorTool(workspace_dir)
        self.web_fetch = WebFetchTool()
        self.web_search = WebSearchTool()
        
        # Track enabled tools
        self.enabled_tools = {
            'text_editor': False,
            'web_fetch': False,
            'web_search': False
        }
    
    def get_api_headers(self, tools: List[str]) -> Dict[str, str]:
        """
        Get the required API headers for the enabled tools.
        
        Args:
            tools: List of tool names to enable ('text_editor', 'web_fetch', 'web_search')
            
        Returns:
            Dictionary of headers to add to the API request
        """
        headers = {}
        
        # Add beta header for web fetch if enabled
        if 'web_fetch' in tools:
            headers['anthropic-beta'] = self.BETA_HEADERS['web_fetch']
        
        # Note: Web search doesn't need a beta header (generally available)
        # Text editor doesn't need a header for Claude 4 models
        
        return headers
    
    def get_tools_config(
        self,
        tools: List[str],
        model: str = 'claude-opus-4-1-20250805',
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get the tools configuration for the API request.
        
        Args:
            tools: List of tool names to enable
            model: The model being used (affects text editor type)
            **kwargs: Additional configuration for each tool
            
        Returns:
            List of tool configurations for the API request
        """
        tool_configs = []
        
        if 'web_fetch' in tools:
            config = {
                'type': self.TOOL_TYPES['web_fetch'],
                'name': 'web_fetch',
                'max_uses': 9999,  # Maximum uses - essentially unlimited
                'citations': {'enabled': True},  # Always enable citations
                'max_content_tokens': 500000  # Very high token limit
            }

            # Allow override but default to maximum permissions
            if 'web_fetch_config' in kwargs:
                fetch_config = kwargs['web_fetch_config']
                if 'max_uses' in fetch_config:
                    config['max_uses'] = fetch_config['max_uses']
                if 'allowed_domains' in fetch_config:
                    config['allowed_domains'] = fetch_config['allowed_domains']
                if 'blocked_domains' in fetch_config:
                    config['blocked_domains'] = fetch_config['blocked_domains']
                if 'enable_citations' in fetch_config:
                    config['citations'] = {'enabled': fetch_config['enable_citations']}
                if 'max_content_tokens' in fetch_config:
                    config['max_content_tokens'] = fetch_config['max_content_tokens']
            # No domain restrictions by default - allow ALL domains

            tool_configs.append(config)
            self.enabled_tools['web_fetch'] = True
        
        if 'web_search' in tools:
            config = {
                'type': self.TOOL_TYPES['web_search'],
                'name': 'web_search',
                'max_uses': 9999  # Maximum uses - essentially unlimited
            }

            # Allow override but default to maximum permissions
            if 'web_search_config' in kwargs:
                search_config = kwargs['web_search_config']
                if 'max_uses' in search_config:
                    config['max_uses'] = search_config['max_uses']
                if 'allowed_domains' in search_config:
                    config['allowed_domains'] = search_config['allowed_domains']
                if 'blocked_domains' in search_config:
                    config['blocked_domains'] = search_config['blocked_domains']
                if 'user_location' in search_config:
                    config['user_location'] = search_config['user_location']
            # No domain restrictions by default - allow ALL domains

            tool_configs.append(config)
            self.enabled_tools['web_search'] = True
        
        if 'text_editor' in tools:
            # Determine text editor type based on model
            if 'claude-4' in model or 'claude-opus-4' in model or 'claude-sonnet-4' in model:
                tool_type = self.TOOL_TYPES['text_editor']['claude-4']
            elif 'claude-3-7' in model or 'claude-3.7' in model:
                tool_type = self.TOOL_TYPES['text_editor']['claude-3-7']
            else:
                tool_type = self.TOOL_TYPES['text_editor']['claude-3-5']
            
            config = {
                'type': tool_type,
                'name': 'str_replace_based_edit_tool',
                'max_characters': 10000000  # 10 million characters - essentially unlimited
            }

            # Allow override but default to maximum permissions
            if 'text_editor_config' in kwargs:
                editor_config = kwargs['text_editor_config']
                if 'max_characters' in editor_config:
                    config['max_characters'] = editor_config['max_characters']
            
            tool_configs.append(config)
            self.enabled_tools['text_editor'] = True
        
        return tool_configs
    
    def handle_tool_use(
        self,
        tool_use_block: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle a tool_use block from Claude's response.
        
        This is primarily for client-side tools like text_editor.
        Server-side tools (web_fetch, web_search) are handled automatically.
        
        Args:
            tool_use_block: The tool_use content block from Claude
            
        Returns:
            Tool result to send back in the conversation
        """
        tool_name = tool_use_block.get('name')
        tool_input = tool_use_block.get('input', {})
        tool_use_id = tool_use_block.get('id')
        
        if tool_name == 'str_replace_based_edit_tool':
            # Handle text editor commands
            result = self.text_editor.execute(tool_input)
            
            # Format as tool_result for the API
            return {
                'type': 'tool_result',
                'tool_use_id': tool_use_id,
                'content': result
            }
        
        # Server-side tools shouldn't reach here
        return {
            'type': 'tool_result',
            'tool_use_id': tool_use_id,
            'content': {
                'success': False,
                'error': f"Unknown tool: {tool_name}"
            }
        }
    
    def process_server_tool_result(
        self,
        tool_result_block: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a server tool result from Claude's response.
        
        This is for server-side tools like web_fetch and web_search.
        
        Args:
            tool_result_block: The tool result block from Claude's response
            
        Returns:
            Processed result for application use
        """
        result_type = tool_result_block.get('type')
        
        if result_type == 'web_fetch_tool_result':
            return self.web_fetch.process_result(tool_result_block)
        
        elif result_type == 'web_search_tool_result':
            return self.web_search.process_result(tool_result_block)
        
        return {
            'success': False,
            'error': f"Unknown tool result type: {result_type}"
        }
    
    def create_api_request(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        tools: List[str],
        max_tokens: int = 4096,
        **tool_configs
    ) -> Dict[str, Any]:
        """
        Create a complete API request with built-in tools configured.
        
        Args:
            model: The model to use
            messages: The conversation messages
            tools: List of built-in tools to enable
            max_tokens: Maximum tokens for the response
            **tool_configs: Configuration for each tool (e.g., web_fetch_config={})
            
        Returns:
            Complete API request body
        """
        request = {
            'model': model,
            'messages': messages,
            'max_tokens': max_tokens
        }
        
        # Add tools configuration if any tools are enabled
        if tools:
            request['tools'] = self.get_tools_config(tools, model, **tool_configs)
        
        return request
    
    def extract_citations(self, response_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract all citations from a response.
        
        Args:
            response_content: The content array from Claude's response
            
        Returns:
            List of extracted citations
        """
        all_citations = []
        
        for block in response_content:
            if block.get('type') == 'text' and 'citations' in block:
                # Handle web search or web fetch citations
                citations = block.get('citations', [])
                
                for citation in citations:
                    if citation.get('type') == 'web_search_result_location':
                        # Web search citation
                        all_citations.append(self.web_search.format_citation_for_display(citation))
                    elif citation.get('type') == 'char_location':
                        # Web fetch citation
                        all_citations.append({
                            'document_title': citation.get('document_title'),
                            'cited_text': citation.get('cited_text'),
                            'char_range': [citation.get('start_char_index'), citation.get('end_char_index')]
                        })
        
        return all_citations
