"""
Menu Voice Agent - Flask Backend API
Provides endpoints for Retell AI to interact with menu data
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import uuid
from datetime import datetime
from difflib import SequenceMatcher

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load menu data
with open('menu_data.json', 'r', encoding='utf-8') as f:
    menu_data = json.load(f)

# In-memory order storage (session-based)
# Format: {session_id: {items: [], total: 0, created_at: timestamp}}
orders = {}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_or_create_session(session_id=None):
    """Get existing session or create new one"""
    if session_id and session_id in orders:
        return session_id

    # Create new session
    new_session_id = str(uuid.uuid4())
    orders[new_session_id] = {
        'items': [],
        'total': 0.0,
        'created_at': datetime.now().isoformat()
    }
    return new_session_id

def calculate_item_price(item_id, modifier_ids):
    """Calculate total price for an item with modifiers"""
    item = menu_data['items'].get(item_id)
    if not item:
        return 0.0

    total = item['base_price']

    # Add modifier prices
    for modifier_id in modifier_ids:
        # Search through all modifier groups
        for group in item['modifiers']['required'] + item['modifiers']['optional']:
            for option in group['options']:
                if option['id'] == modifier_id:
                    total += option['price']
                    break

    return round(total, 2)

def similarity_score(str1, str2):
    """Calculate similarity between two strings (0-1)"""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def search_items(query, threshold=0.6):
    """Search for items by name with fuzzy matching"""
    query_lower = query.lower()
    results = []

    for item_id, item in menu_data['items'].items():
        item_name_lower = item['name'].lower()

        # Exact match
        if query_lower == item_name_lower:
            results.append({
                'id': item_id,
                'name': item['name'],
                'category': item['category'],
                'price': item['base_price'],
                'match_type': 'exact',
                'score': 1.0
            })
        # Contains match
        elif query_lower in item_name_lower or item_name_lower in query_lower:
            results.append({
                'id': item_id,
                'name': item['name'],
                'category': item['category'],
                'price': item['base_price'],
                'match_type': 'partial',
                'score': 0.9
            })
        # Fuzzy match
        else:
            score = similarity_score(query, item['name'])
            if score >= threshold:
                results.append({
                    'id': item_id,
                    'name': item['name'],
                    'category': item['category'],
                    'price': item['base_price'],
                    'match_type': 'fuzzy',
                    'score': score
                })

    # Sort by score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'total_items': menu_data['metadata']['total_items'],
        'total_categories': menu_data['metadata']['total_categories']
    })

@app.route('/api/get_categories', methods=['POST'])
def get_categories():
    """Get all menu categories"""
    categories = [
        {
            'name': cat_data['name'],
            'item_count': cat_data['item_count']
        }
        for cat_data in menu_data['categories'].values()
    ]

    return jsonify({
        'success': True,
        'categories': categories,
        'total': len(categories)
    })

@app.route('/api/get_items_by_category', methods=['POST'])
def get_items_by_category():
    """Get all items in a specific category"""
    data = request.json
    category_name = data.get('category')

    if not category_name:
        return jsonify({
            'success': False,
            'error': 'Category name is required'
        }), 400

    # Find category (case-insensitive)
    category_data = None
    for cat_name, cat_info in menu_data['categories'].items():
        if cat_name.lower() == category_name.lower():
            category_data = cat_info
            break

    if not category_data:
        return jsonify({
            'success': False,
            'error': f'Category "{category_name}" not found',
            'available_categories': list(menu_data['categories'].keys())
        }), 404

    # Get items
    items = []
    for item_id in category_data['item_ids']:
        item = menu_data['items'][item_id]
        items.append({
            'id': item['id'],
            'name': item['name'],
            'price': item['base_price'],
            'description': item['description'],
            'available': item['available']
        })

    return jsonify({
        'success': True,
        'category': category_data['name'],
        'items': items,
        'total': len(items)
    })

@app.route('/api/search_menu', methods=['POST'])
def search_menu():
    """Search for menu items (prevents hallucinations)"""
    data = request.json
    query = data.get('query', '').strip()

    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400

    # Search
    results = search_items(query, threshold=0.6)

    if not results:
        return jsonify({
            'success': True,
            'found': False,
            'query': query,
            'message': f'No items found matching "{query}"',
            'results': []
        })

    return jsonify({
        'success': True,
        'found': True,
        'query': query,
        'results': results[:5],  # Top 5 results
        'total_matches': len(results)
    })

@app.route('/api/get_item_details', methods=['POST'])
def get_item_details():
    """Get detailed information about a specific item"""
    data = request.json
    item_id = data.get('item_id')

    if not item_id:
        return jsonify({
            'success': False,
            'error': 'Item ID is required'
        }), 400

    item = menu_data['items'].get(item_id)

    if not item:
        return jsonify({
            'success': False,
            'error': f'Item with ID "{item_id}" not found'
        }), 404

    return jsonify({
        'success': True,
        'item': item
    })

@app.route('/api/add_to_order', methods=['POST'])
def add_to_order():
    """Add an item to the order"""
    data = request.json
    session_id = data.get('session_id')
    item_id = data.get('item_id')
    modifier_ids = data.get('modifier_ids', [])
    quantity = data.get('quantity', 1)

    if not item_id:
        return jsonify({
            'success': False,
            'error': 'Item ID is required'
        }), 400

    # Validate item exists
    item = menu_data['items'].get(item_id)
    if not item:
        return jsonify({
            'success': False,
            'error': f'Item "{item_id}" not found'
        }), 404

    # Get or create session
    session_id = get_or_create_session(session_id)

    # Calculate price
    item_price = calculate_item_price(item_id, modifier_ids)
    subtotal = item_price * quantity

    # Create order item
    order_item = {
        'item_id': item_id,
        'item_name': item['name'],
        'base_price': item['base_price'],
        'modifier_ids': modifier_ids,
        'quantity': quantity,
        'item_total': item_price,
        'subtotal': subtotal
    }

    # Add to order
    orders[session_id]['items'].append(order_item)
    orders[session_id]['total'] = round(
        orders[session_id]['total'] + subtotal, 2
    )

    return jsonify({
        'success': True,
        'session_id': session_id,
        'order_item': order_item,
        'order_total': orders[session_id]['total']
    })

@app.route('/api/get_order_summary', methods=['POST'])
def get_order_summary():
    """Get current order summary"""
    data = request.json
    session_id = data.get('session_id')

    if not session_id or session_id not in orders:
        return jsonify({
            'success': True,
            'order': {
                'items': [],
                'total': 0.0,
                'item_count': 0
            }
        })

    order = orders[session_id]

    return jsonify({
        'success': True,
        'session_id': session_id,
        'order': {
            'items': order['items'],
            'total': order['total'],
            'item_count': len(order['items']),
            'created_at': order['created_at']
        }
    })

@app.route('/api/clear_order', methods=['POST'])
def clear_order():
    """Clear/reset the order"""
    data = request.json
    session_id = data.get('session_id')

    if session_id and session_id in orders:
        del orders[session_id]

    return jsonify({
        'success': True,
        'message': 'Order cleared'
    })

@app.route('/api/remove_from_order', methods=['POST'])
def remove_from_order():
    """Remove an item from the order"""
    data = request.json
    session_id = data.get('session_id')
    item_index = data.get('item_index')

    if not session_id or session_id not in orders:
        return jsonify({
            'success': False,
            'error': 'Invalid session'
        }), 400

    if item_index is None or item_index < 0:
        return jsonify({
            'success': False,
            'error': 'Valid item index is required'
        }), 400

    order = orders[session_id]

    if item_index >= len(order['items']):
        return jsonify({
            'success': False,
            'error': 'Item index out of range'
        }), 400

    # Remove item and update total
    removed_item = order['items'].pop(item_index)
    order['total'] = round(order['total'] - removed_item['subtotal'], 2)

    return jsonify({
        'success': True,
        'removed_item': removed_item,
        'order_total': order['total']
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("🚀 Starting Menu Voice Agent API...")
    print(f"📊 Loaded {menu_data['metadata']['total_items']} items")
    print(f"📁 Loaded {menu_data['metadata']['total_categories']} categories")
    app.run(debug=True, host='0.0.0.0', port=5000)
