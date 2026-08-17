# HANDOFF — DaiMinhChu-Offline

> File này là nguồn trạng thái chính để phiên ChatGPT sau có thể tiếp tục ngay mà không cần đọc lại toàn bộ lịch sử chat. Mỗi phiên làm việc phải cập nhật file này trước khi kết thúc hoặc sau mỗi mốc kỹ thuật quan trọng.

**Last updated:** 2026-08-18 00:23 (UTC+7)

## 1. Mục tiêu dự án

Phục dựng **Đại Minh Chủ Việt Nam** (SohaGame / Hiker-Emobi) để có thể chơi lại ở chế độ local/offline phục vụ mục đích hoài niệm/nghiên cứu.

Mục tiêu ưu tiên, theo thứ tự:

1. Cho APK gốc khởi động và vượt qua login/server cũ.
2. Dựng local backend tương thích với client mà **không cần GS gốc** nếu khả thi.
3. Load được user / đội hình / đệ tử / trang bị / võ công.
4. Vào được Giang Hồ/phụ bản.
5. Phục dựng battle response / BattleReplay đủ để client chạy trận.
6. Lưu tiến trình local (SQLite/JSON).
7. Chỉ sau khi phần offline cơ bản ổn mới xét tới các hệ thống phụ khác.

Không ưu tiên: nạp tiền, Soha account thật, chat, bang hội online, PvP thật, liên server, leaderboard, payment.

## 2. Repo

- Repository: `maxskill115/DaiMinhChu-Offline`
- URL: `https://github.com/maxskill115/DaiMinhChu-Offline`
- Default branch: `main`
- Trạng thái lúc khởi tạo: repo trống.
- Lưu ý: repo hiện đang **public** theo metadata GitHub lúc 2026-08-18. Không đưa APK gốc, asset game đầy đủ, credential, key riêng tư hoặc dữ liệu có bản quyền không cần thiết lên repo.

## 3. APK mẫu đang phân tích

Tên file người dùng đã cung cấp:

`Đại Minh Chủ (Dai Minh Chu)_8.0.2_apkcombo.com.apk`

Thông tin local trong phiên hiện tại:

- Kích thước: ~50.1 MiB (52,568,975 bytes)
- SHA-256: `2ff6b4db2177dc1362c20866750a48371f283a79a40335d3293a26e39e7e4194`
- Package đã thấy trong assembly: `vn.sohagame.dminhchu`
- APK **không được commit lên repo**.

## 4. Phát hiện đã xác nhận từ APK

### 4.1 Engine / runtime

Đã kiểm tra trực tiếp APK:

- Unity 4.x, Mono runtime.
- Có `assets/bin/Data/Managed/Assembly-CSharp.dll`
- `Assembly-CSharp.dll` size: `2,425,856` bytes.
- Có `lib/armeabi-v7a/libunity.so`
- Có `lib/armeabi-v7a/libmono.so`
- Không phải kiểu IL2CPP-only; đây là lợi thế lớn vì metadata C# còn nhiều tên class/method.

Đường dẫn xác nhận:

```text
assets/bin/Data/Managed/Assembly-CSharp.dll
lib/armeabi-v7a/libunity.so
lib/armeabi-v7a/libmono.so
```

### 4.2 Endpoint/server cũ

Strings trong `Assembly-CSharp.dll` xác nhận:

```text
http://login.minhchu.sohagame.vn/Server/Webservice/User.asmx
```

Login Soha cũ:

```text
https://soap.soha.vn/api/a/GET/auth/login?app_id=ba4b944aee28ea8b5c675ad0542f97f3&email={0}&password={1}&gver=2.0.0&sdkver=0.0.0&clientname=sohagame
```

Các string liên quan:

```text
/Login
/GetUserInfo
```

### 4.3 Class/API đáng chú ý

Tên class/method còn đọc được trong assembly, ví dụ:

```text
HTTPLoginRequest
HTTPLoginResponse
HTTPGetUserInfoRequest
HTTPGetUserInfoResponse
HTTPBattleGiangHoRequest
HTTPBattleGiangHoResponse
BattleReplay
GameManager
LoginForm
GiangHoForm
```

Một số endpoint/hành vi đã thấy hoặc đã được ghi nhận từ static strings/metadata:

```text
/Login
/Register
/GetUserInfo
/GiangHo
/SetDoiHinh
/EquipTrangBi
/UpgradeTrangBi
/UpgradeVoCong
/LuyenKhi
/DauLuanKiem
/GetHuyetChienInfo
/DauHuyetChien
/GetHacMocNhaiBattle
/DanhNienThu
```

