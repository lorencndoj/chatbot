# Search Agent 🔍

An intelligent search agent that provides comprehensive analysis of web search results. Built with Python, FastAPI, and modern web scraping techniques.

## Features

- 🌐 Advanced web scraping with parallel processing
- 📊 Comprehensive result analysis
- 🎯 Smart ranking system
- 🔍 Detailed content extraction
- 🤖 API interface
- ⚡ Async processing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/leomilano33/searchagent.git
cd searchagent
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

## Features

### Search Results Include:
- 📝 Detailed Summary
- 🎯 Key Points
- 📊 Statistics
- 👨‍🔬 Expert Opinions
- ⚖️ Pros & Cons Analysis
- 🔗 Related Topics
- ⭐ Source Credibility Rating

## License

MIT License
