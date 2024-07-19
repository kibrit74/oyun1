import requests
from bs4 import BeautifulSoup
import json
import time

class TrustpilotScraper:
    def __init__(self):
        self.base_url = "https://www.google.com/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def search_company(self, company_name):
        search_url = f"{self.base_url}/search?query={company_name}"
        response = requests.get(search_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        company_link = soup.select_one('a[data-business-unit-id]')
        if company_link:
            return self.base_url + company_link['href']
        return None

    def get_reviews(self, company_url, num_pages=3):
        all_reviews = []
        for page in range(1, num_pages + 1):
            page_url = f"{company_url}?page={page}"
            response = requests.get(page_url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            reviews = soup.select('article[data-service-review-id]')
            for review in reviews:
                review_data = self.parse_review(review)
                all_reviews.append(review_data)
            
            time.sleep(1)  # Bekleyelim ki siteye çok yük bindirmeyelim
        
        return all_reviews

    def parse_review(self, review):
        rating = review.select_one('div[data-service-review-rating]')['data-service-review-rating']
        title = review.select_one('h2[data-service-review-title-typography]').text.strip()
        content = review.select_one('p[data-service-review-text-typography]').text.strip()
        date = review.select_one('time')['datetime']
        author = review.select_one('span[data-consumer-name-typography]').text.strip()
        
        return {
            'rating': rating,
            'title': title,
            'content': content,
            'date': date,
            'author': author
        }

def get_product_reviews(product_name):
    scraper = TrustpilotScraper()
    
    # Ürün adından şirket adını çıkarmaya çalışalım
    company_name = product_name.split()[0]  # İlk kelimeyi alalım
    
    company_url = scraper.search_company(company_name)
    if not company_url:
        return f"Company not found for product: {product_name}"
    
    reviews = scraper.get_reviews(company_url)
    
    data = {
        'product_name': product_name,
        'company_name': company_name,
        'reviews': reviews
    }
    
    json_filename = f'{product_name.replace(" ", "_")}_reviews.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Reviews saved to {json_filename}")
    
    return data

def get_combined_product_reviews(product_name1, product_name2=None):
    combined_data = {}
    
    combined_data['product1'] = get_product_reviews(product_name1)
    
    if product_name2:
        combined_data['product2'] = get_product_reviews(product_name2)
    
    with open('combined_product_reviews.json', 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=4)
    print("Combined reviews saved to combined_product_reviews.json")
    
    return combined_data

# Kullanım örneği
if __name__ == "__main__":
    result = get_combined_product_reviews("iPhone 14 plus", "Samsung Galaxy S23+")
    print(json.dumps(result, indent=2))