import os
import re
import json
import logging
import asyncio
import aiohttp
from typing import List, Dict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dataclasses import dataclass, field
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Search result with key information and analysis"""
    title: str
    url: str
    description: str = ""
    content: str = ""
    
    # Core analysis
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    quick_facts: List[str] = field(default_factory=list)
    detailed_analysis: str = ""
    
    # Additional insights
    pros_cons: Dict[str, List[str]] = field(default_factory=lambda: {"pros": [], "cons": []})
    expert_opinions: List[str] = field(default_factory=list)
    statistics: List[str] = field(default_factory=list)
    source_credibility: str = ""
    related_topics: List[str] = field(default_factory=list)
    ranking_score: float = 0.0

class WebScraper:
    def __init__(self):
        self.session = aiohttp.ClientSession(headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.setup_selenium()
        self.credible_domains = {
            'edu': 0.9, 'gov': 0.9, 'org': 0.8,
            'wikipedia.org': 0.8, 'github.com': 0.8,
            'medium.com': 0.7, 'forbes.com': 0.8,
            'reuters.com': 0.9, 'bloomberg.com': 0.8
        }

    def setup_selenium(self):
        """Setup Selenium WebDriver"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(10)
            
        except Exception as e:
            logger.error(f"Error setting up Selenium: {e}")
            self.driver = None

    async def search_and_scrape(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Perform search and analysis"""
        try:
            # Get initial results
            search_results = await self.search_google(query, max_results * 2)
            
            # Process results in parallel
            tasks = []
            for result in search_results:
                task = asyncio.create_task(self.process_result(result, query))
                tasks.append(task)
            
            # Gather results
            processed_results = []
            for task in asyncio.as_completed(tasks):
                try:
                    result = await task
                    if result and result.content:
                        processed_results.append(result)
                except Exception as e:
                    logger.error(f"Error processing result: {e}")
            
            # Rank and return results
            ranked_results = self.rank_results(processed_results, query)
            return ranked_results[:max_results]
            
        except Exception as e:
            logger.error(f"Error in search and scrape: {e}")
            return []

    async def process_result(self, result: SearchResult, query: str) -> SearchResult:
        """Process a single result with analysis"""
        try:
            content = await self.scrape_url(result.url)
            if not content:
                return result
            
            result.content = content
            
            # Generate analysis
            result.summary = self.generate_summary(content)
            result.key_points = self.extract_key_points(content)
            result.quick_facts = self.extract_quick_facts(content)
            result.detailed_analysis = self.generate_detailed_analysis(content)
            result.pros_cons = self.analyze_pros_cons(content)
            result.expert_opinions = self.extract_expert_opinions(content)
            result.statistics = self.extract_statistics(content)
            result.source_credibility = self.evaluate_source_credibility(result.url)
            result.related_topics = self.find_related_topics(content, query)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing result: {e}")
            return result

    def rank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Rank results based on relevance and quality"""
        try:
            for result in results:
                score = 0
                # Content relevance (40%)
                score += self.calculate_relevance(query, result) * 0.4
                # Source credibility (30%)
                score += float(result.source_credibility.split()[0]) * 0.3
                # Content richness (30%)
                score += (len(result.key_points) * 0.1 +
                         len(result.statistics) * 0.1 +
                         len(result.expert_opinions) * 0.1)
                
                result.ranking_score = score
            
            return sorted(results, key=lambda x: x.ranking_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error ranking results: {e}")
            return results

    async def search_google(self, query: str, max_results: int) -> List[SearchResult]:
        """Perform Google search and extract basic results"""
        try:
            # Construct search URL
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={max_results}"
            
            # Make request
            async with self.session.get(search_url) as response:
                if response.status != 200:
                    return []
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                results = []
                # Find search result divs
                for div in soup.find_all('div', class_='g'):
                    try:
                        # Extract title and link
                        title_elem = div.select_one('h3')
                        link_elem = div.select_one('a')
                        desc_elem = div.select_one('.VwiC3b, .s3v9rd, .st')
                        
                        if title_elem and link_elem:
                            title = title_elem.get_text()
                            url = link_elem.get('href', '')
                            description = desc_elem.get_text() if desc_elem else ''
                            
                            if url.startswith('http'):
                                results.append(SearchResult(
                                    title=title,
                                    url=url,
                                    description=description
                                ))
                    except Exception as e:
                        logger.error(f"Error extracting search result: {e}")
                        continue
                
                return results[:max_results]
                
        except Exception as e:
            logger.error(f"Error in Google search: {e}")
            return []

    async def scrape_url(self, url: str) -> str:
        """Scrape content from a URL using both regular request and Selenium as fallback"""
        try:
            # Try regular request first
            try:
                async with self.session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        return self.extract_text_content(html_content)
            except Exception:
                pass

            # Try Selenium as fallback
            if self.driver:
                try:
                    self.driver.get(url)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    return self.extract_text_content(self.driver.page_source)
                except Exception:
                    pass
            
            return ""
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            return ""

    def extract_text_content(self, html_content: str) -> str:
        """Extract main text content from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Get all paragraphs and headings
            text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            # Extract and clean text
            content = []
            for elem in text_elements:
                text = elem.get_text().strip()
                if len(text) > 20:  # Filter out short snippets
                    content.append(text)
            
            return '\n\n'.join(content)
            
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return ""

    def generate_summary(self, text: str, max_sentences: int = 5) -> str:
        """Generate a detailed summary by extracting key sentences"""
        try:
            if not text:
                return ""
            
            # Split into sentences
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
            
            if not sentences:
                return ""
            
            # Score sentences based on multiple factors
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                score = 0
                
                # Position score (earlier sentences are more important)
                position_score = 1.0 - (i / len(sentences))
                score += position_score * 0.3
                
                # Length score (prefer medium-length sentences)
                words = len(sentence.split())
                if 10 <= words <= 25:
                    score += 0.3
                elif 25 < words <= 40:
                    score += 0.2
                
                # Information density score (sentences with numbers, proper nouns)
                if re.search(r'\d+', sentence):  # Contains numbers
                    score += 0.2
                if re.search(r'[A-Z][a-z]+', sentence):  # Contains proper nouns
                    score += 0.2
                
                # Key phrase score (sentences with important phrases)
                key_phrases = ['important', 'significant', 'result', 'conclude', 'found', 'show', 'demonstrate', 'reveal']
                if any(phrase in sentence.lower() for phrase in key_phrases):
                    score += 0.2
                
                scored_sentences.append((sentence, score))
            
            # Sort by score and get top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            summary_sentences = [s[0] for s in scored_sentences[:max_sentences]]
            
            # Reorder sentences to maintain original flow
            summary_sentences.sort(key=lambda x: sentences.index(x))
            
            # Join sentences and clean up
            summary = '. '.join(summary_sentences)
            if not summary.endswith('.'):
                summary += '.'
                
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return ""

    def extract_key_points(self, text: str, max_points: int = 5) -> List[str]:
        """Extract key points from the content"""
        try:
            if not text:
                return []

            # Split into sentences
            sentences = [s.strip() for s in re.split(r'[.!?]+', text)]
            
            # Score sentences based on key indicators
            scored_sentences = []
            key_indicators = ['key', 'main', 'important', 'essential', 'crucial', 'primary', 'major']
            
            for sentence in sentences:
                score = 0
                # Check for key indicators
                if any(indicator in sentence.lower() for indicator in key_indicators):
                    score += 0.5
                # Check for numbers or statistics
                if re.search(r'\d+%', sentence.lower()):
                    score += 0.3
                # Check for comparison words
                if any(word in sentence.lower() for word in ['more', 'less', 'better', 'worse', 'increase', 'decrease']):
                    score += 0.2
                
                scored_sentences.append((sentence, score))
            
            # Get top scoring sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            key_points = [f"• {s[0]}" for s in scored_sentences[:max_points]]
            
            return key_points

        except Exception as e:
            logger.error(f"Error extracting key points: {e}")
            return []

    def extract_quick_facts(self, text: str, max_facts: int = 5) -> List[str]:
        """Extract quick facts from the content"""
        try:
            if not text:
                return []

            facts = []
            # Look for sentences with numbers, dates, or specific patterns
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
            
            for sentence in sentences:
                # Check for numerical facts
                if re.search(r'\d+', sentence):
                    facts.append(f"📊 {sentence}")
                # Check for dates
                elif re.search(r'\b\d{4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b', sentence):
                    facts.append(f"📅 {sentence}")
                # Check for definitions
                elif ' is ' in sentence.lower() and len(sentence.split()) < 20:
                    facts.append(f"💡 {sentence}")
                
                if len(facts) >= max_facts:
                    break
            
            return facts

        except Exception as e:
            logger.error(f"Error extracting quick facts: {e}")
            return []

    def generate_detailed_analysis(self, text: str, max_length: int = 500) -> str:
        """Generate a detailed analysis of the content"""
        try:
            if not text:
                return ""

            # Split into paragraphs
            paragraphs = text.split('\n')
            
            # Look for paragraphs with analytical content
            analysis_parts = []
            
            for para in paragraphs:
                # Skip short paragraphs
                if len(para.split()) < 10:
                    continue
                
                # Look for analytical indicators
                indicators = ['analysis', 'research', 'study', 'findings', 'conclusion', 'results', 'suggests', 'indicates']
                if any(indicator in para.lower() for indicator in indicators):
                    analysis_parts.append(para)
            
            if not analysis_parts:
                # Fallback to regular paragraphs
                analysis_parts = [p for p in paragraphs if len(p.split()) >= 20][:2]
            
            # Combine and truncate
            analysis = ' '.join(analysis_parts)
            if len(analysis) > max_length:
                analysis = analysis[:max_length] + '...'
            
            return analysis

        except Exception as e:
            logger.error(f"Error generating detailed analysis: {e}")
            return ""

    def analyze_pros_cons(self, text: str) -> Dict[str, List[str]]:
        """Extract pros and cons from content"""
        try:
            pros = []
            cons = []
            sentences = [s.strip() for s in re.split(r'[.!?]+', text)]
            
            # Keywords indicating advantages/disadvantages
            pro_indicators = ['advantage', 'benefit', 'pro', 'positive', 'good', 'better', 'best', 'improve']
            con_indicators = ['disadvantage', 'drawback', 'con', 'negative', 'bad', 'worse', 'worst', 'problem']
            
            for sentence in sentences:
                lower_sent = sentence.lower()
                # Check for pros
                if any(indicator in lower_sent for indicator in pro_indicators):
                    pros.append(f"✅ {sentence}")
                # Check for cons
                elif any(indicator in lower_sent for indicator in con_indicators):
                    cons.append(f"❌ {sentence}")
            
            return {"pros": pros[:5], "cons": cons[:5]}
        except Exception as e:
            logger.error(f"Error analyzing pros/cons: {e}")
            return {"pros": [], "cons": []}

    def find_related_topics(self, text: str, query: str) -> List[str]:
        """Find related topics and themes"""
        try:
            # Extract noun phrases and key terms
            words = text.lower().split()
            query_terms = query.lower().split()
            
            # Find related terms using context
            related = set()
            for i, word in enumerate(words):
                if word in query_terms:
                    # Get surrounding context
                    start = max(0, i - 3)
                    end = min(len(words), i + 4)
                    context = words[start:end]
                    # Add potential related terms
                    related.update(w for w in context if len(w) > 4 and w not in query_terms)
            
            return [f"🔗 {topic.title()}" for topic in list(related)[:5]]
        except Exception as e:
            logger.error(f"Error finding related topics: {e}")
            return []

    def extract_expert_opinions(self, text: str) -> List[str]:
        """Extract expert opinions and quotes"""
        try:
            opinions = []
            sentences = [s.strip() for s in re.split(r'[.!?]+', text)]
            
            expert_indicators = [
                'according to', 'says', 'said', 'states', 'suggests',
                'research shows', 'studies indicate', 'experts'
            ]
            
            for sentence in sentences:
                if any(indicator in sentence.lower() for indicator in expert_indicators):
                    if len(sentence.split()) > 10:  # Ensure it's a substantial quote
                        opinions.append(f"👨‍🔬 {sentence}")
            
            return opinions[:5]
        except Exception as e:
            logger.error(f"Error extracting expert opinions: {e}")
            return []

    def extract_statistics(self, text: str) -> List[str]:
        """Extract statistical information"""
        try:
            stats = []
            sentences = [s.strip() for s in re.split(r'[.!?]+', text)]
            
            for sentence in sentences:
                # Look for percentages
                if re.search(r'\d+%', sentence):
                    stats.append(f"📊 {sentence}")
                # Look for numerical comparisons
                elif re.search(r'\d+\s*(?:times|percent|fold|million|billion|thousand)', sentence.lower()):
                    stats.append(f"📈 {sentence}")
                # Look for dates with numbers
                elif re.search(r'\b\d{4}\b', sentence):
                    stats.append(f"📅 {sentence}")
            
            return stats[:5]
        except Exception as e:
            logger.error(f"Error extracting statistics: {e}")
            return []

    def evaluate_source_credibility(self, url: str) -> str:
        """Evaluate the credibility of the source"""
        try:
            domain = urllib.parse.urlparse(url).netloc.lower()
            
            # Check domain extension
            score = 0.5  # Default score
            for key, value in self.credible_domains.items():
                if key in domain:
                    score = max(score, value)
            
            # Convert score to description
            if score >= 0.9:
                return f"{score:.1f} - Highly Credible Source"
            elif score >= 0.7:
                return f"{score:.1f} - Credible Source"
            elif score >= 0.5:
                return f"{score:.1f} - Moderate Credibility"
            else:
                return f"{score:.1f} - Exercise Caution"
                
        except Exception as e:
            logger.error(f"Error evaluating source credibility: {e}")
            return "0.5 - Credibility Unknown"

    def calculate_relevance(self, query: str, result: SearchResult) -> float:
        """Calculate the relevance of a result to the query"""
        try:
            query_terms = query.lower().split()
            result_terms = result.title.lower().split() + result.description.lower().split()
            
            common_terms = set(query_terms) & set(result_terms)
            relevance = len(common_terms) / len(query_terms)
            
            return relevance
        except Exception as e:
            logger.error(f"Error calculating relevance: {e}")
            return 0.0

async def main():
    scraper = WebScraper()
    try:
        print("\n🔍 Welcome to the Advanced Search Bot!")
        print("Type 'exit' to quit\n")
        
        while True:
            query = input("Enter your search query: ").strip()
            if query.lower() == 'exit':
                print("\nGoodbye! 👋")
                break
                
            if not query:
                print("Please enter a valid search query")
                continue
                
            print("\nSearching... 🔍")
            results = await scraper.search_and_scrape(query)
            
            if not results:
                print("\n❌ No results found. Try a different search query.")
                continue
            
            print("\n📚 Search Results:")
            print("=" * 80)
            
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.title}")
                print(f"URL: {result.url}")
                print(f"Source Credibility: {result.source_credibility}")
                
                if result.summary:
                    print("\n📝 Summary:")
                    print(result.summary)
                
                if result.key_points:
                    print("\n🎯 Key Points:")
                    for point in result.key_points:
                        print(f"• {point}")
                
                if result.statistics:
                    print("\n📊 Statistics:")
                    for stat in result.statistics:
                        print(f"• {stat}")
                
                if result.expert_opinions:
                    print("\n👨‍🔬 Expert Opinions:")
                    for opinion in result.expert_opinions:
                        print(f"• {opinion}")
                
                if result.pros_cons["pros"] or result.pros_cons["cons"]:
                    print("\n⚖️ Pros & Cons:")
                    if result.pros_cons["pros"]:
                        print("✅ Advantages:")
                        for pro in result.pros_cons["pros"]:
                            print(f"  • {pro}")
                    if result.pros_cons["cons"]:
                        print("❌ Disadvantages:")
                        for con in result.pros_cons["cons"]:
                            print(f"  • {con}")
                
                if result.related_topics:
                    print("\n🔗 Related Topics:")
                    for topic in result.related_topics:
                        print(f"• {topic}")
                
                print("-" * 80)
            
            print("\nSearch completed! Type another query or 'exit' to quit.\n")
            
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print("\n❌ An error occurred. Please try again.")
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())