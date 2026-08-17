# HANDOFF — DaiMinhChu-Offline

> **ĐỌC FILE NÀY TRƯỚC KHI TIẾP TỤC Ở CHAT MỚI.** Đây là nguồn trạng thái chính của dự án. Sau mỗi mốc kỹ thuật quan trọng phải cập nhật lại HANDOFF để không phụ thuộc vào lịch sử chat.

**Last updated:** 2026-08-18 (UTC+7)

## 1. Mục tiêu

Phục dựng **Đại Minh Chủ Việt Nam 8.0.2** để chơi local/offline, ưu tiên giữ client/UI/assets gốc. Hướng hiện tại: tái tạo backend tương thích thay vì cần GS gốc.

Ưu tiên:

```text
Login
 -> user/tướng/đội hình/trang bị/võ công
 -> Giang Hồ
 -> BattleReplay
 -> progression/save local
```

Chưa ưu tiên: nạp tiền, Soha account thật, chat, bang hội/PvP online, liên server, leaderboard/payment.

## 2. Repo / APK

Repo: `maxskill115/DaiMinhChu-Offline`, branch `main`, hiện public. Không commit APK gốc, full asset/config dump, credential hay keystore.

File chính:

```text
README.md
HANDOFF.md
.gitignore

docs/protocol/login.md
docs/protocol/first-character.md
docs/protocol/giangho-battle.md

server/app.py
server/crypto.py
server/requirements.txt
server/test_server.py
server/smoke_client.py
server/README.md

tools/patch_client.py
```

APK mẫu:

```text
Đại Minh Chủ (Dai Minh Chu)_8.0.2_apkcombo.com.apk
size:    52,568,975 bytes
SHA256:  2ff6b4db2177dc1362c20866750a48371f283a79a40335d3293a26e39e7e4194
package: vn.sohagame.dminhchu
```

## 3. Engine/runtime — CONFIRMED STATIC

Unity 4.x + Mono, không phải IL2CPP-only:

```text
assets/bin/Data/Managed/Assembly-CSharp.dll
lib/armeabi-v7a/libunity.so
lib/armeabi-v7a/libmono.so
```

`Assembly-CSharp.dll` = `2,425,856` bytes; nhiều symbol C# còn nguyên nên reverse IL/metadata thuận lợi.

## 4. Network / AES — CONFIRMED STATIC

Login URL gốc:

```text
http://login.minhchu.sohagame.vn/Server/Webservice/User.asmx
```

Transport:

```text
LitJson JSON
 -> AES encrypt
 -> Base64
 -> WWW.EscapeURL
 -> POST body: data=<escaped_ciphertext>
 -> UnityEngine.WWW
```

Response:

```text
WWW.text -> AES decrypt -> JSON -> JsonMapper.ToObject<T>()
```

AES:

```text
AES/Rijndael-128
CBC
PKCS7
UTF-8
Key = IV
HEX: 03051f0205060315061705202a1f5620
Base64: AwUfAgUGAxUGFwUgKh9WIA==
```

Repo dùng `server/crypto.py` + `cryptography`.

## 5. Core config nằm sẵn trong APK — CONFIRMED STATIC, rất quan trọng

`GameManager.Awake()` load Unity `Resources` trước login:

```text
ConfigFile/TrangBi
ConfigFile/VoCong
ConfigFile/NhanVat
ConfigFile/GiangHo
ConfigFile/Other
ConfigFile/ChanKhi
ConfigFile/VatPhamTieuThu
ConfigFile/HuyetChien
ConfigFile/GoiVatPhamVIP
ConfigFile/DanhSonTamBao
ConfigFile/KimCham
ConfigFile/LongChau
ConfigFile/TextFilter
Localization/Vietnamese
```

Sau đó `ConfigManager.ReadAllCfg(...)`.

=> `/Login` có thể trả `LoginCfg=null` để bỏ remote config update mà core gameplay config vẫn còn trong APK.

Đã parse `ConfigFile/NhanVat`, khoảng 333 nhân vật; không commit full dump.

## 6. Login / first character — CONFIRMED STATIC + SERVER IMPLEMENTED

### `/Login`

Success `ErrorCode == 1`; `11` = version không đủ/update.

`GameManager.DownloadConfigAndCache()`:

