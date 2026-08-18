# HANDOFF — DaiMinhChu-Offline

> **ĐỌC FILE NÀY TRƯỚC KHI TIẾP TỤC Ở CHAT MỚI.** Đây là nguồn trạng thái chính của dự án. Sau mỗi mốc kỹ thuật quan trọng phải cập nhật lại HANDOFF.

**Last updated:** 2026-08-18 (UTC+7)

## 1. Mục tiêu

Phục dựng **Đại Minh Chủ Việt Nam 8.0.2** để chơi local/offline, ưu tiên giữ client/UI/assets gốc. Hướng hiện tại: backend tương thích local.

Flow mục tiêu:

```text
Login -> user/tướng/đội hình -> Giang Hồ -> BattleReplay -> progression/save
```

Chưa ưu tiên: Soha account thật, nạp tiền, chat, bang hội/PvP online, liên server, leaderboard.

## 2. Repo / APK

Repo: `maxskill115/DaiMinhChu-Offline`, branch `main`.

APK mục tiêu:

```text
package: vn.sohagame.dminhchu
version: 8.0.2
size: 52,568,975 bytes
SHA256: 2ff6b4db2177dc1362c20866750a48371f283a79a40335d3293a26e39e7e4194
Unity 4.x / Mono / ARMv7
```

Không commit APK gốc, full asset/config dump, credential hoặc keystore.

## 3. Network/protocol — CONFIRMED STATIC

Login URL gốc:

```text
http://login.minhchu.sohagame.vn/Server/Webservice/User.asmx
```

Transport:

```text
LitJson JSON -> AES -> Base64 -> WWW.EscapeURL -> POST data=<cipher>
response -> AES decrypt -> LitJson
```

AES:

```text
AES/Rijndael-128 CBC PKCS7 UTF-8
Key = IV = 03051f0205060315061705202a1f5620
```

## 4. Client patch

`tools/patch_client.py` được thiết kế để patch đúng APK SHA:

1. login URL sang local;
2. `LoginForm.OnLoginBtnClick` bỏ `SohaSDKManager.Login()` và gọi trực tiếp `HTTP.Instance.Login(...)`;
3. patch `SohaSDKManager.SetUserInfo(...)` thành no-op (`ret`) để bỏ bridge Soha SDK cũ gây NPE sau `/GetUserInfo`.

Static metadata của đúng APK:

```text
SohaSDKManager.SetUserInfo RVA = 0xCB940
original IL code size = 41 bytes
original IL = 02 7b e4 23 00 04 72 2e cd 01 70 1a 8d 08 00 00 01 25 16 03 a2 25 17 05 a2 25 18 0e 04 a2 25 19 0e 05 a2 6f 99 09 00 0a 2a
replacement IL intended = 2a
```

`tools/verify_client.py` đọc trực tiếp APK và xác minh Login URL, direct-login patch và SetUserInfo body.

## 5. Core config — CONFIRMED STATIC

Client có embedded configs: NhanVat, TrangBi, VoCong, GiangHo, Other, ChanKhi, VatPhamTieuThu, HuyetChien, KimCham, LongChau...

`LoginCfg=null` có thể dùng để bỏ remote config update. Khoảng 333 nhân vật đã được parse từ NhanVat; không commit dump gốc.

## 6. Login / first character — CONFIRMED STATIC + SERVER IMPLEMENTED

Flow:

```text
/Login -> /CheckUser -> /GetUserInfo
```

Nếu `NhanVat.Count==0` -> `BeginCutsceneForm` / Form 13.

Starter:

```text
NV_PhongThanhDuong
NV_LenhHoXung
NV_SoLuuHuong
```

`/SelectStartNhanVat` request: `Aid`, `Token`, `NhanVatCode`.

## 7. Home / Giang Hồ / Battle — CONFIRMED STATIC + SERVER IMPLEMENTED

Home = Form 3. Giang Hồ = Form 4. Battle = Form 7.

Battle endpoint:

```text
POST <BattleURL>/GiangHo
```

Request fields:

```text
aid
token
giangHoIdx
nhiemVuIdx
```

Server hiện tạo BattleReplay deterministic 1v1 / 1 hiệp / 1 đòn thường, Team1 thắng 3 sao.

## 8. Progress/save — SERVER IMPLEMENTED + TESTED

`server/state.py` lưu JSON tại:

```text
server/local_data/save.json
```

GiangHo `Nhiemvu` là JSON-string array của `{S,T}`:

```text
S = best star
T = lượt đánh
```

Embedded GiangHo structure đã xác nhận:

```text
92 chapter
1405 mission
chapter 0: 6 mission
chapter 1: 7 mission
```

Server persist starter, bạc và GiangHo progression.

## 9. Tests — SERVER TESTED

11 unit tests pass trên Windows ngày 2026-08-18.

Encrypted HTTP smoke cũng pass:

```text
Login -> CheckUser -> GetUserInfo -> SelectStartNhanVat -> Battle.asmx/GiangHo
```

## 10. Server runtime hiện tại

Server chạy:

```text
DMC_BASE_URL=http://192.168.1.14:8000
Listen: 0.0.0.0:8000
User.asmx: http://192.168.1.14:8000/Server/Webservice/User.asmx
Battle.asmx: http://192.168.1.14:8000/Server/Webservice/Battle.asmx
```

