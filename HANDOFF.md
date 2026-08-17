# HANDOFF — DaiMinhChu-Offline

> **Nguồn trạng thái chính của dự án.** Phiên ChatGPT mới phải đọc file này trước khi làm tiếp. Sau mỗi mốc kỹ thuật quan trọng hoặc trước khi kết thúc phiên, phải cập nhật HANDOFF để không phụ thuộc vào lịch sử chat.

**Last updated:** 2026-08-18 (UTC+7)

## 1. Mục tiêu dự án

Phục dựng **Đại Minh Chủ Việt Nam** (SohaGame / Hiker-Emobi) để chơi lại local/offline phục vụ hoài niệm/nghiên cứu, ưu tiên giữ client/UI/assets gốc.

Mục tiêu ưu tiên:

1. Client vượt login/server đã đóng.
2. Dựng backend local tương thích mà **không cần GS gốc** nếu khả thi.
3. Load user / đệ tử / đội hình / trang bị / võ công.
4. Vào Giang Hồ/phụ bản.
5. Phục dựng battle response / `BattleReplay` để client phát trận.
6. Save local bằng SQLite/JSON.

Không ưu tiên ở giai đoạn đầu: nạp tiền, Soha account thật, chat, bang hội online, PvP thật, liên server, leaderboard, payment.

## 2. Repository

- Repo: `maxskill115/DaiMinhChu-Offline`
- Default branch: `main`
- Repo đang **public** tại thời điểm kiểm tra.
- Không commit APK gốc, full asset dump, credential hay key riêng tư không cần thiết.

File quan trọng:

```text
README.md
HANDOFF.md
.gitignore
docs/protocol/login.md
server/app.py
server/dmc_crypto.py
server/requirements.txt
server/README.md
tools/patch_client.py
```

## 3. APK mẫu

Người dùng đã upload:

`Đại Minh Chủ (Dai Minh Chu)_8.0.2_apkcombo.com.apk`

Thông tin xác nhận:

- Size: `52,568,975` bytes (~50.1 MiB)
- SHA-256: `2ff6b4db2177dc1362c20866750a48371f283a79a40335d3293a26e39e7e4194`
- Package: `vn.sohagame.dminhchu`
- APK không commit lên repo.

## 4. Engine/runtime — CONFIRMED

APK dùng **Unity 4.x + Mono**, không phải IL2CPP-only.

Có:

```text
assets/bin/Data/Managed/Assembly-CSharp.dll
lib/armeabi-v7a/libunity.so
lib/armeabi-v7a/libmono.so
```

`Assembly-CSharp.dll` size: `2,425,856` bytes.

Nhiều class/method/field C# còn nguyên tên nên reverse thuận lợi.

## 5. Kiến trúc network — CONFIRMED

### 5.1 Base URL login gốc

`HTTP::.ctor` hard-code:

```text
http://login.minhchu.sohagame.vn/Server/Webservice/User.asmx
```

Các path được nối vào base URL:

```text
/Login
/CheckUser
/GetUserInfo
...
```

### 5.2 HTTP transport

`HTTP.SendRequest(url, json, callback, showLoading)`:

```text
JSON plaintext
  -> AES Encrypt
  -> Base64
  -> WWW.EscapeURL
  -> body UTF-8: data=<escaped_ciphertext>
  -> UnityEngine.WWW(url, postBytes)
```

Response:

```text
www.text
  -> AES.Decrypt
  -> JSON plaintext
  -> LitJson.JsonMapper.ToObject<T>
```

=> Đây là **HTTP + JSON có AES wrapper**, không phải bắt buộc GS TCP binary bí hiểm.

## 6. AES — CONFIRMED

Class `Aes` dùng `RijndaelManaged`:

```text
Mode      = CBC
Padding   = PKCS7
KeySize   = 128
BlockSize = 128
Encoding  = UTF-8
```

Default constructor dùng **cùng một 16-byte array làm Key và IV**.

```text
HEX:    03 05 1f 02 05 06 03 15 06 17 05 20 2a 1f 56 20
Base64: AwUfAgUGAxUGFwUgKh9WIA==
```

Đã lấy trực tiếp từ RVA data `$$field-33` trong assembly.

Repo đã có `server/dmc_crypto.py` dùng key/IV này.

## 7. Login flow — CONFIRMED

### 7.1 `HTTPLoginRequest`

Fields/properties:

```text
User        : string
Pass        : string
AccessToken : string
Platform    : string
Version     : int32
```

`HTTP.Login(callback,user,pass)` set:

