from flask import Flask, render_template, request, redirect
import razorpay
from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
from flask import Flask, render_template, request
import razorpay
from config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
import openpyxl
import os
app = Flask(__name__)

# Razorpay client
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/pay', methods=['POST'])
def pay():
    amount = int(request.form['amount']) * 100  # Amount in paise
    payment = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1  # auto capture
    })
    return render_template('payment.html', payment=payment, key=RAZORPAY_KEY_ID)

@app.route('/success', methods=['POST'])
def success():
    razorpay_payment_id = request.form.get('razorpay_payment_id')
    razorpay_order_id = request.form.get('razorpay_order_id')
    razorpay_signature = request.form.get('razorpay_signature')

    print("PAYMENT:", razorpay_payment_id)
    print("ORDER:", razorpay_order_id)
    print("SIGNATURE:", razorpay_signature)

    # Default values (for failed verification)
    amount = None

    try:
        # Razorpay Signature Verification
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })

        # Fetch order details
        order_data = client.order.fetch(razorpay_order_id)
        amount = order_data["amount"] // 100  # Paise → INR

        # Save Success Record
        save_payment_to_excel(
            payment_id=razorpay_payment_id,
            order_id=razorpay_order_id,
            amount=amount,
            status="Success"
        )

        return render_template('success.html', payment_id=razorpay_payment_id)

    except Exception as e:
        # Save Failed Payment Attempt as well
        save_payment_to_excel(
            payment_id=razorpay_payment_id,
            order_id=razorpay_order_id,
            amount=amount,
            status="Failed"
        )

        print("Verification Error:", str(e))
        return "Payment verification failed", 400



def save_payment_to_excel(payment_id, order_id, amount, status):
    file_path = os.path.join("payment_detail", "payment_data.xlsx")

    # Create folder if not exists
    if not os.path.exists("payment_detail"):
        os.makedirs("payment_detail")

    # If file does not exist → create new workbook with headers
    if not os.path.exists(file_path):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Payments"
        sheet.append(["Payment ID", "Order ID", "Amount (INR)", "Status", "Timestamp"])
        workbook.save(file_path)

    # Load workbook
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Append entry
    sheet.append([payment_id, order_id, amount, status, timestamp])

    workbook.save(file_path)



if __name__ == '__main__':
    app.run(debug=True)
