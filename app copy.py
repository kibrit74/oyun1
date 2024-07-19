from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import google.generativeai as genai
from forms.your_forms import YourForm
from flask_login import UserMixin, login_user, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from flask_login import UserMixin, current_user
from flask_login import login_user, logout_user, current_user
import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtubesearchpython import VideosSearch
from google.api_core.exceptions import InternalServerError
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtubesearchpython import VideosSearch

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'gizli_ananiz'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

login_manager.login_message_category = 'info'

admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')


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


class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    search_query = db.Column(db.String(255), nullable=False)
    response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def get_response_for_query(cls, user_id, search_query):
        result = cls.query.filter_by(user_id=user_id, search_query=search_query).first()
        return result.response if result else None

    def __repr__(self):
        return f"<SearchHistory(user_id={self.user_id}, search_query='{self.search_query}', created_at={self.created_at})>"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

def toplam_soru_sayisi(self):
        return Soru.query.filter_by(soru_sahibi_id=self.id).count()
   

class Soru(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    soru_icerik = db.Column(db.String(255), nullable=False)
    soru_sahibi_adi = db.Column(db.String(255), default="Misafir")
    soru_sahibi_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cevaplar = db.relationship('Cevap', back_populates='soru', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    

    def __init__(self, soru_icerik, soru_sahibi_adi):
        self.soru_icerik = soru_icerik
        self.soru_sahibi_adi = soru_sahibi_adi

@staticmethod
def toplam_soru_sayisi():
    return Soru.query.count()


# Cevap Modeli (Örnek)
class Cevap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cevap_icerik = db.Column(db.Text, nullable=False)
    cevap_sahibi_adi = db.Column(db.String(255))
    soru_id = db.Column(db.Integer, db.ForeignKey('soru.id'), nullable=False)
    soru = db.relationship('Soru', back_populates='cevaplar', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, cevap_icerik, cevap_sahibi_adi, soru_id):
        self.cevap_icerik = cevap_icerik
        self.cevap_sahibi_adi = cevap_sahibi_adi
        self.soru_id = soru_id


class TextContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

class UserView(ModelView):
    can_delete = False
    can_create = False
    can_edit = False
    column_exclude_list = ["password"]
    form_columns = ["username", "email", "is_admin"]

# Admin panosuna modelleri ekledik
admin.add_view(UserView(User, db.session))
admin.add_view(ModelView(Soru, db.session))
admin.add_view(ModelView(Cevap, db.session))

# Veritabanını oluşturduk
with app.app_context():
    db.create_all()
    

@app.route('/user_login')
def user_login():
    # Giriş işlemleri
    return render_template('login.html')
@login_manager.user_loader
def load_user(user_id):
    try:
        user_id = int(user_id)
        user = db.session.query(User).get(user_id)

        if user:
            return user
        else:
            print(f"Kullanıcı bulunamadı: {user_id}")
            return None
    except Exception as e:
        print(f"Hata: {e}")
        return None


@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # E-posta adresinin boş olup olmadığını kontrol et
        if not email:
            flash('Geçerli bir e-posta adresi giriniz.', 'danger')
            return redirect(url_for('admin_register'))

        # E-posta adresinin veritabanında zaten var olup olmadığını kontrol et
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta adresi zaten kullanımda.', 'danger')
            return redirect(url_for('admin_register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(username=username, email=email, password=hashed_password, is_admin=True)
        db.session.add(new_user)
        db.session.commit()

        flash('Başarıyla kayıt oldunuz! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))

    return render_template('admin_register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim izniniz yok.', 'danger')
        return redirect(url_for('profil'))

    # Giriş yapan kullanıcının arama geçmişi
    user_search_history = SearchHistory.query.filter_by(user_id=current_user.id).all()

    # Giriş yapan kullanıcının toplam arama sayısı
    user_total_searches = len(user_search_history)

    # Tüm kullanıcılar
    users = User.query.all()
    
    # Toplam üye sayısı
    total_users = len(users)
    
    # Toplam arama geçmişi sayısı
    total_search_history = len(SearchHistory.query.all())

    # Kullanıcı bazında arama sayıları
    user_search_counts = {}
    for user in users:
        user_search_counts[user.id] = len(SearchHistory.query.filter_by(user_id=user.id).all())

    # Son 1 Haftadaki Üye Sayısı
    one_week_ago = datetime.now() - timedelta(days=7)
    new_users_last_week = User.query.filter(User.created_at >= one_week_ago).count()
    # Toplam soru soran kullanıcı sayısı
    total_soru_users = len(Soru.query.filter(Soru.soru_sahibi_adi.isnot(None)).distinct(Soru.soru_sahibi_adi).all())

    # Toplam misafir kullanıcı sayısı ("Misafir" adıyla gösterilen kullanıcılar)
    total_misafir_users = len(Soru.query.filter_by(soru_sahibi_adi="Misafir").all())
    kullanici_sorulari = Soru.query.filter_by(soru_sahibi_id=current_user.id).count()
    toplam_soru_sayisi_last_week = toplam_soru_sayisi_son_hafta()

    return render_template(
        'dashboard.html',
        users=users,
        user_search_history=user_search_history,
        total_users=total_users,
        total_search_history=total_search_history,
        user_total_searches=user_total_searches,
        user_search_counts=user_search_counts,
        new_users_last_week=new_users_last_week,
        toplam_soru_sayisi=total_soru_users,
        soru_adisahibi_adi=total_misafir_users,
        kullanici_sorulari=kullanici_sorulari,toplam_soru_sayisi_last_week=toplam_soru_sayisi_last_week
    )
    

@app.route('/your_route')
def your_route():
    # Son bir hafta içinde üye olanları bul
    current_date = datetime.now()
    last_week = current_date - timedelta(days=7)
    new_users_last_week_count = User.query.filter(User.created_at >= last_week).count()

    # Diğer bilgileri al (örneğin toplam kullanıcı sayısı)
    total_users = User.query.count()
    user_total_searches = 42  # Bu değeri kendi veritabanınıza göre ayarlayın

    # Tüm kullanıcıları alabilirsiniz, veya başka bir kritere göre sorgu yapabilirsiniz
    all_users = User.query.all()
    toplam_soru_sayisi = Soru.toplam_soru_sayisi()
    soru_sahibi_adi=soru_sahibi_adi()
    # Diğer bilgileri render_template'e geçirerek HTML sayfanıza gönderin
    return render_template('your_template.html', total_users=total_users, user_total_searches=user_total_searches, new_users_last_week_count=new_users_last_week_count, all_users=all_users,toplam_soru_sayisi=toplam_soru_sayisi, soru_sahibi_adi=soru_sahibi_adi)


@app.route('/editor', methods=['GET', 'POST'])
def editor():
    # TinyMCE'den gelen metni işleyin
    if request.method == 'POST':
        new_text = request.form.get('content', '')
        # Veritabanına kaydedin veya güncelleyin
        text_content = TextContent.query.first()
        if text_content:
            text_content.content = new_text
        else:
            new_content = TextContent(content=new_text)
            db.session.add(new_content)
            db.session.commit()
        return redirect(url_for('editor'))

    # Metin editörü sayfasını görüntüleyin
    text_content = TextContent.query.first()
    current_text = text_content.content if text_content else ''
    
    return render_template('editor.html', current_text=current_text)

@app.route('/user_details/<int:user_id>')
@login_required
def user_details(user_id):
    selected_user = User.query.get(user_id)
    if selected_user:
        user_search_history = SearchHistory.query.filter_by(user_id=user_id).all()
        
        # Kullanıcı bazında arama sayıları
        users = User.query.all()
        user_search_counts = {}
        for user in users:
            user_search_counts[user.id] = len(SearchHistory.query.filter_by(user_id=user.id).all())

        return render_template('detail.html', user=selected_user, search_history=user_search_history, user_search_counts=user_search_counts)
    else:
        flash('Invalid user ID.')
        return redirect(url_for('dashboard'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        
        if user and bcrypt.check_password_hash(user.password, password):

            login_user(user)
            flash('Başarıyla giriş yaptınız!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))

        else:
            flash('Kullanıcı adı veya şifre hatalı. Lütfen tekrar deneyin.', 'danger')

    return render_template('login.html')

@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    # Sileceğimiz kullanıcıyı çek
    user_to_delete = User.query.get(user_id)

    # Kullanıcıyı veritabanından sil
    db.session.delete(user_to_delete)
    db.session.commit()

    return redirect(url_for('dashboard'))

# Arama geçmişi kaydetme fonksiyonu
def save_search_history(username, search_query, response):
    user = User.query.filter_by(username=username).first()
    if user:
        new_search_history = SearchHistory(
            user_id=user.id,
            search_query=search_query,
            response=response,
        )
        db.session.add(new_search_history)
        db.session.commit()
    else:
        print(f"User {username} not found.")
def save_search_history_with_app_context(app, username, search_query, response):
    with app.app_context():
        save_search_history(username, search_query, response)

@app.route('/admin')
@login_required
def admin():
    # Sadece giriş yapmış kullanıcılar admin sayfasına erişebilir
    if current_user.is_authenticated:
        return render_template('admin.html')
    else:
        # Kullanıcı giriş yapmamışsa, 'login' sayfasına yönlendir
        return redirect(url_for('dashboard'))

# Ana sayfa
@app.route('/')
def index():
    # Burada mevcut metni veritabanından çekin
    text_content = TextContent.query.first()
    current_text = text_content.content if text_content else ''
    return render_template('index.html', current_text=current_text)

# Kullanıcı adını getirme endpoint'i
@app.route('/get-username')
def get_username():
    user = session.get('user')
    if user:
        return jsonify({"username": user})
    else:
        return jsonify({"error": "Kullanıcı adı bulunamadı."})

@app.route('/process_users', methods=['POST'])
def process_users():
    action = request.form.get('action')

    if action == 'delete':
        selected_users = request.form.getlist('selected_users')

        # Silme işlemini gerçekleştiren bir delete_user fonksiyonunuz olduğunu varsayalım
        for user_id in selected_users:
            delete_user(user_id)

        flash('Seçilen kullanıcılar başarıyla silindi.', 'success')
    elif action == 'details':
        # Detayları görüntüleme işlemini gerçekleştirin
        pass
    else:
        flash('Geçersiz işlem.', 'error')

    return redirect(url_for('dashboard'))

# Profil sayfası
@app.route('/profil')
def profil():
    user = session.get('user')
    user_info = User.query.filter_by(username=user).first()
    return render_template('profil.html', user=user)

@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    user = session.get('user')
    user_info = User.query.filter_by(username=user).first()

    if user:
        return redirect('/index')

    error_message = None

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_repeat = request.form.get('password_repeat')

        # Mevcut kullanıcıları kontrol et
        existing_user = User.query.filter(db.or_(User.username == username, User.email == email)).first()

        if existing_user:
            # Kullanıcı zaten varsa hata mesajını ayarla
            error_message = "Bu kullanıcı adı veya email adresi zaten mevcut."
        elif password != password_repeat:
            error_message = "Şifreler uyuşmuyor."
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect('/giris')

    return render_template('kayit.html', user=user, error_message=error_message)


# Giriş sayfası
@app.route('/giris', methods=['GET', 'POST'])
def giris():
    user = session.get('user')
    user_info = User.query.filter_by(username=user).first()
    error_message = None

    if user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user'] = username
            return redirect(url_for('profildata'))
        else:
            error_message = "Kullanıcı adı veya şifre hatalı."

    return render_template('giris.html', error_message=error_message, user=user)

# Kayıt sayfasına yönlendirme
@app.route('/register')
def register():
    return render_template('admin_register.html')

@app.route('/soru', methods=['GET', 'POST'])
def soru():
    user = session.get('user')
    user_info = User.query.filter_by(username=user).first()

    if request.method == 'POST':
        # Ürün arama formundan gelen veriyi al
        search_query = request.form.get('search_query')

        # Eğer arama sorgusu varsa, ürün aramasını yap
        if search_query:
            # Simulate AI model response
            model_response = generate_model_response(search_query)

            # Kaydetme işlemi
            save_search_history(user, search_query, model_response)

            # Ürün listesini ve arama sorgusunu şablonla paylaş
            return render_template('arama_sonuclari.html', search_query=search_query, response=model_response)

    return render_template('soru.html', user=user)

def generate_model_response(search_query):
    # This function should call the AI model to get the response
    # For now, we simulate it with a placeholder response
    return f"Simulated response for '{search_query}'"

# Karşılaştırma sayfası
@app.route('/karsi')
def karsi():
    return render_template('karsi.html')



async def search_product(page, product_name):
    await page.goto('https://www.google.com/')
    await page.fill('textarea[name="q"]', product_name)
    await page.keyboard.press('Enter')
    await page.wait_for_selector('h3')

async def go_to_shopping_tab(page):
    shopping_tab = await page.query_selector('a[href*="tbm=shop"]')
    if shopping_tab:
        await shopping_tab.click()
        await page.wait_for_load_state('networkidle')
        return True
    return False

async def select_product_and_get_details(page, max_attempts=5):
    await page.wait_for_selector('div.sh-dgr__content')
    product_images = await page.query_selector_all('div.sh-dgr__content a')
    
    for i in range(min(len(product_images), max_attempts)):
        try:
            await product_images[i].click()
            await page.wait_for_load_state('networkidle')
            
            # Ürün detayları için muhtemel seçiciler
            detail_selectors = [
                'a:has-text("Ürün ayrıntılarını göster")',
                'div[role="button"]:has-text("Ürün ayrıntılarını göster")',
                'div._-pA > div',
                '#rso > div.sh-sr__shop-result-group > div:nth-child(2) > div > div > div > div > div._-pP > div > div > div._-oY > div._-o0._-oZ > div._-pK > div > a'
            ]
            
            for selector in detail_selectors:
                try:
                    print(f"'{selector}' seçicisi deneniyor...")
                    
                    # Elementin varlığını ve görünürlüğünü kontrol et
                    is_visible = await page.evaluate(f'''
                        () => {{
                            const element = document.querySelector("{selector}");
                            if (element) {{
                                const style = window.getComputedStyle(element);
                                return style && style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                            }}
                            return false;
                        }}
                    ''')
                    
                    if not is_visible:
                        print(f"'{selector}' elementi görünür değil, sonraki seçici deneniyor...")
                        continue
                    
                    # Farklı tıklama yöntemleri dene
                    click_methods = [
                        lambda: page.click(selector),
                        lambda: page.click(selector, force=True),
                        lambda: page.evaluate(f'document.querySelector("{selector}").click()'),
                        lambda: page.evaluate(f'document.querySelector("{selector}").dispatchEvent(new MouseEvent("click", {{bubbles: true}}))'),
                    ]
                    
                    for click_method in click_methods:
                        try:
                            await click_method()
                            await page.wait_for_load_state('networkidle')
                            print(f"'{selector}' elementine başarıyla tıklandı.")
                            
                            # Ürün ayrıntılarının yüklendiğini kontrol et
                            if await page.query_selector('table.D9issd'):
                                print("Ürün ayrıntıları tablosu başarıyla yüklendi.")
                                return True
                            else:
                                print("Ürün ayrıntıları tablosu yüklenemedi, sonraki tıklama yöntemi deneniyor...")
                        except Exception as click_error:
                            print(f"Tıklama hatası: {click_error}")
                    
                except Exception as selector_error:
                    print(f"Seçici hatası: {selector_error}")
            
            print(f"Ürün ayrıntıları bulunamadı (Ürün {i+1})")
            
            if i < min(len(product_images), max_attempts) - 1:
                print("Sonraki ürüne geçiliyor...")
                await page.go_back()
                await page.wait_for_load_state('networkidle')
            else:
                print("Tüm ürünler denendi, detay linki bulunamadı.")
        
        except Exception as e:
            print(f"Ürün seçiminde hata: {str(e)}")
    
    return False


async def click_element(page, selector, timeout=5000):
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        await page.click(selector)
        await page.wait_for_load_state('networkidle')
        return True
    except:
        print(f"'{selector}' elementi tıklanamadı.")
        return False

async def scroll_to_bottom(page):
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(2)

async def extract_reviews(page):
    content = await page.content()
    soup = BeautifulSoup(content, 'html.parser')
    return soup.select('#sh-rol__reviews-cont > div.z6XoBf.fade-in-animate')

def parse_review(review):
    try:
        return {
            'star': review.find('div', class_='UzThIf').get('aria-label'),
            'date': review.find('span', class_='less-spaced ff3bE nMkOOb').text,
            'text': review.find('div', id=lambda x: x and x.endswith('-full')).text,
            'author': review.find('div', class_='sPPcBf').find_all('span')[-1].text
        }
    except Exception as e:
        print(f"Yorumu parse ederken hata oluştu:", e)
        return None

async def extract_product_details(page):
    content = await page.content()
    soup = BeautifulSoup(content, 'html.parser')
    details = {}
    rows = soup.select('tbody tr')
    for row in rows:
        key_elem = row.select_one('td:first-child')
        value_elem = row.select_one('td:nth-child(2)')
        if key_elem and value_elem:
            key = key_elem.text.strip()
            value = value_elem.text.strip()
            details[key] = value
    return details

async def extract_rating(page):
    try:
        rating_selector = 'div.uYNZm, div[data-ved] div.EbPs6b'
        rating_element = await page.query_selector(rating_selector)
        if rating_element:
            rating = await rating_element.inner_text()
            rating = ''.join(filter(lambda x: x.isdigit() or x == '.', rating))
            return rating.strip()
        else:
            print("Değerlendirme puanı elementi bulunamadı")
            return "Değerlendirme puanı bulunamadı"
    except Exception as e:
        print(f"Değerlendirme puanı alınırken hata oluştu: {e}")
        return "Değerlendirme puanı alınamadı"


        return []

async def search_video_and_get_transcript(query):
    try:
        search_query = f"{query} review"
        videos_search = VideosSearch(search_query, limit=1)
        results = videos_search.result()
        
        if not results['result']:
            return None, None, "Video bulunamadı"
        
        video_id = results['result'][0]['id']
        print(f"Bulunan video: {video_id}, aranan: {search_query}")
        
        transcript, error = await get_transcript(video_id, ['tr', 'en'])
        
        if not transcript:
            transcript, error = await get_available_transcript(video_id)
        
        if not transcript:
            print(f"Video için transkript bulunamadı: {video_id}")
        
        return video_id, transcript, error
    except Exception as e:
        print(f"Video arama hatası: {str(e)}")
        return None, None, f"Video arama hatası: {str(e)}"

async def get_transcript(video_id, language_codes):
    try:
        transcript = await asyncio.to_thread(YouTubeTranscriptApi.get_transcript, video_id, languages=language_codes)
        return transcript, None
    except Exception as e:
        return None, str(e)

async def get_available_transcript(video_id):
    try:
        transcript_list = await asyncio.to_thread(YouTubeTranscriptApi.list_transcripts, video_id)
        for transcript in transcript_list:
            return await asyncio.to_thread(transcript.fetch), None
    except Exception as e:
        return None, f"Hiçbir dilde transkript bulunamadı: {str(e)}"

import os


async def process_product(page, product_name):
    await search_product(page, product_name)
    if not await go_to_shopping_tab(page):
        return {"error": "Alışveriş sekmesine geçiş yapılamadı."}
    if not await select_product_and_get_details(page):
        return {"error": "Ürün detayları bulunamadı."}

    rating = await extract_rating(page)
    product_details = {'rating': rating}

    all_reviews = []
    if await click_element(page, 'a:has-text("Tüm yorumlar")'):
        for _ in range(3):
            await scroll_to_bottom(page)
            reviews = await extract_reviews(page)
            for review in reviews:
                parsed_review = parse_review(review)
                if parsed_review and parsed_review not in all_reviews:
                    all_reviews.append(parsed_review)
            if not await click_element(page, 'div.sh-btn__background'):
                break

    await page.go_back()
    await page.wait_for_load_state('networkidle')

    if await click_element(page, 'a:has-text("Tüm özellikleri görüntüle")'):
        additional_details = await extract_product_details(page)
        product_details.update(additional_details)

   

    video_id, transcript, youtube_error = await search_video_and_get_transcript(product_name)

    return {
        'reviews': all_reviews,
        'product_details': product_details,
        
        'youtube_data': {
            'video_id': video_id,
            'transcript': transcript,
            'error': youtube_error
        }
    }

async def main(product_name, product_index=1):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            data = await process_product(page, product_name)

            if data.get('reviews') or data.get('product_details'):
                json_filename = f'product{product_index}.json'
                print(f"Veriler {json_filename} dosyasına kaydediliyor")
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print(f"Ürün Bilgileri ve Yorumlar Başarıyla {json_filename} dosyasına kaydedildi.")
                return json_filename
            else:
                print("Kaydedilecek veri yok.")
                return f"Aranan ürün: {product_name}"

        except Exception as e:
            print("Bir hata oluştu:", e)
            return f"Bir hata oluştu: {e}"
        finally:
            await browser.close()


    
  
@app.route("/compare-content", methods=["POST"])
async def compare_content():
    try:
        if 'image1' not in request.files or 'image2' not in request.files:
            app.logger.error("Two images are required.")
            return jsonify({"error": "Two images are required."}), 400

        image1 = request.files['image1']
        image2 = request.files['image2']
        product_name_input1 = request.form.get('product_name1', '').strip()
        product_name_input2 = request.form.get('product_name2', '').strip()

        if not image1 or not image2:
            app.logger.error("One or both images are missing.")
            return jsonify({"error": "Two images are required."}), 400

        image_parts1 = [{"mime_type": image1.mimetype, "data": image1.read()}]
        image_parts2 = [{"mime_type": image2.mimetype, "data": image2.read()}]

        prompt1 = f"Match the product in this image with the name or code '{product_name_input1}' and identify the product. Only write the product name clearly suitable for product search." if product_name_input1 else "Identify the product in this image and only write the product name clearly suitable for product search."
        prompt2 = f"Match the product in this image with the name or code '{product_name_input2}' and identify the product. Only write the product name clearly suitable for product search." if product_name_input2 else "Identify the product in this image and only write the product name clearly suitable for product search."

        loop = asyncio.get_event_loop()
        response1 = await loop.run_in_executor(executor, partial(model.generate_content, [prompt1, image_parts1[0]]))
        response2 = await loop.run_in_executor(executor, partial(model.generate_content, [prompt2, image_parts2[0]]))

        product_desc1 = ''.join([part.text for part in response1.candidates[0].content.parts])
        product_desc2 = ''.join([part.text for part in response2.candidates[0].content.parts])

        product_name1 = product_name_input1 or product_desc1.split('\n')[0]
        product_name2 = product_name_input2 or product_desc2.split('\n')[0]

        combined_data = await get_combined_product_data(product_name1, product_name2)

        if 'product1' not in combined_data or 'product2' not in combined_data:
            app.logger.error(f"Missing product data in combined_data: {combined_data}")
            return jsonify({"error": "Birleştirilmiş veride ürün bilgileri eksik."}), 500

        comparison_prompt = f"""
            Bu iki ürünü detaylı bir şekilde karşılaştırın:
            Ürün 1: {product_desc1}
            Google Verileri: {json.dumps(combined_data['product1'].get('google_data', {}), ensure_ascii=False)}
            Ürün 2: {product_desc2}
            Google Verileri: {json.dumps(combined_data['product2'].get('google_data', {}), ensure_ascii=False)}
            YouTube Karşılaştırma Verileri: {json.dumps(combined_data.get('youtube_data', {}), ensure_ascii=False)}
            Lütfen aşağıdaki kriterlere göre kapsamlı bir karşılaştırma yapın:

            [Your existing comparison criteria here]
            """
        
        comparison_response = await loop.run_in_executor(executor, partial(model.generate_content, [comparison_prompt]))
        comparison_text = ''.join([part.text for part in comparison_response.candidates[0].content.parts])

        username = session.get('user')
        await loop.run_in_executor(
            executor, 
            partial(save_search_history_with_app_context, current_app._get_current_object(), username, "", comparison_text)
        )

        return jsonify({"content": comparison_text, "combined_data": combined_data})

    except Exception as e:
        app.logger.error(f"An error occurred in compare_content: {str(e)}", exc_info=True)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
        
def get_combined_product_data(product_name1, image_path1, product_name2=None, image_path2=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        
        try:
            combined_data = {}
            
            page = context.new_page()
            data1 = process_product(page, product_name1, image_path1)
            combined_data['product1'] = {
                'name': product_name1,
                'data': data1
            }
            
            if product_name2 and image_path2:
                data2 = process_product(page, product_name2, image_path2)
                combined_data['product2'] = {
                    'name': product_name2,
                    'data': data2
                }
            
            return combined_data
        
        except Exception as e:
            print(f"get_combined_product_data fonksiyonunda bir hata oluştu: {e}")
            return {"error": str(e)}
        finally:
            browser.close()

# Make sure to add these imports at the top of your file
import asyncio
from flask import current_app
from concurrent.futures import ThreadPoolExecutor
from functools import partial

# And add this to your app initialization
executor = ThreadPoolExecutor(max_workers=3)


       


@app.route("/generate-content", methods=["POST"])
async def generate_content():
    try:
        if 'image' not in request.files or not request.files['image']:
            raise ValueError("Bir resim dosyası gereklidir.")

        image = request.files['image']
        product_name_input = request.form.get('product_name', '').strip()

        if not image:
            raise ValueError("Bir resim dosyası gereklidir.")

        image_parts = [{"mime_type": image.mimetype, "data": image.read()}]

        if product_name_input:
            prompt = f"Bu resimdeki ürünü '{product_name_input}' adı veya koduyla eşleştirin ve kısaca açıklayın."
            product_name = product_name_input
        else:
            prompt = "Bu resimdeki ürünü tanımlayın ve sadece ürün adını net bir şekilde ürün aramasına uygun şekilde yazın."
            response = await asyncio.to_thread(model.generate_content, [prompt, image_parts[0]])
            product_name = ''.join([part.text for part in response.candidates[0].content.parts]).strip()

        # Google araması yap
        try:
            result = await main(product_name)
            if isinstance(result, dict):
                google_data = result.get('google_data', {})
            elif isinstance(result, str) and result.endswith('.json'):
                with open(result, 'r', encoding='utf-8') as f:
                    google_data = json.load(f)
            else:
                google_data = {}
        except Exception as e:
            app.logger.warning(f"{product_name} için Google arama sonuçları alınamadı: {str(e)}")
            google_data = {}

        # YouTube video ve transkript araması yap
        try:
            video_id, transcript, error = await search_video_and_get_transcript(product_name)
            youtube_data = {'video_id': video_id, 'transcript': transcript} if not error else None
            
            if transcript:
                output_file = f"{video_id}.json"
                output_dir = r'C:\Users\seyma\OneDrive\Masaüstü\oyuncak\static\transcripts'
                os.makedirs(output_dir, exist_ok=True)
                file_path = os.path.join(output_dir, output_file)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(transcript, f, ensure_ascii=False, indent=4)
                
                app.logger.info(f"{file_path} adlı transkript kaydedildi.")
        except Exception as e:
            app.logger.error(f"YouTube verileri alınırken hata oluştu: {str(e)}")
            youtube_data = None

        # Tüm verileri topla
        all_data = {
            'google_data': google_data,
            'youtube_data': youtube_data
        }

        # Prompt parçalarını hazırla ve içerik oluştur
        prompt_parts = [
            f"""
Kullanıcının gönderdiği fotoğraftaki ürünü analiz et ve aşağıdaki başlıklar altında detaylı bir rapor hazırla:
Ürün Adı: {product_name}

Lütfen aşağıdaki kriterlere göre kapsamlı bir karşılaştırma yapın:

            Özellikler ve Teknik Detaylar:

             ürünün temel özelliklerini listeleyip .
            Teknik özelliklerdeki vurgulayın. rünün kendine özgü veya yenilikçi özelliklerini belirtin.


            Performans ve Kullanım:

            Ürünün performansını (hız, verimlilik, dayanıklılık vb.).
            Kullanım kolaylığı ve kullanıcı deneyimi açısından değerlendirin.


            Tasarım ve Estetik:

            Fiziksel özellikleri, boyutları ve ağırlıkları karşılaştırın.
            Estetik açıdan değerlendirme yapın ve hedef kitlenin tercihlerini göz önünde bulundurun.


            Kullanıcı Yorumları ve Değerlendirmeleri:

            Google verilerinden elde edilen kullanıcı yorumlarını ve puanlarını analiz edin.
            Yaygın olumlu ve olumsuz görüşleri özetleyin.
            Varsa, profesyonel değerlendirmeleri veya uzman görüşlerini dahil edin.

            YouTube İçeriği Analizi:

            YouTube transkriptinden elde edilen bilgileri kullanarak ürün hakkındaki görüşleri özetleyin.
            Video içeriğinde vurgulanan önemli noktaları belirtin.
            Varsa, YouTube içerik üreticisinin tercihini veya önerisini belirtin.

            Hedef Kitle ve Kullanım Alanları:

            ürünün hangi kullanıcı grubuna veya kullanım senaryosuna daha uygun olduğunu belirtin.

            Marka İtibarı ve Güvenilirlik:

            Markaların pazar konumunu ve itibarını karşılaştırın.
            Garanti, müşteri hizmetleri ve satış sonrası destek konularını değerlendirin.


            Genel Değerlendirme ve Öneri:

            Tüm bu faktörleri göz önünde bulundurarak, hangi ürünün hangi tür kullanıcılar için daha uygun olduğuna dair genel bir değerlendirme yapın.
            Farklı öncelikler veya ihtiyaçlar için hangi ürünün tercih edilebileceğini belirtin.



            Not: Eğer YouTube verilerinin alınmasında herhangi bir hata oluştuysa, lütfen bunu kısaca belirtin ve analizinizi mevcut verilere dayanarak yapın.
            Lütfen bu karşılaştırmayı objektif, dengeli ve bilgilendirici bir şekilde yapın. Varsa belirsiz noktaları veya ek araştırma gerektiren alanları da belirtin.
            """,
            {"text": json.dumps(all_data, ensure_ascii=False, indent=4)}
        ]

        # İçeriği oluştur
        response = await asyncio.to_thread(model.generate_content, prompt_parts)
        response_text = ''.join([part.text for part in response.candidates[0].content.parts])

        # Kullanıcı oturumunu al ve arama geçmişini kaydet
        username = session.get('user')
        await asyncio.to_thread(save_search_history, username, "", response_text)
        
        return jsonify({"content": response_text})

    except Exception as e:
        app.logger.error(f"Bir hata oluştu: {str(e)}", exc_info=True)
        return jsonify({"error": f"Bir hata oluştu: {str(e)}"}), 500


# Profil ve arama geçmişi sayfası
@app.route('/profildata', methods=['GET', 'POST'])
def profildata():
    username = session.get('user')
    if not username:
        flash('Lütfen önce giriş yapın.')
        return redirect(url_for('kayit'))

    user_info = User.query.filter_by(username=username).first()
    if not user_info:
        flash('Kullanıcı bilgileri bulunamadı.')
        return redirect(url_for('kayit'))

    user_search_history = SearchHistory.query.filter_by(user_id=user_info.id).order_by(SearchHistory.created_at.desc()).limit(5).all()
    last_search_response = user_search_history[-1].response if user_search_history else ''
    total_searches = len(user_search_history)
    recent_search_summaries = [{'query': history.search_query, 'response': history.response} for history in user_search_history]
    all_searches = SearchHistory.query.filter_by(user_id=user_info.id).order_by(SearchHistory.created_at.desc()).all()
    search_query = request.form.get('search_query', '')
    form = YourForm()

    if request.method == 'POST':
        if search_query:
            new_search_history = SearchHistory(
                user_id=user_info.id,
                search_query=search_query,
                response="Arama sonuçları burada...", 
            )
            db.session.add(new_search_history)
            db.session.commit()

            search_result = {'search_query': search_query, 'other_data': ''}
            return render_template('profildata.html', user_search_history=user_search_history,
                                   user=user_info, response=last_search_response,
                                   recent_search_summaries=recent_search_summaries,
                                   all_searches=all_searches, total_searches=total_searches, form=form,
                                   search_query=search_query,
                                   search_result=search_result)

    return render_template('profildata.html', user_search_history=user_search_history,
                           user=user_info, response=last_search_response,
                           recent_search_summaries=recent_search_summaries,
                           all_searches=all_searches, total_searches=total_searches, form=form,
                           search_query=search_query)
# Örnek: Veritabanından arama geçmişini kaldıran bir işlev
def delete_search_from_history(user_id, search_id):
    # user_id parametresi kullanıcının kimliğini belirtir
    # search_id parametresi silinecek aramanın kimliğini belirtir
    # Burada veritabanınıza veya depolama mekanizmanıza göre uygun silme işlemlerini gerçekleştirin
    # Örneğin SQLAlchemy kullanılıyorsa:
    search_to_delete = SearchHistory.query.filter_by(user_id=user_id, id=search_id).first()
    if search_to_delete:
        db.session.delete(search_to_delete)
        db.session.commit()
    
       
@app.route('/delete_search', methods=['POST'])
def delete_search():
    user_id = request.form.get('user_id')
    search_id = request.form.get('search_id')

    # Burada kullanıcı kimliği ve silinecek arama kimliği alınır ve delete_search_from_history
    # fonksiyonu çağrılarak arama geçmişi güncellenir
    delete_search_from_history(user_id, search_id)

    return jsonify({'success': True})

@app.route('/sss1')
def sss1():
    # Giriş işlemleri
    return render_template('sss1.html')


sayfa_boyutu = 20

@app.route('/sss', methods=['GET', 'POST'])
def sss():
    sorular = Soru.query.all()
    cevaplar = Cevap.query.all()

    # Görünen toplam soru ve cevap sayısını hesaplayın
    toplam_soru_ve_cevap = len(sorular) + len(cevaplar)

    # Daha fazla göster linki için bir bayrak
    daha_fazla_goster = False

    gosterilen_soru_sayisi = sayfa_boyutu  # sayfa_boyutu'nu gosterilen_soru_sayisi olarak başlatın

    if request.method == 'POST':
        soru_icerik = request.form.get('soru_icerik')
        soru_sahibi_adi = request.form.get('soru_sahibi_adi', default="Misafir")
        cevap_icerik = request.form.get('cevap_icerik')

        if not soru_icerik:
            flash('Soru içeriği boş olamaz.', 'error')
            return redirect(url_for('sss'))

        yeni_soru = Soru(soru_icerik=soru_icerik, soru_sahibi_adi=soru_sahibi_adi)
        db.session.add(yeni_soru)
        db.session.commit()

        # Eğer cevap içeriği girilmişse ve soru eklenmişse
        if cevap_icerik and yeni_soru:
            yeni_cevap = Cevap(cevap_icerik=cevap_icerik, soru_id=yeni_soru.id, cevap_sahibi_adi=soru_sahibi_adi)
            db.session.add(yeni_cevap)
            db.session.commit()
        elif cevap_icerik:
            flash('Cevap eklemek için önce bir soru sorun.', 'error')

        # Yeniden sorgu yaparak güncellenmiş soru listesini al
        sorular = Soru.query.all()

    # Sayfa boyutu tanımlanması

    # Toplam görünen soru ve cevap sayısı, şu ana kadar gösterilen sayfa sayısının
    # (sayfa_boyutu * sayfa_numarasi) kadar olmalıdır.
    if gosterilen_soru_sayisi < toplam_soru_ve_cevap:
        daha_fazla_goster = True

    return render_template('sss.html', sorular=sorular, cevaplar=cevaplar, current_user=current_user, daha_fazla_goster=daha_fazla_goster, gosterilen_soru_sayisi=gosterilen_soru_sayisi)

from flask import jsonify, redirect, url_for

@app.route('/cevap_ver/<int:soru_id>', methods=['POST'])
def cevap_ver(soru_id):
    selected_soru = Soru.query.get(soru_id)

    if request.method == 'POST':
        if 'user' in session:
            cevap_sahibi_adi = session['user']
        else:
            cevap_sahibi_adi = request.form.get('cevap_sahibi_adi')

        cevap_icerik = request.form.get('cevap_icerik')

        if not cevap_icerik:
            print('Hata: Cevap içeriği boş olamaz.')
            return jsonify({'success': False, 'message': 'Cevap içeriği boş olamaz.'})

        if len(cevap_icerik) > 1000:
            print('Hata: Cevap içeriği 1000 karakteri geçemez.')
            return jsonify({'success': False, 'message': 'Cevap içeriği 1000 karakteri geçemez.'})

        yeni_cevap = Cevap(cevap_icerik=cevap_icerik, soru_id=soru_id, cevap_sahibi_adi=cevap_sahibi_adi)

        db.session.add(yeni_cevap)
        db.session.commit()

    sorular = Soru.query.all()
    cevaplar = Cevap.query.all()
    return render_template('sss.html', sorular=sorular, cevaplar=cevaplar, current_user=current_user)


@app.route('/soru_sor', methods=['POST'])
def soru_sor():
    if request.method == 'POST':
        soru_icerik = request.form.get('soru_icerik')

        # Kullanıcı girişi yapılmış mı kontrol et
        if 'user' in session:
            soru_sahibi_adi = session['user']  # Eğer oturum varsa, kullanıcının adını al
        else:
            soru_sahibi_adi = request.form.get('soru_sahibi_adi')
            # Eğer oturum yoksa, formdan gelen soru_sahibi_adi'yi kullan

            # Kullanıcı adı girilmemişse hata mesajı ver ve işlemi durdur
            if not soru_sahibi_adi:
                flash('Kullanıcı adı boş olamaz.', 'danger')
                return redirect(url_for('sss'))

        if soru_icerik:
            yeni_soru = Soru(soru_icerik=soru_icerik, soru_sahibi_adi=soru_sahibi_adi)
            db.session.add(yeni_soru)
            db.session.commit()

            return redirect(url_for('sss'))

        flash('Soru içerik boş olamaz.', 'danger')

    # Soruları güncel al
    sorular = Soru.query.all()
    cevaplar = Cevap.query.all()

    return render_template('sss.html', sorular=sorular, cevaplar=cevaplar, current_user=current_user)

@app.route('/soru_sil/<int:soru_id>', methods=['GET'])
def soru_sil(soru_id):
    soru = Soru.query.get_or_404(soru_id)

    # Kullanıcı girişi yapılmış mı kontrol et
    if 'user' in session:
        soru_sahibi_adi = session['user']  # Eğer oturum varsa, kullanıcının adını al
        if soru.user.username == soru_sahibi_adi:
            db.session.delete(soru)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Soru silindi.'})
        else:
            return jsonify({'success': False, 'message': 'Bu işlemi gerçekleştirmek için yetkiniz yok.'})
    else:
        return jsonify({'success': False, 'message': 'Kullanıcı oturumu yok.'})
    
def toplam_soru_sayisi_son_hafta():
    one_week_ago = datetime.now() - timedelta(days=7)
    return Soru.query.filter(
        Soru.created_at >= one_week_ago
    ).count()


def get_user_question_counts(users):
    user_question_counts = {}
    for user in users:
        question_count = Soru.query.filter_by(soru_sahibi_id=user.id).count()
        user_question_counts[user.id] = question_count
    return user_question_counts


@app.route('/cikis')
def cikis():
    session.pop('user', None)
    return redirect('/')
@app.route('/logout')
@login_required
def logout():
    logout_user()  # Flask-Login ile kullanıcıyı çıkış yaptırın
    session.pop('user', None)
    session.pop('admin_username', None)
    return redirect(url_for('login'))


if __name__ == "__main__":


    app.run(debug=True)
    