```text
User
Pass
Version = GameManager.VERSION
```

rồi:

```text
JsonMapper.ToJson(request)
POST LoginURL + "/Login"
```

### 7.2 `HTTPLoginResponse`

Schema chính:

```text
ListUserServer    : List<int>
ErrorCode         : HTTP_ERROR_CODE
Token             : string
UserId            : string
SohaToken         : string
Servers           : List<ServerInfo>
ErrorMsg          : string
UrlUpdateAndroid  : string
UrlIphoneAppstore : string
UrlIphoneJb       : string
UrlWPJb           : string
LoginCfg          : LoginConfig
```

`ServerInfo`:

```text
ServerID : int32
Name     : string
Url      : string
Status   : string
```

### 7.3 ErrorCode

`WaitForLogin` xác nhận:

```text
ErrorCode == 1  -> success
ErrorCode == 11 -> VERSION_KHONG_DU / update popup
```

=> local mock dùng `ErrorCode: 1`.

### 7.4 Bỏ download config server cũ

`GameManager.DownloadConfigAndCache` có logic:

```text
if LoginResponse.LoginCfg == null:
    LoginForm.OnLoginSuccess()
    skip remote config bundle download
```

Đây là phát hiện rất quan trọng.

=> Prototype `/Login` trả:

```json
"LoginCfg": null
```

để vào form chọn server mà không tải config remote.

## 8. Soha SDK login — CONFIRMED

APK còn flow Soha HTTPS:

```text
https://soap.soha.vn/api/a/GET/auth/login?app_id=ba4b944aee28ea8b5c675ad0542f97f3&email={0}&password={1}&gver=2.0.0&sdkver=0.0.0&clientname=sohagame
```

`LoginForm.OnLoginBtnClick` bản Android thực tế gọi:

```text
SohaSDKManager.Login()
```

và Java bridge gọi `RequestLoginSoha`.

Đây là blocker nếu để nguyên client.

### Bypass đã viết

`tools/patch_client.py` đã patch IL `LoginForm.OnLoginBtnClick` thành flow trực tiếp:

```text
HTTP.Instance.Login(
    new OnRequest(HTTP.Instance.WaitForLogin),
    accountInput.text,
    passInput.text
)
```

=> bỏ Java Soha SDK cho nút login.

Patcher cũng sửa hard-coded `HTTP.loginURL` sang URL local do người chạy chỉ định.

Patcher chỉ chấp nhận APK có SHA-256 đúng bản 8.0.2 đang nghiên cứu để tránh patch nhầm version.

## 9. `/CheckUser` — CONFIRMED

`HTTP.CheckUser(callback, serverUrl)`:

```text
LobbyURL = serverUrl
request.User  = HTTP.UserInfo.User
request.Token = HTTP.UserInfo.AccessToken
POST LobbyURL + "/CheckUser"
```

`HTTPCheckUserRequest`:

```text
User  : string
Token : string
```

`HTTPCheckUserResponse` quan trọng:

```text
LoginMessage       : List<string>
EventAnGaLuotCount : int32
ErrorCode          : HTTP_ERROR_CODE
Aid                : int32
UserInfo           : HTTPGetUserInfoResponse
ErrorMsg           : string
ServerID           : int32
```

Success `ErrorCode == 1`.

Khi success:

```text
HTTP.UserInfo.AID = response.Aid
SelectServerForm.OnLobbyLoginSuccess()
```

## 10. Sau CheckUser — CONFIRMED

`SelectServerForm.OnLobbyLoginSuccess()`:

1. lưu ServerID;
2. nếu server chưa có trong `LoginResponse.ListUserServer` thì có thể gọi `UserAppendServer`;
3. gọi `GameManager.LoadAllUserInfo(HTTP.WaitForGetUserInfo)`.

=> prototype `/Login` trả:

```json
"ListUserServer": [1]
```

để tránh request `UserAppendServer` cho server offline ID 1.

## 11. `/GetUserInfo` — CONFIRMED

Request:

```text
Aid      = HTTP.UserInfo.AID
Token    = HTTP.UserInfo.AccessToken
Property = List<property>
```

`property` có:

```text
Name : string
```

`GameManager.LoadAllUserInfo` request đúng 21 property:

```text
account
nhanVat
trangBi
voCong
orb
vatPhamTieuThu
giaTriThoiGian
doiHinh
giangHo
tanChuong
honNhanVat
mail
banbe
danhhieu
danhson
serverinfo
lienminh
kimcham
moiruou
longchau
amkhi
```

