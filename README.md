# IntelX Checking - Asilla Data Breach Monitoring

Hệ thống tự động giám sát rò rỉ dữ liệu trên IntelX cho các domain và email của Asilla, với thông báo qua Slack.

## 📋 Tổng quan

Dự án này scan 68 URLs (domains + emails) trên IntelX API (free tier) để phát hiện dữ liệu rò rỉ. Khi phát hiện thay đổi (tăng/giảm/xuất hiện mới), hệ thống tự động gửi thông báo qua Slack.

### Tính năng chính

- ✅ **Progress Tracking**: Lưu tiến độ sau mỗi URL, không mất dữ liệu khi gián đoạn
- ✅ **Daily Quota Management**: Tự động dừng khi đạt 50 URLs/ngày (giới hạn free tier)
- ✅ **Change Detection**: So sánh với lịch sử, chỉ thông báo khi có thay đổi
- ✅ **Auto Reset**: Tự động reset cycle khi hoàn thành tất cả URLs
- ✅ **Error Handling**: Xử lý 401/402/429 errors, retry logic
- ✅ **Slack Integration**: Thông báo realtime + tổng kết cuối ngày

## 🏗️ Cấu trúc dự án

```
intelx-checking/
├── intelx_search_new.py    # Script chính
├── database.json            # Cấu hình + progress tracking
├── intelx_history.json      # Lịch sử scan để so sánh
├── .env                     # API keys (không commit)
├── .env.example             # Template cho .env
├── requirements.txt         # Python dependencies
├── setup_cron.sh           # Script setup cronjob
└── README.md               # File này
```

## 📊 Luồng hoạt động

### 1. Khởi tạo (Startup)

```
1. Load .env → Lấy INTELX_API_KEY, SLACK_TOKEN, SLACK_CHANNEL_ID
2. Load database.json → Lấy LIST_CHECK_URL (68 URLs) + done_check_urls (tiến độ)
3. Load intelx_history.json → Lấy kết quả scan trước đó để so sánh
4. Tính remaining_urls = LIST_CHECK_URL - done_check_urls
```

### 2. Check URLs (Daily Scan)

**Ví dụ: 65 URLs cần check**

#### Ngày 1 - Check 50 URLs đầu tiên
```
Loop through remaining_urls (65 URLs):
  ├─ URL 1-50: Check thành công ✅
  │  ├─ Call IntelX API: intelligent_search() → get search_id
  │  ├─ Get results: intelligent_search_result() → parse data
  │  ├─ So sánh với history → Phát hiện thay đổi?
  │  │  ├─ Có thay đổi → Gửi Slack ngay lập tức
  │  │  └─ Không thay đổi → Skip Slack, chỉ log console
  │  ├─ Lưu data vào current_scan{} trong memory
  │  └─ Update progress: done_check_urls.append(url) → save_progress()
  │
  ├─ URL 51: API trả về 402 (Quota exceeded) ⛔
  │  └─ Break loop ngay lập tức
  │
  └─ End of day:
     ├─ history.update(current_scan) → Merge 50 URLs mới
     ├─ save_history() → Ghi file 1 lần duy nhất
     └─ send_slack("Checked 50 URLs, 15 còn lại")
     
database.json lúc này: done_check_urls = [50 URLs]
```

#### Ngày 2 - Check 15 URLs còn lại
```
Load database.json → done_check_urls = [50 URLs]
Calculate remaining_urls = 65 - 50 = 15 URLs

Loop through remaining_urls (15 URLs):
  ├─ URL 51-65: Check thành công ✅
  │  └─ (Same flow như trên)
  │
  └─ End of day:
     ├─ history.update(current_scan) → Merge 15 URLs mới
     ├─ save_history() → Ghi file
     └─ send_slack("Checked 15 URLs, CYCLE COMPLETE!")
     
database.json lúc này: done_check_urls = [65 URLs]
```

#### Ngày 3 - Reset và bắt đầu cycle mới
```
Load database.json → done_check_urls = [65 URLs]
Calculate remaining_urls = 65 - 65 = 0 URLs

if remaining_urls == 0:
  ├─ reset_progress() → done_check_urls = []
  └─ remaining_urls = LIST_CHECK_URL (65 URLs)
  
→ Bắt đầu check lại từ đầu
```

### 3. Change Detection

