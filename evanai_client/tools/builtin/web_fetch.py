"""
Web Fetch Tool - Anthropic Built-in Tool Wrapper

This module provides handling for Anthropic's built-in web fetch tool.
It processes the results that Claude returns through the Messages API.

The tool supports:
- Fetching full content from web pages and PDFs
- Domain filtering (allowed/blocked domains)
- Citations for fetched content
- Content token limits

Based on Anthropic's web_fetch_20250910 documentation.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import base64


class WebFetchTool:
    """
    Handler for Anthropic's web fetch tool responses.

    This class processes the responses that come back when Claude uses
    the web_fetch_20250910 tool.
    """

    def __init__(self):
        """
        Initialize the web fetch tool handler.
        """
        self.fetch_cache: Dict[str, Dict[str, Any]] = {}

    def process_result(self, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a web fetch tool result from Claude.

        Args:
            tool_result: The web_fetch_tool_result from Claude's response

        Returns:
            Processed result dictionary
        """
        if not isinstance(tool_result, dict):
            return self._error("Invalid tool result format")

        result_type = tool_result.get("type")
        if result_type != "web_fetch_tool_result":
            return self._error(f"Unexpected result type: {result_type}")

        content = tool_result.get("content", {})

        # Check for errors
        if content.get("type") == "web_fetch_tool_error":
            error_code = content.get("error_code", "unknown")
            return self._handle_error(error_code)

        # Process successful fetch
        if content.get("type") == "web_fetch_result":
            return self._process_fetch_result(content)

        return self._error(f"Unknown content type: {content.get('type')}")

    def _process_fetch_result(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a successful web fetch result.

        Args:
            content: The web_fetch_result content

        Returns:
            Processed result with extracted content
        """
        url = content.get("url")
        document = content.get("content", {})
        retrieved_at = content.get("retrieved_at")

        if not url:
            return self._error("Missing URL in fetch result")

        # Cache the result
        self.fetch_cache[url] = {
            "content": document,
            "retrieved_at": retrieved_at,
            "cached_at": datetime.now().isoformat()
        }

        # Extract the actual content
        source = document.get("source", {})
        source_type = source.get("type")
        media_type = source.get("media_type")
        data = source.get("data")

        result = {
            "success": True,
            "url": url,
            "retrieved_at": retrieved_at,
            "media_type": media_type,
            "title": document.get("title"),
            "citations_enabled": document.get("citations", {}).get("enabled", False)
        }

        if source_type == "text":
            # Text content (HTML converted to markdown)
            result["content"] = data
            result["content_type"] = "text"
        elif source_type == "base64":
            # Binary content (e.g., PDFs)
            result["content"] = data  # Keep as base64
            result["content_type"] = "base64"
            result["decoded_size"] = len(base64.b64decode(data)) if data else 0
        else:
            result["content_type"] = "unknown"
            result["raw_data"] = data

        return result

    def _handle_error(self, error_code: str) -> Dict[str, Any]:
        """
        Handle web fetch tool errors.

        Args:
            error_code: The error code from the API

        Returns:
            Error result dictionary
        """
        error_messages = {
            "invalid_input": "Invalid URL format",
            "url_too_long": "URL exceeds maximum length (250 characters)",
            "url_not_allowed": "URL blocked by domain filtering rules",
            "url_not_accessible": "Failed to fetch content (HTTP error)",
            "too_many_requests": "Rate limit exceeded",
            "unsupported_content_type": "Content type not supported (only text and PDF)",
            "max_uses_exceeded": "Maximum web fetch tool uses exceeded",
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
        enable_citations: bool = False,
        max_content_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate the tool configuration for the API request.

        Args:
            max_uses: Maximum number of fetches per request
            allowed_domains: Whitelist of domains to fetch from
            blocked_domains: Blacklist of domains to block
            enable_citations: Whether to enable citations
            max_content_tokens: Maximum content length in tokens

        Returns:
            Tool configuration dictionary
        """
        config = {
            "type": "web_fetch_20250910",
            "name": "web_fetch"
        }

        if max_uses is not None:
            config["max_uses"] = max_uses

        if allowed_domains:
            config["allowed_domains"] = allowed_domains
        elif blocked_domains:  # Can't use both
            config["blocked_domains"] = blocked_domains

        if enable_citations:
            config["citations"] = {"enabled": True}

        if max_content_tokens is not None:
            config["max_content_tokens"] = max_content_tokens

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
            if citation.get("type") == "char_location":
                processed.append({
                    "document_index": citation.get("document_index"),
                    "document_title": citation.get("document_title"),
                    "start_char": citation.get("start_char_index"),
                    "end_char": citation.get("end_char_index"),
                    "cited_text": citation.get("cited_text")
                })

        return processed

    def get_cached_content(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get cached content for a URL if available.

        Args:
            url: The URL to check

        Returns:
            Cached content or None
        """
        return self.fetch_cache.get(url)

    def clear_cache(self):
        """
        Clear the fetch cache.
        """
        self.fetch_cache.clear()

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
