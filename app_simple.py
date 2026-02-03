"""
Simplified Fraud Detection System
Focus: Location-based fraud detection and account behavior tracking
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import json
from collections import defaultdict

app = Flask(__name__)
CORS(app)
app.secret_key = 'fraud-detection-key-2026'

# Database functions
def get_db():
    """Get database connection."""
    conn = sqlite3.connect('fraud_detection_simple.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Transactions table - track all transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            sender_name TEXT NOT NULL,
            receiver_name TEXT NOT NULL,
            sender_location TEXT NOT NULL,
            receiver_location TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_fraud INTEGER DEFAULT 0,
            fraud_reason TEXT,
            account_id TEXT NOT NULL
        )
    ''')
    
    # Account behavior table - track suspicious accounts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_behavior (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT UNIQUE NOT NULL,
            total_transactions INTEGER DEFAULT 0,
            fraud_count INTEGER DEFAULT 0,
            suspicious_locations TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_flagged INTEGER DEFAULT 0,
            flag_reason TEXT
        )
    ''')
    
    # Location whitelist - trusted sender-receiver location pairs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS location_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT NOT NULL,
            sender_location TEXT NOT NULL,
            receiver_location TEXT NOT NULL,
            frequency INTEGER DEFAULT 1,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_verified INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized")

def check_transaction_fraud(data):
    """
    Analyze transaction for fraud indicators.
    Returns: {is_fraud: bool, confidence: float, reasons: list}
    """
    reasons = []
    fraud_score = 0
    max_score = 100
    
    sender_name = data.get('sender_name', '').strip()
    receiver_name = data.get('receiver_name', '').strip()
    sender_location = data.get('sender_location', '').strip().upper()
    receiver_location = data.get('receiver_location', '').strip().upper()
    amount = float(data.get('amount', 0))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check 1: Location mismatch - sender and receiver at extreme distance
    location_distance_score = check_location_mismatch(sender_location, receiver_location)
    if location_distance_score > 0:
        fraud_score += location_distance_score
        reasons.append(f"Unusual location pattern: {sender_location} → {receiver_location}")
    
    # Check 2: Has this account sent to this location pair before?
    is_known_pair, pair_frequency = check_known_location_pair(
        sender_name, sender_location, receiver_location, cursor
    )
    
    if not is_known_pair:
        fraud_score += 20
        reasons.append(f"New location pair detected for account {sender_name}")
    elif pair_frequency == 1:
        fraud_score += 10
        reasons.append(f"First time sending from {sender_location} to {receiver_location}")
    
    # Check 3: Unusual amount for this account
    avg_amount, max_amount = get_account_transaction_stats(sender_name, cursor)
    if avg_amount > 0 and amount > (max_amount * 1.5):
        fraud_score += 25
        reasons.append(f"Unusually high amount: ${amount} (normal max: ${max_amount})")
    
    # Check 4: Account flagged as suspicious
    is_flagged, flag_reason = check_account_flag_status(sender_name, cursor)
    if is_flagged:
        fraud_score += 30
        reasons.append(f"Account flagged: {flag_reason}")
    
    # Check 5: Same receiver, different locations (multiple sends in short time)
    duplicate_receiver_score = check_duplicate_receiver_pattern(
        sender_name, receiver_name, receiver_location, cursor
    )
    if duplicate_receiver_score > 0:
        fraud_score += duplicate_receiver_score
        reasons.append(f"Sending to {receiver_name} from multiple locations recently")
    
    # Check 6: Location rotation pattern (trying different unauthorized locations)
    location_rotation_score = check_location_rotation_pattern(sender_name, sender_location, cursor)
    if location_rotation_score > 0:
        fraud_score += location_rotation_score
        reasons.append("Suspicious location rotation pattern detected")
    
    conn.close()
    
    # Determine if fraud based on score
    is_fraud = fraud_score >= 50
    confidence = min(fraud_score, max_score) / max_score
    
    return {
        'is_fraud': is_fraud,
        'confidence': round(confidence * 100, 2),
        'score': fraud_score,
        'reasons': reasons,
        'severity': 'HIGH' if fraud_score >= 75 else ('MEDIUM' if fraud_score >= 50 else 'LOW')
    }

def check_location_mismatch(sender_loc, receiver_loc):
    """Check if locations are unusual (e.g., geographically far apart)."""
    score = 0
    
    # Define suspicious location combinations
    suspicious_pairs = [
        ('US', 'NG'),    # US to Nigeria
        ('US', 'GH'),    # US to Ghana
        ('US', 'IN'),    # US to India
        ('UK', 'CN'),    # UK to China
        ('CA', 'RU'),    # Canada to Russia
        ('AU', 'KP'),    # Australia to North Korea
    ]
    
    pair = (sender_loc[:2], receiver_loc[:2]) if len(sender_loc) >= 2 and len(receiver_loc) >= 2 else None
    
    if pair and pair in suspicious_pairs:
        score = 35
    elif sender_loc != receiver_loc:
        score = 10  # Different locations is mildly suspicious
    
    return score

def check_known_location_pair(sender_name, sender_loc, receiver_loc, cursor):
    """Check if sender has made this sender-receiver location pair transaction before."""
    cursor.execute('''
        SELECT frequency FROM location_pairs 
        WHERE account_name = ? AND sender_location = ? AND receiver_location = ?
    ''', (sender_name, sender_loc, receiver_loc))
    
    result = cursor.fetchone()
    if result:
        return True, result['frequency']
    return False, 0

def get_account_transaction_stats(sender_name, cursor):
    """Get average and max transaction amounts for an account."""
    cursor.execute('''
        SELECT AVG(amount) as avg_amount, MAX(amount) as max_amount 
        FROM transactions 
        WHERE sender_name = ? AND is_fraud = 0
    ''', (sender_name,))
    
    result = cursor.fetchone()
    if result and result['avg_amount']:
        return float(result['avg_amount']), float(result['max_amount'])
    return 0, 0

def check_account_flag_status(sender_name, cursor):
    """Check if account is flagged as suspicious."""
    cursor.execute('''
        SELECT is_flagged, flag_reason FROM account_behavior 
        WHERE account_name = ?
    ''', (sender_name,))
    
    result = cursor.fetchone()
    if result and result['is_flagged']:
        return True, result['flag_reason']
    return False, None

def check_duplicate_receiver_pattern(sender_name, receiver_name, receiver_loc, cursor):
    """Check if same receiver is receiving from sender in different locations."""
    # Check last 7 days
    week_ago = datetime.now() - timedelta(days=7)
    
    cursor.execute('''
        SELECT COUNT(DISTINCT sender_location) as location_count 
        FROM transactions 
        WHERE sender_name = ? AND receiver_name = ? 
        AND timestamp > ? AND is_fraud = 0
    ''', (sender_name, receiver_name, week_ago))
    
    result = cursor.fetchone()
    if result and result['location_count'] > 1:
        return result['location_count'] * 10  # 20, 30, 40 points based on variety
    return 0

def check_location_rotation_pattern(sender_name, current_location, cursor):
    """Check if account is cycling through different locations (potential VPN/spoofing)."""
    # Check last 24 hours
    day_ago = datetime.now() - timedelta(hours=24)
    
    cursor.execute('''
        SELECT COUNT(DISTINCT sender_location) as unique_locations 
        FROM transactions 
        WHERE sender_name = ? AND timestamp > ?
    ''', (sender_name, day_ago))
    
    result = cursor.fetchone()
    if result and result['unique_locations'] > 3:
        return 25  # Suspicious location rotation
    return 0

def update_account_behavior(sender_name, is_fraud, fraud_reason=None):
    """Update account behavior tracking."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO account_behavior (account_name, total_transactions, fraud_count, is_flagged, flag_reason)
        VALUES (?, 1, ?, ?, ?)
        ON CONFLICT(account_name) DO UPDATE SET
            total_transactions = total_transactions + 1,
            fraud_count = fraud_count + ?,
            last_updated = CURRENT_TIMESTAMP,
            is_flagged = CASE WHEN fraud_count >= 3 THEN 1 ELSE is_flagged END,
            flag_reason = CASE WHEN fraud_count >= 3 THEN ? ELSE flag_reason END
    ''', (sender_name, 1 if is_fraud else 0, 1 if is_fraud else 0, 
          fraud_reason or 'Multiple fraud attempts detected'))
    
    conn.commit()
    conn.close()

# Routes

@app.route('/')
def index():
    """Main page."""
    return render_template('index_simple.html')

@app.route('/check-transaction', methods=['POST'])
def check_transaction():
    """Check if transaction is fraud."""
    try:
        data = request.get_json() or request.form
        
        # Validate input
        required_fields = ['sender_name', 'receiver_name', 'sender_location', 
                          'receiver_location', 'amount', 'account_id']
        
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check fraud
        result = check_transaction_fraud(data)
        
        # Store transaction
        conn = get_db()
        cursor = conn.cursor()
        
        import uuid
        transaction_id = str(uuid.uuid4())[:8]
        
        cursor.execute('''
            INSERT INTO transactions 
            (transaction_id, sender_name, receiver_name, sender_location, 
             receiver_location, amount, is_fraud, fraud_reason, account_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            transaction_id,
            data['sender_name'],
            data['receiver_name'],
            data['sender_location'].upper(),
            data['receiver_location'].upper(),
            float(data['amount']),
            1 if result['is_fraud'] else 0,
            ' | '.join(result['reasons']) if result['reasons'] else None,
            data.get('account_id', 'UNKNOWN')
        ))
        
        # Update location pair whitelist
        if not result['is_fraud']:
            cursor.execute('''
                INSERT INTO location_pairs 
                (account_name, sender_location, receiver_location)
                VALUES (?, ?, ?)
                ON CONFLICT DO UPDATE SET 
                    frequency = frequency + 1,
                    last_seen = CURRENT_TIMESTAMP
            ''', (data['sender_name'], data['sender_location'].upper(), 
                  data['receiver_location'].upper()))
        
        conn.commit()
        conn.close()
        
        # Update account behavior
        update_account_behavior(data['sender_name'], result['is_fraud'], 
                              ' | '.join(result['reasons']) if result['reasons'] else None)
        
        return jsonify({
            'transaction_id': transaction_id,
            'is_fraud': result['is_fraud'],
            'is_valid': not result['is_fraud'],
            'confidence': result['confidence'],
            'severity': result['severity'],
            'reasons': result['reasons'],
            'message': 'TRANSACTION BLOCKED - FRAUD DETECTED' if result['is_fraud'] else 'TRANSACTION APPROVED - VALID',
            'score': result['score']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/history')
def history():
    """View transaction history."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM transactions 
        ORDER BY timestamp DESC LIMIT 100
    ''')
    
    transactions = cursor.fetchall()
    conn.close()
    
    return render_template('history_simple.html', transactions=transactions)

@app.route('/flagged-accounts')
def flagged_accounts():
    """View flagged accounts."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM account_behavior 
        WHERE is_flagged = 1 
        ORDER BY fraud_count DESC
    ''')
    
    accounts = cursor.fetchall()
    conn.close()
    
    return render_template('flagged_accounts.html', accounts=accounts)

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM transactions')
    total_txn = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as fraud_count FROM transactions WHERE is_fraud = 1')
    fraud_count = cursor.fetchone()['fraud_count']
    
    cursor.execute('SELECT COUNT(*) as flagged FROM account_behavior WHERE is_flagged = 1')
    flagged_count = cursor.fetchone()['flagged']
    
    conn.close()
    
    return jsonify({
        'total_transactions': total_txn,
        'fraud_detected': fraud_count,
        'fraud_rate': round((fraud_count / total_txn * 100), 2) if total_txn > 0 else 0,
        'flagged_accounts': flagged_count
    })

@app.route('/api/transactions')
def api_transactions():
    """API endpoint for transactions."""
    limit = request.args.get('limit', 50, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM transactions 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    transactions = [dict(row) for row in rows]
    return jsonify(transactions)

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('error_simple.html', error='Page not found'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error_simple.html', error='Server error'), 500

if __name__ == '__main__':
    init_db()
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     Location-Based Fraud Detection System              ║
    ║     Detects unauthorized account behavior              ║
    ╚══════════════════════════════════════════════════════════╝
    
    Starting server at: http://127.0.0.1:5000
    
    Features:
    ✓ Location-based fraud detection
    ✓ Account behavior tracking
    ✓ Unauthorized location detection
    ✓ Suspicious account flagging
    
    Routes:
    • / - Transaction checker
    • /history - Recent transactions
    • /flagged-accounts - Suspicious accounts
    • /api/stats - Statistics
    """)
    app.run(debug=True, port=5000)
