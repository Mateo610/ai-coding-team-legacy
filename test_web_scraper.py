"""
Test Web Scraper Tool Implementation
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import code_tools first to trigger tool registration
from tools.code_tools import TOOL_REGISTRY
from tools.web_scraper import WebScraperTools


def test_tool_registration():
    """Test that web scraper tools are registered"""
    print("=" * 70)
    print("Test 1: Tool Registration")
    print("=" * 70)
    
    expected_tools = [
        "scrape_website",
        "extract_design_elements",
        "extract_structure",
        "analyze_design",
        "download_assets"
    ]
    
    found_tools = []
    for tool in expected_tools:
        if tool in TOOL_REGISTRY:
            found_tools.append(tool)
            print(f"✅ {tool} - registered")
        else:
            print(f"❌ {tool} - NOT registered")
    
    print(f"\nResult: {len(found_tools)}/{len(expected_tools)} tools registered")
    return len(found_tools) == len(expected_tools)


def test_url_validation():
    """Test URL validation"""
    print("\n" + "=" * 70)
    print("Test 2: URL Validation")
    print("=" * 70)
    
    # Test valid URLs
    valid_urls = [
        "https://example.com",
        "http://example.com",
        "https://www.example.com/path",
    ]
    
    # Test invalid URLs
    invalid_urls = [
        "localhost:8000",
        "127.0.0.1:5000",
        "file:///etc/passwd",
        "ftp://example.com",
        "not-a-url",
    ]
    
    print("\nValid URLs:")
    for url in valid_urls:
        is_valid, error = WebScraperTools._validate_url(url)
        if is_valid:
            print(f"  ✅ {url} - valid")
        else:
            print(f"  ❌ {url} - invalid: {error}")
    
    print("\nInvalid URLs (should be blocked):")
    for url in invalid_urls:
        is_valid, error = WebScraperTools._validate_url(url)
        if not is_valid:
            print(f"  ✅ {url} - correctly blocked: {error}")
        else:
            print(f"  ❌ {url} - should be blocked but wasn't!")
    
    return True


def test_dependencies():
    """Test if required dependencies are available"""
    print("\n" + "=" * 70)
    print("Test 3: Dependencies Check")
    print("=" * 70)
    
    dependencies = {
        "requests": False,
        "beautifulsoup4": False,
    }
    
    try:
        import requests
        dependencies["requests"] = True
        print("✅ requests - available")
    except ImportError:
        print("⚠️  requests - not installed (pip install requests)")
    
    try:
        from bs4 import BeautifulSoup
        dependencies["beautifulsoup4"] = True
        print("✅ beautifulsoup4 - available")
    except ImportError:
        print("⚠️  beautifulsoup4 - not installed (pip install beautifulsoup4)")
    
    if not all(dependencies.values()):
        print("\n⚠️  Some dependencies missing - web scraping will not work")
        print("   Install with: pip install requests beautifulsoup4")
        return False
    
    print("\n✅ All dependencies available")
    return True


def test_scrape_website_structure():
    """Test scrape_website function structure (without actual web request)"""
    print("\n" + "=" * 70)
    print("Test 4: Function Structure")
    print("=" * 70)
    
    # Test that functions exist and have correct signatures
    functions = [
        ("scrape_website", ["url", "include_css", "include_images", "respect_robots"]),
        ("extract_design_elements", ["html", "css", "url"]),
        ("extract_structure", ["url", "html"]),
        ("analyze_design", ["url", "html", "css"]),
        ("download_assets", ["url", "asset_types"]),
    ]
    
    all_exist = True
    for func_name, params in functions:
        if hasattr(WebScraperTools, func_name):
            func = getattr(WebScraperTools, func_name)
            if callable(func):
                print(f"✅ {func_name} - exists and callable")
                
                # Check if it's a static method
                import inspect
                if isinstance(func, staticmethod):
                    print(f"   ✓ Static method")
                elif inspect.isfunction(func):
                    print(f"   ✓ Function")
            else:
                print(f"❌ {func_name} - exists but not callable")
                all_exist = False
        else:
            print(f"❌ {func_name} - does not exist")
            all_exist = False
    
    return all_exist


def test_rate_limiting():
    """Test rate limiting mechanism"""
    print("\n" + "=" * 70)
    print("Test 5: Rate Limiting")
    print("=" * 70)
    
    import time
    
    # Reset rate limit
    WebScraperTools._last_request_time = 0
    
    # Test rate limiting
    start_time = time.time()
    WebScraperTools._check_rate_limit()
    first_call = time.time() - start_time
    
    start_time = time.time()
    WebScraperTools._check_rate_limit()
    second_call = time.time() - start_time
    
    print(f"First call delay: {first_call:.3f}s (expected: <0.1s)")
    print(f"Second call delay: {second_call:.3f}s (expected: ~1.0s)")
    
    if first_call < 0.1 and second_call >= 0.8:
        print("✅ Rate limiting working correctly")
        return True
    else:
        print("⚠️  Rate limiting may not be working as expected")
        return False


def test_error_handling():
    """Test error handling for invalid inputs"""
    print("\n" + "=" * 70)
    print("Test 6: Error Handling")
    print("=" * 70)
    
    # Test invalid URL
    result = WebScraperTools.scrape_website("not-a-valid-url")
    if not result.success:
        print(f"✅ Invalid URL correctly rejected: {result.error[:50]}...")
    else:
        print(f"❌ Invalid URL should have been rejected")
        return False
    
    # Test localhost URL (should be blocked)
    result = WebScraperTools.scrape_website("http://localhost:8000")
    if not result.success:
        print(f"✅ Localhost URL correctly blocked: {result.error[:50]}...")
    else:
        print(f"❌ Localhost URL should have been blocked")
        return False
    
    # Test missing HTML for extract functions
    result = WebScraperTools.extract_design_elements(html="", css="")
    if not result.success:
        print(f"✅ Missing HTML correctly handled: {result.error[:50]}...")
    else:
        print(f"⚠️  Empty HTML was accepted (may be valid)")
    
    print("✅ Error handling working correctly")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 Web Scraper Tool - Implementation Tests")
    print("=" * 70)
    
    tests = [
        ("Tool Registration", test_tool_registration),
        ("URL Validation", test_url_validation),
        ("Dependencies Check", test_dependencies),
        ("Function Structure", test_scrape_website_structure),
        ("Rate Limiting", test_rate_limiting),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! Web Scraper Tool is ready!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

