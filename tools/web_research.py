"""
Web Research/Information tools for agents to read web pages for information and documentation
"""
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse

from tools.code_tools import ToolResult
from tools.web_scraper import WebScraperTools
from agents.timeout_config import TIMEOUT_CONFIG

# Try to import required libraries
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class WebResearchTools:
    """Tools for reading web pages for information and documentation"""
    
    # Common documentation domains
    DOCUMENTATION_DOMAINS = [
        "docs.python.org",
        "pypi.org",
        "flask.palletsprojects.com",
        "fastapi.tiangolo.com",
        "docs.djangoproject.com",
        "developer.mozilla.org",
        "www.w3.org",
        "github.com",
        "stackoverflow.com",
    ]
    
    @staticmethod
    def _extract_text_content(soup) -> str:
        """Extract readable text content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    @staticmethod
    def _extract_code_examples(soup) -> List[str]:
        """Extract code examples from HTML"""
        code_examples = []
        
        # Find code blocks (pre, code tags)
        for pre in soup.find_all(['pre', 'code']):
            code_text = pre.get_text().strip()
            if len(code_text) > 10:  # Only include substantial code
                code_examples.append(code_text)
        
        # Also check for code in divs with class 'code' or 'highlight'
        for div in soup.find_all(['div'], class_=re.compile(r'code|highlight|example', re.I)):
            code_text = div.get_text().strip()
            if len(code_text) > 10:
                code_examples.append(code_text)
        
        return code_examples[:10]  # Limit to 10 examples
    
    @staticmethod
    def _summarize_content(text: str, max_length: int = 1000) -> str:
        """Summarize content to max_length characters"""
        if len(text) <= max_length:
            return text
        
        # Try to summarize intelligently
        sentences = re.split(r'[.!?]\s+', text)
        
        # Take first few sentences that fit
        summary = ""
        for sentence in sentences:
            if len(summary + sentence) < max_length:
                summary += sentence + ". "
            else:
                break
        
        # If still too long, truncate
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary.strip()
    
    @staticmethod
    def read_web_page(
        url: str,
        extract_code: bool = True,
        summarize: bool = False,
        max_summary_length: int = 1000
    ) -> ToolResult:
        """
        Read and summarize web page content for information.
        
        Args:
            url: URL to read
            extract_code: Whether to extract code examples (default: True)
            summarize: Whether to summarize content (default: False)
            max_summary_length: Maximum summary length in characters (default: 1000)
        
        Returns:
            ToolResult with page content and information
        """
        try:
            # Reuse web scraper's scraping functionality
            scrape_result = WebScraperTools.scrape_website(
                url,
                include_css=False,
                include_images=False,
                respect_robots=True
            )
            
            if not scrape_result.success:
                return scrape_result
            
            html_content = scrape_result.result.get("html", "")
            title = scrape_result.result.get("title", "")
            
            if not html_content:
                return ToolResult(
                    success=False,
                    result=None,
                    error="No HTML content retrieved"
                )
            
            # Parse HTML
            if not REQUESTS_AVAILABLE:
                return ToolResult(
                    success=False,
                    result=None,
                    error="BeautifulSoup not available. Install with: pip install beautifulsoup4"
                )
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content
            text_content = WebResearchTools._extract_text_content(soup)
            
            # Extract code examples if requested
            code_examples = []
            if extract_code:
                code_examples = WebResearchTools._summarize_content(
                    '\n\n---\n\n'.join(WebResearchTools._extract_code_examples(soup))
                )
            
            # Summarize if requested
            summary = None
            full_content = text_content
            if summarize:
                summary = WebResearchTools._summarize_content(text_content, max_summary_length)
            else:
                # Limit content to reasonable length
                if len(text_content) > 5000:
                    summary = WebResearchTools._summarize_content(text_content, max_summary_length)
                    full_content = text_content  # Keep full content but provide summary
            
            # Extract key information (headings, paragraphs)
            headings = [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3'])[:10]]
            paragraphs = [p.get_text().strip() for p in soup.find_all('p')[:5]]
            
            return ToolResult(
                success=True,
                result={
                    "url": url,
                    "title": title,
                    "content": text_content[:5000] if not summarize else summary,  # Limit to 5000 chars
                    "summary": summary if summary else WebResearchTools._summarize_content(text_content, max_summary_length),
                    "code_examples": code_examples if code_examples else None,
                    "headings": headings,
                    "key_paragraphs": paragraphs,
                    "content_length": len(text_content)
                },
                metadata={
                    "url": url,
                    "title": title,
                    "has_code": bool(code_examples),
                    "content_length": len(text_content)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error reading web page: {str(e)}"
            )
    
    @staticmethod
    def read_documentation(
        url: str,
        topic: str = None
    ) -> ToolResult:
        """
        Read documentation sites for specific topics.
        
        Args:
            url: Documentation URL
            topic: Specific topic to look for (optional)
        
        Returns:
            ToolResult with documentation content
        """
        try:
            # Read the page
            result = WebResearchTools.read_web_page(
                url,
                extract_code=True,
                summarize=False,
                max_summary_length=2000
            )
            
            if not result.success:
                return result
            
            content = result.result
            
            # If topic specified, try to find relevant sections
            if topic:
                # Search for topic in headings
                relevant_headings = [
                    h for h in content.get("headings", [])
                    if topic.lower() in h.lower()
                ]
                
                # Search in content
                lines = content.get("content", "").split('\n')
                relevant_lines = [
                    line for line in lines
                    if topic.lower() in line.lower()
                ][:10]  # Limit to 10 lines
                
                content["relevant_sections"] = {
                    "headings": relevant_headings,
                    "lines": relevant_lines
                }
            
            # Mark as documentation
            content["is_documentation"] = any(
                domain in url for domain in WebResearchTools.DOCUMENTATION_DOMAINS
            )
            
            return ToolResult(
                success=True,
                result=content,
                metadata={
                    "url": url,
                    "topic": topic,
                    "is_documentation": content.get("is_documentation", False)
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error reading documentation: {str(e)}"
            )
    
    @staticmethod
    def extract_information(
        url: str,
        information_type: str = "general"
    ) -> ToolResult:
        """
        Extract specific information from web page.
        
        Args:
            url: URL to read
            information_type: Type of information to extract
                Options: "general", "code_examples", "api_reference", "version", "installation"
        
        Returns:
            ToolResult with extracted information
        """
        try:
            # Read the page
            result = WebResearchTools.read_web_page(
                url,
                extract_code=True,
                summarize=False
            )
            
            if not result.success:
                return result
            
            content = result.result
            extracted = {
                "url": url,
                "type": information_type
            }
            
            if information_type == "code_examples":
                extracted["code_examples"] = content.get("code_examples", [])
                extracted["summary"] = "Code examples extracted"
            
            elif information_type == "api_reference":
                # Extract API-like information (function signatures, parameters)
                api_info = []
                code_examples = content.get("code_examples", "")
                if code_examples:
                    # Try to extract function/class definitions
                    func_pattern = r'def\s+(\w+)\([^)]*\)'
                    matches = re.findall(func_pattern, code_examples)
                    api_info.extend(matches)
                
                extracted["api_functions"] = api_info[:20]  # Limit to 20
                extracted["summary"] = f"Found {len(api_info)} API functions"
            
            elif information_type == "version":
                # Extract version information
                content_text = content.get("content", "")
                version_patterns = [
                    r'version["\s:]+([0-9]+\.[0-9]+(?:\.[0-9]+)?)',
                    r'v([0-9]+\.[0-9]+(?:\.[0-9]+)?)',
                    r'([0-9]+\.[0-9]+(?:\.[0-9]+)?)\s+\(latest\)',
                ]
                
                versions = []
                for pattern in version_patterns:
                    matches = re.findall(pattern, content_text, re.IGNORECASE)
                    versions.extend(matches)
                
                extracted["version"] = versions[0] if versions else None
                extracted["all_versions"] = list(set(versions))[:5]
                extracted["summary"] = f"Version: {extracted['version']}" if extracted["version"] else "Version not found"
            
            elif information_type == "installation":
                # Extract installation instructions
                content_text = content.get("content", "")
                
                # Look for installation patterns
                install_patterns = [
                    r'pip\s+install[^\n]+',
                    r'npm\s+install[^\n]+',
                    r'pipenv\s+install[^\n]+',
                    r'poetry\s+add[^\n]+',
                ]
                
                install_commands = []
                for pattern in install_patterns:
                    matches = re.findall(pattern, content_text, re.IGNORECASE)
                    install_commands.extend(matches)
                
                extracted["installation_commands"] = list(set(install_commands))[:5]
                extracted["summary"] = f"Found {len(extracted['installation_commands'])} installation commands"
            
            else:  # general
                extracted["summary"] = content.get("summary")
                extracted["headings"] = content.get("headings", [])[:10]
                extracted["key_paragraphs"] = content.get("key_paragraphs", [])[:5]
            
            return ToolResult(
                success=True,
                result=extracted,
                metadata={
                    "url": url,
                    "information_type": information_type,
                    "extracted": True
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error extracting information: {str(e)}"
            )
    
    @staticmethod
    def get_web_summary(
        url: str,
        max_length: int = 500
    ) -> ToolResult:
        """
        Get summary of web page content.
        
        Args:
            url: URL to summarize
            max_length: Maximum summary length (default: 500)
        
        Returns:
            ToolResult with page summary
        """
        try:
            result = WebResearchTools.read_web_page(
                url,
                extract_code=False,
                summarize=True,
                max_summary_length=max_length
            )
            
            if not result.success:
                return result
            
            content = result.result
            
            return ToolResult(
                success=True,
                result={
                    "url": url,
                    "title": content.get("title"),
                    "summary": content.get("summary"),
                    "headings": content.get("headings", [])[:5],
                    "length": len(content.get("summary", ""))
                },
                metadata={
                    "url": url,
                    "summary_length": len(content.get("summary", ""))
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error getting web summary: {str(e)}"
            )
    
    @staticmethod
    def search_web(
        query: str,
        max_results: int = 5
    ) -> ToolResult:
        """
        Search the web (using DuckDuckGo HTML search - no API key needed).
        
        Args:
            query: Search query
            max_results: Maximum number of results (default: 5)
        
        Returns:
            ToolResult with search results
        """
        try:
            if not REQUESTS_AVAILABLE:
                return ToolResult(
                    success=False,
                    result=None,
                    error="requests library not installed. Install with: pip install requests"
                )
            
            # Use DuckDuckGo HTML search (no API key needed)
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            
            # Enforce rate limiting
            WebScraperTools._check_rate_limit()
            
            headers = {
                'User-Agent': WebScraperTools.USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            timeout = min(TIMEOUT_CONFIG.get_code_execution_timeout(), 10)
            response = requests.get(search_url, headers=headers, timeout=timeout, allow_redirects=True)
            
            if response.status_code != 200:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Search failed: HTTP {response.status_code}"
                )
            
            # Parse search results
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # DuckDuckGo result structure
            result_links = soup.find_all('a', class_='result__a', limit=max_results)
            
            for link in result_links:
                url = link.get('href', '')
                title = link.get_text().strip()
                
                if url and title:
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": ""  # Can extract snippet if needed
                    })
            
            # If no results found, try alternative parsing
            if not results:
                # Try finding links in result blocks
                result_blocks = soup.find_all('div', class_='result', limit=max_results)
                for block in result_blocks:
                    link = block.find('a')
                    if link:
                        url = link.get('href', '')
                        title = link.get_text().strip()
                        snippet_elem = block.find('a', class_='result__snippet')
                        snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                        
                        if url and title:
                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": snippet
                            })
            
            return ToolResult(
                success=True,
                result={
                    "query": query,
                    "results": results,
                    "count": len(results)
                },
                metadata={
                    "query": query,
                    "count": len(results)
                }
            )
        
        except requests.exceptions.Timeout:
            return ToolResult(
                success=False,
                result=None,
                error="Search request timed out"
            )
        except requests.exceptions.RequestException as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Search request failed: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error searching web: {str(e)}"
            )

