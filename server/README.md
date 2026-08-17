# Local compatibility server

Prototype backend local cho client **Đại Minh Chủ Việt Nam 8.0.2**.

Static reverse + server implementation hiện đi tới:

```text
Login
 -> CheckUser
 -> GetUserInfo
 -> BeginCutsceneForm / load save
 -> SelectStartNhanVat
 -> Home (Form 3)
 -> GiangHoForm (Form 4)
 -> Battle.asmx/GiangHo
 -> BattleForm (Form 7)
 -> BattleReplay 1v1 tối thiểu
 -> result panel
 -> save star / unlock mission / reward bạc
```

> **Client Android runtime vẫn PENDING.** Server/AES/save/progression đã test local, nhưng APK Unity vẫn cần chạy thật để xác nhận toàn bộ flow.

## Cài đặt

```bat
cd server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Unit test

```bat
python -m unittest -v
```

Hiện có **11 test**: AES, login URL, persist/reload nhân vật, unlock mission, JSON `Nhiemvu`, best-star + lượt đánh, khóa mission, hoàn thành chapter và BattleReplay null-safe.

## Chạy server

```bat
python app.py
```

Mặc định:

```text
listen: http://0.0.0.0:8000
User URL:   http://10.0.2.2:8000/Server/Webservice/User.asmx
Battle URL: http://10.0.2.2:8000/Server/Webservice/Battle.asmx
save:       server/local_data/save.json
```

Health check:

```text
http://127.0.0.1:8000/health
```

### Điện thoại thật / emulator khác

```bat
set DMC_BASE_URL=http://192.168.1.10:8000
python app.py
```

Patcher APK phải dùng cùng địa chỉ mà Android truy cập được.

## Save local

File mặc định:

```text
server/local_data/save.json
```

Override:

```bat
set DMC_SAVE_FILE=C:\DMC\save.json
python app.py
```

Reset save:

```bat
python reset_save.py
```

Hiện save giữ nhân vật đã chọn, account cơ bản, bạc và tiến trình Giang Hồ.

## Endpoint hiện có

```text
POST /Server/Webservice/User.asmx/Login
POST /Server/Webservice/User.asmx/CheckUser
POST /Server/Webservice/User.asmx/GetUserInfo
POST /Server/Webservice/User.asmx/SelectStartNhanVat
POST /Server/Webservice/Battle.asmx/GiangHo
```

Transport:

```text
request:  form data=<URL-escaped Base64 AES(JSON)>
response: Base64 AES(JSON)
```

AES: 128-bit CBC + PKCS7 với key/IV reverse từ `Assembly-CSharp.dll`.

## Progress Giang Hồ

Client lưu mission progress trong:

```text
giangho.Nhiemvu = JSON string của List<HTTPNhiemVuGiangHoRecord>
```

Mỗi record:

```text
S = best star (0..3)
T = số lượt đã đánh trong ngày
```

Độ dài list là ranh giới mission đã unlock. Khi thắng mission, server giữ best star, tăng `T`, thêm record `{S:0,T:0}` cho mission kế. Thắng mission cuối đặt `HoanThanh=1` để client mở chapter kế.

Embedded `ConfigFile/GiangHo` xác nhận **92 chapter / 1405 mission**; server chỉ giữ structural mission counts, không lưu full config dump.

## Smoke test server thật

Terminal 1:

```bat
python app.py
```

Terminal 2:

```bat
python smoke_client.py --hero NV_SoLuuHuong
```

Chuỗi request AES thật:

```text
Login -> CheckUser -> GetUserInfo -> SelectStartNhanVat -> Battle.asmx/GiangHo
```

Đã test local thành công. Sau battle đầu, save có dạng logic:

```text
hero = NV_SoLuuHuong
Bac = 10100
GiangHo[0].Nhiemvu = [{S:3,T:1},{S:0,T:0}]
```

Đây là **SERVER TESTED**, không phải Android runtime confirmation.

## Bước quan trọng tiếp theo

Chạy APK đã patch + local server và mong đợi:

```text
POST ...User.asmx/Login
POST ...User.asmx/CheckUser
POST ...User.asmx/GetUserInfo
[BeginCutscene hoặc Home nếu đã có save]
POST ...User.asmx/SelectStartNhanVat   # chỉ lần đầu
[Home]
[Giang Hồ]
POST ...Battle.asmx/GiangHo
[BattleForm phát replay]
[result panel]
[quay Giang Hồ: mission kế mở + sao hiển thị]
```

Nếu fail: giữ server console log + `adb logcat`, reverse đúng request/exception cuối cùng.

Xem thêm: `docs/protocol/login.md`, `docs/protocol/first-character.md`, `docs/protocol/giangho-battle.md`, `HANDOFF.md`.