```python
compare_results(url, current_stats, previous_stats):
  ├─ First scan: "🆕 First time scan"
  ├─ New data found: "⚠️ NEW DATA FOUND"
  ├─ Data removed: "✅ All data removed"
  ├─ Increase: "📈 pastes: +5 (was 10, now 15)"
  ├─ Decrease: "📉 leaks: -3 (was 20, now 17)"
  ├─ New type: "🆕 New type: darknet (5)"
  ├─ Removed type: "❌ Removed: paste (was 10)"
  └─ No change: "✅ No changes detected"
```

### 4. Slack Notifications

**Gửi 2 loại thông báo:**

1. **Per-URL Alert** (khi có thay đổi):
```
*⚠️ IntelX Change Detected - 2026-02-12 10:30:00*
URL: `example.com`
📈 pastes: +5 (was 10, now 15)
🆕 New type: darknet (3)
```

2. **Daily Summary** (cuối ngày):
```
*✅ IntelX Daily Scan - 2026-02-12 23:59:00*
📊 Checked today: 50 URLs
📈 Progress: 50/65 total
✅ No changes detected
_All checked URLs are stable_
```

## 🚀 Cài đặt

### Option 1: Chạy trực tiếp với Python (Cũ)

#### 1. Clone repository
```bash
git clone <repository-url> intelx-checking
cd intelx-checking
```

### Option 1: Chạy trực tiếp với Python (Cũ)

#### 1. Clone repository
```bash
git clone <repository-url> intelx-checking
cd intelx-checking
```

#### 2. Cài đặt dependencies
```bash
pip3 install -r requirements.txt
```

#### 3. Cấu hình environment variables
```bash
cp .env.example .env
vim .env
```

Điền các giá trị:
```env
INTELX_API_KEY=your_intelx_api_key_here
SLACK_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_ID=C0A21V42A64
```

#### 4. Cấu hình URLs cần check
Mở `database.json` và thêm URLs (nếu chưa có):
```json
{
  "LIST_CHECK_URL": [
    "asilla.jp",
    "example@asilla.jp",
    "..."
  ],
  "done_check_urls": []
}
```

---

## 🐳 Docker Architecture

### Files cấu trúc
```
intelx-checking/
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose config
├── .dockerignore          # Files bỏ qua khi build
├── run_docker_cron.sh     # Script chạy container (được gọi bởi cron)
└── setup_docker_cron.sh   # Script setup cronjob
```

### Dockerfile
- Base image: `python:3.11-slim`
- Install dependencies từ `requirements.txt`
- Copy source code và `database.json`
- Volume mount cho `intelx_history.json` và `database.json` để persist data

### docker-compose.yml
- Service: `intelx-checker`
- Load `.env` file tự động
- Mount volumes để data không bị mất sau khi container stop
- Network isolation

### Volume mounts
```yaml
volumes:
  - ./database.json:/app/database.json          # Progress tracking
  - ./intelx_history.json:/app/intelx_history.json  # Scan history
```

**Data persistence:** Mọi thay đổi trong container sẽ được lưu vào host machine, không bị mất sau khi container dừng.

---

## 📁 File Configuration
```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

---

### Option 2: Docker + Cronjob (Khuyến nghị) 🐳

**Ưu điểm:**
- ✅ Môi trường cô lập, không ảnh hưởng hệ thống
- ✅ Dễ deploy trên bất kỳ máy nào có Docker
- ✅ Không cần cài Python dependencies thủ công
- ✅ Volume mount để persist data giữa các lần chạy

#### 1. Clone repository
```bash
git clone <repository-url> intelx-checking
cd intelx-checking
```

#### 2. Cấu hình environment variables
```bash
cp .env.example .env
vim .env
```

Điền các giá trị:
```env
INTELX_API_KEY=your_intelx_api_key_here
SLACK_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_ID=C0A21V42A64
```

#### 3. Cấu hình URLs cần check
Mở `database.json` và thêm URLs:
```json
{
  "LIST_CHECK_URL": [
    "asilla.jp",
    "example@asilla.jp"
  ],
  "done_check_urls": []
}
```

#### 4. Build và test Docker image
```bash
# Build image
docker-compose build

# Test chạy thủ công
docker-compose up
```

#### 5. Setup cronjob (tự động chạy 9h sáng thứ 2 hàng tuần)
```bash
chmod +x setup_docker_cron.sh run_docker_cron.sh
./setup_docker_cron.sh
```

#### 6. Kiểm tra cronjob
```bash
# Xem cronjob đã được tạo
crontab -l | grep intelx

