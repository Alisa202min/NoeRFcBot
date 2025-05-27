"""
Simple Web Application Test for RFCBot
"""

import requests
import sys

def test_endpoints():
    """Test basic web application endpoints"""
    base_url = "http://localhost:5000"
    endpoints = [
        "/",                     # Home page
        "/search",               # Search page
        "/login",                # Login page
    ]
    
    print("===== Testing Basic Endpoints =====")
    success = True
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"Testing {url}...")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"✓ Success ({response.status_code})")
            else:
                print(f"✗ Failed ({response.status_code})")
                success = False
        except Exception as e:
            print(f"✗ Error: {e}")
            success = False
    
    return success

def test_search_functionality():
    """Test search functionality with different parameters"""
    base_url = "http://localhost:5000"
    search_tests = [
        {
            "name": "Basic search",
            "params": {"query": "test"}
        },
        {
            "name": "Product search with filters",
            "params": {
                "query": "test", 
                "type": "product",
                "min_price": "100",
                "max_price": "10000"
            }
        },
        {
            "name": "Service search with filters",
            "params": {
                "query": "test", 
                "type": "service"
            }
        },
        {
            "name": "Sort by price (ascending)",
            "params": {
                "sort_by": "price",
                "sort_order": "asc"
            }
        },
        {
            "name": "Sort by price (descending)",
            "params": {
                "sort_by": "price",
                "sort_order": "desc"
            }
        },
        {
            "name": "Search with page parameter",
            "params": {
                "page": "1"
            }
        }
    ]
    
    print("\n===== Testing Search Functionality =====")
    success = True
    
    for test in search_tests:
        print(f"Testing {test['name']}...")
        try:
            url = f"{base_url}/search"
            response = requests.get(url, params=test['params'])
            if response.status_code == 200:
                print(f"✓ Success ({response.status_code})")
            else:
                print(f"✗ Failed ({response.status_code})")
                success = False
        except Exception as e:
            print(f"✗ Error: {e}")
            success = False
    
    return success

if __name__ == '__main__':
    endpoints_success = test_endpoints()
    search_success = test_search_functionality()
    
    overall_success = endpoints_success and search_success
    
    print("\n===== Overall Result =====")
    print(f"Basic endpoints: {'✓ Passed' if endpoints_success else '✗ Failed'}")
    print(f"Search functionality: {'✓ Passed' if search_success else '✗ Failed'}")
    print(f"Overall: {'✓ Passed' if overall_success else '✗ Failed'}")
    
    sys.exit(0 if overall_success else 1)