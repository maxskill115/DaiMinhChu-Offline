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

`tools/patch_client.py` patch đúng APK SHA:

1. login URL sang local;
2. `LoginForm.OnLoginBtnClick` bỏ `SohaSDKManager.Login()` và gọi trực tiếp `HTTP.Instance.Login(...)`;
3. patch `SohaSDKManager.SetUserInfo(...)` thành no-op (`ret`) để bỏ bridge Soha SDK cũ gây NPE sau `/GetUserInfo`.

Static metadata của đúng APK đã xác nhận:

```text
SohaSDKManager.SetUserInfo RVA = 0xCB940
original IL code size = 41 bytes
replacement IL = 0x2A (ret)
```

Patcher chạy local đã in:

```text
Patched legacy SohaSDKManager.SetUserInfo to no-op for offline runtime.
```

Nhưng runtime retest 10:58 vẫn thấy stack chạy `SohaSDKManager.SetUserInfo`, vì vậy **chưa được coi patch #3 đã có hiệu lực trên APK thực sự đang chạy**.

Để phân biệt "APK output đúng nhưng LDPlayer vẫn chạy bản cũ/cache" với "patcher ghi sai", đã thêm:

```text
tools/verify_client.py
```

Tool này đọc trực tiếp APK và xác minh:

```text
Login URL
Direct login patch
Soha SetUserInfo no-op
SetUserInfo IL
```

Commit tool verify:

```text
7bb09977  Thêm tool xác minh APK đã patch/cài đặt
```

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

Bản patched signed khởi động thành công đến màn hình Start/Login/SelectServer.

Client thật đã giao tiếp thành công với local backend qua AES:

```text
POST /Server/Webservice/User.asmx/Login -> HTTP 200 ErrorCode=1
POST /Server/Webservice/User.asmx/CheckUser -> HTTP 200 ErrorCode=1
POST /Server/Webservice/User.asmx/GetUserInfo -> HTTP 200 ErrorCode=1
```

## 12. Runtime blocker sau GetUserInfo — CONFIRMED RUNTIME

Root cause ban đầu đã xác định:

```text
AndroidJavaException: java.lang.NullPointerException
SohaSDK.setUserConfig(...) on a null object reference
at SohaSDKManager.SetUserInfo(...)
at HTTP+<WaitForGetUserInfo>c__IteratorC4.MoveNext()
```

Patcher đã được sửa để no-op `SohaSDKManager.SetUserInfo`.

### Retest mới lúc 10:58

APK được build lại từ APK gốc, zipalign và ký lại. Log mới có PID mới `4324`, flow:

```text
Form StartForm active
Form LoginForm active
Form SelectServerForm active
WaitForCheckUser done
```

Nhưng vẫn xuất hiện cùng stack:

```text
SohaSDKManager.SetUserInfo(...)
SohaSDK.setUserConfig(...) -> NPE
```

=> **CONFIRMED:** package runtime vẫn thực thi body cũ của `SetUserInfo`.

Chưa kết luận nguyên nhân là patcher hay cài/cache. Bước tiếp theo bắt buộc là xác minh bytecode của:

1. `DMC_local_signed.apk` trên PC;
2. `base.apk` thực sự đang cài trong LDPlayer.

## 13. Việc cần làm NGAY

1. `git pull` lấy `tools/verify_client.py`.
2. Chạy:

```bat
python tools\verify_client.py DMC_local_signed.apk
```

Expected nếu output trên PC đúng:

```text
Direct login patch: OK
Soha SetUserInfo no-op: OK
SetUserInfo IL: 2a
```

3. Lấy chính APK đang cài trong LDPlayer:

```bat
"C:\LDPlayer\OSLink\1.3.22.3_20251203110251\adb.exe" -s 127.0.0.1:5601 shell pm path vn.sohagame.dminhchu
```

Dùng path `package:/data/app/.../base.apk` trả về để pull, ví dụ:

```bat
"C:\LDPlayer\OSLink\1.3.22.3_20251203110251\adb.exe" -s 127.0.0.1:5601 pull /data/app/.../base.apk installed_dmc.apk
```

4. Verify APK thực cài:

```bat
python tools\verify_client.py installed_dmc.apk
```

5. Nếu PC APK = OK nhưng installed APK = MISSING -> LDPlayer chưa cài đúng bản mới. Gỡ package hoàn toàn rồi cài lại.
6. Nếu cả hai = OK nhưng runtime vẫn chạy `SetUserInfo` -> kiểm tra Unity/Mono cache/extracted managed assembly trong app data; gỡ package + clear data/reinstall là test tiếp theo.
7. Chỉ sau khi runtime không còn stack `SetUserInfo` mới tiếp tục tới `BeginCutsceneForm`.

ADB serial hiện tại:

```text
127.0.0.1:5601
```

Không dùng LDPlayer 64-bit cho test chính.

## 14. Trạng thái chính xác

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
  root cause = legacy SohaSDK SetUserInfo call

PATCHER:
  claims SetUserInfo -> ret
  runtime still executes old body
  VERIFY INSTALLED APK PENDING
```

## 15. Quy tắc bắt buộc

- Luôn phân biệt `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore.
- Ưu tiên flow nhỏ, deterministic, testable.
- **Sau mỗi mốc quan trọng phải cập nhật HANDOFF**.
