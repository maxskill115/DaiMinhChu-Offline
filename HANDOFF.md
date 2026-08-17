# HANDOFF — DaiMinhChu-Offline

> **ĐỌC FILE NÀY TRƯỚC KHI TIẾP TỤC Ở CHAT MỚI.** Đây là nguồn trạng thái chính của dự án. Sau mỗi mốc kỹ thuật quan trọng phải cập nhật lại HANDOFF.

**Last updated:** 2026-08-18 (UTC+7)

## 1. Mục tiêu

Phục dựng **Đại Minh Chủ Việt Nam 8.0.2** để chơi local/offline, ưu tiên giữ client/UI/assets gốc. Hướng hiện tại là tái tạo backend tương thích thay vì cần GS gốc.

Ưu tiên:

```text
Login -> user/tướng/đội hình -> Giang Hồ -> BattleReplay -> progression/save
```

Chưa ưu tiên: nạp tiền, Soha account thật, chat, bang hội/PvP online, liên server, leaderboard.

## 2. Repo / APK

Repo: `maxskill115/DaiMinhChu-Offline`, branch `main`, hiện public.

Không commit APK gốc, full asset/config dump, credential hay keystore.

APK mẫu:

```text
Đại Minh Chủ (Dai Minh Chu)_8.0.2_apkcombo.com.apk
size: 52,568,975 bytes
SHA256: 2ff6b4db2177dc1362c20866750a48371f283a79a40335d3293a26e39e7e4194
package: vn.sohagame.dminhchu
```

## 3. Engine / protocol — CONFIRMED STATIC

Unity 4.x + Mono; `Assembly-CSharp.dll` còn nhiều symbol C#.

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

## 4. Core config trong APK — CONFIRMED STATIC

`GameManager.Awake()` load trước login các Unity Resources:

```text
ConfigFile/NhanVat
ConfigFile/TrangBi
ConfigFile/VoCong
ConfigFile/GiangHo
ConfigFile/Other
ConfigFile/ChanKhi
ConfigFile/VatPhamTieuThu
ConfigFile/HuyetChien
ConfigFile/KimCham
ConfigFile/LongChau
...
```

=> local `/Login` có thể trả `LoginCfg=null` để bỏ remote config update mà core gameplay config vẫn tồn tại.

Đã parse `ConfigFile/NhanVat` khoảng 333 nhân vật. Không commit dump gốc.

## 5. Login / first character — CONFIRMED STATIC + SERVER IMPLEMENTED

`tools/patch_client.py` đã patch đúng APK SHA trên:

1. login URL sang local;
2. `LoginForm.OnLoginBtnClick` bỏ `SohaSDKManager.Login()` và gọi trực tiếp `HTTP.Instance.Login(...)`.

Flow:

```text
/Login
 -> /CheckUser
 -> /GetUserInfo
```

Nếu `NhanVat.Count==0` → Form 13 = `BeginCutsceneForm`.

Ba start hero:

```text
NV_PhongThanhDuong -> Phong Thanh Dương, Mau260 Cong284 Thu155 NoiLuc234
NV_LenhHoXung      -> Lệnh Hồ Xung,      Mau180 Cong180 Thu60  NoiLuc300
NV_SoLuuHuong      -> Sở Lưu Hương,      Mau250 Cong150 Thu160 NoiLuc305
```

`/SelectStartNhanVat` request:

```text
Aid int
Token string
NhanVatCode string
```

Response là `HTTPGetUserInfoResponse`; success `UpdateData()` rồi đi Home/Form 3. Prototype dùng hero ID 1 + `DoiHinh.Slot1=1`.

## 6. Home -> Giang Hồ — CONFIRMED STATIC

`MenuGroup.OnGiangHoBtnClick()` đặt `GameManager.ActiveForm=4`; Form 4 = `GiangHoForm`.

Mở Giang Hồ không cần request mạng ngay; UI dùng embedded `ConfigManager.giangHoCfgs` + `HTTP.UserInfo.Data`.

User mới `GiangHo=[]` vẫn hợp lệ: client tự tạo record `{S:0,T:0}` cho mission đầu chapter 0.

