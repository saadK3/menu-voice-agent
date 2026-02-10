"""
Test Suite for Menu Voice Agent API
Run with: python test_api.py
"""

import requests
import json
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

BASE_URL = 'http://localhost:5000'

def print_test(test_name):
    """Print test header"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}TEST: {test_name}")
    print(f"{Fore.CYAN}{'='*60}")

def print_success(message):
    """Print success message"""
    print(f"{Fore.GREEN}✓ {message}")

def print_error(message):
    """Print error message"""
    print(f"{Fore.RED}✗ {message}")

def print_info(message):
    """Print info message"""
    print(f"{Fore.YELLOW}ℹ {message}")

def test_health_check():
    """Test health check endpoint"""
    print_test("Health Check")

    response = requests.get(f'{BASE_URL}/health')

    if response.status_code == 200:
        data = response.json()
        print_success(f"API is healthy")
        print_info(f"Total items: {data['total_items']}")
        print_info(f"Total categories: {data['total_categories']}")
        return True
    else:
        print_error(f"Health check failed: {response.status_code}")
        return False

def test_get_categories():
    """Test get categories endpoint"""
    print_test("Get Categories")

    response = requests.post(f'{BASE_URL}/api/get_categories', json={})

    if response.status_code == 200:
        data = response.json()
        print_success(f"Retrieved {data['total']} categories")

        # Print first 5 categories
        for i, cat in enumerate(data['categories'][:5]):
            print_info(f"  {cat['name']}: {cat['item_count']} items")

        return True
    else:
        print_error(f"Failed: {response.status_code}")
        return False

def test_get_items_by_category():
    """Test get items by category"""
    print_test("Get Items by Category")

    # Test with valid category
    response = requests.post(
        f'{BASE_URL}/api/get_items_by_category',
        json={'category': 'Omelets & Breakfast'}
    )

    if response.status_code == 200:
        data = response.json()
        print_success(f"Retrieved {data['total']} items from '{data['category']}'")

        # Print first 3 items
        for item in data['items'][:3]:
            print_info(f"  {item['name']}: ${item['price']}")

        return True
    else:
        print_error(f"Failed: {response.status_code}")
        return False

def test_search_menu():
    """Test search menu endpoint"""
    print_test("Search Menu")

    # Test 1: Exact match
    print(f"\n{Fore.YELLOW}Test 1: Exact match - 'Pancakes'")
    response = requests.post(
        f'{BASE_URL}/api/search_menu',
        json={'query': 'Pancakes'}
    )

    if response.status_code == 200:
        data = response.json()
        if data['found']:
            print_success(f"Found {data['total_matches']} match(es)")
            for result in data['results']:
                print_info(f"  {result['name']} - {result['match_type']} (score: {result['score']:.2f})")
        else:
            print_error("No results found")

    # Test 2: Partial match
    print(f"\n{Fore.YELLOW}Test 2: Partial match - 'tuna'")
    response = requests.post(
        f'{BASE_URL}/api/search_menu',
        json={'query': 'tuna'}
    )

    if response.status_code == 200:
        data = response.json()
        if data['found']:
            print_success(f"Found {data['total_matches']} match(es)")
            for result in data['results']:
                print_info(f"  {result['name']} - {result['match_type']}")
        else:
            print_error("No results found")

    # Test 3: Non-existent item (hallucination prevention)
    print(f"\n{Fore.YELLOW}Test 3: Non-existent item - 'cheeseburger'")
    response = requests.post(
        f'{BASE_URL}/api/search_menu',
        json={'query': 'cheeseburger'}
    )

    if response.status_code == 200:
        data = response.json()
        if not data['found']:
            print_success("Correctly returned no results for non-existent item")
            print_info(f"  Message: {data['message']}")
        else:
            print_error("Should not have found results for 'cheeseburger'")

    # Test 4: Fuzzy match (typo)
    print(f"\n{Fore.YELLOW}Test 4: Fuzzy match - 'omlet' (typo)")
    response = requests.post(
        f'{BASE_URL}/api/search_menu',
        json={'query': 'omlet'}
    )

    if response.status_code == 200:
        data = response.json()
        if data['found']:
            print_success(f"Found {data['total_matches']} match(es) despite typo")
            for result in data['results']:
                print_info(f"  {result['name']} - {result['match_type']} (score: {result['score']:.2f})")
        else:
            print_info("No fuzzy matches found")

    return True

def test_get_item_details():
    """Test get item details"""
    print_test("Get Item Details")

    # First, search for an item to get its ID
    search_response = requests.post(
        f'{BASE_URL}/api/search_menu',
        json={'query': 'Breakfast Special'}
    )

    if search_response.status_code == 200:
        search_data = search_response.json()
        if search_data['found']:
            item_id = search_data['results'][0]['id']

            # Get details
            response = requests.post(
                f'{BASE_URL}/api/get_item_details',
                json={'item_id': item_id}
            )

            if response.status_code == 200:
                data = response.json()
                item = data['item']
                print_success(f"Retrieved details for '{item['name']}'")
                print_info(f"  Price: ${item['base_price']}")
                print_info(f"  Category: {item['category']}")
                print_info(f"  Required modifiers: {len(item['modifiers']['required'])}")
                print_info(f"  Optional modifiers: {len(item['modifiers']['optional'])}")
                return True

    print_error("Failed to get item details")
    return False

def test_order_flow():
    """Test complete order flow"""
    print_test("Order Flow (Add, View, Remove, Clear)")

    session_id = None

    # Step 1: Search for item
    print(f"\n{Fore.YELLOW}Step 1: Search for 'Pancakes'")
    search_response = requests.post(
        f'{BASE_URL}/api/search_menu',
        json={'query': 'Pancakes'}
    )

    if search_response.status_code != 200 or not search_response.json()['found']:
        print_error("Failed to find item")
        return False

    item_id = search_response.json()['results'][0]['id']
    print_success(f"Found item ID: {item_id}")

    # Step 2: Add to order
    print(f"\n{Fore.YELLOW}Step 2: Add to order")
    add_response = requests.post(
        f'{BASE_URL}/api/add_to_order',
        json={
            'item_id': item_id,
            'modifier_ids': [],
            'quantity': 2
        }
    )

    if add_response.status_code == 200:
        add_data = add_response.json()
        session_id = add_data['session_id']
        print_success(f"Added to order (Session: {session_id[:8]}...)")
        print_info(f"  Item: {add_data['order_item']['item_name']}")
        print_info(f"  Quantity: {add_data['order_item']['quantity']}")
        print_info(f"  Subtotal: ${add_data['order_item']['subtotal']}")
        print_info(f"  Order total: ${add_data['order_total']}")
    else:
        print_error("Failed to add to order")
        return False

    # Step 3: Get order summary
    print(f"\n{Fore.YELLOW}Step 3: Get order summary")
    summary_response = requests.post(
        f'{BASE_URL}/api/get_order_summary',
        json={'session_id': session_id}
    )

    if summary_response.status_code == 200:
        summary_data = summary_response.json()
        order = summary_data['order']
        print_success(f"Order summary retrieved")
        print_info(f"  Items: {order['item_count']}")
        print_info(f"  Total: ${order['total']}")
    else:
        print_error("Failed to get order summary")
        return False

    # Step 4: Add another item
    print(f"\n{Fore.YELLOW}Step 4: Add another item (Omelet)")
    search_response2 = requests.post(
        f'{BASE_URL}/api/search_menu',
        json={'query': 'Omelet'}
    )

    if search_response2.status_code == 200 and search_response2.json()['found']:
        item_id2 = search_response2.json()['results'][0]['id']

        add_response2 = requests.post(
            f'{BASE_URL}/api/add_to_order',
            json={
                'session_id': session_id,
                'item_id': item_id2,
                'modifier_ids': [],
                'quantity': 1
            }
        )

        if add_response2.status_code == 200:
            add_data2 = add_response2.json()
            print_success(f"Added second item")
            print_info(f"  New total: ${add_data2['order_total']}")

    # Step 5: Remove first item
    print(f"\n{Fore.YELLOW}Step 5: Remove first item")
    remove_response = requests.post(
        f'{BASE_URL}/api/remove_from_order',
        json={
            'session_id': session_id,
            'item_index': 0
        }
    )

    if remove_response.status_code == 200:
        remove_data = remove_response.json()
        print_success(f"Removed item")
        print_info(f"  Removed: {remove_data['removed_item']['item_name']}")
        print_info(f"  New total: ${remove_data['order_total']}")

    # Step 6: Clear order
    print(f"\n{Fore.YELLOW}Step 6: Clear order")
    clear_response = requests.post(
        f'{BASE_URL}/api/clear_order',
        json={'session_id': session_id}
    )

    if clear_response.status_code == 200:
        print_success("Order cleared")
        return True

    return False

def run_all_tests():
    """Run all tests"""
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}MENU VOICE AGENT API - TEST SUITE")
    print(f"{Fore.MAGENTA}{'='*60}")

    tests = [
        ("Health Check", test_health_check),
        ("Get Categories", test_get_categories),
        ("Get Items by Category", test_get_items_by_category),
        ("Search Menu", test_search_menu),
        ("Get Item Details", test_get_item_details),
        ("Order Flow", test_order_flow)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Exception in {test_name}: {str(e)}")
            results.append((test_name, False))

    # Print summary
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}TEST SUMMARY")
    print(f"{Fore.MAGENTA}{'='*60}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{Fore.GREEN}PASS" if result else f"{Fore.RED}FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{Fore.CYAN}Total: {passed}/{total} tests passed")

    if passed == total:
        print(f"{Fore.GREEN}{'='*60}")
        print(f"{Fore.GREEN}ALL TESTS PASSED! ✓")
        print(f"{Fore.GREEN}{'='*60}")
    else:
        print(f"{Fore.RED}{'='*60}")
        print(f"{Fore.RED}SOME TESTS FAILED")
        print(f"{Fore.RED}{'='*60}")

if __name__ == '__main__':
    print(f"\n{Fore.YELLOW}Make sure the Flask server is running on {BASE_URL}")
    print(f"{Fore.YELLOW}Run: python app.py")
    input(f"\n{Fore.YELLOW}Press Enter when server is ready...")

    run_all_tests()
