import os

import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()

os.environ["REQUEST_CA_BUNDLE"] = certifi.where()

from playwright.sync_api import sync_playwright

from bs4 import BeautifulSoup

import re


def clean(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)  # collapse excess newlines

    text = re.sub(r'[ \t]{2,}', ' ', text)  # collapse spaces

    text = re.sub(r'(Previous|Next)\s*$', '', text, flags=re.MULTILINE)  # strip nav

    return text.strip()


with sync_playwright() as p:
    request_context = p.request.new_context(base_url=", ignore_https_errors=True)

    response = request_context.get(
        "/en/cloud/saas/analytics/26r1/faiae/prerequisites-fusion-erp-analytics.html#GUID-9500DE59-BD65-4F0D-A7AD-326FB60E7253")

    html_content = response.text()

    soup = BeautifulSoup(html_content, 'html.parser')

    page_title = soup.find("title").text

    print(f"Webpage title ={page_title}")

    sections = soup.find_all('div', class_='sect2')

    for section in sections:

        heading = section.find(['h2', 'h3'])

        body = section.find('div', class_='section')

        if heading and body:
            print(f"## {heading.get_text(strip=True)}")

            print(clean(body.get_text(strip=True)))

            print("---")

    request_context.dispose()