## 7. Battle.asmx/GiangHo — CONFIRMED STATIC

Click mission gọi:

```text
HTTP.DanhGiangHo(...)
POST <BattleURL>/GiangHo
```

Request:

```text
aid int32
token string
giangHoIdx uint8
nhiemVuIdx uint8
```

`BattleURL` = `User.asmx` đổi thành `Battle.asmx`.

Response root:

```text
BattleReplay   KetQuaTranDau
Reward         BattleReward
giangHoIdx     uint8
nhiemVuIdx     uint8
star           uint8
UpdateUserInfo HTTPGetUserInfoResponse
ErrorCode / ErrorMsg
```

Success → Form 7 `BattleForm` → `PlayGame(replay,false)`.

## 8. BattleReplay tối thiểu — CONFIRMED STATIC + SERVER TESTED

DTO chính:

```text
KetQuaTranDau: Team1, Team2, DoiThang, Hiep1/Hiep2/Hiep3
HiepDau: DoiHinh1, DoiHinh2, LuotDau
VoGia: Name, Mau, NoiLuc, Buffs, BuaChu, BiThuat
LuotDau: DoiTanCong, NguoiTanCong, DanhSachThuongTon, VoCong
ThuongTon: Value, TrangThaiThuongTon
```

Team enum:

```text
Team1=0
Team2=1
```

`VoCong=""` dùng nhánh normal attack, tránh lookup skill config.

Null-safety tối thiểu đã reverse: Team1/2, Hiep1, 2 đội hình, LuotDau, Buffs, DanhSachThuongTon và TrangThaiThuongTon phải non-null. Hiep2/Hiep3 có thể null.

Server hiện tạo replay deterministic 1v1 / 1 hiệp / 1 đòn thường, Team1 thắng 3 sao.

## 9. Progress Giang Hồ — PHÁT HIỆN MỚI, CONFIRMED STATIC

Class:

```text
giangho.GiangHoIndx int
giangho.HoanThanh int
giangho.Nhiemvu string
```

`HTTPUserInfo.GetNhiemVuGiangHo()` gọi generic đã resolve chính xác:

```text
LitJson.JsonMapper.ToObject<List<HTTPNhiemVuGiangHoRecord>>(Nhiemvu)
```

=> `Nhiemvu` là **JSON string chứa array**.

Record:

```text
S byte = best star (0..3)
T byte = số lượt đã đánh mission trong ngày
```

`GH_NhiemVuSlider` dùng **độ dài array** làm ranh giới mission đã unlock. Ví dụ sau thắng mission 0:

```json
[{"S":3,"T":1},{"S":0,"T":0}]
```

Record thứ 2 mở mission 1.

`HoanThanh>0` làm client mở chapter `GiangHoIndx+1`.

Embedded `ConfigFile/GiangHo` đã parse:

```text
92 chapter
1405 mission
mission/chapter min=6 max=17
chapter 0 có 6 mission
chapter 1 có 7 mission
```

`server/state.py` giữ toàn bộ 92 mission-counts dạng structural integers, không lưu full config/dialogue.

## 10. Save local — SERVER IMPLEMENTED + SERVER TESTED

Mới thêm `server/state.py`.

File save mặc định:

```text
server/local_data/save.json
```

Giữ:

```text
hero_code / hero_level / hero_exp
account: DisplayName, Level, Exp, ExpMax, Bac, Vang, Vip
giangho[]: GiangHoIndx, HoanThanh, missions[{S,T}]
```

`/SelectStartNhanVat` persist hero ngay. Restart server → `/GetUserInfo` trả lại hero + `DoiHinh.Slot1=1`, nên theo static flow client đi thẳng Home thay vì chọn nhân vật lại.

Sau battle Giang Hồ:

1. validate mission đã unlock;
2. `S=max(oldS,newStar)`;
3. `T += 1`;
4. thắng mission thường → append `{S:0,T:0}` để mở mission kế;
5. thắng mission cuối → `HoanThanh=1`;
6. cộng reward bạc;
7. persist JSON;
8. trả `UpdateUserInfo.Account/NhanVat/GiangHo`.

Reset save:

