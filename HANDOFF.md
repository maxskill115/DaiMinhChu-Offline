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
3. `SohaSDKManager.SetUserInfo(...)` thành no-op để bỏ bridge Soha SDK cũ gây NPE sau `/GetUserInfo`.

SetUserInfo metadata:

```text
RVA = 0xCB940
CodeSize = 41
original IL = 02 7b e4 23 00 04 72 2e cd 01 70 1a 8d 08 00 00 01 25 16 03 a2 25 17 05 a2 25 18 0e 04 a2 25 19 0e 05 a2 6f 99 09 00 0a 2a
patched IL = 2a + 40 x 00
```

Patcher tự verify in-memory và on-disk; verifier riêng: `tools/verify_client.py`.

## 5. Core config — CONFIRMED STATIC

Client có embedded configs: NhanVat, TrangBi, VoCong, GiangHo, Other, ChanKhi, VatPhamTieuThu, HuyetChien, KimCham, LongChau...

`LoginCfg=null` bỏ remote config update. Khoảng 333 nhân vật đã parse từ NhanVat; không commit dump gốc.

## 6. Login / first character — CONFIRMED STATIC + SERVER IMPLEMENTED

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

`/SelectStartNhanVat`: `Aid`, `Token`, `NhanVatCode`.

## 7. Home / Giang Hồ / Battle — CONFIRMED STATIC + SERVER IMPLEMENTED

Home = Form 3. Giang Hồ = Form 4. Battle = Form 7.

Battle endpoint:

```text
POST <BattleURL>/GiangHo
```

Server tạo BattleReplay deterministic 1v1 / 1 hiệp / 1 đòn thường, Team1 thắng 3 sao.

## 8. Progress/save — SERVER IMPLEMENTED + TESTED

`server/state.py` lưu:

```text
server/local_data/save.json
```

GiangHo `Nhiemvu` là JSON-string array `{S,T}`; embedded structure: 92 chapter / 1405 mission.

## 9. Tests — SERVER TESTED

11 unit tests pass trên Windows 2026-08-18.

Encrypted HTTP smoke pass:

```text
Login -> CheckUser -> GetUserInfo -> SelectStartNhanVat -> Battle.asmx/GiangHo
```

## 10. Server runtime

```text
DMC_BASE_URL=http://192.168.1.14:8000
Listen: 0.0.0.0:8000
User.asmx: http://192.168.1.14:8000/Server/Webservice/User.asmx
Battle.asmx: http://192.168.1.14:8000/Server/Webservice/Battle.asmx
```

LDPlayer `/health` thành công.

## 11. Emulator compatibility — CONFIRMED RUNTIME

### LDPlayer 64-bit

APK gốc + patched đều crash gần Unity/OpenGL init. Không dùng cho test chính.

### LDPlayer 32-bit

Client boot và chạy thật:

```text
/Login -> /CheckUser -> /GetUserInfo
```

ADB serial hiện tại:

```text
127.0.0.1:5601
```

## 12. Runtime blocker cũ — CONFIRMED RUNTIME

Sau `/GetUserInfo`:

```text
AndroidJavaException: java.lang.NullPointerException
SohaSDK.setUserConfig(...) on a null object reference
at SohaSDKManager.SetUserInfo(...)
at HTTP+<WaitForGetUserInfo>c__IteratorC4.MoveNext()
```

=> blocker là legacy Soha SDK bridge.

## 13. Artifact diagnosis cũ

Bản signed cũ và `base.apk` pull từ LDPlayer đều có direct-login patch nhưng SetUserInfo no-op **MISSING**. Đã loại trừ cache/cài nhầm; lỗi nằm ở patch artifact.

## 14. PATCHER FIX — CONFIRMED ARTIFACT

Commits:

```text
59c87cf4  Fix SetUserInfo patch and verify output APK
c30790a1  Update verifier for padded SetUserInfo no-op
dc65546b  Cập nhật HANDOFF
```

Unsigned v2:

```text
DMC_local_v2_unsigned.apk
Direct login patch: OK
Soha SetUserInfo no-op: OK
SetUserInfo CodeSize: 41
SetUserInfo IL: 2a 00 00 ... 00
```

Patched Assembly-CSharp SHA256:

```text
bd5f89c6db69ba852fb46789e5d2dd193b46a51a6f64c1b94efdb16e75e61b66
```

## 15. SIGNED V2 — CONFIRMED ARTIFACT

`apksigner.bat` wrapper trên máy user không tạo output nhưng cũng không in lỗi. Chạy trực tiếp jar hoạt động:

```bat
java -jar "%LOCALAPPDATA%\Android\Sdk\build-tools\35.0.0\lib\apksigner.jar" sign --verbose --ks dmc-test.jks --ks-key-alias dmc --out DMC_local_v2_signed.apk DMC_local_v2_aligned.apk
```

Kết quả:

```text
Signed
DMC_local_v2_signed.apk size = 52,569,585 bytes
```

Signature verify:

```text
Verifies
v1 = true
v2 = true
v3 = true
v3.1 = false
v4 = false
Number of signers = 1
```

Warning hiện tại:

```text
META-INF/client.txt not protected by signature
```

Không coi warning này là blocker cho runtime test hiện tại.

Verifier trên signed APK:

```text
Login URL: http://192.168.1.14:8000/Server/Webservice/User.asmx
Direct login patch: OK
Soha SetUserInfo no-op: OK
SetUserInfo CodeSize: 41
SetUserInfo IL: 2a + 40 x 00
```

=> **CONFIRMED ARTIFACT:** signed v2 vừa có chữ ký hợp lệ vừa giữ nguyên cả direct-login patch và SetUserInfo no-op.

## 16. Việc cần làm NGAY

1. Cài `DMC_local_v2_signed.apk` vào **LDPlayer 32-bit**.
2. Clear logcat:

```bat
"C:\LDPlayer\OSLink\1.3.22.3_20251203110251\adb.exe" -s 127.0.0.1:5601 logcat -c
```

3. Mở logcat:

```bat
"C:\LDPlayer\OSLink\1.3.22.3_20251203110251\adb.exe" -s 127.0.0.1:5601 logcat
```

4. Mở game -> Bắt đầu -> Vào Game.
5. Expected đầu tiên: **không còn** `SohaSDKManager.SetUserInfo -> SohaSDK.setUserConfig NPE`.
6. Nếu vào `BeginCutsceneForm`, chụp ảnh + kiểm tra server có nhận `/SelectStartNhanVat` khi chọn starter.
7. Nếu lỗi mới, lấy exact stack rồi xử lý tiếp; không đoán.
8. Nếu runtime v2 ổn qua starter: tiếp tục Home -> GiangHo -> battle.

## 17. Trạng thái chính xác

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
  old blocker = SohaSDK SetUserInfo NPE

CONFIRMED ARTIFACT:
  DMC_local_v2_unsigned.apk patch OK
  DMC_local_v2_signed.apk signature v1/v2/v3 OK
  signed APK direct-login OK
  signed APK SetUserInfo no-op OK

RUNTIME RETEST PENDING:
  install signed v2 -> confirm old Soha NPE gone -> BeginCutsceneForm
```

## 18. Quy tắc bắt buộc

- Luôn phân biệt `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore.
- Ưu tiên flow nhỏ, deterministic, testable.
- **Sau mỗi mốc quan trọng phải cập nhật HANDOFF**.
