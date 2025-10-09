"""Alert system for cruise deals"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from datetime import datetime
import config
from models import CruiseDeal


class AlertSystem:
    """Handles alerts for cruise deals"""
    
    @staticmethod
    def send_console_alert(deals: List[CruiseDeal]):
        """Print deals to console"""
        if not deals:
            print("\n" + "="*80)
            print("ℹ️  No deals found under $100/day AUD")
            print("="*80)
            return
        
        print("\n" + "="*80)
        print(f"🎉 FOUND {len(deals)} AMAZING CRUISE DEAL(S) UNDER ${config.PRICE_THRESHOLD}/DAY! 🎉")
        print("="*80)
        
        # Sort by price per day
        deals.sort(key=lambda x: x.price_per_day)
        
        for i, deal in enumerate(deals, 1):
            print(f"\n{'*'*80}")
            print(f"DEAL #{i}")
            print(str(deal))
    
    @staticmethod
    def send_email_alert(deals: List[CruiseDeal]):
        """Send email alert for deals"""
        if not config.EMAIL_ENABLED:
            return
        
        if not deals:
            return
        
        if not all([config.SENDER_EMAIL, config.SENDER_PASSWORD, config.RECIPIENT_EMAIL]):
            print("⚠️  Email settings not configured. Skipping email alert.")
            return
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚢 {len(deals)} Cruise Deal(s) Under ${config.PRICE_THRESHOLD}/day!"
            msg['From'] = config.SENDER_EMAIL
            msg['To'] = config.RECIPIENT_EMAIL
            
            # Create HTML content
            html = AlertSystem._create_html_email(deals)
            
            # Attach HTML
            msg.attach(MIMEText(html, 'html'))
            
            # Send email
            with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
                server.starttls()
                server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ Email alert sent to {config.RECIPIENT_EMAIL}")
            
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
    
    @staticmethod
    def _create_html_email(deals: List[CruiseDeal]) -> str:
        """Create HTML email content"""
        # Sort by price per day
        deals.sort(key=lambda x: x.price_per_day)
        
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .deal {{
                    border: 2px solid #667eea;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 20px;
                    background: #f9f9f9;
                }}
                .deal-title {{
                    color: #667eea;
                    font-size: 24px;
                    margin-bottom: 10px;
                }}
                .price-highlight {{
                    background: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 20px;
                    font-weight: bold;
                    display: inline-block;
                    margin: 10px 0;
                }}
                .detail-row {{
                    margin: 8px 0;
                }}
                .label {{
                    font-weight: bold;
                    color: #555;
                }}
                .button {{
                    background: #667eea;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                    margin-top: 10px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #888;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚢 Amazing Cruise Deals Alert! 🚢</h1>
                <p>Found {len(deals)} cruise(s) under ${config.PRICE_THRESHOLD}/day AUD</p>
                <p style="font-size: 14px;">Scraped on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        for i, deal in enumerate(deals, 1):
            html += f"""
            <div class="deal">
                <div class="deal-title">🌊 Deal #{i}: {deal.cruise_line} - {deal.ship_name}</div>
                
                <div class="price-highlight">
                    ${deal.price_per_day:.2f} AUD per day
                </div>
                
                <div class="detail-row">
                    <span class="label">📍 Destination:</span> {deal.destination}
                </div>
                <div class="detail-row">
                    <span class="label">📅 Departure Date:</span> {deal.departure_date.strftime('%d %B %Y')}
                </div>
                <div class="detail-row">
                    <span class="label">🚢 Departure Port:</span> {deal.departure_port}
                </div>
                <div class="detail-row">
                    <span class="label">⏱️ Duration:</span> {deal.duration_days} days
                </div>
                <div class="detail-row">
                    <span class="label">🛏️ Cabin Type:</span> {deal.cabin_type}
                </div>
                <div class="detail-row">
                    <span class="label">💰 Total Price:</span> ${deal.total_price_aud:.2f} AUD
                </div>
                {f'<div class="detail-row"><span class="label">🎁 Special Offers:</span> {deal.special_offers}</div>' if deal.special_offers else ''}
                
                <a href="{deal.url}" class="button">View Deal →</a>
            </div>
            """
        
        html += """
            <div class="footer">
                <p>This is an automated alert from your Cruise Deal Scraper</p>
                <p>Happy sailing! ⛵</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def save_to_file(deals: List[CruiseDeal], filename: str = None):
        """Save deals to a text file"""
        if not deals:
            return
        
        if filename is None:
            filename = f"cruise_deals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"CRUISE DEALS UNDER ${config.PRICE_THRESHOLD}/DAY AUD\n")
                f.write(f"Scraped on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total deals found: {len(deals)}\n")
                f.write("="*80 + "\n\n")
                
                # Sort by price per day
                deals.sort(key=lambda x: x.price_per_day)
                
                for i, deal in enumerate(deals, 1):
                    f.write(f"DEAL #{i}\n")
                    f.write(str(deal))
                    f.write("\n")
            
            print(f"✅ Deals saved to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save deals to file: {e}")

