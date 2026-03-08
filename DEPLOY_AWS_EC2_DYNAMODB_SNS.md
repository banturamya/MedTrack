# MedTrack Deployment: EC2 + DynamoDB + SNS

This guide deploys MedTrack on AWS EC2, uses DynamoDB for persistence, and SNS for notifications.

## 1. AWS Resources

Create the following resources first:

- DynamoDB tables:
  - `MedTrack_Users` with partition key `user_id` (String)
  - `MedTrack_Appointments` with partition key `appointment_id` (String)
  - `MedTrack_Notifications` with partition key `notification_id` (String)
- SNS topic:
  - Example: `arn:aws:sns:us-east-1:123456789012:medtrack-notifications`
- EC2 instance:
  - Ubuntu 22.04 LTS, t2.micro or larger
  - Security group inbound rules:
    - SSH `22` from your IP
    - HTTP `80` from `0.0.0.0/0`
    - Optional direct app port `5000` from trusted IPs only

## 2. IAM Role for EC2 (Recommended)

Attach an IAM role to EC2 with least-privilege access to:

- `dynamodb:Scan`, `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:UpdateItem` for the 3 tables
- `sns:Publish` for the SNS topic

If you use IAM role credentials, leave `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` empty.

## 3. Server Setup on EC2

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv nginx

cd /opt
sudo git clone <your-repo-url> medtrack
cd medtrack/HealthCare

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in `HealthCare/`:

```env
FLASK_SECRET_KEY=replace_with_strong_random_key
FLASK_DEBUG=0
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

DATABASE_TYPE=dynamodb
AWS_REGION=us-east-1
USERS_TABLE=MedTrack_Users
APPOINTMENTS_TABLE=MedTrack_Appointments
NOTIFICATIONS_TABLE=MedTrack_Notifications

ENABLE_SNS_NOTIFICATIONS=true
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:medtrack-notifications

# Optional if not using IAM role
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
```

## 4. Run with Gunicorn

```bash
source .venv/bin/activate
cd /opt/medtrack/HealthCare
gunicorn -w 3 -b 0.0.0.0:5000 app:app
```

## 5. Configure systemd Service

Create `/etc/systemd/system/medtrack.service`:

```ini
[Unit]
Description=MedTrack Flask App
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/opt/medtrack/HealthCare
Environment="PATH=/opt/medtrack/HealthCare/.venv/bin"
ExecStart=/opt/medtrack/HealthCare/.venv/bin/gunicorn -w 3 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable medtrack
sudo systemctl start medtrack
sudo systemctl status medtrack
```

## 6. Reverse Proxy with Nginx

Create `/etc/nginx/sites-available/medtrack`:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/medtrack /etc/nginx/sites-enabled/medtrack
sudo nginx -t
sudo systemctl restart nginx
```

## 7. Validation Checklist

- Open `http://<EC2_PUBLIC_IP>/`
- Register/login works
- Booking appointment writes records to `MedTrack_Appointments`
- Registering users writes records to `MedTrack_Users`
- Completing appointment updates DynamoDB record
- New booking and completion events publish to SNS topic
