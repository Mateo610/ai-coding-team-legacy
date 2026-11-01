"""
Consolidated Web Research Tools
Replaces: read_web_page, read_documentation, download_assets, extract_information, get_web_summary, scrape_website, extract_design_elements, extract_structure, analyze_design
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.code_tools import ToolResult
from tools.web_research import WebResearchTools
from tools.web_scraper import WebScraperTools


class WebTools:
    """Consolidated web research and scraping tools with mode-based operations"""
    
    @staticmethod
    def web_get(url: str, mode: str = "read", **kwargs) -> ToolResult:
        """
        Fetch web content or assets.
        
        Replaces: read_web_page, read_documentation, download_assets
        
        Args:
            url: URL to fetch
            mode: Operation mode:
                - "read" (default): Read web page content
                - "documentation": Read documentation page
                - "assets": Download assets
            **kwargs: Additional arguments for specific modes:
                - read: extract_code (optional, default: True), summarize (optional, default: False)
                - documentation: section (optional)
                - assets: asset_types (optional, default: ["css", "images"])
        
        Returns:
            ToolResult with web content based on mode
        
        Examples:
            web_get("https://example.com", mode="read")  # Read web page
            web_get("https://docs.python.org/3/library/os.html", mode="documentation")  # Read docs
            web_get("https://example.com", mode="assets")  # Download assets
        """
        try:
            if mode == "read":
                # Use WebResearchTools.read_web_page
                extract_code = kwargs.get("extract_code", True)
                summarize = kwargs.get("summarize", False)
                result = WebResearchTools.read_web_page(url, extract_code=extract_code, summarize=summarize)
                return result
            elif mode == "documentation":
                # Use WebResearchTools.read_documentation
                section = kwargs.get("section")
                result = WebResearchTools.read_documentation(url, section=section)
                return result
            elif mode == "assets":
                # Use WebScraperTools.download_assets
                asset_types = kwargs.get("asset_types", ["css", "images"])
                result = WebScraperTools.download_assets(url, asset_types=asset_types)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'read', 'documentation', 'assets'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in web_get with mode '{mode}': {str(e)}"
            )
    
    @staticmethod
    def web_analyze(url: str, mode: str = "extract", **kwargs) -> ToolResult:
        """
        Analyze web pages for info or design patterns.
        
        Replaces: extract_information, get_web_summary, scrape_website, extract_design_elements, extract_structure, analyze_design
        
        Args:
            url: URL to analyze
            mode: Operation mode:
                - "extract" (default): Extract specific information
                - "summary": Get web page summary
                - "scrape": Scrape website
                - "design_elements": Extract design elements
                - "structure": Extract HTML structure
                - "design": Analyze design patterns
            **kwargs: Additional arguments for specific modes:
                - extract: info_type (required)
                - summary: max_length (optional, default: 1000)
                - scrape: include_css (optional, default: True), include_images (optional, default: False)
                - design_elements: element_types (optional, default: ["colors", "fonts", "layout"])
        
        Returns:
            ToolResult with analysis results based on mode
        
        Examples:
            web_analyze("https://example.com", mode="extract", info_type="version")  # Extract info
            web_analyze("https://example.com", mode="summary")  # Get summary
            web_analyze("https://example.com", mode="scrape")  # Scrape website
            web_analyze("https://example.com", mode="design_elements")  # Extract design elements
            web_analyze("https://example.com", mode="structure")  # Extract structure
            web_analyze("https://example.com", mode="design")  # Analyze design
        """
        try:
            if mode == "extract":
                # Use WebResearchTools.extract_information
                info_type = kwargs.get("info_type")
                if not info_type:
                    return ToolResult(
                        success=False,
                        result=None,
                        error="info_type required for mode='extract'"
                    )
                result = WebResearchTools.extract_information(url, info_type=info_type)
                return result
            elif mode == "summary":
                # Use WebResearchTools.get_web_summary
                max_length = kwargs.get("max_length", 1000)
                result = WebResearchTools.get_web_summary(url, max_length=max_length)
                return result
            elif mode == "scrape":
                # Use WebScraperTools.scrape_website
                include_css = kwargs.get("include_css", True)
                include_images = kwargs.get("include_images", False)
                result = WebScraperTools.scrape_website(url, include_css=include_css, include_images=include_images)
                return result
            elif mode == "design_elements":
                # Use WebScraperTools.extract_design_elements
                element_types = kwargs.get("element_types", ["colors", "fonts", "layout"])
                result = WebScraperTools.extract_design_elements(url, element_types=element_types)
                return result
            elif mode == "structure":
                # Use WebScraperTools.extract_structure
                result = WebScraperTools.extract_structure(url)
                return result
            elif mode == "design":
                # Use WebScraperTools.analyze_design
                result = WebScraperTools.analyze_design(url)
                return result
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Invalid mode: {mode}. Supported modes: 'extract', 'summary', 'scrape', 'design_elements', 'structure', 'design'"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error in web_analyze with mode '{mode}': {str(e)}"
            )

