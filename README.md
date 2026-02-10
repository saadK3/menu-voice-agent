# Menu Voice Agent Backend

Flask backend API for a voice-powered restaurant ordering system using Retell AI.

## 🎯 Features

- **109 menu items** across 14 categories
- **Smart search** with fuzzy matching for typos
- **Hallucination prevention** - only returns items that actually exist
- **Order management** with automatic price calculation
- **Modifier support** for item customization
- **RESTful API** ready for Retell AI integration

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/menu-voice-agent.git
cd menu-voice-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
python app.py
```

Server will start at `http://localhost:5000`

### Running Tests

```bash
python test_api.py
```

## 📡 API Endpoints

| Endpoint                     | Method | Description                       |
| ---------------------------- | ------ | --------------------------------- |
| `/health`                    | GET    | Health check                      |
| `/api/get_categories`        | POST   | Get all menu categories           |
| `/api/get_items_by_category` | POST   | Get items in a category           |
| `/api/search_menu`           | POST   | Search for items (fuzzy matching) |
| `/api/get_item_details`      | POST   | Get full item details             |
| `/api/add_to_order`          | POST   | Add item to order                 |
| `/api/get_order_summary`     | POST   | Get current order                 |
| `/api/remove_from_order`     | POST   | Remove item from order            |
| `/api/clear_order`           | POST   | Clear order                       |

## 🌐 Deployment

### Deploy to Render

1. Push code to GitHub
2. Go to [render.com](https://render.com)
3. Create new Web Service
4. Connect GitHub repository
5. Render auto-detects configuration from `render.yaml`
6. Deploy!

Your API will be live at: `https://your-app-name.onrender.com`

## 🧪 Testing

The test suite validates:

- ✅ All API endpoints
- ✅ Search functionality (exact, partial, fuzzy matching)
- ✅ Hallucination prevention (non-existent items return empty)
- ✅ Order flow (add, view, remove, clear)
- ✅ Price calculation with modifiers

## 📊 Project Structure

```
menu-voice-agent/
├── data/                    # CSV menu files
├── menu_data.json          # Optimized menu data
├── app.py                  # Flask API
├── test_api.py             # Test suite
├── convert_menu_data.py    # Data converter
├── requirements.txt        # Dependencies
├── render.yaml            # Render config
└── README.md              # This file
```

## 🔐 Environment Variables

No environment variables required for basic operation.

## 📝 License

MIT

## 🤝 Contributing

Pull requests welcome!
