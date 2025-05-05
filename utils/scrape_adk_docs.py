import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, urlparse


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)


def clean_filename(url):
    """Create a clean filename from URL path."""
    # Remove any anchors (#) from the URL
    url_without_anchor = url.split('#')[0]

    path = urlparse(url_without_anchor).path.strip('/')
    if not path:
        return 'index'

    # Replace slashes with underscores for filename
    filename = path.replace('/', '_')
    if '.' in filename:
        filename = filename.rsplit('.', 1)[0]
    return filename


def extract_title(soup):
    """Extract title from page."""
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.text.strip()
    return None


def extract_content_text(soup):
    """Extract main content from page as text."""
    # Look for main content container - adjust selectors based on site structure
    main_content = soup.find('main') or soup.find('div', class_='md-content') or soup.find('article')
    if not main_content:
        main_content = soup.body  # Fallback to body

    # Remove script and style elements
    for script in main_content(["script", "style"]):
        script.extract()

    # Get text and clean it
    text = main_content.get_text()
    # Remove excessive whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text


def should_scrape_url(url, base_url, visited_urls):
    """Determine if a URL should be scraped."""
    # Skip URLs that don't start with the base URL
    if not url.startswith(base_url):
        return False

    # Skip URLs already visited
    if url in visited_urls:
        return False

    # Skip anchor links (same page, different section)
    parsed_url = urlparse(url)
    if parsed_url.fragment:
        # Get the URL without the fragment
        url_without_fragment = url.split('#')[0]
        # If we've already visited the page without the fragment, skip this URL
        if url_without_fragment in visited_urls:
            return False

    return True


def scrape_page(url, html_dir, text_dir, visited_urls, base_url):
    try:
        # Remove any anchors for fetching the page
        fetch_url = url.split('#')[0]

        # Skip if we've already fetched this page
        if fetch_url in visited_urls:
            return []

        print(f"Fetching {fetch_url}")
        response = requests.get(fetch_url)
        if response.status_code != 200:
            print(f"Failed to fetch {fetch_url}: Status code {response.status_code}")
            return []

        visited_urls.add(fetch_url)

        soup = BeautifulSoup(response.text, 'html.parser')
        title = extract_title(soup) or urlparse(fetch_url).path
        content_text = extract_content_text(soup)

        # Create base filename
        base_filename = clean_filename(fetch_url)

        # Save HTML version
        html_filepath = os.path.join(html_dir, f"{base_filename}.html")
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)

        # Save text version
        text_filepath = os.path.join(text_dir, f"{base_filename}.txt")
        with open(text_filepath, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n")
            f.write(f"URL: {fetch_url}\n\n")
            f.write(content_text)

        print(f"Saved {fetch_url} to HTML and TXT formats")

        # Extract links for further scraping
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(fetch_url, href)

            # Filter out URLs we don't want to scrape
            if should_scrape_url(full_url, base_url, visited_urls):
                links.append(full_url)

        return links
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []


def scrape_adk_docs(start_url, docs_dir):
    # Define base URL for filtering
    base_url = start_url

    create_directory(docs_dir)

    # Create subdirectories
    html_dir = os.path.join(docs_dir, "html")
    text_dir = os.path.join(docs_dir, "text")
    create_directory(html_dir)
    create_directory(text_dir)

    visited_urls = set()
    queued_urls = [start_url]

    while queued_urls:
        current_url = queued_urls.pop(0)

        # Skip if we've already processed this exact URL including anchors
        if current_url in visited_urls:
            continue

        new_links = scrape_page(current_url, html_dir, text_dir, visited_urls, base_url)

        time.sleep(0.2)

        # Add new links to the queue
        for link in new_links:
            if link not in visited_urls and link not in queued_urls:
                queued_urls.append(link)

    # Create a consolidated text file for easier reference
    consolidated_path = os.path.join(docs_dir, "adk_docs_consolidated.txt")
    with open(consolidated_path, 'w', encoding='utf-8') as outfile:
        outfile.write("# GOOGLE ADK DOCUMENTATION\n\n")
        outfile.write(f"Source: {start_url}\n\n")

        for filename in sorted(os.listdir(text_dir)):
            if filename.endswith(".txt"):
                filepath = os.path.join(text_dir, filename)
                outfile.write(f"\n\n{'=' * 80}\n\n")
                with open(filepath, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())

    # Create index file with links to all text files
    index_path = os.path.join(docs_dir, "index.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("# Google ADK Documentation Index\n\n")
        f.write("This index contains links to all scraped ADK documentation pages.\n\n")

        for filename in sorted(os.listdir(text_dir)):
            if filename.endswith(".txt"):
                filepath = os.path.join(text_dir, filename)
                # Read the title from the file
                with open(filepath, 'r', encoding='utf-8') as infile:
                    first_line = infile.readline().strip()
                    title = first_line[7:] if first_line.startswith("Title: ") else filename

                relative_path = os.path.relpath(filepath, docs_dir)
                f.write(f"- [{title}]({relative_path})\n")

    print(f"Created index at {index_path}")
    print(f"Created consolidated documentation at {consolidated_path}")


if __name__ == "__main__":
    start_url = "https://google.github.io/adk-docs/"
    docs_dir = "./adk_docs"

    print(f"Starting to scrape {start_url} to {docs_dir}")
    scrape_adk_docs(start_url, docs_dir)
    print("Scraping completed!")