```text
if LoginResponse.LoginCfg == null:
    LoginForm.OnLoginSuccess()
    skip remote config download
```

### Bypass Soha SDK

`tools/patch_client.py` đã patch:

1. hard-coded login URL sang local;
2. `LoginForm.OnLoginBtnClick` từ `SohaSDKManager.Login()` sang `HTTP.Instance.Login(...)`.

Patcher chỉ nhận đúng SHA256 APK trên; IL sau patch đã disassemble lại đúng dự kiến.

### `/CheckUser`

Request `User, Token`; success trả `Aid, ServerID`. Prototype dùng server ID `1` + `ListUserServer=[1]` để tránh `/UserAppendServer`.

### `/GetUserInfo`

Request `Aid, Token, Property[]`. `LoadAllUserInfo()` yêu cầu 21 nhóm:

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

Nếu `NhanVat.Count == 0` → Form index 13; nếu có tướng → Form 3.

### Form 13 = `BeginCutsceneForm`

Ba code nhân vật đầu:

```text
NV_PhongThanhDuong -> Phong Thanh Dương: Mau 260, Cong 284, Thu 155, NoiLuc 234
NV_LenhHoXung      -> Lệnh Hồ Xung:      Mau 180, Cong 180, Thu 60,  NoiLuc 300
NV_SoLuuHuong      -> Sở Lưu Hương:      Mau 250, Cong 150, Thu 160, NoiLuc 305
```

`/SelectStartNhanVat` request:

```text
Aid int
Token string
NhanVatCode string
```

Response deserialize thành `HTTPGetUserInfoResponse`; success:

```text
HTTP.UserInfo.UpdateData(response)
BeginCutsceneForm.OnSelectCharacterComplete()
```

Prototype trả hero ID `1` + `DoiHinh.Slot1 = 1`, static trace sau cutscene đi tới **Home / Form 3**.

Chi tiết: `docs/protocol/login.md`, `docs/protocol/first-character.md`.

## 7. Home -> Giang Hồ — CONFIRMED STATIC

`MenuGroup.OnGiangHoBtnClick()`:

```text
GameManager.ActiveForm = 4
```

Form 4 = `GiangHoForm`.

Mở Giang Hồ **không cần request mạng ngay**; `GiangHoForm.OnActive()` sync dữ liệu local/config đã load.

`GiangHoSlider` dựng chapter/stage từ `ConfigManager.giangHoCfgs`.

### User mới với `GiangHo=[]` vẫn hợp lệ

`GH_NhiemVuSlider.SyncWithNetworkData()` có nhánh khi:

```text
currentGiangHoIdx == HTTP.UserInfo.Data.GiangHo.Count
```

Client tự tạo record nhiệm vụ tạm:

```text
S = 0
T = 0
```

=> prototype chưa cần giả progress Giang Hồ chỉ để hiện chapter đầu.

## 8. Click nhiệm vụ / Battle.asmx — CONFIRMED STATIC

`GH_NhiemVu_Item.OnBattleClick()` gọi:

```text
HTTP.DanhGiangHo(HTTP.WaitForDanhGiangHo, giangHoIdx, nhiemVuIdx)
```

`HTTPBattleGiangHoRequest` dùng public fields lowercase:

```text
aid        int32
token      string
giangHoIdx uint8
nhiemVuIdx uint8
```

Gửi tới:

```text
<BattleURL>/GiangHo
```

`BattleURL` client tạo bằng:

```text
User.asmx -> Battle.asmx
```

Ví dụ local:

```text
http://10.0.2.2:8000/Server/Webservice/Battle.asmx/GiangHo
```

### Response root

`HTTPBattleGiangHoResponse`:

```text
BattleReplay   KetQuaTranDau
Reward         BattleReward
giangHoIdx     uint8
nhiemVuIdx     uint8
star           uint8
UpdateUserInfo HTTPGetUserInfoResponse
ErrorCode      HTTP_ERROR_CODE
ErrorMsg       string
```

Success `ErrorCode == 1` → `GiangHoForm.OnReceiveBattleResult(BattleReplay)` →

```text
BattleForm.environment = 0   // GiangHo
GameManager.ActiveForm = 7   // BattleForm
BattleForm.PlayGame(replay, false)
```

## 9. BattleReplay DTO — CONFIRMED STATIC

`KetQuaTranDau`:

