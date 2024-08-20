import requests
from bs4 import BeautifulSoup
import json
from dataclasses import dataclass, asdict
import os
import re
from datetime import datetime


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
    video_duration: str
    word_count: int
    classes: list  # Added to store classes metadata


class SitemapParser:
    def __init__(self):
        self.current_date = datetime.now()

    def generate_sitemap_urls(self):
        sitemap_urls = []
        year = 2020
        month =11

        while year > 2010:  # Arbitrary cutoff year to stop
            sitemap_url = f"https://www.almayadeen.net/sitemaps/all/sitemap-{year}-{month:02}.xml"
            sitemap_urls.append(sitemap_url)

            # Move to the previous month
            month -= 1
            if month == 0:
                month = 12
                year -= 1

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

            # Ensure the page contains the "tawsiyat-metadata" script
            script_tag = soup.find('script', {'id': 'tawsiyat-metadata', 'type': 'text/tawsiyat'})
            if not script_tag:
                print(f"Skipping non-article page (no 'tawsiyat' metadata): {self.url}")
                return None

            try:
                metadata = json.loads(script_tag.string)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse JSON-LD for article {self.url}. Error: {e}")
                return None

            # Extract main article content from <p> tags
            content = ' '.join([p.get_text() for p in soup.find_all('p')])
            word_count = len(content.split())

            return Article(
                url=self.url,
                post_id=metadata.get('postid', 'No Post ID'),
                title=metadata.get('title', 'No Title'),
                keywords=metadata.get('keywords', []),
                thumbnail=metadata.get('thumbnail', 'No Thumbnail'),
                publication_date=metadata.get('published_time', 'No Date'),
                last_updated_date=metadata.get('last_updated', 'No Date'),
                author=metadata.get('author', 'No Author'),
                content=content,
                video_duration=metadata.get('video_duration', None),
                word_count=word_count,
                classes=metadata.get('classes', [])  # Extracting classes metadata
            )
        except Exception as e:
            print(f"Error scraping article {self.url}: {e}")
            return None


class FileUtility:
    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.directory = f'./data/{self.year}_{self.month}'
        os.makedirs(self.directory, exist_ok=True)

    def sanitize_filename(self, name):
        # Remove any characters that aren't alphanumeric or basic punctuation
        return re.sub(r'[<>:"/\\|?*]+', '', name)

    def save_article(self, article):
        if not article:
            print("No article to save.")
            return
        sanitized_post_id = self.sanitize_filename(article.post_id)
        filename = f'{self.directory}/article_{sanitized_post_id}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(article), f, ensure_ascii=False, indent=4)
        print(f"Saved article to {filename}")


def main():
    max_articles = 2000
    total_articles = 0
    parser = SitemapParser()
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
                    print(f"Processed article {total_articles}/{max_articles}")

            print(f"Processed {len(article_urls)} articles for {year}-{month}. Total so far: {total_articles}")

            if total_articles >= max_articles:
                print(f"Reached {max_articles} articles. Stopping.")
                break

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