```bat
cd server
python reset_save.py
```

## 11. Server hiện tại

File chính:

```text
server/app.py       # DMCOffline/0.4
server/state.py     # JSON save + GiangHo progression
server/crypto.py
server/test_server.py
server/smoke_client.py
server/reset_save.py
```

Routes:

```text
GET /health
POST /Login
POST /CheckUser
POST /GetUserInfo
POST /SelectStartNhanVat
POST /Server/Webservice/Battle.asmx/GiangHo
```

## 12. Tests — SERVER TESTED

Sau persistence/progression: **11 unit tests pass local**.

Bao gồm:

```text
AES roundtrip
new account không có hero
3 start heroes persist
reload save trả hero + DoiHinh
battle đầu mở mission kế
Nhiemvu JSON đúng shape
replay giữ best star + tăng T
locked mission bị reject
complete chapter 0 -> HoanThanh=1
chapter 1 unlock sau chapter 0
minimal BattleReplay null-safe
```

Encrypted HTTP smoke pass:

```text
Login -> CheckUser -> GetUserInfo -> SelectStartNhanVat -> Battle.asmx/GiangHo
```

Kết quả test thực local sau battle đầu:

```text
ErrorCode=1
winner=0
star=3
turns=1
Nhiemvu=[{"S":3,"T":1},{"S":0,"T":0}]
Bac=10100
save.json được tạo thành công
```

**Đây vẫn là SERVER TESTED, không phải client runtime.**

## 13. Trạng thái chính xác

```text
CONFIRMED STATIC:
  login -> first character -> Home -> GiangHo -> BattleForm -> result
  + schema/semantics GiangHo progression

SERVER IMPLEMENTED:
  login/user/start hero/battle/save/progression

SERVER TESTED:
  AES + HTTP chain + persistence + mission unlock

CLIENT RUNTIME:
  PENDING
```

Không được nói game đã vào Home/phát trận/hiện sao thành công trên Android cho tới khi có runtime log.

## 14. Việc cần làm NGAY ở chat tiếp theo

### Ưu tiên #1: runtime Android/emulator

1. clone/pull repo;
2. `cd server` → `pip install -r requirements.txt`;
3. `python -m unittest -v`;
4. chạy `python app.py` với `DMC_BASE_URL` là địa chỉ PC Android truy cập được;
5. patch đúng APK 8.0.2 bằng `tools/patch_client.py` với cùng URL;
6. zipalign/sign/install APK;
7. mở game, login bất kỳ;
8. theo dõi server console + `adb logcat`.

Expected lần đầu:

```text
/Login
/CheckUser
/GetUserInfo
BeginCutsceneForm
/SelectStartNhanVat
Home
GiangHo
/Battle.asmx/GiangHo
BattleForm -> result
quay GiangHo -> thấy 3 sao + mission kế mở
```

Sau đó restart server/game để xác nhận `/GetUserInfo` load hero/progress từ `save.json` và đi thẳng Home.

Nếu fail: lấy **request cuối + server log + adb logcat/stack** rồi reverse đúng điểm fail, không đoán.

### Nếu chưa runtime được

Tiếp tục static theo thứ tự:

1. equipment/skill/formation schema cần cho Home;
2. reward/EXP/level progression chuẩn hơn;
3. battle generator dùng đội hình/stat/config thật.

## 15. Commit/mốc gần nhất

Các mốc mới nhất trước HANDOFF update này:

```text
4619fcf7  root README: save local
533d8f4d  server README: progression
3ff2979e  app v0.4 + tests + reset_save
21b3fd91  state.py JSON save/progression
20891385  handoff GiangHo/BattleReplay
f5abbd8d  README BattleReplay
42ce749f  server README smoke battle
a5db4a1e  docs giangho-battle
a5c9c170  smoke_client
e217d3b1  minimal Battle.asmx/GiangHo
```

## 16. Quy tắc bắt buộc

- Luôn phân biệt `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump.
- Ưu tiên flow nhỏ, deterministic, testable.
- **Sau mỗi mốc quan trọng phải cập nhật HANDOFF** để chat mới tiếp tục ngay, đúng yêu cầu người dùng.