# Xem logs
tail -f logs/cron.log

# Test chạy thủ công
./run_docker_cron.sh
```

**Lịch chạy:** Mỗi thứ 2 lúc 9:00 sáng (Cron: `0 9 * * 1`)

**Thay đổi lịch chạy:**
Chỉnh sửa file `setup_docker_cron.sh`, dòng:
```bash
# Ví dụ khác:
# 0 9 * * 1    # Thứ 2 lúc 9h sáng (hiện tại)
# 0 2 * * *    # Hàng ngày lúc 2h sáng
# 0 9 * * 2,4  # Thứ 3 và thứ 5 lúc 9h sáng
# 0 */6 * * *  # Mỗi 6 tiếng
```

---

### 4. Cấu hình URLs cần check
Mở `database.json` và thêm URLs vào `LIST_CHECK_URL`:
```json
{
  "LIST_CHECK_URL": [
    "asilla.jp",
    "example@asilla.jp",
    "..."
  ],
  "done_check_urls": []
}
```

### 5. Chạy thử
```bash
python3 intelx_search_new.py
```

### 6. Setup cronjob (tự động chạy hàng ngày 2h sáng)
```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

## 📁 File Configuration

### database.json
```json
{
  "LIST_CHECK_URL": [
    "asilla.jp",
    "example@asilla.jp"
  ],
  "done_check_urls": [
    "asilla.jp"
  ]
}
```
- `LIST_CHECK_URL`: Danh sách URLs cần check (68 URLs)
- `done_check_urls`: URLs đã check trong cycle hiện tại (auto reset)

### intelx_history.json
```json
{
  "asilla.jp": {
    "date": "2026-02-12 10:30:00",
    "media": [
      {"mediah": "pastes", "count": 15},
      {"mediah": "darknet", "count": 3}
    ]
  }
}
```
- Lưu kết quả scan gần nhất để so sánh
- Được cập nhật sau mỗi session (batch write)

### .env
```env
INTELX_API_KEY=your_api_key_here
SLACK_TOKEN=xoxb-xxx
SLACK_CHANNEL_ID=C0A21V42A64
```

## ⚙️ Rate Limiting & Quota

### Free Tier Limits
- **Daily quota**: 50 searches/day
- **Rate limit**: 1 second giữa các requests
- **Delay giữa URLs**: 2 seconds

### Xử lý Errors
- `401` (Invalid key) → Stop ngay, báo lỗi
- `402` (Quota exceeded) → Break loop, tiếp tục ngày mai
- `429` (Rate limit) → Wait 60s, retry 1 lần

## 🔄 Progress Tracking Strategy

### Performance Trade-offs

**Current Strategy: Incremental Progress + Batch History**

1. **Progress saving**: SAU MỖI URL
   - ✅ An toàn: Không mất tiến độ khi crash
   - ⚠️ Trade-off: N writes vào `database.json`

2. **History saving**: 1 LẦN cuối session
   - ✅ Performance: Chỉ 1 write vào `intelx_history.json`
   - ⚠️ Trade-off: Nếu crash giữa chừng, mất history của session đó


## 📝 Logging

### Console Output
```
============================================================
[+] Check Date: 2026-02-12 10:30:00
[+] Progress: 1/65
[+] Checking URL: asilla.jp
============================================================
[+] Searching for: asilla.jp
[+] Search ID: abc123xyz
[+] Getting search results...
[+] URL: asilla.jp
[+] Current data: 15 pastes, 3 darknet
[+] Status: 📈 pastes: +5 (was 10, now 15)
[✓] Changes detected - sent to Slack
[+] Progress saved: 1/65 URLs completed
```

## 🐛 Troubleshooting

### "INTELX_API_KEY not found in .env file"
→ Kiểm tra file `.env` đã tạo và có key `INTELX_API_KEY`

### "Error 402: Payment required"
→ Đã hết quota ngày hôm nay, chạy lại ngày mai

### "Error 429: Rate limit exceeded"
→ Script tự động retry sau 60s


## 📈 Monitoring

Theo dõi qua Slack channel:
- Thông báo realtime khi có thay đổi
- Tổng kết cuối mỗi session
- Progress tracking: X/65 URLs completed

## 📄 License

Internal use only - Asilla Inc.
