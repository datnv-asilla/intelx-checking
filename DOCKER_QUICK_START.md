# Quick Start - Docker Setup

## 🚀 Setup nhanh trong 5 phút

### 1. Cấu hình .env
```bash
cp .env.example .env
vim .env  # Điền API keys
```

### 2. Build Docker image
```bash
docker-compose build
```

### 3. Test chạy thử
```bash
docker-compose up
```

### 4. Setup cronjob (9h sáng thứ 2 hàng tuần)
```bash
chmod +x setup_docker_cron.sh run_docker_cron.sh
./setup_docker_cron.sh
```

## ✅ Kiểm tra

```bash
# Xem cronjob
crontab -l | grep intelx

# Xem logs
tail -f logs/cron.log

# Test chạy thủ công
./run_docker_cron.sh
```

## 📅 Lịch chạy mặc định

**Cron:** `0 9 * * 1` = Mỗi thứ 2 lúc 9:00 sáng

### Thay đổi lịch chạy

Chỉnh trong `setup_docker_cron.sh`:

```bash
# Hàng ngày 2h sáng
0 2 * * *

# Thứ 3 và thứ 5 lúc 9h sáng  
0 9 * * 2,4

# Mỗi 6 tiếng
0 */6 * * *

# Thứ 2 lúc 9h sáng (mặc định)
0 9 * * 1
```

Sau đó chạy lại:
```bash
./setup_docker_cron.sh
```

## 🔧 Troubleshooting

### Container không chạy
```bash
# Xem logs chi tiết
docker-compose up

# Xem container status
docker ps -a
```

### File .env không được load
```bash
# Kiểm tra .env có trong thư mục
ls -la .env

# Test environment variables
docker-compose config
```

### Data bị mất sau khi chạy
```bash
# Kiểm tra volume mounts
docker-compose config | grep volumes

# Verify files được mount
docker-compose up
# Trong terminal khác:
docker exec -it intelx-checker ls -la /app
```

## 📝 Commands hữu ích

```bash
# Build lại image
docker-compose build --no-cache

# Xóa container cũ
docker-compose down

# Xem logs container
docker-compose logs

# Chạy interactive
docker-compose run --rm intelx-checker bash

# Stop tất cả containers
docker-compose down --volumes
```
