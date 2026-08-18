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
3. **mới:** patch `SohaSDKManager.SetUserInfo(...)` thành no-op (`ret`) để bỏ bridge Soha SDK cũ gây NPE sau `/GetUserInfo`.

Patch #3 được xác định từ runtime thật và static metadata của đúng APK:

```text
SohaSDKManager.SetUserInfo RVA = 0xCB940
original IL code size = 41 bytes
replacement IL = 0x2A (ret)
```

APK patched trước đó đã zipalign + ký test. `apksigner verify`:

```text
v1=true
v2=true
v3=true
```

Commit patch Soha runtime blocker:

```text
db5bf82d  Patch Soha SDK user-info crash
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

Bản patched signed đã khởi động thành công đến màn hình **Đại Minh Chủ / Bắt đầu / Phiên bản 8.0.0**.

Khi nhấn Bắt đầu, client thật đã giao tiếp thành công với local backend qua AES:

```text
POST /Server/Webservice/User.asmx/Login -> HTTP 200 ErrorCode=1
POST /Server/Webservice/User.asmx/CheckUser -> HTTP 200 ErrorCode=1
POST /Server/Webservice/User.asmx/GetUserInfo -> HTTP 200 ErrorCode=1
```

Request `/GetUserInfo` runtime thật hỏi đủ 21 property:

```text
account, nhanVat, trangBi, voCong, orb, vatPhamTieuThu,
giaTriThoiGian, doiHinh, giangHo, tanChuong, honNhanVat,
mail, banbe, danhhieu, danhson, serverinfo, lienminh,
kimcham, moiruou, longchau, amkhi
```

Server hiện trả tối thiểu:

```text
Account
GiaTriThoiGian
NhanVat=[]
GiangHo=[]
```

## 12. Runtime blocker sau GetUserInfo — CONFIRMED RUNTIME, ROOT CAUSE FOUND

Logcat chính xác trên LDPlayer 32-bit sau `WaitForCheckUser done`:

```text
AndroidJavaException: java.lang.NullPointerException:
Attempt to invoke virtual method
'void vn.soha.game.sdk.SohaSDK.setUserConfig(...)'
on a null object reference

at SohaSDKManager.SetUserInfo(...)
at HTTP+<WaitForGetUserInfo>c__IteratorC4.MoveNext()
```

=> blocker **không phải thiếu field `/GetUserInfo` như giả thuyết trước**. `/GetUserInfo` đã decode và flow đi tiếp đến `HTTP.WaitForGetUserInfo`; chính client sau đó gọi bridge Soha SDK legacy và Java singleton `SohaSDK` đang null trong môi trường offline.

Đây là **CONFIRMED RUNTIME**.

Fix đã commit vào `tools/patch_client.py`: `SohaSDKManager.SetUserInfo` được patch thành no-op `ret`. Chưa có runtime retest của bản patch mới tại thời điểm handoff này.

## 13. Việc cần làm NGAY

1. `git pull` để lấy commit `db5bf82d`.
2. Rebuild lại APK từ **APK gốc** bằng `tools/patch_client.py` (không patch chồng lên APK patched cũ).
3. zipalign + ký lại bằng keystore test hiện có.
4. Cài bản mới vào **LDPlayer 32-bit**.
5. Giữ server local chạy tại `192.168.1.14:8000`.
6. Clear logcat, mở game, nhấn Bắt đầu/Vào Game.
7. Expected tiếp theo: vượt qua `SohaSDKManager.SetUserInfo` và đi vào `BeginCutsceneForm` nếu `NhanVat=[]`.
8. Nếu lỗi mới xuất hiện, lấy stack trace chính xác rồi patch/reverse tiếp, không đoán.
9. Khi hiện màn chọn starter, test `/SelectStartNhanVat` -> Home -> GiangHo -> battle.

ADB serial hiện tại của instance LDPlayer 32-bit trong lần test:

```text
127.0.0.1:5601
```

Ví dụ:

```bat
"C:\LDPlayer\OSLink\1.3.22.3_20251203110251\adb.exe" -s 127.0.0.1:5601 logcat -c
"C:\LDPlayer\OSLink\1.3.22.3_20251203110251\adb.exe" -s 127.0.0.1:5601 logcat
```

Không dùng LDPlayer 64-bit cho test chính lúc này.

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
  APK patched boot
  /Login
  /CheckUser
  /GetUserInfo transport/decrypt
  root cause sau GetUserInfo = SohaSDKManager.SetUserInfo -> Java SohaSDK null

CLIENT PATCHED, RUNTIME RETEST PENDING:
  SohaSDKManager.SetUserInfo -> no-op ret
```

## 15. Quy tắc bắt buộc

- Luôn phân biệt `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore.
- Ưu tiên flow nhỏ, deterministic, testable.
- **Sau mỗi mốc quan trọng phải cập nhật HANDOFF**.