Cần tiếp tục xác nhận chính xác request/response schema từng endpoint từ IL/decompile, không chỉ dựa vào string.

### 4.4 Serialization / transport

Assembly chứa các dấu hiệu:

```text
WWWForm
LitJson
JsonMapper
ToJson
JsonReader
JsonWriter
```

Giả thuyết mạnh hiện tại: phần lớn backend game dùng HTTP + form/JSON, thay vì bắt buộc một GS TCP binary phức tạp.

**Chưa được phép coi là hoàn toàn xác nhận** cho tất cả endpoint cho tới khi trace/decompile method tạo request.

### 4.5 Battle / BattleReplay

Tên class và field liên quan battle đã thấy:

```text
HTTPBattleGiangHoRequest
HTTPBattleGiangHoResponse
BattleReplay
BattleGiangHoResultPanel
BattleReplayPanel
```

Các field/tên đã ghi nhận từ lần phân tích trước trong cùng dự án:

```text
GiangHoIdx
NhiemVuIdx
Star
BattleReplay
Reward
UpdateUserInfo
```

BattleReplay được ghi nhận có cấu trúc kiểu:

```text
DoiThang
Team1
Team2
Hiep1
Hiep2
Hiep3
```

Các khái niệm lượt đánh/kết quả đã thấy/ghi nhận:

```text
DoiTanCong
NguoiTanCong
DanhSachThuongTon
VoCong
BaoKich
NeDon
PhanKich
PhanChan
HoThe
HapHuyet
PhanChuong
```

**Suy luận hiện tại:** server nhiều khả năng tạo kết quả trận + `BattleReplay`, client nhận replay rồi phát animation. Vì vậy client gốc không đủ để chơi hoàn chỉnh nếu không có backend tương thích. Tuy nhiên không cần GS gốc nếu ta có thể tái tạo response đúng schema.

### 4.6 Logic gameplay có trong client

Các tên method đã ghi nhận cho thấy client chứa khá nhiều logic/config chỉ số, ví dụ:

```text
GetCongCoSo
GetThuCoSo
GetMauCoSo
GetNoiLucCoSo
GetChiSoNhanVat
GetChiSoTrangBi
GetEffectsFromVoCong
GetEffectsFromDuyenPhanVoCong
GetEffectsFromDuyenPhanDoiHinh
GetEffectsFromKinhMach
GetEffectsFromLongChau
GetEffectsFromAmKhi
```

Điều này cho thấy có cơ hội tái sử dụng công thức/config ở client để dựng mini-GS thay vì viết lại mọi thứ từ đầu.

### 4.7 Crypto

Assembly có các tên:

```text
Aes
RijndaelManaged
MD5CryptoServiceProvider
Encrypt
Decrypt
base64key
base64iv
```

Cần xác định crypto được dùng cho endpoint nào, key/IV lấy ở đâu và request/response có cần mã hóa không.

## 5. Kết luận kỹ thuật hiện tại

- **Chỉ có APK thì chưa chạy offline ngay được.**
- **Không nhất thiết phải có GS gốc** nếu reverse được protocol/schema và viết backend tương thích.
- APK này thuận lợi hơn nhiều so với client native/IL2CPP đã strip vì là Unity Mono và còn nhiều symbol C#.
- Hướng khả thi nhất hiện tại là **local HTTP backend + patch/redirect endpoint của client**.

Đánh giá sơ bộ:

| Thành phần | Đánh giá hiện tại |
|---|---|
| Khởi động client/UI | Khả thi |
| Bỏ Soha login | Rất khả thi |
| Fake server/login | Khả thi |
| GetUserInfo | Khả thi sau khi biết schema |
| Đội hình / tướng / trang bị / võ công | Khả thi |
| Save local | Khả thi |
| Giang Hồ | Khả thi sau khi dựng schema |
| Combat | Khó hơn; cần sinh `BattleReplay` hợp lệ |
| GS gốc Soha | Không bắt buộc nếu mini-GS đủ tương thích |

## 6. Kiến trúc mục tiêu dự kiến

```text
APK gốc (hoặc APK patch endpoint)
        |
        | HTTP/JSON/form
        v
Local Compatibility Server
        |
        +-- Auth/Login mock
        +-- User/Profile
        +-- Hero/Formation
        +-- Inventory/Equipment/Skill
        +-- GiangHo
        +-- BattleReplay generator
        |
        v
SQLite hoặc JSON save local
```

