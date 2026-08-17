# Local compatibility server

Prototype backend local cho client **Đại Minh Chủ Việt Nam 8.0.2**.

Static reverse + server fixture hiện đã đi tới:

```text
Login
 -> CheckUser
 -> GetUserInfo
 -> BeginCutsceneForm
 -> SelectStartNhanVat
 -> Home (Form 3)
 -> GiangHoForm (Form 4)
 -> Battle.asmx/GiangHo
 -> BattleForm (Form 7)
 -> BattleReplay 1v1 tối thiểu
 -> result panel
```

> **Chưa có client runtime confirmation.** Server/AES/fixture đã test local, nhưng APK Unity vẫn cần chạy thật trên Android/emulator để xác nhận toàn bộ flow.

## Cài đặt

```bat
cd server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Dependency:

```text
cryptography>=42,<47
```

## Unit test

```bat
python -m unittest -v
```

Hiện có 6 test, gồm AES, login URL, 3 nhân vật đầu và cấu trúc replay Giang Hồ tối thiểu/null-safe theo các dereference đã reverse.

## Chạy server

```bat
python app.py
```

Mặc định:

```text
listen: http://0.0.0.0:8000
User URL:   http://10.0.2.2:8000/Server/Webservice/User.asmx
Battle URL: http://10.0.2.2:8000/Server/Webservice/Battle.asmx
```

Health check:

```text
http://127.0.0.1:8000/health
```

### Điện thoại thật / emulator khác

`127.0.0.1` trong Android không phải PC. Đặt IP LAN của PC:

```bat
set DMC_BASE_URL=http://192.168.1.10:8000
python app.py
```

Patcher APK cũng phải dùng cùng địa chỉ mà Android truy cập được.

## Endpoint hiện có

```text
POST /Server/Webservice/User.asmx/Login
POST /Server/Webservice/User.asmx/CheckUser
POST /Server/Webservice/User.asmx/GetUserInfo
POST /Server/Webservice/User.asmx/SelectStartNhanVat
POST /Server/Webservice/Battle.asmx/GiangHo
```

Server match theo suffix nên cũng nhận `/Login`, `/CheckUser`, `/GiangHo`... khi test thủ công.

Transport:

```text
request:  form data=<URL-escaped Base64 AES(JSON)>
response: Base64 AES(JSON)
```

AES: 128-bit CBC + PKCS7 với key/IV đã reverse từ `Assembly-CSharp.dll`.

## Smoke test server thật

Mở terminal 1:

```bat
python app.py
```

Terminal 2:

```bat
python smoke_client.py
```

Hoặc chọn hero:

```bat
python smoke_client.py --hero NV_SoLuuHuong
```

Script gửi **request AES thật qua HTTP** theo chuỗi:

```text
Login
 -> CheckUser
 -> GetUserInfo
 -> SelectStartNhanVat
 -> Battle.asmx/GiangHo
```

Kết quả local đã xác nhận:

```text
ErrorCode=1 cho toàn chuỗi
GiangHo: DoiThang=0, star=3, Hiep1 có 1 lượt đánh
```

Đây là **server smoke test**, không được nhầm với client Android runtime test.

## Battle fixture hiện tại

`/GiangHo` tạo trận deterministic đơn giản:

```text
Team1 = hero đã chọn
Team2 = một hero config hợp lệ khác
1 hiệp
1 đòn đánh thường
Team2 mất toàn bộ HP
Team1 thắng 3 sao
```

`VoCong=""` cố ý dùng nhánh normal attack của client, tránh lookup config võ công. Các list mà client gọi `.Count`/`.Contains` không null-check (`Buffs`, `TrangThaiThuongTon`...) được gửi `[]`.

`Reward` và `UpdateUserInfo.NhanVat` cũng được gửi vì result panel dereference trực tiếp các object này.

**GiangHo progress chưa persist**; milestone này ưu tiên chứng minh replay compatibility trước.

## Bước test quan trọng tiếp theo

Chạy APK đã patch + local server và mong đợi:

```text
POST ...User.asmx/Login
POST ...User.asmx/CheckUser
POST ...User.asmx/GetUserInfo
POST ...User.asmx/SelectStartNhanVat
[Home]
[Giang Hồ]
POST ...Battle.asmx/GiangHo
[BattleForm phát trận]
[result panel]
```

Nếu fail: giữ server console log + `adb logcat`, reverse đúng request/exception cuối cùng.

Xem thêm:

- [`../docs/protocol/login.md`](../docs/protocol/login.md)
- [`../docs/protocol/first-character.md`](../docs/protocol/first-character.md)
- [`../docs/protocol/giangho-battle.md`](../docs/protocol/giangho-battle.md)
- [`../HANDOFF.md`](../HANDOFF.md)