```text
BuaChuBiThuatMP1 List<VoCongBuffAll>
BuaChuBiThuatMP2 List<VoCongBuffAll>
DoiThang          TeamEnum
Team1             Team
Team2             Team
Hiep1             HiepDau
Hiep2             HiepDau
Hiep3             HiepDau
```

`Team`:

```text
Name string
AccountID string
DanhVong int
```

`HiepDau`:

```text
DoiHinh1 List<VoGia>
DoiHinh2 List<VoGia>
LuotDau  List<LuotDau>
```

`VoGia`:

```text
Name string
Mau int64
NoiLuc float
Buffs List<BuffValue>
BuaChu List<BuffValue>
BiThuat List<BuffValue>
```

`LuotDau`:

```text
DoiTanCong        TeamEnum
NguoiTanCong      int
DanhSachThuongTon List<ThuongTon>
VoCong             string
```

`ThuongTon`:

```text
Value              int64
TrangThaiThuongTon List<TrangThai>
```

### TeamEnum / normal attack

Static branches xác nhận:

```text
Team1 = 0
Team2 = 1
```

Nếu `VoCong` null/empty → client dùng **normal attack**, không lookup config võ công.

Normal attack unconditionally lấy `DanhSachThuongTon[0]`, nên list damage phải có ít nhất 1 item.

`BiTanCong` / `PlayImpact` gọi `.Contains(...)` trên `TrangThaiThuongTon`, nên list này không được null. Fixture dùng `[]`.

Một số status suy ra từ branch client:

```text
1 = BaoKich
2 = NeDon
3 = PhanKich
5 = HoThe
```

### Minimum null-safe replay đã xác nhận

Cần:

```text
Team1 != null
Team2 != null
Hiep1 != null
Hiep1.DoiHinh1 có >=1 fighter
Hiep1.DoiHinh2 có >=1 fighter
Hiep1.LuotDau có >=1 turn
VoGia.Name là key hợp lệ trong ConfigManager.nhanVatCfgs
VoGia.Buffs != null
DanhSachThuongTon có >=1 item
TrangThaiThuongTon != null
```

`Hiep2/Hiep3` có thể null. Top-level BuaChu/BiThuat lists prototype gửi `[]`.

Chi tiết: `docs/protocol/giangho-battle.md`.

## 10. Battle result — CONFIRMED STATIC

`BattleGiangHoResultPanel.SetResult()` coi:

```text
DoiThang == 0
```

là Team1/player thắng.

`star`: 0 thua; 1/2/3 = thắng 1/2/3 sao.

Result panel đọc trực tiếp:

```text
Reward.ExpMonPhai
Reward.Bac
UpdateUserInfo.NhanVat
```

nên `Reward` và `UpdateUserInfo` phải non-null.

Khi đóng result, môi trường GiangHo gọi:

```text
HTTP.UserInfo.UpdateData(response.UpdateUserInfo)
GameManager.ActiveForm = 4
```

và kiểm tra `Reward.Items`.

## 11. Local server — SERVER IMPLEMENTED + SERVER TESTED

`server/app.py` hiện version `DMCOffline/0.3`.

Routes:

```text
GET  /health
POST /Login
POST /CheckUser
POST /GetUserInfo
POST /SelectStartNhanVat
POST /GiangHo   // suffix match, dùng Battle.asmx/GiangHo
```

Server derive:

```text
PUBLIC_BATTLE_URL = PUBLIC_USER_URL.replace("User.asmx", "Battle.asmx")
```

Memory-only state:

```text
STATE = {"selected_hero": "NV_LenhHoXung"}
```

`/SelectStartNhanVat` cập nhật hero đã chọn. Chưa có persistent save.

### Replay fixture hiện tại

Deterministic 1v1:

```text
Team1 = hero đã chọn
Team2 = một start hero hợp lệ khác
1 hiệp
1 đòn đánh thường
Team2 mất toàn bộ HP
DoiThang = 0
star = 3
Reward.Bac = 100
Reward.ExpMonPhai = 10
Reward.ExpNhanVat = 10
Reward.Items = []
UpdateUserInfo.NhanVat = hero ID 1
```

GiangHo progress **chưa persist**, cố ý để tập trung test compatibility trước.

## 12. Tests — SERVER TESTED, KHÔNG PHẢI CLIENT RUNTIME

