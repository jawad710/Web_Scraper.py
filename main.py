import requests
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass, asdict
import os
from urllib.parse import urljoin


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
    def __init__(self, sitemap_index_url):
        self.sitemap_index_url = sitemap_index_url

    def get_monthly_sitemaps(self):
        response = requests.get(self.sitemap_index_url)
        soup = BeautifulSoup(response.content, 'xml')
        sitemaps = [loc.text for loc in soup.find_all('loc')]
        return sitemaps

    def get_article_urls(self, sitemap_url):
        response = requests.get(sitemap_url)
        soup = BeautifulSoup(response.content, 'xml')
        urls = [loc.text for loc in soup.find_all('loc')]
        return urls


class ArticleScraper:
    def __init__(self, url):
        self.url = url

    def scrape(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract metadata from the <script> tag containing text/tawsiyat
        script_tag = soup.find('script', text=lambda t: t and 'tawsiyat' in t)
        metadata = json.loads(script_tag.string) if script_tag else {}

        # Extract main article content from <p> tags
        content = ' '.join([p.get_text() for p in soup.find_all('p')])

        return Article(
            url=self.url,
            post_id=self.extract_post_id(),
            title=metadata.get('title', ''),
            keywords=metadata.get('keywords', []),
            thumbnail=metadata.get('thumbnail', ''),
            publication_date=metadata.get('publication_date', ''),
            last_updated_date=metadata.get('last_updated_date', ''),
            author=metadata.get('author', ''),
            content=content
        )

    def extract_post_id(self):
        return self.url.split('-')[-1]


class FileUtility:
    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.filename = f'articles_{self.year}_{self.month}.json'

    def save(self, articles):
        os.makedirs(f'./data/{self.year}', exist_ok=True)
        filepath = f'./data/{self.year}/{self.filename}'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([asdict(article) for article in articles], f, ensure_ascii=False, indent=4)


def main():
    sitemap_index_url = "https://www.almayadeen.net/sitemaps/sitemap.xml"
    parser = SitemapParser(sitemap_index_url)

    # Process each monthly sitemap
    for sitemap_url in parser.get_monthly_sitemaps():
        year, month = sitemap_url.split('-')[-2], sitemap_url.split('-')[-1].replace('.xml', '')
        article_urls = parser.get_article_urls(sitemap_url)

        articles = []
        for url in article_urls:
            scraper = ArticleScraper(url)
            article = scraper.scrape()
            articles.append(article)

        # Save the articles to a JSON file
        file_utility = FileUtility(year, month)
        file_utility.save(articles)


if __name__ == "__main__":
    main()