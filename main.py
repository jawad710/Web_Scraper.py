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
    def __init__(self, base_url, years):
        self.base_url = base_url
        self.years = years

    def get_monthly_sitemaps(self):
        sitemaps = []
        for year in self.years:
            for month in range(1, 13):  # Loop through all months
                month_str = f"{month:02d}"  # Format month as two digits
                sitemap_url = f"{self.base_url}/sitemap-{year}-{month_str}.xml"
                sitemaps.append(sitemap_url)
        return sitemaps

    def get_article_urls(self, sitemap_url):
        response = requests.get(sitemap_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            urls = [loc.text for loc in soup.find_all('loc')]
            return urls
        else:
            return []


class ArticleScraper:
    def __init__(self, url):
        self.url = url

    def scrape(self):
        response = requests.get(self.url)
        if response.status_code == 200 :

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
        else:
            return None

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
    sitemap_index_url = "https://www.almayadeen.net/sitemaps/sitemap.xml"
    years=[2020,2021,2022,2023,2024]
    parser = SitemapParser(sitemap_index_url,years)
    total_articles = 0
    max_articles = 10000

    try:
        # Process each monthly sitemap
        for sitemap_url in parser.get_monthly_sitemaps():
            if total_articles >= max_articles:
                print(f"Reached the limit of {max_articles} articles.")
                break

            year, month = sitemap_url.split('-')[-2], sitemap_url.split('-')[-1].replace('.xml', '')
            article_urls = parser.get_article_urls(sitemap_url)

            print(f"Found {len(article_urls)} articles.")

            articles = []
            for url in article_urls:
                if total_articles >= max_articles:
                    break
                scraper = ArticleScraper(url)
                article = scraper.scrape()
                if article:
                    articles.append(article)
                    total_articles += 1

            # Save the articles to a JSON file
            FileUtility.save(articles)
            print(f"Saved {len(articles)} articles to {FileUtility.filename}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()