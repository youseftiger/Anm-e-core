#!/usr/bin/env python3
import http.server
import socketserver
import json
from pathlib import Path
import os
from datetime import datetime

# Twilio SMS configuration (install with: pip install twilio)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE = os.getenv('TWILIO_PHONE', '')  # Your Twilio number
COMPANY_PHONE = os.getenv('COMPANY_PHONE', '+39 3759119687')  # Company phone number

# Optional: Try to import Twilio, but don't fail if not installed
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE)
except ImportError:
    TWILIO_AVAILABLE = False

PORT = 8000

def send_sms_to_company(booking_data):
    """Send SMS notification to company when someone books a table."""
    if not TWILIO_AVAILABLE:
        print("[SMS] Twilio not configured. Skipping SMS notification.")
        return False
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Format booking details
        message_text = (
            f"New Table Booking!\n"
            f"Name: {booking_data.get('name')}\n"
            f"Phone: {booking_data.get('phone')}\n"
            f"Date: {booking_data.get('date')}\n"
            f"Time: {booking_data.get('time')}\n"
            f"Guests: {booking_data.get('guests', 2)}\n"
            f"Received: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        # Send SMS to company phone
        message = client.messages.create(
            body=message_text,
            from_=TWILIO_PHONE,
            to=COMPANY_PHONE
        )
        
        print(f"[SMS] Notification sent to {COMPANY_PHONE} - Message ID: {message.sid}")
        return True
    except Exception as e:
        print(f"[SMS ERROR] Failed to send SMS: {str(e)}")
        return False

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/book':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                # Log booking request
                print(f"[BOOKING] Received from {data.get('name')} ({data.get('phone')})")
                print(f"[BOOKING] Date: {data.get('date')}, Time: {data.get('time')}, Guests: {data.get('guests', 2)}")
                
                # Send SMS notification to company
                sms_sent = send_sms_to_company(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = json.dumps({
                    'message': f'Thank you {data.get("name")}! We received your booking request for {data.get("date")} at {data.get("time")}. We will call you at {data.get("phone")} to confirm.',
                    'sms_notified': sms_sent
                })
                self.wfile.write(response.encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = json.dumps({'error': str(e)})
                self.wfile.write(response.encode())
        else:
            super().do_POST()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

if __name__ == '__main__':
    print("=" * 60)
    print("Anme Coor Restaurant Server")
    print("=" * 60)
    
    # Check SMS configuration
    if TWILIO_AVAILABLE:
        print(f"✓ SMS notifications ENABLED")
        print(f"  Company Phone: {COMPANY_PHONE}")
    else:
        print("✗ SMS notifications DISABLED")
        print("  To enable: pip install twilio")
        print("  Then set environment variables:")
        print("  - TWILIO_ACCOUNT_SID")
        print("  - TWILIO_AUTH_TOKEN")
        print("  - TWILIO_PHONE (your Twilio number)")
        print("  - COMPANY_PHONE (company phone to receive notifications)")
    
    print("=" * 60)
    
    handler = RequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"✓ Server running at http://localhost:{PORT}")
        print("✓ Press Ctrl+C to stop the server")
        print("=" * 60)
        httpd.serve_forever()

