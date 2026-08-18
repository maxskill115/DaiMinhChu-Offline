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
3. patch `SohaSDKManager.SetUserInfo(...)` thành no-op để bỏ bridge Soha SDK cũ gây NPE sau `/GetUserInfo`.

Static metadata của đúng APK:

```text
SohaSDKManager.SetUserInfo RVA = 0xCB940
original IL code size = 41 bytes
original IL = 02 7b e4 23 00 04 72 2e cd 01 70 1a 8d 08 00 00 01 25 16 03 a2 25 17 05 a2 25 18 0e 04 a2 25 19 0e 05 a2 6f 99 09 00 0a 2a
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

Cả APK gốc và patched đều crash gần lúc Unity/OpenGL init, process chết signal 6. Không dùng cho test chính.

### LDPlayer 32-bit

Bản patched signed boot thành công và client thật đã chạy:

```text
/Login -> /CheckUser -> /GetUserInfo
```

qua AES/local HTTP thành công.

ADB serial hiện tại:

```text
127.0.0.1:5601
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

## 13. CONFIRMED ARTIFACT DIAGNOSIS

User đã verify cả:

```text
DMC_local_signed.apk
installed_dmc.apk  # pull trực tiếp từ /data/app/.../base.apk
```

Cả hai:

```text
Direct login patch: OK
Soha SetUserInfo no-op: MISSING
SetUserInfo IL: 02 7b e4 23 00 04 ... 6f 99 09 00 0a 2a
```

=> loại trừ LDPlayer cache/cài nhầm. Artifact thật sự thiếu patch SetUserInfo.

## 14. PATCHER FIX MỚI — IMPLEMENTED, RUNTIME RETEST PENDING

Đã sửa `tools/patch_client.py` và `tools/verify_client.py`.

Patcher mới:

- không đổi `SetUserInfo CodeSize` nữa;
- giữ `CodeSize=41` và thay body thành:

```text
2a 00 00 00 ... 00
```

(`RET + NOP padding`, tổng 41 bytes);
- kiểm tra exact original 41-byte IL trước khi patch, khác thì dừng;
- self-verify patched assembly trong memory;
- sau khi ghi APK unsigned, mở lại **chính file trên disk** và verify lần nữa;
- nếu direct-login hoặc SetUserInfo no-op thiếu thì raise lỗi, không báo thành công;
- in SHA256 patched `Assembly-CSharp.dll` để đối chiếu.

Verifier mới expect:

```text
Direct login patch: OK
Soha SetUserInfo no-op: OK
SetUserInfo CodeSize: 41
SetUserInfo IL: 2a 00 00 ... 00
```

Commits:

```text
59c87cf4  Fix SetUserInfo patch and verify output APK
c30790a1  Update verifier for padded SetUserInfo no-op
```

## 15. Việc cần làm NGAY

1. Pull code mới:

```bat
git pull
```

2. Patch lại từ APK gốc, nên dùng output mới để tránh nhầm:

```bat
python tools\patch_client.py "daiminhchu.apk" "DMC_local_v2_unsigned.apk" --base-url http://192.168.1.14:8000/Server/Webservice/User.asmx
```

Expected bắt buộc:

```text
Direct login patch: OK
Soha SetUserInfo no-op: OK
```

3. Verify unsigned:

```bat
python tools\verify_client.py DMC_local_v2_unsigned.apk
```

Expected:

```text
Direct login patch: OK
Soha SetUserInfo no-op: OK
SetUserInfo CodeSize: 41
SetUserInfo IL: 2a 00 00 ... 00
```

4. Chỉ khi verify OK mới zipalign + sign.
5. Verify signed APK thêm một lần trước khi cài.
6. Cài vào LDPlayer 32-bit, clear logcat và runtime test.
7. Nếu không còn `SetUserInfo` NPE, tiếp tục tới `BeginCutsceneForm` / `/SelectStartNhanVat`.

## 16. Trạng thái chính xác

```text
CONFIRMED STATIC:
  login -> first character -> Home -> GiangHo -> BattleForm -> result

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
  previous signed + installed APK had SetUserInfo no-op MISSING

PATCHER FIXED, RUNTIME RETEST PENDING:
  SetUserInfo keeps CodeSize=41
  body = RET + NOP padding
  in-memory + on-disk self-verification
```

## 17. Quy tắc bắt buộc

- Luôn phân biệt `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore.
- Ưu tiên flow nhỏ, deterministic, testable.
- **Sau mỗi mốc quan trọng phải cập nhật HANDOFF**.
