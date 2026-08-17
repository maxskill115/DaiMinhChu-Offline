# Local compatibility server

Prototype backend local cho client **Đại Minh Chủ Việt Nam 8.0.2**.

Hiện server đã đi được về mặt **static reverse** tới flow:

```text
Login
  -> CheckUser
  -> GetUserInfo
  -> BeginCutsceneForm
  -> chọn 1 trong 3 nhân vật đầu
  -> SelectStartNhanVat
  -> Home (Form 3)
```

> Lưu ý: flow trên đã được xác nhận từ IL/metadata của client và đã có fixture/server tương ứng, nhưng **chưa được xác nhận end-to-end trên Android thật/emulator**.

## Cài đặt

```bat
cd server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Dependency hiện tại:

```text
cryptography>=42,<47
```

## Chạy test

```bat
python -m unittest -v
```

Test hiện kiểm tra:

- AES encrypt/decrypt round-trip;
- URL `User.asmx` được quảng bá đúng;
- tài khoản mới bắt đầu với `NhanVat: []`;
- cả 3 nhân vật khởi đầu đều sinh response hợp lệ;
- mã nhân vật không hợp lệ bị từ chối.

## Chạy server

```bat
python app.py
```

Mặc định:

```text
listen: 0.0.0.0:8000
advertised root: http://10.0.2.2:8000
```

Server tự chuẩn hóa advertised root thành:

```text
http://10.0.2.2:8000/Server/Webservice/User.asmx
```

Health check:

```text
http://127.0.0.1:8000/health
```

## Android Emulator / điện thoại thật

`127.0.0.1` bên trong Android là chính Android, không phải PC.

### Android Emulator chuẩn

Thông thường có thể dùng:

```text
10.0.2.2
```

nên mặc định hiện tại phù hợp cho kiểu emulator đó.

### Điện thoại/tablet thật hoặc emulator khác

Đặt `DMC_BASE_URL` thành IP LAN của PC, ví dụ:

```bat
set DMC_BASE_URL=http://192.168.1.10:8000
python app.py
```

Không cần tự thêm `/Server/Webservice/User.asmx`; server sẽ thêm nếu thiếu.

Patcher client cũng phải dùng cùng địa chỉ mà Android truy cập được.

## Endpoint hiện có

Server match theo suffix path nên chấp nhận dạng đầy đủ như:

```text
POST /Server/Webservice/User.asmx/Login
POST /Server/Webservice/User.asmx/CheckUser
POST /Server/Webservice/User.asmx/GetUserInfo
POST /Server/Webservice/User.asmx/SelectStartNhanVat
```

và dạng rút gọn:

```text
POST /Login
POST /CheckUser
POST /GetUserInfo
POST /SelectStartNhanVat
```

Request được xử lý theo đúng transport client:

```text
form data=<URL-escaped Base64 AES(JSON)>
```

Response trả:

```text
Base64 AES(JSON)
```

AES: 128-bit CBC + PKCS7, key/IV đã reverse từ `Assembly-CSharp.dll`.

## Nhân vật khởi đầu đã xác nhận từ config client

```text
NV_PhongThanhDuong
NV_LenhHoXung
NV_SoLuuHuong
```

`/SelectStartNhanVat` hiện tạo một hero ID `1` và đặt `DoiHinh.Slot1 = 1` để client có dữ liệu tối thiểu đi tiếp tới Home.

## Bước test thật tiếp theo

Khi chạy APK đã patch + server local, log mong đợi là:

```text
POST .../Login
POST .../CheckUser
POST .../GetUserInfo
POST .../SelectStartNhanVat
```

Sau đó cần kiểm tra client có vào được Home hay có request/schema mới phát sinh.

Xem thêm:

- [`../docs/protocol/login.md`](../docs/protocol/login.md)
- [`../docs/protocol/first-character.md`](../docs/protocol/first-character.md)
- [`../HANDOFF.md`](../HANDOFF.md)
