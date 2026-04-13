from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import pickle
from datetime import datetime
from blockchain import Blockchain
import os
import google.generativeai as genai


#load
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['DATABASE'] = os.getenv("DATABASE")
app.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER")

# ✅ Initialize database (IMPORTANT FIX)
with app.app_context():
    init_db()

api_key = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

genai.configure(api_key=api_key)
model = genai.GenerativeModel(MODEL_NAME)

# Initialize blockchain
blockchain = Blockchain()


# Load ML models
with open('ml_models/sentiment_model.pkl', 'rb') as f:
    sentiment_model, sentiment_vectorizer = pickle.load(f)

with open('ml_models/fake_news_model.pkl', 'rb') as f:
    fake_news_model, fake_news_vectorizer = pickle.load(f)

# Database connection
def get_db():
    
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db  

# Initialize database
def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                reporter_id INTEGER NOT NULL,
                sentiment TEXT,
                is_fake BOOLEAN,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                blockchain_hash TEXT,
                FOREIGN KEY (reporter_id) REFERENCES users (id)
            )
        ''')
        try:
            db.execute('ALTER TABLE news ADD COLUMN detailed_analysis TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        db.commit()

# Helper functions
def analyze_sentiment(text):
    if sentiment_model:
        # Use existing ML model if available
        processed_text = text.lower()
        vectorized = sentiment_vectorizer.transform([processed_text])
        prediction = sentiment_model.predict(vectorized)[0]
        
        if isinstance(prediction, str):
            return prediction.lower()
        elif isinstance(prediction, (int, float)):
            return 'positive' if prediction == 1 else 'negative'
        else:
            return 'negative'
    else:
        # Use Gemini AI for sentiment analysis
        prompt = f"""
        Analyze the sentiment of the following news text and respond with only one word: 'positive' or 'negative'.
        
        Text: {text}
        
        Consider the overall tone, language, and emotional impact. Respond with only 'positive' or 'negative'.
        """
        
        try:
            response = genai.GenerativeModel(MODEL_NAME).generate_content(prompt)
            ai_text = response.candidates[0].content.parts[0].text.lower()
            ai_response = response.text.strip().lower()
            if 'positive' in ai_response:
                return 'positive'
            elif 'negative' in ai_response:
                return 'negative'
            else:
                return 'negative'  # Default to negative if unclear
        except Exception as e:
            print(f"Gemini sentiment error: {e}")
            return 'negative'
def detect_fake_news(text):
    """
    Enhanced fake news detection using real-time fact checking with Gemini AI
    """
    prompt = f"""
    ACT as a professional fact-checker and news verification expert. 
    Analyze the following news claim and determine if it's TRUE or FALSE based on current, verifiable information.

    NEWS CLAIM: "{text}"

    Please follow these steps:
    1. Analyze the claim for logical consistency and plausibility
    2. Consider if this matches known facts and current events
    3. Check for common fake news patterns (exaggeration, missing context, impossible claims)
    4. Provide your assessment

    IMPORTANT: 
    - Base your analysis on current knowledge up to 2024
    - If the claim is about future events (beyond 2024), consider it unverifiable
    - If the claim contradicts established facts, mark it as likely fake
    - Be conservative - when in doubt, flag for human review

    Respond in this EXACT JSON format:
    {{
        "is_fake": true/false,
        "confidence": "high/medium/low",
        "reasoning": "Brief explanation of your assessment",
        "verification_status": "verified_false/unverifiable/plausible/verified_true"
    }}

    Only respond with the JSON object, nothing else.
    """

    try:
        response = model.generate_content(prompt)

        # ✅ Correct variable
        ai_response = response.candidates[0].content.parts[0].text.strip()
        print(f"Raw Gemini response: {ai_response}")

        # -------- JSON PARSING --------
        import json

        cleaned_response = ai_response

        # Remove markdown blocks if present
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.replace("```json", "").replace("```", "")
        cleaned_response = cleaned_response.strip()

        try:
            result = json.loads(cleaned_response)
            print(f"Parsed fake news detection result: {result}")

            # Extract safely
            is_fake = bool(result.get("is_fake", False))
            confidence = result.get("confidence", "low").lower()
            verification_status = result.get("verification_status", "unverifiable")

            print(
                f"Extracted → is_fake={is_fake}, "
                f"confidence={confidence}, "
                f"verification_status={verification_status}"
            )

            # -------- DECISION LOGIC (UNCHANGED INTENT) --------
            if verification_status == "verified_false":
                return True
            elif confidence == "high" and is_fake:
                return True
            elif confidence == "medium" and is_fake:
                return True
            else:
                return False

        except json.JSONDecodeError as e:
            print("JSON Decode Error:", e)
            print("Fallback analysis activated")

            response_lower = ai_response.lower()

            fake_indicators = [
                "fake", "false", "untrue", "incorrect",
                "fabricated", "not true", "misinformation"
            ]
            true_indicators = [
                "true", "real", "accurate",
                "correct", "verified_true"
            ]

            fake_count = sum(word in response_lower for word in fake_indicators)
            true_count = sum(word in response_lower for word in true_indicators)

            if fake_count > true_count:
                print("Fallback result: flagged as fake")
                return True
            else:
                print("Fallback result: not flagged as fake")
                return False

    except Exception as e:
        print(f"Gemini fake news detection error: {e}")
        return False  # Conservative default

def detailed_fact_check(text):
    """
    Get detailed fact-checking analysis for admin review
    """
    prompt = f"""
    You are a professional fact-checker. Analyze this news claim in detail:

    "{text}"

    Provide a comprehensive fact-check report including:

    1. **Claim Analysis**: Break down the key claims in the statement
    2. **Fact Check**: Verify each claim against known information
    3. **Evidence Assessment**: What evidence would be needed to verify this?
    4. **Context Analysis**: Is this plausible given current knowledge?
    5. **Final Verdict**: TRUE, FALSE, or UNVERIFIABLE
    6. **Explanation**: Detailed reasoning for your verdict
    7. **Recommendation**: Should this be published? (YES/NO/REVIEW)

    Format your response clearly with headings for each section.
    """
    
    try:
        response = client.models.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Fact-check analysis unavailable. Error: {e}"
def get_detailed_analysis(text):
    """Get detailed analysis from Gemini for admin review"""
    prompt = f"""
    Provide a detailed analysis of this news article for content moderation:
    
    TITLE: Please analyze this news content
    CONTENT: {text}
    
    Please provide:
    1. Sentiment Analysis (Positive/Negative/Neutral)
    2. Likelihood of being Fake News (High/Medium/Low)
    3. Key reasons for your assessment
    4. Recommended action (Approve/Review/Reject)
    
    Format your response clearly with these sections.
    """
    
    try:
        response = client.models.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Analysis unavailable. Error: {e}"

def add_to_blockchain(news_id, title, content):
    data = f"{news_id}:{title}:{content}"
    return blockchain.add_block(data)

# Routes
@app.route('/')
def index():
    db = get_db()
    news = db.execute('''
        SELECT news.*, users.username 
        FROM news 
        JOIN users ON news.reporter_id = users.id 
        WHERE status = 'approved'
        ORDER BY created_at DESC
        LIMIT 10
    ''').fetchall()
    return render_template('index.html', news=news)

@app.route('/news/<int:news_id>')
def news_detail(news_id):
    db = get_db()
    article = db.execute('''
        SELECT news.*, users.username 
        FROM news 
        JOIN users ON news.reporter_id = users.id 
        WHERE news.id = ?
    ''', (news_id,)).fetchone()
    
    # Verify blockchain
    is_verified = False
    if article['blockchain_hash']:
        block = blockchain.get_block_by_hash(article['blockchain_hash'])
        if block:
            stored_data = f"{article['id']}:{article['title']}:{article['content']}"
            is_verified = (block.data == stored_data)
    
    return render_template('news_detail.html', article=article, is_verified=is_verified)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        db = get_db()
        try:
            db.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), role)
            )
            db.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'reporter':
                return redirect(url_for('reporter_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    db = get_db()
    pending_news = db.execute('''
        SELECT news.*, users.username 
        FROM news 
        JOIN users ON news.reporter_id = users.id 
        WHERE status = 'pending'
        ORDER BY created_at DESC
    ''').fetchall()
    
    return render_template('admin.html', pending_news=pending_news)

@app.route('/admin/approve/<int:news_id>')
def approve_news(news_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    db = get_db()
    news = db.execute('SELECT * FROM news WHERE id = ?', (news_id,)).fetchone()
    
    if news:
        # Only add to blockchain if not fake or if admin explicitly approves fake news
        block_hash = add_to_blockchain(news['id'], news['title'], news['content'])
        
        db.execute(
            'UPDATE news SET status = "approved", blockchain_hash = ?, is_fake = 0 WHERE id = ?',
            (block_hash, news_id)
        )
        db.commit()
        flash('News approved and added to blockchain!', 'success')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:news_id>')
def reject_news(news_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    db = get_db()
    db.execute('UPDATE news SET status = "rejected" WHERE id = ?', (news_id,))
    db.commit()
    flash('News rejected.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/reporter/dashboard')
def reporter_dashboard():
    if 'user_id' not in session or session['role'] != 'reporter':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    db = get_db()
    my_news = db.execute('''
        SELECT * FROM news 
        WHERE reporter_id = ?
        ORDER BY created_at DESC
    ''', (session['user_id'],)).fetchall()
    
    return render_template('reporter.html', news=my_news)
@app.route('/reporter/submit', methods=['GET', 'POST'])
def submit_news():
    if 'user_id' not in session or session['role'] != 'reporter':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        print(f"Analyzing news: {title}")  # Debug
        
        # Analyze with enhanced models
        sentiment = analyze_sentiment(content)
        is_fake = detect_fake_news(f"{title}. {content}")  # Combine title and content for better analysis
        
        print(f"Sentiment: {sentiment}")  # Debug
        print(f"Is fake: {is_fake}")  # Debug
        
        # Get detailed fact-check for admin (only if flagged or for transparency)
        detailed_analysis = ""
        if is_fake or sentiment == 'negative':
            detailed_analysis = detailed_fact_check(f"{title}. {content}")
        
        # Enhanced status determination
        status = 'pending'
        if not is_fake and sentiment == 'positive':
            status = 'auto_approved'
        elif is_fake:
            status = 'pending'
            flash('Potential fake news detected - submitted for admin review.', 'warning')
        else:
            status = 'pending'
            flash('News submitted for admin review.', 'info')
        
        db = get_db()
        db.execute(
            'INSERT INTO news (title, content, reporter_id, sentiment, is_fake, status, detailed_analysis) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (title, content, session['user_id'], sentiment, is_fake, status, detailed_analysis)
        )
        db.commit()
        
        if status == 'auto_approved':
            news_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            block_hash = add_to_blockchain(news_id, title, content)
            db.execute(
                'UPDATE news SET status = "approved", blockchain_hash = ? WHERE id = ?',
                (block_hash, news_id)
            )
            db.commit()
            flash('✅ News automatically approved and added to blockchain!', 'success')
        
        return redirect(url_for('reporter_dashboard'))
    
    return render_template('submit_news.html')
@app.route('/blockchain')
def view_blockchain():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    
    blockchain_data = []
    for block in blockchain.chain:
        blockchain_data.append({
            'index': block.index,
            'timestamp': datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'data': block.data,
            'previous_hash': block.previous_hash,
            'hash': block.hash
        })
    
    # Pass both the blockchain object and the data list
    return render_template('blockchain.html', 
                         blockchain=blockchain_data,
                         blockchain_obj=blockchain)  # Add this line
@app.route('/get-analysis', methods=['POST'])
def get_analysis():
    if 'user_id' not in session or session['role'] != 'admin':
        return {'error': 'Unauthorized'}, 403
    
    content = request.json.get('content', '')
    analysis = get_detailed_analysis(content)
    return {'analysis': analysis}
@app.route('/get-detailed-factcheck', methods=['POST'])
def get_detailed_factcheck():
    if 'user_id' not in session or session['role'] != 'admin':
        return {'error': 'Unauthorized'}, 403
    
    content = request.json.get('content', '')
    title = request.json.get('title', '')
    full_text = f"{title}. {content}"
    
    analysis = detailed_fact_check(full_text)
    return {'analysis': analysis}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)