`HTTPGetUserInfoResponse` chứa các nhóm tương ứng.

### Tối thiểu client đọc ngay khi success

`WaitForGetUserInfo` truy cập ngay:

```text
GiaTriThoiGian.TimeServer
Account.DisplayName
Account.Level
NhanVat
```

Nếu:

```text
NhanVat == null hoặc Count == 0
```

client chuyển sang **Form index 13** — nhánh account chưa có nhân vật / chọn nhân vật ban đầu.

Nếu `NhanVat.Count > 0`, client chuyển sang **Form index 3** — flow gameplay chính và cần nhiều schema hơn.

=> milestone đầu cố ý dùng `NhanVat: []` để chứng minh end-to-end login trước.

## 12. Local compatibility server đã tạo

Repo:

```text
server/app.py
server/dmc_crypto.py
server/requirements.txt
server/README.md
```

Server hiện có:

```text
GET  /health
POST /Login
POST /CheckUser
POST /GetUserInfo
```

Handler match suffix nên cũng nhận:

```text
/Server/Webservice/User.asmx/Login
/Server/Webservice/User.asmx/CheckUser
/Server/Webservice/User.asmx/GetUserInfo
```

Server:

- decrypt request AES;
- log JSON plaintext;
- dựng mock response;
- encrypt response lại đúng AES client.

Dependency hiện tại:

```text
pycryptodome>=3.20,<4
```

## 13. Patcher client đã tạo và đã validate static

File:

```text
tools/patch_client.py
```

Patcher làm 2 việc:

1. sửa string login server gốc trong `Assembly-CSharp.dll` thành local base URL;
2. thay IL `LoginForm.OnLoginBtnClick` để gọi thẳng `HTTP.Login` thay vì `SohaSDKManager.Login`.

Test local đã chạy thành công trên APK mẫu:

```text
HTTP::.ctor loginURL
  -> http://10.0.2.2:8000/Server/Webservice/User.asmx
```

IL sau patch đã disassemble lại thành:

```text
call HTTP::get_Instance
call HTTP::get_Instance
ldftn HTTP::WaitForLogin
newobj OnRequest::.ctor
ldarg.0
ldfld LoginForm::accountInput
callvirt UIInput::get_text
ldarg.0
ldfld LoginForm::passInput
callvirt UIInput::get_text
callvirt HTTP::Login
ret
```

=> patch IL về mặt metadata/IL đã đúng theo dự kiến.

Patcher rebuild APK nên original signature không còn hợp lệ. Code hiện loại signature files cũ khi rebuild; APK phải được sign lại trước khi install.

## 14. Artifact local đã tạo trong phiên này

Không commit APK lên GitHub.

Đã tạo thử trong workspace ChatGPT:

```text
/mnt/data/DaiMinhChu_8.0.2_local_unsigned2.apk
/mnt/data/DaiMinhChu_8.0.2_local_debugsigned.apk
```

Bản `local_debugsigned.apk` đã được ký test bằng certificate tạm/self-signed và `jarsigner -verify` báo **jar verified**.

URL patch trong artifact test là:

```text
http://10.0.2.2:8000/Server/Webservice/User.asmx
```

=> phù hợp chủ yếu với Android Emulator kiểu có host gateway `10.0.2.2`; chưa chắc phù hợp LDPlayer/máy thật. Nếu test trên máy thật/LAN nên chạy patcher với IP PC thực tế.

Không lưu/không chia sẻ keystore tạm.

## 15. Battle — trạng thái hiện tại

Đã xác nhận class:

```text
HTTPBattleGiangHoRequest
HTTPBattleGiangHoResponse
KetQuaTranDau / BattleReplay
BattleReward
```

`HTTPBattleGiangHoRequest` fields:

```text
aid        : int32
token      : string
giangHoIdx : uint8
nhiemVuIdx : uint8
```

`HTTPBattleGiangHoResponse`:

```text
BattleReplay  : KetQuaTranDau
Reward        : BattleReward
giangHoIdx    : uint8
nhiemVuIdx    : uint8
star          : uint8
UpdateUserInfo: HTTPGetUserInfoResponse
ErrorCode     : HTTP_ERROR_CODE
ErrorMsg      : string
```

Suy luận mạnh: server sinh kết quả/replay; client chủ yếu phát animation. Cần reverse nested replay sau khi login end-to-end chạy thật.

## 16. Kiến trúc mục tiêu

