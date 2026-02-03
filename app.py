"""
Credit Card Fraud Detection System
Simple transaction fraud detection based on location and account behavior
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import hashlib

app = Flask(__name__)
app.secret_key = 'fraud_detection_secret_key_2026'

# ============== Sample Transaction Data ==============

def generate_sample_data():
    """Generate sample transaction data with fraud indicators."""
    
    # Define locations with coordinates (lat, lon)
    locations = {
        'New York': (40.7128, -74.0060, 'USA'),
        'Los Angeles': (34.0522, -118.2437, 'USA'),
        'Chicago': (41.8781, -87.6298, 'USA'),
        'Houston': (29.7604, -95.3698, 'USA'),
        'Mumbai': (19.0760, 72.8777, 'India'),
        'Delhi': (28.7041, 77.1025, 'India'),
        'London': (51.5074, -0.1278, 'UK'),
        'Tokyo': (35.6762, 139.6503, 'Japan'),
        'Sydney': (33.8688, 151.2093, 'Australia'),
        'Dubai': (25.2048, 55.2708, 'UAE'),
        'Unknown Location': (0, 0, 'Unknown'),
        'Suspicious IP': (0, 0, 'VPN/Proxy'),
    }
    
    # Account names
    accounts = [
        'John Smith', 'Sarah Johnson', 'Mike Wilson', 'Emily Davis', 
        'Robert Brown', 'Lisa Anderson', 'David Martinez', 'Jennifer Taylor',
        'James Garcia', 'Maria Rodriguez', 'Suspicious_Account_X', 'Anonymous_User_123'
    ]
    
    # Receiver accounts
    receivers = [
        'Amazon Store', 'Walmart', 'Local Restaurant', 'Gas Station',
        'Online Shopping', 'Utility Company', 'Unknown Merchant', 
        'Offshore Account', 'Crypto Exchange', 'Gaming Platform'
    ]
    
    transactions = []
    
    for i in range(1, 201):  # 200 sample transactions
        # Determine if this should be a suspicious transaction (20% fraud rate)
        is_fraud = random.random() < 0.20
        
        sender = random.choice(accounts)
        receiver = random.choice(receivers)
        
        if is_fraud:
            # Suspicious patterns
            fraud_type = random.choice(['location', 'amount', 'velocity', 'account'])
            
            if fraud_type == 'location':
                sender_location = random.choice(['Unknown Location', 'Suspicious IP'])
                receiver_location = random.choice(list(locations.keys())[:6])
                amount = random.uniform(100, 5000)
                fraud_reason = 'Unauthorized Location'
            elif fraud_type == 'amount':
                sender_location = random.choice(list(locations.keys())[:8])
                receiver_location = random.choice(['Offshore Account', 'Crypto Exchange'])
                amount = random.uniform(5000, 50000)  # Unusually high amount
                fraud_reason = 'High Amount Transfer'
            elif fraud_type == 'velocity':
                sender_location = random.choice(list(locations.keys())[:8])
                receiver_location = random.choice(list(locations.keys())[:8])
                amount = random.uniform(500, 2000)
                fraud_reason = 'Multiple Rapid Transactions'
            else:
                sender = random.choice(['Suspicious_Account_X', 'Anonymous_User_123'])
                sender_location = random.choice(list(locations.keys()))
                receiver_location = random.choice(['Unknown Merchant', 'Offshore Account'])
                amount = random.uniform(1000, 10000)
                fraud_reason = 'Suspicious Account Behavior'
        else:
            # Normal transaction
            sender_location = random.choice(list(locations.keys())[:8])
            receiver_location = random.choice(list(locations.keys())[:8])
            amount = random.uniform(10, 2000)
            fraud_reason = None
        
        # Calculate distance between locations
        sender_coords = locations[sender_location]
        receiver_coords = locations.get(receiver_location, locations['New York'])
        distance = calculate_distance(sender_coords[0], sender_coords[1], 
                                     receiver_coords[0], receiver_coords[1])
        
        # Generate timestamp (last 30 days)
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
        
        transactions.append({
            'TransactionID': f'TXN{i:05d}',
            'Timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'SenderName': sender,
            'SenderLocation': sender_location,
            'SenderCountry': sender_coords[2],
            'ReceiverName': receiver,
            'ReceiverLocation': receiver_location,
            'Amount': round(amount, 2),
            'Distance_KM': round(distance, 2),
            'IsFraud': is_fraud,
            'FraudReason': fraud_reason,
            'RiskScore': calculate_risk_score(amount, distance, sender_location, sender, is_fraud)
        })
    
    return pd.DataFrame(transactions)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def calculate_risk_score(amount, distance, location, sender, is_fraud):
    """Calculate risk score based on multiple factors."""
    score = 0
    
    # Amount factor
    if amount > 10000:
        score += 40
    elif amount > 5000:
        score += 25
    elif amount > 2000:
        score += 10
    
    # Location factor
    if location in ['Unknown Location', 'Suspicious IP']:
        score += 35
    
    # Distance factor (rapid international transfers)
    if distance > 5000:
        score += 15
    
    # Suspicious account names
    if 'Suspicious' in sender or 'Anonymous' in sender:
        score += 30
    
    # Add some randomness
    score += random.randint(-5, 10)
    
    return min(max(score, 0), 100)

# Generate data on startup
random.seed(42)  # For consistent sample data
df = generate_sample_data()

# Simple user for demo
DEMO_USER = {
    'username': 'analyst',
    'password': hashlib.sha256('analyst123'.encode()).hexdigest(),
    'name': 'Fraud Analyst'
}

# ============== Routes ==============

@app.route('/')
def home():
    """Landing page."""
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if username == DEMO_USER['username'] and password_hash == DEMO_USER['password']:
            session['logged_in'] = True
            session['username'] = username
            session['name'] = DEMO_USER['name']
            flash('Login successful! Welcome to Fraud Detection System.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard with transaction analysis."""
    if not session.get('logged_in'):
        flash('Please login to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    
    # Statistics
    total_transactions = len(df)
    fraud_transactions = df[df['IsFraud'] == True]
    fraud_count = len(fraud_transactions)
    fraud_rate = round((fraud_count / total_transactions) * 100, 2)
    total_amount = df['Amount'].sum()
    fraud_amount = fraud_transactions['Amount'].sum()
    
    # Fraud by reason
    fraud_by_reason = fraud_transactions.groupby('FraudReason').size().to_dict()
    
    # Suspicious accounts
    suspicious_accounts = fraud_transactions.groupby('SenderName').agg({
        'TransactionID': 'count',
        'Amount': 'sum'
    }).reset_index()
    suspicious_accounts.columns = ['Account', 'FraudCount', 'TotalAmount']
    suspicious_accounts = suspicious_accounts.sort_values('FraudCount', ascending=False).head(5)
    
    # Unauthorized locations
    unauthorized_locations = fraud_transactions[
        fraud_transactions['FraudReason'] == 'Unauthorized Location'
    ]['SenderLocation'].value_counts().to_dict()
    
    # Recent fraud transactions
    recent_fraud = fraud_transactions.sort_values('Timestamp', ascending=False).head(10).to_dict(orient='records')
    
    stats = {
        'total_transactions': total_transactions,
        'fraud_count': fraud_count,
        'fraud_rate': fraud_rate,
        'total_amount': round(total_amount, 2),
        'fraud_amount': round(fraud_amount, 2),
        'fraud_by_reason': fraud_by_reason,
        'suspicious_accounts': suspicious_accounts.to_dict(orient='records'),
        'unauthorized_locations': unauthorized_locations,
        'recent_fraud': recent_fraud
    }
    
    return render_template('dashboard.html', stats=stats)

@app.route('/transactions')
def transactions():
    """View all transactions with fraud detection."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    filter_type = request.args.get('filter', 'all')
    search = request.args.get('search', '')
    
    filtered_df = df.copy()
    
    # Apply filter
    if filter_type == 'fraud':
        filtered_df = filtered_df[filtered_df['IsFraud'] == True]
    elif filter_type == 'legitimate':
        filtered_df = filtered_df[filtered_df['IsFraud'] == False]
    elif filter_type == 'high_risk':
        filtered_df = filtered_df[filtered_df['RiskScore'] >= 50]
    elif filter_type == 'location':
        filtered_df = filtered_df[filtered_df['FraudReason'] == 'Unauthorized Location']
    
    # Apply search
    if search:
        filtered_df = filtered_df[
            filtered_df['TransactionID'].str.contains(search, case=False) |
            filtered_df['SenderName'].str.contains(search, case=False) |
            filtered_df['ReceiverName'].str.contains(search, case=False) |
            filtered_df['SenderLocation'].str.contains(search, case=False)
        ]
    
    transactions_list = filtered_df.sort_values('Timestamp', ascending=False).to_dict(orient='records')
    
    return render_template('transactions.html', 
                          transactions=transactions_list, 
                          filter_type=filter_type,
                          search=search,
                          total=len(transactions_list))

@app.route('/transaction/<transaction_id>')
def transaction_detail(transaction_id):
    """View single transaction details."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    txn = df[df['TransactionID'] == transaction_id]
    
    if txn.empty:
        flash('Transaction not found.', 'danger')
        return redirect(url_for('transactions'))
    
    transaction = txn.iloc[0].to_dict()
    
    return render_template('transaction_detail.html', transaction=transaction)

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """Analyze a new transaction."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    result = None
    
    if request.method == 'POST':
        sender_name = request.form.get('sender_name', '')
        sender_location = request.form.get('sender_location', '')
        receiver_name = request.form.get('receiver_name', '')
        receiver_location = request.form.get('receiver_location', '')
        amount = float(request.form.get('amount', 0))
        
        # Analyze the transaction
        risk_factors = []
        risk_score = 0
        
        # Check sender location
        suspicious_locations = ['Unknown Location', 'Suspicious IP', 'VPN', 'Proxy', 'Unknown']
        if any(loc.lower() in sender_location.lower() for loc in suspicious_locations):
            risk_factors.append('⚠️ Sender location is unauthorized/unknown')
            risk_score += 35
        
        # Check amount
        if amount > 10000:
            risk_factors.append('🚨 Very high transaction amount (>$10,000)')
            risk_score += 40
        elif amount > 5000:
            risk_factors.append('⚠️ High transaction amount (>$5,000)')
            risk_score += 25
        
        # Check receiver
        suspicious_receivers = ['offshore', 'crypto', 'unknown', 'anonymous']
        if any(rec.lower() in receiver_name.lower() for rec in suspicious_receivers):
            risk_factors.append('🚨 Suspicious receiver type detected')
            risk_score += 30
        
        # Check sender name
        if 'suspicious' in sender_name.lower() or 'anonymous' in sender_name.lower():
            risk_factors.append('🚨 Suspicious sender account name')
            risk_score += 30
        
        # Determine if fraud
        is_fraud = risk_score >= 50
        
        if not risk_factors:
            risk_factors.append('✅ No suspicious patterns detected')
        
        result = {
            'sender_name': sender_name,
            'sender_location': sender_location,
            'receiver_name': receiver_name,
            'receiver_location': receiver_location,
            'amount': amount,
            'risk_score': min(risk_score, 100),
            'risk_factors': risk_factors,
            'is_fraud': is_fraud,
            'status': 'SPAM/FRAUD' if is_fraud else 'LEGITIMATE'
        }
    
    return render_template('analyze.html', result=result)

@app.route('/suspicious-accounts')
def suspicious_accounts():
    """View accounts with suspicious behavior."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Get fraud transactions
    fraud_df = df[df['IsFraud'] == True]
    
    # Aggregate by sender
    account_stats = fraud_df.groupby('SenderName').agg({
        'TransactionID': 'count',
        'Amount': ['sum', 'mean'],
        'RiskScore': 'mean'
    }).reset_index()
    account_stats.columns = ['Account', 'FraudCount', 'TotalAmount', 'AvgAmount', 'AvgRiskScore']
    account_stats = account_stats.sort_values('FraudCount', ascending=False)
    
    # Get transactions for each suspicious account
    accounts = []
    for _, row in account_stats.iterrows():
        account_txns = fraud_df[fraud_df['SenderName'] == row['Account']]
        locations = account_txns['SenderLocation'].value_counts().to_dict()
        reasons = account_txns['FraudReason'].value_counts().to_dict()
        
        accounts.append({
            'name': row['Account'],
            'fraud_count': int(row['FraudCount']),
            'total_amount': round(row['TotalAmount'], 2),
            'avg_amount': round(row['AvgAmount'], 2),
            'avg_risk_score': round(row['AvgRiskScore'], 1),
            'locations': locations,
            'fraud_reasons': reasons
        })
    
    return render_template('suspicious_accounts.html', accounts=accounts)

@app.route('/location-analysis')
def location_analysis():
    """Analyze transactions by location."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Location statistics
    location_stats = df.groupby('SenderLocation').agg({
        'TransactionID': 'count',
        'IsFraud': 'sum',
        'Amount': 'sum',
        'RiskScore': 'mean'
    }).reset_index()
    location_stats.columns = ['Location', 'TotalTxns', 'FraudTxns', 'TotalAmount', 'AvgRiskScore']
    location_stats['FraudRate'] = (location_stats['FraudTxns'] / location_stats['TotalTxns'] * 100).round(2)
    location_stats = location_stats.sort_values('FraudRate', ascending=False)
    
    locations = location_stats.to_dict(orient='records')
    
    # Unauthorized locations
    unauthorized = df[df['SenderLocation'].isin(['Unknown Location', 'Suspicious IP'])]
    unauthorized_txns = unauthorized.to_dict(orient='records')
    
    return render_template('location_analysis.html', 
                          locations=locations, 
                          unauthorized_txns=unauthorized_txns)

# ============== API Endpoints ==============

@app.route('/api/check-transaction', methods=['POST'])
def api_check_transaction():
    """API to check if a transaction is fraud."""
    data = request.get_json()
    
    sender_location = data.get('sender_location', '')
    receiver_name = data.get('receiver_name', '')
    amount = float(data.get('amount', 0))
    sender_name = data.get('sender_name', '')
    
    risk_score = 0
    reasons = []
    
    # Location check
    if 'unknown' in sender_location.lower() or 'suspicious' in sender_location.lower():
        risk_score += 35
        reasons.append('Unauthorized location')
    
    # Amount check
    if amount > 10000:
        risk_score += 40
        reasons.append('Very high amount')
    elif amount > 5000:
        risk_score += 25
        reasons.append('High amount')
    
    # Receiver check
    if any(x in receiver_name.lower() for x in ['offshore', 'crypto', 'unknown']):
        risk_score += 30
        reasons.append('Suspicious receiver')
    
    # Sender check
    if 'suspicious' in sender_name.lower() or 'anonymous' in sender_name.lower():
        risk_score += 30
        reasons.append('Suspicious sender')
    
    is_fraud = risk_score >= 50
    
    return jsonify({
        'is_fraud': is_fraud,
        'status': 'SPAM' if is_fraud else 'LEGITIMATE',
        'risk_score': min(risk_score, 100),
        'reasons': reasons if reasons else ['No suspicious patterns']
    })

@app.route('/api/stats')
def api_stats():
    """Get statistics."""
    fraud_df = df[df['IsFraud'] == True]
    
    return jsonify({
        'total_transactions': len(df),
        'fraud_count': len(fraud_df),
        'fraud_rate': round(len(fraud_df) / len(df) * 100, 2),
        'total_amount': round(df['Amount'].sum(), 2),
        'fraud_amount': round(fraud_df['Amount'].sum(), 2)
    })

# ============== Template Filters ==============

@app.template_filter('currency')
def currency_filter(value):
    """Format as currency."""
    return f"${value:,.2f}"

@app.context_processor
def utility_processor():
    """Add utility functions to templates."""
    return {
        'now': datetime.now()
    }

# ============== Run Application ==============

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Credit Card Fraud Detection System")
    print("=" * 60)
    print(f"Total Sample Transactions: {len(df)}")
    print(f"Fraud Transactions: {len(df[df['IsFraud'] == True])}")
    print("=" * 60)
    print("Login Credentials:")
    print("  Username: analyst")
    print("  Password: analyst123")
    print("=" * 60)
    print("Starting server at: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    
    app.run(debug=True, port=5000)
