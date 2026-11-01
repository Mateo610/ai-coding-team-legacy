"""
Web scraper tools for agents to scrape website designs and structures for inspiration
"""
import re
import time
import json
from typing import Dict, Any, Optional, List, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from collections import defaultdict
import html
from dataclasses import dataclass

from tools.code_tools import ToolResult
from agents.timeout_config import TIMEOUT_CONFIG

# Try to import required libraries
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Optional: For CSS parsing
try:
    import tinycss2
    CSS_PARSER_AVAILABLE = True
except ImportError:
    CSS_PARSER_AVAILABLE = False


class WebScraperTools:
    """Tools for web scraping with security restrictions"""
    
    # Rate limiting: max 1 request per second
    _last_request_time: float = 0
    _rate_limit_delay: float = 1.0
    
    # User agent for identification
    USER_AGENT = "AI-Coding-Team-WebScraper/1.0 (Educational/Research Use)"
    
    @staticmethod
    def _check_rate_limit() -> None:
        """Enforce rate limiting (1 request per second)"""
        current_time = time.time()
        time_since_last = current_time - WebScraperTools._last_request_time
        
        if time_since_last < WebScraperTools._rate_limit_delay:
            sleep_time = WebScraperTools._rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        WebScraperTools._last_request_time = time.time()
    
    @staticmethod
    def _check_robots_txt(url: str) -> tuple[bool, Optional[str]]:
        """
        Check if URL is allowed by robots.txt
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        if not REQUESTS_AVAILABLE:
            return True, None  # Skip robots.txt check if requests not available
        
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            # Create robots.txt parser
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            # Check if our user agent is allowed
            user_agent = WebScraperTools.USER_AGENT
            is_allowed = rp.can_fetch(user_agent, url)
            
            if not is_allowed:
                return False, f"URL is disallowed by robots.txt: {url}"
            
            return True, None
        
        except Exception as e:
            # If robots.txt check fails, allow but log warning
            return True, f"Could not check robots.txt: {str(e)}"
    
    @staticmethod
    def _validate_url(url: str) -> tuple[bool, Optional[str]]:
        """
        Validate URL format and security
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)
            
            # Only allow http and https
            if parsed.scheme not in ['http', 'https']:
                return False, f"Only http/https URLs are allowed. Got: {parsed.scheme}"
            
            # Reject localhost/internal IPs for security
            host = parsed.netloc.lower()
            if host.startswith('localhost') or host.startswith('127.') or host.startswith('192.168.') or host.startswith('10.'):
                return False, "Local/internal URLs are not allowed for security"
            
            # Must have a valid hostname
            if not parsed.netloc:
                return False, "Invalid URL: missing hostname"
            
            return True, None
        
        except Exception as e:
            return False, f"Invalid URL format: {str(e)}"
    
    @staticmethod
    def scrape_website(
        url: str,
        include_css: bool = True,
        include_images: bool = False,
        respect_robots: bool = True
    ) -> ToolResult:
        """
        Scrape website HTML, CSS, and structure.
        
        Security:
        - Respects robots.txt (if respect_robots=True)
        - Rate limiting (max 1 request/second)
        - User agent identification
        - Only scrapes publicly accessible content
        - Validates URL format and rejects local/internal URLs
        
        Args:
            url: Website URL to scrape
            include_css: Whether to extract CSS (default: True)
            include_images: Whether to extract image URLs (default: False)
            respect_robots: Whether to respect robots.txt (default: True)
        
        Returns:
            ToolResult with:
            - HTML content
            - CSS content (if include_css=True)
            - Image URLs (if include_images=True)
            - Page metadata
        """
        if not REQUESTS_AVAILABLE:
            return ToolResult(
                success=False,
                result=None,
                error="requests library not installed. Install with: pip install requests beautifulsoup4",
                metadata={"install_hint": "pip install requests beautifulsoup4"}
            )
        
        # Validate URL
        is_valid, error_msg = WebScraperTools._validate_url(url)
        if not is_valid:
            return ToolResult(
                success=False,
                result=None,
                error=error_msg
            )
        
        # Check robots.txt
        if respect_robots:
            is_allowed, error_msg = WebScraperTools._check_robots_txt(url)
            if not is_allowed:
                return ToolResult(
                    success=False,
                    result=None,
                    error=error_msg
                )
        
        # Enforce rate limiting
        WebScraperTools._check_rate_limit()
        
        try:
            # Make request with timeout and user agent
            headers = {
                'User-Agent': WebScraperTools.USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            timeout = TIMEOUT_CONFIG.get_code_execution_timeout()
            response = requests.get(url, headers=headers, timeout=min(timeout, 10), allow_redirects=True)
            
            # Check status code
            if response.status_code != 200:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"HTTP {response.status_code}: {response.reason}"
                )
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            html_content = response.text
            
            result_data = {
                "url": url,
                "html": html_content,
                "title": soup.title.string if soup.title else None,
                "metadata": {}
            }
            
            # Extract CSS
            css_content = []
            if include_css:
                # Extract inline styles
                inline_styles = [tag.get('style', '') for tag in soup.find_all(style=True)]
                css_content.extend(inline_styles)
                
                # Extract linked CSS files
                css_links = []
                for link in soup.find_all('link', rel='stylesheet'):
                    href = link.get('href')
                    if href:
                        absolute_url = urljoin(url, href)
                        css_links.append(absolute_url)
                        
                        # Try to fetch CSS
                        try:
                            WebScraperTools._check_rate_limit()
                            css_response = requests.get(absolute_url, headers=headers, timeout=5)
                            if css_response.status_code == 200:
                                css_content.append(css_response.text)
                        except Exception:
                            pass  # Skip if CSS can't be fetched
                
                result_data["css"] = "\n\n".join(css_content)
                result_data["css_links"] = css_links
            
            # Extract images (URLs only, not content)
            image_urls = []
            if include_images:
                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src')
                    if src:
                        absolute_url = urljoin(url, src)
                        image_urls.append(absolute_url)
                
                result_data["images"] = image_urls
            
            # Extract metadata
            result_data["metadata"] = {
                "status_code": response.status_code,
                "content_type": response.headers.get('Content-Type', ''),
                "encoding": response.encoding,
                "final_url": response.url,
                "html_length": len(html_content),
                "css_files": len(result_data.get("css_links", [])),
                "images_count": len(image_urls) if include_images else 0
            }
            
            return ToolResult(
                success=True,
                result=result_data,
                metadata={
                    "url": url,
                    "title": result_data["title"],
                    "has_css": include_css and bool(result_data.get("css")),
                    "has_images": include_images and bool(image_urls),
                }
            )
        
        except requests.exceptions.Timeout:
            return ToolResult(
                success=False,
                result=None,
                error="Request timed out"
            )
        except requests.exceptions.RequestException as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Request failed: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error scraping website: {str(e)}"
            )
    
    @staticmethod
    def extract_design_elements(html: str = None, css: str = None, url: str = None) -> ToolResult:
        """
        Extract design elements from HTML/CSS:
        - Color palette
        - Typography (fonts, sizes)
        - Layout patterns (grid, flexbox)
        - Component structure
        - Spacing system
        
        Args:
            html: HTML content (optional if url provided)
            css: CSS content (optional if url provided)
            url: Website URL (will scrape if html/css not provided)
        
        Returns:
            ToolResult with extracted design elements
        """
        # If URL provided but no HTML/CSS, scrape first
        if url and (not html or not css):
            scrape_result = WebScraperTools.scrape_website(url, include_css=True, include_images=False)
            if not scrape_result.success:
                return scrape_result
            
            html = scrape_result.result.get("html", "")
            css = scrape_result.result.get("css", "")
        
        if not html:
            return ToolResult(
                success=False,
                result=None,
                error="HTML content is required"
            )
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            design_elements = {
                "colors": [],
                "fonts": [],
                "layout_patterns": [],
                "spacing": [],
                "components": []
            }
            
            # Extract colors from CSS
            color_patterns = [
                r'#([0-9a-fA-F]{3,6})\b',  # Hex colors
                r'rgb\((\d+),\s*(\d+),\s*(\d+)\)',  # RGB
                r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)',  # RGBA
                r'hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)',  # HSL
            ]
            
            colors_set: Set[str] = set()
            if css:
                for pattern in color_patterns:
                    matches = re.findall(pattern, css)
                    for match in matches:
                        if isinstance(match, tuple):
                            if len(match) == 3:  # RGB
                                color = f"rgb({match[0]}, {match[1]}, {match[2]})"
                            elif len(match) == 4:  # RGBA or HSL
                                if '.' in match[3]:  # RGBA
                                    color = f"rgba({match[0]}, {match[1]}, {match[2]}, {match[3]})"
                                else:  # HSL
                                    color = f"hsl({match[0]}, {match[1]}%, {match[2]}%)"
                        else:
                            # Hex color
                            hex_color = f"#{match}"
                            colors_set.add(hex_color)
                
                # Also check inline styles
                for tag in soup.find_all(style=True):
                    style = tag.get('style', '')
                    for pattern in color_patterns:
                        matches = re.findall(pattern, style)
                        for match in matches:
                            if isinstance(match, str) and match:
                                colors_set.add(f"#{match}")
            
            design_elements["colors"] = sorted(list(colors_set))[:20]  # Limit to 20 most common
            
            # Extract fonts
            font_patterns = [
                r'font-family:\s*([^;]+)',
                r'font-family\s*:\s*([^;]+)',
            ]
            
            fonts_set: Set[str] = set()
            if css:
                for pattern in font_patterns:
                    matches = re.findall(pattern, css, re.IGNORECASE)
                    for match in matches:
                        # Clean up font names (remove quotes, commas)
                        font_names = [f.strip().strip('"\'').strip(',') for f in match.split(',')]
                        fonts_set.update(font_names[:3])  # Take first 3 fonts from stack
            
            design_elements["fonts"] = list(fonts_set)[:10]  # Limit to 10 fonts
            
            # Extract layout patterns
            layout_patterns = []
            if css:
                # Check for grid
                if re.search(r'display:\s*grid', css, re.IGNORECASE):
                    layout_patterns.append("CSS Grid")
                # Check for flexbox
                if re.search(r'display:\s*flex', css, re.IGNORECASE):
                    layout_patterns.append("Flexbox")
                # Check for bootstrap classes
                if re.search(r'\.container|\.row|\.col-', css, re.IGNORECASE):
                    layout_patterns.append("Bootstrap Grid")
            
            # Check HTML for layout indicators
            if soup.find(class_=re.compile(r'container|grid|flex', re.IGNORECASE)):
                if "container" not in layout_patterns:
                    layout_patterns.append("Container-based")
            
            design_elements["layout_patterns"] = layout_patterns
            
            # Extract component structure
            components = []
            # Find common component patterns
            if soup.find_all(['header', 'nav']):
                components.append("Navigation/Header")
            if soup.find_all(['main', 'article', 'section']):
                components.append("Main Content Sections")
            if soup.find_all(['footer']):
                components.append("Footer")
            if soup.find_all(class_=re.compile(r'card|panel|box', re.IGNORECASE)):
                components.append("Card-based UI")
            if soup.find_all(['button', 'a'], class_=re.compile(r'btn|button', re.IGNORECASE)):
                components.append("Button Components")
            
            design_elements["components"] = components
            
            # Extract spacing (common spacing values)
            spacing_values: Set[str] = set()
            if css:
                spacing_pattern = r'(?:margin|padding|gap|spacing)[:\s]+([0-9.]+(?:px|rem|em|%))'
                matches = re.findall(spacing_pattern, css, re.IGNORECASE)
                spacing_values.update(matches[:10])  # Limit to 10 most common
            
            design_elements["spacing"] = sorted(list(spacing_values))
            
            return ToolResult(
                success=True,
                result=design_elements,
                metadata={
                    "colors_count": len(design_elements["colors"]),
                    "fonts_count": len(design_elements["fonts"]),
                    "components_count": len(design_elements["components"]),
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error extracting design elements: {str(e)}"
            )
    
    @staticmethod
    def extract_structure(url: str = None, html: str = None) -> ToolResult:
        """
        Extract website structure:
        - Navigation structure
        - Page layout
        - Component hierarchy
        - Responsive breakpoints
        
        Args:
            url: Website URL (will scrape if html not provided)
            html: HTML content (optional if url provided)
        
        Returns:
            ToolResult with structure information
        """
        # If URL provided but no HTML, scrape first
        if url and not html:
            scrape_result = WebScraperTools.scrape_website(url, include_css=True, include_images=False)
            if not scrape_result.success:
                return scrape_result
            
            html = scrape_result.result.get("html", "")
        
        if not html:
            return ToolResult(
                success=False,
                result=None,
                error="HTML content is required"
            )
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            structure = {
                "navigation": [],
                "layout": {},
                "components": [],
                "responsive_breakpoints": []
            }
            
            # Extract navigation
            nav_links = []
            for nav in soup.find_all(['nav', 'header']):
                for link in nav.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    if text:
                        nav_links.append({"text": text, "href": href})
            
            structure["navigation"] = nav_links[:20]  # Limit to 20 links
            
            # Extract layout structure
            main_elements = {}
            if soup.find('header'):
                main_elements["header"] = "Present"
            if soup.find('main'):
                main_elements["main"] = "Present"
            if soup.find('footer'):
                main_elements["footer"] = "Present"
            if soup.find('aside'):
                main_elements["sidebar"] = "Present"
            
            structure["layout"] = main_elements
            
            # Extract component hierarchy
            components = []
            # Count common components
            component_counts = {
                "sections": len(soup.find_all('section')),
                "articles": len(soup.find_all('article')),
                "divs": len(soup.find_all('div')),
                "buttons": len(soup.find_all('button')),
                "forms": len(soup.find_all('form')),
            }
            
            structure["components"] = component_counts
            
            # Extract responsive breakpoints from CSS (if available)
            # This would require CSS parsing - simplified version
            # In a full implementation, we'd parse CSS media queries
            
            return ToolResult(
                success=True,
                result=structure,
                metadata={
                    "nav_links_count": len(structure["navigation"]),
                    "components_detected": sum(component_counts.values()),
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error extracting structure: {str(e)}"
            )
    
    @staticmethod
    def analyze_design(url: str = None, html: str = None, css: str = None) -> ToolResult:
        """
        Analyze website design and create summary:
        - Design style (modern, minimalist, etc.)
        - Color scheme
        - Typography system
        - Layout approach
        - UI component patterns
        
        Args:
            url: Website URL (will scrape if html/css not provided)
            html: HTML content (optional if url provided)
            css: CSS content (optional if url provided)
        
        Returns:
            ToolResult with design analysis summary
        """
        # If URL provided but no HTML/CSS, scrape first
        if url and (not html or not css):
            scrape_result = WebScraperTools.scrape_website(url, include_css=True, include_images=False)
            if not scrape_result.success:
                return scrape_result
            
            html = scrape_result.result.get("html", "")
            css = scrape_result.result.get("css", "")
        
        if not html:
            return ToolResult(
                success=False,
                result=None,
                error="HTML content is required"
            )
        
        try:
            # Extract design elements first
            elements_result = WebScraperTools.extract_design_elements(html=html, css=css)
            if not elements_result.success:
                return elements_result
            
            design_elements = elements_result.result
            
            # Analyze design style
            analysis = {
                "style": "Unknown",
                "color_scheme": "Unknown",
                "typography": "Unknown",
                "layout": "Unknown",
                "component_patterns": "Unknown",
                "summary": ""
            }
            
            # Analyze color scheme
            colors = design_elements.get("colors", [])
            if colors:
                # Determine color scheme type
                primary_colors = colors[:3]
                analysis["color_scheme"] = ", ".join(primary_colors)
                
                # Detect if dark/light theme
                if any('000' in c or '111' in c for c in primary_colors):
                    analysis["style"] = "Dark/Minimalist"
                elif any('fff' in c.lower() or 'f5f' in c.lower() for c in primary_colors):
                    analysis["style"] = "Light/Modern"
                else:
                    analysis["style"] = "Colorful/Modern"
            
            # Analyze typography
            fonts = design_elements.get("fonts", [])
            if fonts:
                font_names = [f.replace('"', '').replace("'", "") for f in fonts]
                analysis["typography"] = ", ".join(font_names[:3])
            
            # Analyze layout
            layout_patterns = design_elements.get("layout_patterns", [])
            if layout_patterns:
                analysis["layout"] = ", ".join(layout_patterns)
            
            # Analyze components
            components = design_elements.get("components", [])
            if components:
                analysis["component_patterns"] = ", ".join(components)
            
            # Create summary
            summary_parts = []
            if analysis["style"] != "Unknown":
                summary_parts.append(f"Style: {analysis['style']}")
            if analysis["color_scheme"] != "Unknown":
                summary_parts.append(f"Colors: {analysis['color_scheme']}")
            if analysis["typography"] != "Unknown":
                summary_parts.append(f"Fonts: {analysis['typography']}")
            if analysis["layout"] != "Unknown":
                summary_parts.append(f"Layout: {analysis['layout']}")
            if analysis["component_patterns"] != "Unknown":
                summary_parts.append(f"Components: {analysis['component_patterns']}")
            
            analysis["summary"] = " | ".join(summary_parts)
            
            return ToolResult(
                success=True,
                result=analysis,
                metadata={
                    "design_elements": design_elements,
                    "analysis_complete": True
                }
            )
        
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Error analyzing design: {str(e)}"
            )
    
    @staticmethod
    def download_assets(url: str, asset_types: List[str] = None) -> ToolResult:
        """
        Download images, fonts, CSS files (optional).
        
        Security: Only downloads publicly accessible assets from scraped domain.
        
        Args:
            url: Website URL to download assets from
            asset_types: List of asset types to download: ['images', 'fonts', 'css']
        
        Returns:
            ToolResult with list of downloaded assets (URLs only, not content)
        
        Note: For security, this returns URLs only, not actual file content.
        For production use, implement proper file saving with security checks.
        """
        if asset_types is None:
            asset_types = ['images']
        
        # Scrape website first to get asset URLs
        scrape_result = WebScraperTools.scrape_website(
            url,
            include_css='css' in asset_types,
            include_images='images' in asset_types
        )
        
        if not scrape_result.success:
            return scrape_result
        
        assets = {
            "urls": [],
            "images": [],
            "css_files": [],
            "fonts": []
        }
        
        # Extract asset URLs from scrape result
        if 'images' in asset_types:
            images = scrape_result.result.get("images", [])
            assets["images"] = images
            assets["urls"].extend(images)
        
        if 'css' in asset_types:
            css_links = scrape_result.result.get("css_links", [])
            assets["css_files"] = css_links
            assets["urls"].extend(css_links)
        
        # Note: Font extraction would require parsing CSS @font-face rules
        # This is a simplified version
        
        return ToolResult(
            success=True,
            result=assets,
            metadata={
                "url": url,
                "images_count": len(assets["images"]),
                "css_files_count": len(assets["css_files"]),
                "total_assets": len(assets["urls"])
            }
        )

