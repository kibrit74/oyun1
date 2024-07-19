from flask import Flask, render_template, request, jsonify
import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Google Generative AI modelini yapılandırma
genai.configure(api_key="AIzaSyBWC2gp-UjhlnGQgM0S77lftXnSl0uhqQ0")

generation_config = {
    "temperature": 0.1,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 5000,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", generation_config=generation_config, safety_settings=safety_settings
)

# Arama ve veri çekme fonksiyonları
async def search_product(page, product_name):
    await page.goto('https://www.google.com/')
    await page.wait_for_selector('textarea[name="q"]')
    await page.fill('textarea[name="q"]', product_name)
    await page.keyboard.press('Enter')
    await page.wait_for_selector('h3')

async def go_to_shopping_tab(page):
    await page.wait_for_selector('a[href*="tbm=shop"]')
    shopping_tab = await page.query_selector('a[href*="tbm=shop"]')
    if shopping_tab:
        await shopping_tab.click()
        await page.wait_for_load_state('networkidle')
        return True
    return False

async def select_second_product(page):
    await page.wait_for_selector('div.sh-dgr__content')
    product_images = await page.query_selector_all('div.sh-dgr__content a')
    if len(product_images) > 3:
        await product_images[1].click()
        await page.wait_for_load_state('networkidle')
        return True
    return False

async def click_link_by_text(page, link_text):
    try:
        await page.wait_for_selector(f'a:has-text("{link_text}")', timeout=20000)
        link = await page.query_selector(f'a:has-text("{link_text}")')
        if link:
            # Doğrudan JavaScript ile tıklama
            await page.evaluate('''(link) => link.click()''', link)
            await page.wait_for_load_state('networkidle')
            return True
    except Exception as e:
        print(f'Failed to click link "{link_text}":', e)
    return False

async def click_button_by_selector(page, selector):
    try:
        await page.wait_for_selector(selector, timeout=20000)
        button = await page.query_selector(selector)
        if button:
            await button.click()
            await page.wait_for_load_state('networkidle')
            return True
    except Exception as e:
        print(f'Failed to click button with selector "{selector}":', e)
    return False

async def scroll_to_bottom(page):
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(2)  # Wait for 2 seconds

