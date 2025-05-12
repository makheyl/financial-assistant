from flask import Flask, jsonify, render_template, request
import sqlite3
import pandas as pd
import textwrap
import re
from threading import Thread
import uuid
import time
from llama_cpp import Llama

llm = Llama(model_path="C:/Users/Mchail/Documents/finproj/models/mistral-7b-instruct-v0.1.Q4_0.gguf", n_ctx=2048, seed=42)
app = Flask(__name__)
advice_tasks = {}  # Store { task_id: {"status": "pending"|"done", "result": "..." } }

def init_db():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            amount REAL,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def generate_advice(task_id, summary_str):
    prompt = textwrap.dedent(f"""
        You are a highly skilled financial advisor 🧠💼. Analyze the user's spending and give detailed, personalized, and engaging financial advice 🎯.
        Avoid showing specific categories or amounts. Focus only on spending behavior.
        The advice must be unique, non-repetitive, and full of helpful, actionable ideas. Use plenty of fun emojis to make it engaging! 💰📊✨🔥📉🌱📈🎉💸

        Spending breakdown: {summary_str}

        Give your financial advice now:
    """)

    try:
        output = llm(prompt=prompt, max_tokens=500, temperature=0.9, top_p=0.95, stop=["</s>"])
        response = output["choices"][0]["text"].strip()
        if not re.search(r'[💰📉💡📊💸🛠️✨🔑⚖️💬🔥🌱📈🎉]', response):
            response += " 💰📉💡📊💸🛠️✨🔑⚖️💬🔥🌱📈🎉"
        advice_tasks[task_id]["status"] = "done"
        advice_tasks[task_id]["result"] = response
    except Exception as e:
        advice_tasks[task_id]["status"] = "error"
        advice_tasks[task_id]["result"] = f"Error: {str(e)}"

@app.route('/ai_financial_advice', methods=['GET'])
def ai_financial_advice():
    conn = sqlite3.connect('finance.db')
    df = pd.read_sql_query('SELECT * FROM expenses', conn)
    conn.close()

    if df.empty:
        return jsonify({'error': "No spending data available."}), 400

    # Build summary
    spending_summary = df.groupby('category')['amount'].sum()
    internal_summary = [f"{category.lower()}: ₱{amount:.2f}" for category, amount in spending_summary.items()]
    summary_str = "; ".join(internal_summary)

    # Create a task ID and spawn a thread
    task_id = str(uuid.uuid4())
    advice_tasks[task_id] = {"status": "pending", "result": None}
    thread = Thread(target=generate_advice, args=(task_id, summary_str))
    thread.start()

    return jsonify({'task_id': task_id})

@app.route('/advice_status/<task_id>', methods=['GET'])
def advice_status(task_id):
    task = advice_tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Invalid task ID'}), 404
    return jsonify(task)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_expense', methods=['POST'])
def add_expense():
    try:
        data = request.json
        category = data['category']
        amount = data['amount']
        date = data['date']

        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO expenses (category, amount, date) VALUES (?, ?, ?)', (category, amount, date))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Expense added successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/remove_expense/<int:expense_id>', methods=['DELETE'])
def remove_expense(expense_id):
    try:
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()
        conn.close()

        return jsonify({'message': f'Expense with ID {expense_id} removed successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_expenses', methods=['GET'])
def get_expenses():
    conn = sqlite3.connect('finance.db')
    df = pd.read_sql_query('SELECT * FROM expenses', conn)
    conn.close()
    return df.to_json(orient='records')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
