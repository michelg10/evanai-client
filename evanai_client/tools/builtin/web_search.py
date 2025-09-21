"""
Web Search Tool - Anthropic Built-in Tool Wrapper

This module provides handling for Anthropic's built-in web search tool.
It processes the results that Claude returns through the Messages API.

The tool supports:
- Real-time web search with automatic citations
- Domain filtering (allowed/blocked domains)
- Localized search results
- Multi-turn conversations with encrypted content preservation

Based on Anthropic's web_search_20250305 documentation.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class WebSearchTool:
    """
    Handler for Anthropic's web search tool responses.

    This class processes the responses that come back when Claude uses
    the web_search_20250305 tool.
    """

    def __init__(self):
        """
        Initialize the web search tool handler.
        """
        # Store search results for multi-turn conversations
        self.search_history: List[Dict[str, Any]] = []
        self.encrypted_content_cache: Dict[str, str] = {}

    def process_result(self, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a web search tool result from Claude.

        Args:
            tool_result: The web_search_tool_result from Claude's response

        Returns:
            Processed result dictionary
        """
        if not isinstance(tool_result, dict):
            return self._error("Invalid tool result format")

        result_type = tool_result.get("type")
        if result_type != "web_search_tool_result":
            return self._error(f"Unexpected result type: {result_type}")

        content = tool_result.get("content")

        # Check for errors
        if isinstance(content, dict) and content.get("type") == "web_search_tool_result_error":
            error_code = content.get("error_code", "unknown")
            return self._handle_error(error_code)

        # Process successful search results
        if isinstance(content, list):
            return self._process_search_results(content)

        return self._error(f"Unexpected content format")

    def _process_search_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process successful web search results.

        Args:
            results: List of web_search_result items

        Returns:
            Processed results dictionary
        """
        processed_results = []

        for result in results:
            if result.get("type") != "web_search_result":
                continue

            url = result.get("url")
            title = result.get("title")
            encrypted_content = result.get("encrypted_content")
            page_age = result.get("page_age")

            # Store encrypted content for multi-turn conversations
            if url and encrypted_content:
                self.encrypted_content_cache[url] = encrypted_content

            processed_results.append({
                "url": url,
                "title": title,
                "page_age": page_age,
                "has_encrypted_content": bool(encrypted_content)
            })

        # Add to history
        search_record = {
            "timestamp": datetime.now().isoformat(),
            "results": processed_results,
            "result_count": len(processed_results)
        }
        self.search_history.append(search_record)

        return {
            "success": True,
            "results": processed_results,
            "result_count": len(processed_results)
        }

    def _handle_error(self, error_code: str) -> Dict[str, Any]:
        """
        Handle web search tool errors.

        Args:
            error_code: The error code from the API

        Returns:
            Error result dictionary
        """
        error_messages = {
            "too_many_requests": "Rate limit exceeded",
            "invalid_input": "Invalid search query parameter",
            "max_uses_exceeded": "Maximum web search tool uses exceeded",
            "query_too_long": "Query exceeds maximum length",
            "unavailable": "An internal error occurred"
        }

        return {
            "success": False,
            "error": error_messages.get(error_code, f"Unknown error: {error_code}"),
            "error_code": error_code
        }

    def get_tool_config(
        self,
        max_uses: Optional[int] = None,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None,
        user_location: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate the tool configuration for the API request.

        Args:
            max_uses: Maximum number of searches per request
            allowed_domains: Whitelist of domains to include in results
            blocked_domains: Blacklist of domains to exclude from results
            user_location: Location info for localized search

        Returns:
            Tool configuration dictionary
        """
        config = {
            "type": "web_search_20250305",
            "name": "web_search"
        }

        if max_uses is not None:
            config["max_uses"] = max_uses

        if allowed_domains:
            config["allowed_domains"] = allowed_domains
        elif blocked_domains:  # Can't use both
            config["blocked_domains"] = blocked_domains

        if user_location:
            # Validate required location fields
            if all(k in user_location for k in ["city", "region", "country", "timezone"]):
                config["user_location"] = {
                    "type": "approximate",
                    "city": user_location["city"],
                    "region": user_location["region"],
                    "country": user_location["country"],
                    "timezone": user_location["timezone"]
                }

        return config

    def extract_citations(self, text_block: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract citations from a text block.

        Args:
            text_block: A text block from Claude's response

        Returns:
            List of citation dictionaries
        """
        citations = text_block.get("citations", [])
        processed = []

        for citation in citations:
            if citation.get("type") == "web_search_result_location":
                processed.append({
                    "url": citation.get("url"),
                    "title": citation.get("title"),
                    "cited_text": citation.get("cited_text"),
                    "encrypted_index": citation.get("encrypted_index")
                })

        return processed

    def format_citation_for_display(self, citation: Dict[str, Any]) -> str:
        """
        Format a citation for user-friendly display.

        Args:
            citation: Citation dictionary

        Returns:
            Formatted citation string
        """
        title = citation.get("title", "Untitled")
        url = citation.get("url", "")
        cited_text = citation.get("cited_text", "")

        if cited_text:
            return f'[{title}]({url}): "{cited_text[:150]}..."'
        else:
            return f'[{title}]({url})'

    def get_encrypted_content(self, url: str) -> Optional[str]:
        """
        Get encrypted content for a URL (for multi-turn conversations).

        Args:
            url: The URL to get encrypted content for

        Returns:
            Encrypted content string or None
        """
        return self.encrypted_content_cache.get(url)

    def get_search_history(self) -> List[Dict[str, Any]]:
        """
        Get the search history.

        Returns:
            List of search records
        """
        return self.search_history.copy()

    def clear_history(self):
        """
        Clear search history and encrypted content cache.
        """
        self.search_history.clear()
        self.encrypted_content_cache.clear()

    def _error(self, message: str) -> Dict[str, Any]:
        """
        Return an error response.

        Args:
            message: Error message

        Returns:
            Error dictionary
        """
        return {
            "success": False,
            "error": message
        }
