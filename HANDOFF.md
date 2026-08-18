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

11 unit tests pass trên Windows 2026-08-18 trước khi thêm các compatibility stub mới.

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

ADB serial hiện tại:

```text
127.0.0.1:5601
```

## 12. Runtime blocker cũ — ĐÃ VƯỢT QUA

Blocker cũ sau `/GetUserInfo` là:

```text
SohaSDKManager.SetUserInfo -> SohaSDK.setUserConfig -> NPE
```

Signed v2 đã patch đúng và runtime mới **vượt qua blocker này**.

## 13. PATCHER / SIGNED V2 — CONFIRMED ARTIFACT

Unsigned + signed v2 đều verify:

```text
Direct login patch: OK
Soha SetUserInfo no-op: OK
SetUserInfo CodeSize: 41
SetUserInfo IL: 2a + 40 x 00
```

Signed APK:

```text
DMC_local_v2_signed.apk
size = 52,569,585 bytes
v1 = true
v2 = true
v3 = true
```

`apksigner.bat` wrapper trên máy user không tạo output; chạy trực tiếp `apksigner.jar` thì ký thành công.

## 14. MỐC RUNTIME MỚI — CONFIRMED: ĐÃ VÀO STARTER -> HOME

Runtime log mới trên LDPlayer 32-bit:

```text
Form StartForm active
Form LoginForm active
Form SelectServerForm active
Form BeginCutsceneForm active
Form BeginCutsceneForm deactive
Form HomeForm active
```

=> **CONFIRMED RUNTIME:** client đã vào được màn chọn starter, chọn starter thành công và vào Home. Đây là mốc lớn: login/local AES/client patch/backend first-character đều hoạt động thật.

Ảnh runtime cho thấy Home hiển thị tài khoản `Offline`, level 1, tài nguyên và các menu game.

## 15. Runtime discovery: nhiều chức năng khác chưa có endpoint

User xác nhận hiện tại **Giang Hồ hoạt động**, còn nhiều menu khác chưa hoạt động.

Log + ảnh đã xác nhận ít nhất các request còn thiếu:

```text
User.asmx/GetSystemHighLight
Battle.asmx/GetMiniBossInfo
User.asmx/LayNhanVat
```

Cụ thể:

- `HomeForm` active -> gọi `/GetSystemHighLight` -> trước đây HTTP 404 -> Unity `java.io.FileNotFoundException`.
- `LuyenCongForm` active -> gọi `/GetMiniBossInfo` -> trước đây HTTP 404.
- Chợ/thu nhận đệ tử -> gọi `/LayNhanVat` -> ảnh runtime hiển thị `FileNotFoundException` endpoint này.

Giang Hồ runtime:

```text
Form GiangHoForm active
Request start GiangHO : 0 - 0
Form BattleForm active
BattleReplay JSON được client nhận/parse
```

Có log:

```text
Can not get nhiem vu Info from giang ho 0, nhiem vu 0
```

nhưng BattleReplay vẫn được nhận và battle chạy; cần xử lý config/progression riêng sau.

## 16. SERVER 0.5 — compatibility endpoints mới IMPLEMENTED (RUNTIME RETEST PENDING)

Đã thêm vào `server/app.py`:

```text
/GetSystemHighLight
/GetMiniBossInfo
/LayNhanVat
```

Trạng thái chính xác:

### GetSystemHighLight

**CONFIRMED RUNTIME endpoint name**, response hiện là empty compatibility snapshot:

```json
{
  "ErrorCode": 1,
  "ErrorMsg": "",
  "SystemHighLightList": [],
  "SystemHighLight": []
}
```

`SystemHighLightList` là symbol đã thấy trong Assembly-CSharp. Mục tiêu trước mắt là bỏ 404/popup; chưa tái tạo hoạt động/event thật.

### GetMiniBossInfo

**CONFIRMED RUNTIME endpoint name**, hiện trả empty/no-event snapshot để bỏ 404. Chưa phải MiniBoss gameplay hoàn chỉnh.

### LayNhanVat

**CONFIRMED RUNTIME endpoint name**, hiện trả current hero/account snapshot, không trừ vàng và chưa random/thêm đệ tử mới. Đây chỉ là compatibility stub, chưa được coi chức năng Chợ/thu nhận đã hoàn chỉnh.

Server version tăng:

```text
DMCOffline/0.5
```

Unknown route giờ được log rõ:

```text
Unhandled route: <path>
```

Commits:

```text
208b8ef1  Thêm các endpoint runtime còn thiếu
e9042395  Test các endpoint runtime mới
```

Test file đã thêm test registration/safe response cho 3 route mới. Cần user `git pull` rồi chạy unit tests trên Windows để xác nhận tổng số test mới pass.

## 17. Việc cần làm NGAY

1. User chạy:

```bat
cd /d "F:\Downloads\img\đạiminhchủ\DaiMinhChu-Offline"
git pull
cd server
python -m unittest -v
```

2. Restart server local để nạp app.py 0.5.
3. Không cần build APK lại; client v2 hiện tại dùng được.
4. Mở game -> vào Home -> thử lại:
   - Home/Hoạt động
   - Luyện Công
   - Chợ/Thu nhận
5. Quan sát server console + logcat. Mục tiêu trước mắt:

```text
không còn HTTP 404/FileNotFoundException cho 3 endpoint trên
```

6. Nếu response shape chưa đúng và client báo NullReference/LitJson lỗi, reverse chính DTO đó rồi sửa minimal schema; không đoán thêm field hàng loạt.
7. Click tuần tự các menu khác để lấy danh sách endpoint runtime thật. Mỗi endpoint mới: log request JSON -> reverse DTO -> implement fixture -> test -> runtime retest.
8. Tiếp tục ưu tiên chức năng core theo thứ tự: Đội hình/Đệ tử -> Võ công/Trang bị -> Chợ/recruit -> Luyện công -> Kỳ ngộ/Hoạt động. Các hệ PvP/liên server để sau.

## 18. Trạng thái chính xác

```text
CONFIRMED STATIC:
  login -> first character -> Home -> GiangHo -> BattleForm -> result

SERVER IMPLEMENTED:
  login/user/start hero/battle/save/progression
  + compatibility stubs: GetSystemHighLight, GetMiniBossInfo, LayNhanVat

SERVER TESTED:
  core AES + HTTP chain + persistence + mission unlock
  new 0.5 tests committed, Windows rerun pending

CONFIRMED RUNTIME (LDPlayer 32-bit):
  patched APK boot
  /Login
  /CheckUser
  /GetUserInfo
  BeginCutsceneForm
  SelectStartNhanVat
  HomeForm
  GiangHoForm
  BattleForm + BattleReplay parse/run

CURRENT LIMITATION:
  đa số feature server endpoints chưa được dựng
  GiangHo là feature gameplay đầu tiên chạy được
  3 endpoint 404 đầu tiên đã có stub, runtime retest pending
```

## 19. Quy tắc bắt buộc

- Luôn phân biệt `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore.
- Không gọi compatibility stub là feature hoàn chỉnh.
- Ưu tiên flow nhỏ, deterministic, testable.
- **Sau mỗi mốc quan trọng phải cập nhật HANDOFF**.