```text
Patched APK
    |
    | HTTP + data=<AES(Base64(JSON))>
    v
Local Compatibility Server
    |
    +-- Login
    +-- CheckUser
    +-- User/Profile
    +-- Hero/Formation
    +-- Inventory/Equipment/Skills
    +-- GiangHo
    +-- BattleReplay generator
    |
    v
SQLite / JSON local save
```

## 17. Roadmap / trạng thái

### Phase 0 — Bootstrap repo

- [x] Repo
- [x] README
- [x] HANDOFF
- [x] `.gitignore`
- [x] protocol docs
- [x] server skeleton
- [x] patcher skeleton

### Phase 1 — Reverse login flow

- [x] Xác định HTTP class và endpoint builder
- [x] `/Login` request/response schema
- [x] `/CheckUser` request/response schema
- [x] `/GetUserInfo` request/response chính
- [x] AES algorithm + Key/IV
- [x] Flow Soha SDK cần bypass
- [x] `LoginCfg=null` để skip config remote
- [x] 21 property GetUserInfo
- [ ] Test runtime thật trên Android/emulator

### Phase 2 — Minimal local server

- [x] `/health`
- [x] `/Login`
- [x] `/CheckUser`
- [x] `/GetUserInfo`
- [x] request logging
- [x] AES decrypt/encrypt
- [ ] Run server + client thật và xác nhận request đến PC
- [ ] Fix schema/date serialization nếu runtime báo lỗi

### Phase 3 — Patch/redirect client

- [x] Patch base login URL
- [x] Bypass `SohaSDKManager.Login` ở nút login bằng IL patch
- [x] Rebuild APK
- [x] Static disassembly validation
- [x] Debug-sign test artifact bằng v1/JAR signature
- [ ] Install/run trên Android thật
- [ ] Nếu `PlayerPrefs login != 0` làm auto Soha login: clear app data trước hoặc patch `LoginForm.OnActive`

### Phase 4 — User/game state

- [ ] Tạo/chọn starter hero
- [ ] NhanVat schema
- [ ] DoiHinh
- [ ] TrangBi
- [ ] VoCong
- [ ] inventory
- [ ] save local

### Phase 5 — Giang Hồ/Battle

- [ ] Full GiangHo schema
- [ ] Full `KetQuaTranDau/BattleReplay` nested schema
- [ ] replay fixture đơn giản
- [ ] client phát được 1 battle
- [ ] battle generator

## 18. Việc cần làm NGAY tiếp theo

**Ưu tiên số 1: test end-to-end thật.**

1. Xác định môi trường Android user sẽ dùng: emulator nào / máy thật / IP PC.
2. Chạy local server từ repo:

```text
cd server
pip install -r requirements.txt
set DMC_BASE_URL=http://<IP-PC>:8000
python app.py
```

3. Chạy `tools/patch_client.py` với cùng IP/base URL.
4. Sign APK patched.
5. Clear app data để tránh PlayerPrefs auto Soha login cũ.
6. Mở APK, bấm login.
7. Quan sát console server xem có request `/Login` không.
8. Nếu `/Login` OK, theo dõi `/CheckUser` và `/GetUserInfo`.
9. Thu log + ảnh màn hình lỗi/success.
10. Sửa response schema theo lỗi runtime.

**Definition of milestone:** client đi được từ màn login đến form chọn server rồi form tạo/chọn nhân vật bằng local server.

## 19. Quy tắc làm việc cho các phiên ChatGPT sau

1. **Luôn đọc `HANDOFF.md` trước.**
2. Không yêu cầu người dùng kể lại những gì đã có trong HANDOFF.
3. Phân biệt rõ **CONFIRMED** và **HYPOTHESIS**.
4. Không reverse lan man feature chưa cần; ưu tiên đường critical path offline.
5. Commit code/docs sau mỗi mốc có giá trị.
6. Sau mỗi mốc, cập nhật HANDOFF với:
   - phát hiện mới;
   - file/commit đã thay đổi;
   - test đã chạy;
   - blocker;
   - bước tiếp theo cụ thể.
7. APK gốc và full game asset không đưa lên repo.

## 20. Ghi chú người dùng

- Người dùng từng chơi Đại Minh Chủ Việt Nam bản cũ và muốn chơi lại offline để hoài niệm.
- Người dùng yêu cầu dự án phải giữ trạng thái trên GitHub/HANDOFF để có thể mở chat mới và tiếp tục ngay khi cuộc chat hiện tại quá dài.
- Vì vậy **cập nhật HANDOFF là yêu cầu bắt buộc liên tục, không cần đợi người dùng nhắc lại**.