LDPlayer truy cập `/health` thành công.

## 11. Emulator compatibility — CONFIRMED RUNTIME

### LDPlayer 64-bit

Cả APK gốc và patched đều crash gần lúc Unity/OpenGL init, process chết signal 6. Vì APK gốc cũng crash nên không quy lỗi cho patch/server.

### LDPlayer 32-bit

**Đây là môi trường runtime đúng hiện tại.**

Bản patched signed khởi động thành công đến Start/Login/SelectServer và client thật đã giao tiếp thành công với local backend qua AES:

```text
POST /Server/Webservice/User.asmx/Login -> HTTP 200 ErrorCode=1
POST /Server/Webservice/User.asmx/CheckUser -> HTTP 200 ErrorCode=1
POST /Server/Webservice/User.asmx/GetUserInfo -> HTTP 200 ErrorCode=1
```

## 12. Runtime blocker sau GetUserInfo — CONFIRMED RUNTIME

Root cause:

```text
AndroidJavaException: java.lang.NullPointerException
SohaSDK.setUserConfig(...) on a null object reference
at SohaSDKManager.SetUserInfo(...)
at HTTP+<WaitForGetUserInfo>c__IteratorC4.MoveNext()
```

=> transport/backend đã qua; blocker là legacy Soha SDK bridge.

## 13. Phát hiện mới nhất — CONFIRMED: APK output thực tế CHƯA chứa Soha no-op patch

User đã pull repo tới commit `999082dd` và chạy `tools/verify_client.py` trên cả file signed ở PC và chính `base.apk` pull từ LDPlayer.

### PC artifact

```text
python tools\verify_client.py DMC_local_signed.apk

Login URL: http://192.168.1.14:8000/Server/Webservice/User.asmx
Direct login patch: OK
Soha SetUserInfo no-op: MISSING
SetUserInfo IL: 02 7b e4 23 00 04 72 2e cd 01 70 1a 8d 08 00 00 01 25 16 03 a2 25 17 05 a2 25 18 0e 04 a2 25 19 0e 05 a2 6f 99 09 00 0a 2a
```

### Installed APK pulled directly from LDPlayer

ADB path:

```text
/data/app/vn.sohagame.dminhchu-1/base.apk
```

Verify:

```text
Direct login patch: OK
Soha SetUserInfo no-op: MISSING
SetUserInfo IL: 02 7b e4 23 00 04 72 2e cd 01 70 1a 8d 08 00 00 01 25 16 03 a2 25 17 05 a2 25 18 0e 04 a2 25 19 0e 05 a2 6f 99 09 00 0a 2a
```

=> **Đã loại trừ LDPlayer cache/cài nhầm APK** ở bước này. File signed trên PC và APK thật đang cài đều cùng thiếu patch #3. Direct-login patch và URL patch có mặt, chỉ `SetUserInfo` vẫn nguyên body 41 byte.

Patcher trước đó có in dòng "Patched legacy SohaSDKManager.SetUserInfo..." nhưng artifact chứng minh dòng thông báo đó không đủ để xác nhận patch đã được ghi. Phải sửa/siết pipeline để self-verify artifact trước khi sign/install.

## 14. Việc cần làm NGAY

1. Điều tra `tools/patch_client.py` tại bước ghi `Assembly-CSharp.dll` và xác minh `DMC_local_unsigned.apk` ngay sau patch.
2. Xóa artifact cũ hoặc dùng tên output mới để tránh nhầm file.
3. Sau patch, bắt buộc chạy:

```bat
python tools\verify_client.py <unsigned-apk>
```

và chỉ được tiếp tục zipalign/sign nếu:

```text
Direct login patch: OK
Soha SetUserInfo no-op: OK
SetUserInfo IL: 2a
```

4. Verify lại file signed trước khi cài.
5. Cài vào LDPlayer 32-bit, pull `base.apk` và verify lần cuối nếu cần.
6. Runtime retest. Nếu không còn `SetUserInfo` NPE, tiếp tục tới BeginCutsceneForm / SelectStartNhanVat.

ADB serial hiện tại:

```text
127.0.0.1:5601
```

Không dùng LDPlayer 64-bit cho test chính.

## 15. Trạng thái chính xác

```text
CONFIRMED STATIC:
  login -> first character -> Home -> GiangHo -> BattleForm -> result
  + schema/semantics GiangHo progression

SERVER IMPLEMENTED:
  login/user/start hero/battle/save/progression

SERVER TESTED:
  AES + HTTP chain + persistence + mission unlock

CONFIRMED RUNTIME (LDPlayer 32-bit):
  APK boot
  /Login
  /CheckUser
  /GetUserInfo transport/decrypt
  blocker = legacy SohaSDK SetUserInfo call

CONFIRMED ARTIFACT STATE:
  DMC_local_signed.apk: direct-login OK, SetUserInfo no-op MISSING
  installed base.apk: direct-login OK, SetUserInfo no-op MISSING
  => không phải LDPlayer cache; cần sửa build/patch artifact
```

## 16. Quy tắc bắt buộc

- Luôn phân biệt `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore.
- Ưu tiên flow nhỏ, deterministic, testable.
- **Sau mỗi mốc quan trọng phải cập nhật HANDOFF**.