Ngôn ngữ backend đề xuất ban đầu: **Python** để reverse/prototype nhanh. Sau này chỉ đổi stack nếu có lý do rõ ràng.

## 7. Roadmap thực thi

### Phase 0 — Bootstrap repo

- [x] Tạo repo.
- [x] Tạo HANDOFF chuẩn.
- [ ] Tạo README / docs / skeleton server.
- [ ] Tạo `.gitignore`.

### Phase 1 — Reverse login flow

Mục tiêu: xác định chính xác luồng từ mở app đến màn hình chính.

- [ ] Decompile `Assembly-CSharp.dll` đủ sâu để lấy method signatures.
- [ ] Xác định class trung tâm thực hiện HTTP request.
- [ ] Xác định base URL / endpoint builder.
- [ ] Xác định body của `/Login`.
- [ ] Xác định schema `HTTPLoginResponse`.
- [ ] Xác định body/schema `/GetUserInfo`.
- [ ] Xác định token/session flow.
- [ ] Xác định có encryption/signature/checksum không.

**Definition of done:** có tài liệu request/response đủ để viết mock `/Login` + `/GetUserInfo`.

### Phase 2 — Minimal local server

- [ ] Python server chạy localhost/LAN.
- [ ] `/health`
- [ ] `/Login`
- [ ] `/GetUserInfo`
- [ ] logging toàn bộ request.
- [ ] fixture JSON/form response.

**Definition of done:** client kết nối vào server local và tiến xa hơn trạng thái server-dead ban đầu.

### Phase 3 — Patch/redirect client

Các phương án cần thử theo thứ tự ít xâm lấn:

1. DNS/hosts redirect nếu host/HTTP cho phép.
2. Patch string base URL trong `Assembly-CSharp.dll`.
3. Patch C# method tạo endpoint nếu cần.
4. Resign APK và test Android/emulator.

### Phase 4 — User/game state

- [ ] User info
- [ ] Currency/resource
- [ ] Hero list
- [ ] Formation
- [ ] Equipment
- [ ] Skills
- [ ] Upgrade endpoints tối thiểu
- [ ] Save local

### Phase 5 — Giang Hồ / Battle

- [ ] Reverse `HTTPBattleGiangHoRequest`.
- [ ] Reverse đầy đủ `HTTPBattleGiangHoResponse`.
- [ ] Reverse nested `BattleReplay` classes.
- [ ] Tạo replay fixture tối thiểu.
- [ ] Test client phát được 1 trận.
- [ ] Sau đó mới viết battle generator thực sự.

## 8. Quy tắc phát triển

1. Không commit APK gốc hoặc dump asset đầy đủ lên repo.
2. Tài liệu reverse phải ghi rõ cái gì là **CONFIRMED**, cái gì là **HYPOTHESIS**.
3. Mọi endpoint sau khi reverse phải ghi:
   - method HTTP
   - path
   - request fields
   - response fields
   - encoding/encryption
   - sample fixture tự tạo
   - nơi client gọi endpoint đó
4. Không cố phục dựng mọi online feature trước khi login → gameplay cơ bản hoạt động.
5. Ưu tiên tạo test fixture nhỏ, deterministic.
6. Trước khi kết thúc mỗi phiên ChatGPT: cập nhật `HANDOFF.md` với:
   - đã làm gì
   - file/commit nào thay đổi
   - phát hiện mới
   - blocker
   - bước tiếp theo chính xác

## 9. Việc cần làm NGAY ở phiên tiếp theo

1. Đọc `HANDOFF.md` trước.
2. Lấy APK 8.0.2 nếu phiên mới vẫn còn attachment; nếu không có thì người dùng có thể cần upload lại APK cho việc phân tích binary local.
3. Reverse `HTTPLoginRequest`, `HTTPLoginResponse`, `HTTPGetUserInfoRequest`, `HTTPGetUserInfoResponse` từ `Assembly-CSharp.dll`.
4. Tạo `docs/protocol/login.md` với schema cụ thể.
5. Dựng `server/` prototype chỉ sau khi schema đủ rõ.
6. Cập nhật lại HANDOFF sau mỗi mốc.

## 10. Ghi chú từ người dùng

- Người dùng từng chơi Đại Minh Chủ bản Việt Nam cũ và mục tiêu chính là chơi lại offline để hoài niệm.
- Người dùng chủ động muốn GitHub làm nơi lưu trạng thái dự án để khi chat quá dài có thể mở chat mới và tiếp tục ngay.
- Vì vậy `HANDOFF.md` phải được coi là bắt buộc và cập nhật liên tục, không đợi tới khi người dùng nhắc lại.
