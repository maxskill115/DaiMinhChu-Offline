# Local compatibility server

Prototype backend tối thiểu cho client Đại Minh Chủ 8.0.2.

## Cài đặt

```bash
cd server
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
pip install -r requirements.txt
```

## Chạy

Mặc định server listen mọi interface ở port `8000`:

```bat
python app.py
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Khi client chạy trên emulator/điện thoại

`127.0.0.1` trong Android là chính thiết bị Android, không phải PC. Hãy quảng bá IP mà Android truy cập được, ví dụ IP LAN của PC:

```bat
set DMC_BASE_URL=http://192.168.1.10:8000
python app.py
```

Hoặc với Android Emulator chuẩn có thể dùng gateway host phù hợp như `10.0.2.2` nếu môi trường đó hỗ trợ.

## Endpoint hiện có

Prototype xử lý suffix path, nên cả hai kiểu đều được:

```text
/Login
/CheckUser
/GetUserInfo
```

và:

```text
/Server/Webservice/User.asmx/Login
/Server/Webservice/User.asmx/CheckUser
/Server/Webservice/User.asmx/GetUserInfo
```

Request được decrypt AES và log ra console. Response được encode lại đúng transport AES của client.

## Trạng thái

Server hiện chỉ nhằm milestone đầu:

```text
Login -> CheckUser -> GetUserInfo -> nhánh tài khoản chưa có NhanVat
```

Nó chưa phải GS hoàn chỉnh và chưa có battle/save thật.

Xem schema/reverse tại [`../docs/protocol/login.md`](../docs/protocol/login.md).
