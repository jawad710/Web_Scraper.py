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

        script_tag = soup.find('script', string=lambda t: t and 'tawsiyat' in t)  # Updated to use 'string'

        metadata = {}

        if script_tag:
            try:
                metadata = json.loads(script_tag.string)  # Parse JSON if valid
            except json.JSONDecodeError:
                print(f"Warning: Failed to parse JSON for article {self.url}")

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
    def __init__(self):
        pass

    @staticmethod
    def save(articles, year, month):
        if not articles:
            print("No articles to save.")
            return
        directory = f'./data/{year}'
        os.makedirs(directory, exist_ok=True)
        filepath = f'{directory}/articles_{year}_{month}.json'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([asdict(article) for article in articles], f, ensure_ascii=False, indent=4)
        print(f"Saved {len(articles)} articles to {filepath}")

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

            if not article_urls:  # Updated to handle case where no articles are found
                print("No articles found.")
                continue

            print(f"Found {len(article_urls)} articles.")

            articles = []
            for url in article_urls:
                if total_articles >= max_articles:
                    break
                scraper = ArticleScraper(url)
                article = scraper.scrape()
                articles.append(article)
                total_articles += 1

            # Save the articles to a JSON file
            if articles:
                file_utility = FileUtility(year, month)
                file_utility.save(articles)
                print(f"Saved {len(articles)} articles to {file_utility.filename}")
                print(f"Processed {len(articles)} articles for {year}-{month}. Total so far: {total_articles}")

            if total_articles >= max_articles:
                print(f"Reached {max_articles} articles. Stopping.")
                break

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()