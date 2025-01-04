# Intelligent Chatbot 🤖

An advanced chatbot with web search capabilities and comprehensive analysis features.

## Features

- 🌐 Smart web search and analysis
- 📊 Detailed result summaries
- 🎯 Key points extraction
- 📈 Statistical analysis
- 👨‍🔬 Expert opinion gathering
- ⚖️ Pros & cons analysis
- 🔗 Related topics discovery
- ⭐ Source credibility rating

## Installation

1. Clone the repository:
```bash
git clone https://github.com/lorencndoj/chatbot.git
cd chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### CLI Mode
Run the chatbot directly:
```bash
python chatbot.py
```

### API Mode
Start the API server:
```bash
python api.py
```

The API will be available at `http://localhost:8000`

## Features

### Search Results Include:
- 📝 Comprehensive summaries
- 🎯 Key points
- 📊 Statistics and data
- 👨‍🔬 Expert insights
- ⚖️ Pros & cons
- 🔗 Related topics
- ⭐ Credibility ratings

## API Endpoints

- `GET /` - Welcome page and API info
- `POST /search` - Perform a search query

Example search request:
```json
{
    "query": "your search query",
    "max_results": 10
}
```

## License

MIT License