### Unit tests

`server/test_server.py`: 6 tests pass local:

```text
AES roundtrip
User/Battle URL
new user NhanVat empty
3 start heroes
invalid hero reject
minimal GiangHo replay null-safe theo confirmed dereferences
```

### Encrypted HTTP smoke

Đã gửi AES request thật qua local HTTP tới:

```text
/Server/Webservice/Battle.asmx/GiangHo
```

và decrypt response thành công:

```text
ErrorCode=1
star=3
DoiThang=0
hero=NV_LenhHoXung
turns=1
Items=[]
```

`server/smoke_client.py` test toàn chuỗi:

```text
Login -> CheckUser -> GetUserInfo -> SelectStartNhanVat -> GiangHo
```

Kết quả local:

```text
[Login] ErrorCode=1
[CheckUser] ErrorCode=1
[GetUserInfo] ErrorCode=1
[SelectStartNhanVat] ErrorCode=1
[GiangHo] ErrorCode=1
replay: winner=0 star=3 turns=1
```

**Đây là SERVER TESTED, chưa phải Unity/Android runtime.**

## 13. Trạng thái chính xác hiện tại

```text
CONFIRMED STATIC:
  login -> first character -> Home -> GiangHo -> BattleForm -> replay/result panel

SERVER IMPLEMENTED:
  Login / CheckUser / GetUserInfo / SelectStartNhanVat / Battle.asmx/GiangHo

SERVER TESTED:
  AES + HTTP chain + minimal battle fixture

CLIENT RUNTIME:
  PENDING
```

Tuyệt đối không nói game đã login/vào Home/phát trận thành công trên Android cho tới khi có runtime log.

## 14. Việc cần làm NGAY tiếp theo

### Ưu tiên số 1: runtime Android

1. `cd server`
2. cài requirements
3. `python -m unittest -v`
4. chạy `python app.py` với `DMC_BASE_URL` đúng IP PC mà Android truy cập được
5. patch APK bằng `tools/patch_client.py` với cùng địa chỉ
6. zipalign/sign/install APK
7. mở game, nhập user/pass bất kỳ
8. theo dõi server console + `adb logcat`

Expected:

```text
POST ...User.asmx/Login
POST ...User.asmx/CheckUser
POST ...User.asmx/GetUserInfo
[BeginCutsceneForm]
POST ...User.asmx/SelectStartNhanVat
[Home]
[Giang Hồ]
POST ...Battle.asmx/GiangHo
[BattleForm phát replay]
[result panel]
```

Nếu fail: lấy **request cuối + server log + adb logcat/stack** rồi reverse đúng điểm fail, không đoán.

### Nếu chưa runtime test được

Tiếp tục static theo thứ tự:

1. reverse serialization `giangho.Nhiemvu` + progress update;
2. dựng save/load JSON/SQLite;
3. sau battle update star/progress/resource;
4. sau đó mở rộng equipment/skill/formation và battle generator thật.

Các field progress đã biết:

```text
giangho.GiangHoIndx int
giangho.HoanThanh   int
giangho.Nhiemvu     string
HTTPNhiemVuGiangHoRecord.S byte
HTTPNhiemVuGiangHoRecord.T byte
```

Cần xác nhận format string `Nhiemvu` trước khi implement persist.

## 15. Commit/mốc gần nhất

Current main trước HANDOFF update này:

```text
f5abbd8d  Cập nhật milestone Giang Hồ và BattleReplay
42ce749f  Cập nhật hướng dẫn smoke test Giang Hồ
a5db4a1e  docs/protocol/giangho-battle.md
a5c9c170  server/smoke_client.py
e217d3b1  Battle.asmx/GiangHo replay tối thiểu
```

Các mốc trước:

```text
a1e861b3  handoff tới flow chọn nhân vật
364f5362  server SelectStartNhanVat
9483c920  cryptography
a6499192  unit tests
1a265ccf  xóa dmc_crypto.py
5f5134f4  docs first-character
```

## 16. Quy tắc bắt buộc

- Luôn phân biệt `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump.
- Ưu tiên flow nhỏ, deterministic, testable.
- **Sau mỗi mốc quan trọng phải cập nhật HANDOFF**; đây là yêu cầu trực tiếp của người dùng để chat mới tiếp tục được ngay.
