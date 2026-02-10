"""
Menu Data Converter
Converts CSV menu files into optimized JSON format for Retell AI voice agent
"""

import pandas as pd
import json
import glob
import os
from pathlib import Path

def clean_category_name(filename):
    """Extract and clean category name from filename"""
    # Remove path and extension
    name = Path(filename).stem

    # Replace underscores with spaces and title case
    name = name.replace('_', ' ').title()

    # Special cases
    replacements = {
        'Pastriesmuffinsdonuts': 'Pastries, Muffins & Donuts',
        'Omelets Breakfast': 'Omelets & Breakfast',
        'Bagels Sandwiches': 'Bagels & Sandwiches',
        'Paninis Wraps': 'Paninis & Wraps',
        'Soup Farina': 'Soup & Farina',
        'Spreads Vegetables': 'Spreads & Vegetables',
        'Grab N Go': 'Grab & Go',
        'Patis Pastries': "Pati's Pastries",
        'Patis Savory': "Pati's Savory",
        'Chefs Specialties Sandwiches': "Chef's Specialties Sandwiches"
    }

    for old, new in replacements.items():
        if old in name:
            name = new
            break

    return name

def parse_modifiers(modifiers_json_str):
    """Parse the modifiers JSON string and organize by required/optional"""
    if pd.isna(modifiers_json_str) or modifiers_json_str == '[]':
        return {
            'required': [],
            'optional': []
        }

    try:
        modifiers = json.loads(modifiers_json_str)

        required_groups = []
        optional_groups = []

        for group in modifiers:
            group_data = {
                'group_name': group['group_name'],
                'options': []
            }

            # Add max selections if mentioned in group name
            if 'Choose Up To' in group['group_name']:
                import re
                match = re.search(r'Choose Up To (\d+)', group['group_name'])
                if match:
                    group_data['max_selections'] = int(match.group(1))

            # Process modifiers
            for mod in group['modifiers']:
                option = {
                    'id': mod['modifier_id'],
                    'name': mod['name'],
                    'price': mod['price'] if mod['price'] is not None else 0
                }
                group_data['options'].append(option)

            # Categorize as required or optional
            if group.get('required', False):
                required_groups.append(group_data)
            else:
                optional_groups.append(group_data)

        return {
            'required': required_groups,
            'optional': optional_groups
        }

    except json.JSONDecodeError as e:
        print(f"Error parsing modifiers: {e}")
        return {
            'required': [],
            'optional': []
        }

def process_menu_data(data_dir='data', output_file='menu_data.json'):
    """Process all CSV files and create optimized JSON"""

    print("🔄 Processing menu data...")

    menu_data = {
        'metadata': {
            'total_items': 0,
            'total_categories': 0,
            'generated_at': pd.Timestamp.now().isoformat()
        },
        'categories': {},
        'items': {},
        'search_index': []  # For quick searching
    }

    # Find all CSV files
    csv_files = glob.glob(f'{data_dir}/*.csv')

    if not csv_files:
        print(f"❌ No CSV files found in '{data_dir}' directory")
        return

    print(f"📁 Found {len(csv_files)} CSV files")

    for csv_file in csv_files:
        filename = os.path.basename(csv_file)

        # Skip menu summary
        if 'menu_summary' in filename.lower():
            continue

        category = clean_category_name(filename)
        print(f"   Processing: {category}")

        # Read CSV
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            print(f"   ⚠️  Error reading {filename}: {e}")
            continue

        # Initialize category
        menu_data['categories'][category] = {
            'name': category,
            'item_ids': [],
            'item_count': 0
        }

        # Process each item
        for _, row in df.iterrows():
            item_id = row['pos_id']

            # Parse modifiers
            modifiers = parse_modifiers(row.get('modifiers_json', '[]'))

            # Create item object
            item = {
                'id': item_id,
                'name': row['item_name'],
                'category': category,
                'base_price': float(row['base_price']),
                'description': row['description'] if pd.notna(row['description']) else '',
                'available': row['available'] == 'Yes',
                'modifiers': modifiers
            }

            # Add to items
            menu_data['items'][item_id] = item
            menu_data['categories'][category]['item_ids'].append(item_id)

            # Add to search index (for quick lookups)
            menu_data['search_index'].append({
                'id': item_id,
                'name': row['item_name'].lower(),
                'category': category,
                'keywords': row['item_name'].lower().split()
            })

        # Update category count
        menu_data['categories'][category]['item_count'] = len(menu_data['categories'][category]['item_ids'])

    # Update metadata
    menu_data['metadata']['total_items'] = len(menu_data['items'])
    menu_data['metadata']['total_categories'] = len(menu_data['categories'])

    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(menu_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Successfully processed menu data!")
    print(f"   📊 Total items: {menu_data['metadata']['total_items']}")
    print(f"   📁 Total categories: {menu_data['metadata']['total_categories']}")
    print(f"   💾 Saved to: {output_file}")

    # Print category breakdown
    print(f"\n📋 Category Breakdown:")
    for cat_name, cat_data in menu_data['categories'].items():
        print(f"   • {cat_name}: {cat_data['item_count']} items")

    return menu_data

def create_sample_output(menu_data, sample_file='menu_sample.json'):
    """Create a sample output with a few items for inspection"""

    sample = {
        'sample_items': [],
        'note': 'This is a sample of 5 items from the menu for inspection'
    }

    # Get first 5 items
    item_ids = list(menu_data['items'].keys())[:5]
    for item_id in item_ids:
        sample['sample_items'].append(menu_data['items'][item_id])

    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample, f, indent=2, ensure_ascii=False)

    print(f"   📄 Sample output saved to: {sample_file}")

if __name__ == '__main__':
    # Process the data
    menu_data = process_menu_data()

    if menu_data:
        # Create sample for inspection
        create_sample_output(menu_data)

        print("\n🎉 Data conversion complete!")
        print("   Next steps:")
        print("   1. Review menu_data.json")
        print("   2. Check menu_sample.json for data structure")
        print("   3. Use this JSON with your Retell AI backend")
