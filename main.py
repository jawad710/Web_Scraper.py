import requests
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass, asdict
import os


@dataclass
class Article:
    url: str
    post_id: str
    title: str
    keywords: list
    thumbnail: str
    publication_date: str
    last_updated_date: str
    author: str
    content: str


class SitemapParser:
    def __init__(self, start_year, end_year):
        self.start_year = start_year
        self.end_year = end_year

    def generate_sitemap_urls(self):
        sitemap_urls = []
        for year in range(self.start_year, self.end_year + 1):
            for month in range(1, 13):
                sitemap_url = f"https://www.almayadeen.net/sitemaps/all/sitemap-{year}-{month}.xml"
                sitemap_urls.append(sitemap_url)
        return sitemap_urls

    def get_article_urls(self, sitemap_url):
        try:
            print(f"Fetching sitemap: {sitemap_url}")
            response = requests.get(sitemap_url)
            response.raise_for_status()  # Raise an error for HTTP issues
            soup = BeautifulSoup(response.content, 'xml')
            urls = [loc.text for loc in soup.find_all('loc')]
            print(f"Found {len(urls)} articles in sitemap.")
            return urls
        except Exception as e:
            print(f"Error fetching sitemap {sitemap_url}: {e}")
            return []


class ArticleScraper:
    def __init__(self, url):
        self.url = url

    def scrape(self):
        try:
            print(f"Scraping article: {self.url}")
            response = requests.get(self.url)
            response.raise_for_status()  # Raise an error for HTTP issues
            soup = BeautifulSoup(response.content, 'html.parser')

            # Check if the page has a recognizable structure for an article
            article_content = soup.find_all('p')
            if not article_content:
                print(f"Skipping non-article page: {self.url}")
                return None

            # Initialize metadata dictionary
            metadata = {}

            # Try to extract JSON-LD metadata
            json_ld_script = soup.find('script', type='application/ld+json')
            if json_ld_script:
                try:
                    metadata = json.loads(json_ld_script.string)
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to parse JSON-LD for article {self.url}. Error: {e}")
                    print(f"Raw JSON data: {json_ld_script.string}")

            # If JSON-LD is not found, check for meta tags
            if not metadata:
                metadata = {
                    'title': soup.find('meta', attrs={'property': 'og:title'})['content'] if soup.find('meta', attrs={'property': 'og:title'}) else 'No Title',
                    'keywords': soup.find('meta', attrs={'name': 'keywords'})['content'].split(',') if soup.find('meta', attrs={'name': 'keywords'}) else [],
                    'thumbnail': soup.find('meta', attrs={'property': 'og:image'})['content'] if soup.find('meta', attrs={'property': 'og:image'}) else 'No Thumbnail',
                    'publication_date': soup.find('meta', attrs={'property': 'article:published_time'})['content'] if soup.find('meta', attrs={'property': 'article:published_time'}) else 'No Date',
                    'last_updated_date': soup.find('meta', attrs={'property': 'article:modified_time'})['content'] if soup.find('meta', attrs={'property': 'article:modified_time'}) else 'No Date',
                    'author': soup.find('meta', attrs={'name': 'author'})['content'] if soup.find('meta', attrs={'name': 'author'}) else 'No Author'
                }

            # Extract main article content from <p> tags
            content = ' '.join([p.get_text() for p in article_content])

            return Article(
                url=self.url,
                post_id=self.extract_post_id(),
                title=metadata.get('title', 'No Title'),
                keywords=metadata.get('keywords', []),
                thumbnail=metadata.get('thumbnail', 'No Thumbnail'),
                publication_date=metadata.get('publication_date', 'No Date'),
                last_updated_date=metadata.get('last_updated_date', 'No Date'),
                author=metadata.get('author', 'No Author'),
                content=content
            )
        except Exception as e:
            print(f"Error scraping article {self.url}: {e}")
            return None

    def extract_post_id(self):
        return self.url.split('-')[-1]


class FileUtility:
    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.directory = f'./data/{self.year}_{self.month}'
        os.makedirs(self.directory, exist_ok=True)

    def save_article(self, article):
        if not article:
            print("No article to save.")
            return
        filename = f'{self.directory}/article_{article.post_id}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(article), f, ensure_ascii=False, indent=4)
        print(f"Saved article to {filename}")


def main():
    start_year = 2020
    end_year = 2024
    max_articles = 10000
    total_articles = 0
    parser = SitemapParser(start_year, end_year)
    sitemap_urls = parser.generate_sitemap_urls()

    try:
        # Process each monthly sitemap
        for sitemap_url in sitemap_urls:
            print(f"Processing sitemap: {sitemap_url}")
            year, month = sitemap_url.split('-')[-2], sitemap_url.split('-')[-1].replace('.xml', '')
            article_urls = parser.get_article_urls(sitemap_url)

            if not article_urls:
                print("No articles found.")
                continue

            print(f"Found {len(article_urls)} articles.")

            file_utility = FileUtility(year, month)
            for url in article_urls:
                if total_articles >= max_articles:
                    break
                scraper = ArticleScraper(url)
                article = scraper.scrape()
                if article:  # Only save valid articles
                    file_utility.save_article(article)
                    total_articles += 1

            print(f"Processed {len(article_urls)} articles for {year}-{month}. Total so far: {total_articles}")

            if total_articles >= max_articles:
                print(f"Reached {max_articles} articles. Stopping.")
                break

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