async def extract_reviews(page):
    try:
        await page.wait_for_selector('#sh-rol__reviews-cont', timeout=20000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        reviews = soup.select('#sh-rol__reviews-cont > div.z6XoBf.fade-in-animate')
        return reviews
    except Exception as e:
        print("Error extracting reviews:", e)
    return []

def parse_review(review):
    try:
        star = review.find('div', class_='UzThIf').get('aria-label')
        date = review.find('span', class_='less-spaced ff3bE nMkOOb').text
        text = review.find('div', id=lambda x: x and x.endswith('-full')).text
        author = review.find('div', class_='sPPcBf').find_all('span')[-1].text
        return {
            'star': star,
            'date': date,
            'text': text,
            'author': author
        }
    except Exception as e:
        print(f"Failed to parse review:", e)
        return None

async def extract_product_details(page):
    try:
        await page.wait_for_selector('tbody')
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        details = {}
        rows = soup.select('tbody tr.vm91i')
        for row in rows:
            key = row.select_one('div.ipBhab').text.strip()
            value = row.select_one('td.AnDf0c').text.strip()
            details[key] = value
        return details
    except Exception as e:
        print("Error extracting product details:", e)
    return {}

async def main(product_name):
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            await search_product(page, product_name)
            if not await go_to_shopping_tab(page):
                print("Failed to navigate to the shopping tab.")
                return

            if not await select_second_product(page):
                print("Failed to select the second product.")
                return

            if not await click_link_by_text(page, "Ürün ayrıntılarını göster"):
                print("Failed to click 'Ürün ayrıntılarını göster' link.")
                return

            # Click "Tüm yorumlar" link and extract reviews
            if not await click_link_by_text(page, "Tüm yorumlar"):
                print("Failed to click 'Tüm yorumlar' link.")
                return

            all_reviews = []

            # Click "Diğer incelemeler" button 3 times and extract reviews
            for i in range(6):
                await scroll_to_bottom(page)
                if not await click_button_by_selector(page, 'div.sh-btn__background'):
                    print("Failed to click 'Diğer incelemeler' button.")
                    return
                await asyncio.sleep(5)  # Wait for 5 seconds

                reviews = await extract_reviews(page)
                print(f"Çekilen yorum sayısı {len(reviews)} adet.")

                for review in reviews:
                    parsed_review = parse_review(review)
                    if (parsed_review):
                        all_reviews.append(parsed_review)

            # Navigate back to the product details page
            await page.go_back()
            await page.wait_for_load_state('networkidle')

            # Click "Tüm özellikleri görüntüle" link and extract product details
            if not await click_link_by_text(page, "Tüm özellikleri görüntüle"):
                print("Failed to click 'Tüm özellikleri görüntüle' link.")
                return

            product_details = await extract_product_details(page)

            # Save reviews and product details to a JSON file
            data = {
                'reviews': all_reviews,
                'product_details': product_details
            }

            with open('product_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print("Ürün Bilgileri ve Yorumlar Başarıyla kaydedildi.... ")
            return data

        except Exception as e:
            print("An error occurred:", e)
        finally:
            await browser.close()

@app.route("/deneme1")
def deneme1():
    return render_template("deneme1.html")

@app.route("/generate-content", methods=["POST"])
def generate_content():
    try:
        if 'image' not in request.files:
            raise ValueError("No image provided.")

        image = request.files['image']

        if not image:
            raise ValueError("No image provided.")

        image_parts = [{"mime_type": image.mimetype, "data": image.read()}]

        # Burada resimdeki ürünü tanıyan bir model kullanmalısınız
        # Örneğin, image_parts'ı kullanarak ürünü tanıyan bir model çağırabilirsiniz
        # product_name = model_identify_product(image_parts)

        # Örnek olarak, Google Generative AI modelini kullanarak ürünü tanımlayalım
        prompt = "Bu resimdeki ürünü kısa ve öz bir şekilde tanımla. Sadece ürün adı ve kodunu döndür:"
        response = model.generate_content([prompt, image_parts[0]])
        product_name = response.text.strip()

        # Playwright ile ürün bilgilerini ve yorumları çek
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(main(product_name))

        # Modeli çağırarak içerik oluştur
        prompt_parts = [
            f"[Kullanıcının gönderdiği fotoğraftaki ürünü tanımlıyorum]. Ürün adını ve varsa teknik özelliklerini getireceğim. **Ürün yorumlarını analiz et:** Amazon.com.tr, Trendyol.com ve Hepsiburada.com sitelerindeki yorumları inceleyerek, olumlu ve olumsuz görüşleri analiz edip paylaşacağım. Ayrıca, sitelerdeki değerlendirme puanlarını da sunacağım ve kullanıcı yorumlarından çıkan genel eğilimi özetleyeceğim. **Olumlu ve olumsuz yorumları seçerken, Her siteninin değerlendirme puanını getireceğim, Örnek olarak her siteden olumlu ve olumsuz yorumlar getireceğim. yorumların kalitesini ve kullanıcının ürüne verdiği puanı dikkate alacağım. Örnek olsun diye birkaç tane olumlu ve olumsuz yorum getireceğim.** Yorumları her siteden getirip, sonuç kısmında ürünün genel değerlendirmesini yapacağım.Sonuç kısımında daha detaylı değerlendiröe yapacaksın.'",
            f"Ürün Adı: {product_name}",
            " ",
            {"text": json.dumps(data, ensure_ascii=False, indent=4)},
        ]

        response = model.generate_content(prompt_parts)
        return jsonify({"content": response.text})

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)