# HANDOFF — DaiMinhChu-Offline

> ĐỌC FILE NÀY TRƯỚC KHI TIẾP TỤC Ở CHAT MỚI. Sau mỗi mốc kỹ thuật phải cập nhật lại.

**Last updated:** 2026-08-18 (UTC+7)

## Mục tiêu
Phục dựng **Đại Minh Chủ Việt Nam 8.0.2** để chơi local/offline, giữ client/UI/assets gốc. Hướng hiện tại: viết backend tương thích thay GS gốc. Ưu tiên login → user/tướng/đội hình/trang bị/võ công → Giang Hồ → BattleReplay → save local. Không ưu tiên nạp tiền/chat/PvP/bang hội online.

## Repo / APK
Repo: `maxskill115/DaiMinhChu-Offline`, branch `main`, hiện public. Không commit APK/full asset dump/credential/keystore.

APK mẫu:
```text
size 52,568,975 bytes
SHA256 2ff6b4db2177dc1362c20866750a48371f283a79a40335d3293a26e39e7e4194
package vn.sohagame.dminhchu
```
Unity 4.x + Mono; `Assembly-CSharp.dll` 2,425,856 bytes, nhiều symbol C# còn nguyên.

## Network — CONFIRMED STATIC
Login URL gốc:
`http://login.minhchu.sohagame.vn/Server/Webservice/User.asmx`

Transport:
`JSON -> AES -> Base64 -> WWW.EscapeURL -> POST data=<cipher>`; response làm ngược lại qua LitJson.

AES-128 CBC + PKCS7, Key=IV:
`03051f0205060315061705202a1f5620`.
Chi tiết: `docs/protocol/login.md`.

## Core config trong APK — CONFIRMED STATIC
`GameManager.Awake()` load trước login các Resources như `ConfigFile/NhanVat`, `TrangBi`, `VoCong`, `GiangHo`, `Other`, `ChanKhi`, `VatPhamTieuThu`, `HuyetChien`, `KimCham`, `LongChau`, localization... rồi `ConfigManager.ReadAllCfg(...)`.

=> `/Login` có thể trả `LoginCfg=null` để bỏ remote update mà core gameplay config vẫn còn. `ConfigFile/NhanVat` parse được khoảng 333 nhân vật; không commit dump gốc.

## Login flow — CONFIRMED STATIC
`/Login`: success `ErrorCode==1`; `LoginCfg==null` bỏ remote config download.

`tools/patch_client.py` đã patch:
1. login URL sang local;
2. `LoginForm.OnLoginBtnClick` từ `SohaSDKManager.Login()` sang `HTTP.Instance.Login(...)`.
Patcher chỉ nhận đúng SHA256 APK trên; IL sau patch đã disassemble đúng.

`/CheckUser`: request `User,Token`; success trả `Aid,ServerID`. Prototype dùng server 1 + `ListUserServer=[1]` để tránh `/UserAppendServer`.

`/GetUserInfo`: request `Aid,Token,Property[]`. Nếu `NhanVat.Count==0` → Form 13; nếu có tướng → Form 3.

## Form 13 + nhân vật đầu — CONFIRMED STATIC
Form 13 = `BeginCutsceneForm`.

Ba code:
```text
NV_PhongThanhDuong -> Phong Thanh Dương: Mau260 Cong284 Thu155 NoiLuc234
NV_LenhHoXung      -> Lệnh Hồ Xung:      Mau180 Cong180 Thu60  NoiLuc300
NV_SoLuuHuong      -> Sở Lưu Hương:      Mau250 Cong150 Thu160 NoiLuc305
```

Click gọi `/SelectStartNhanVat` với request:
```text
Aid int
Token string
NhanVatCode string
```
Response deserialize thành `HTTPGetUserInfoResponse`. Success → `HTTP.UserInfo.UpdateData(response)` → `BeginCutsceneForm.OnSelectCharacterComplete()` → Home/Form 3.

Fixture server trả hero ID 1 + `DoiHinh.Slot1=1`. Chi tiết: `docs/protocol/first-character.md`.

## Server hiện tại
Files:
```text
server/app.py
server/crypto.py
server/requirements.txt
server/test_server.py
server/README.md
```
`server/dmc_crypto.py` cũ đã xóa.

Routes:
```text
GET /health
POST /Login
POST /CheckUser
POST /GetUserInfo
POST /SelectStartNhanVat
```
Dependency: `cryptography>=42,<47`. `DMC_BASE_URL` nhận root URL và server tự thêm `/Server/Webservice/User.asmx`. Mặc định emulator `http://10.0.2.2:8000`.

Có 5 unit tests (AES, URL, user mới, 3 start hero, invalid hero), đã chạy local OK trước commit.

## Milestone hiện tại
```text
Patched LoginForm
 -> /Login
 -> /CheckUser
 -> /GetUserInfo (NhanVat=[])
 -> BeginCutsceneForm / Form 13
 -> chọn 1 trong 3 nhân vật
 -> /SelectStartNhanVat
 -> UpdateData(NhanVat + DoiHinh)
 -> Home / Form 3
```

**QUAN TRỌNG:** mới là **CONFIRMED STATIC + SERVER IMPLEMENTED**, CHƯA có `CONFIRMED RUNTIME`. Không nói game đã vào Home thật cho tới khi test Android/emulator.

## Battle đã biết
`HTTPBattleGiangHoRequest`: `aid,token,giangHoIdx(byte),nhiemVuIdx(byte)`.
`HTTPBattleGiangHoResponse`: `BattleReplay: KetQuaTranDau`, `Reward`, stage indexes, star, `UpdateUserInfo`, ErrorCode/ErrorMsg. Suy luận mạnh server sinh replay, client phát animation. Chưa reverse nested replay đầy đủ.

## Việc làm NGAY tiếp theo
Ưu tiên runtime Android:
1. `cd server`, cài requirements, `python -m unittest -v`.
2. `python app.py` với `DMC_BASE_URL` đúng IP PC Android truy cập được.
3. patch APK bằng `tools/patch_client.py` với cùng địa chỉ, zipalign/sign/install.
4. mở game, nhập user/pass bất kỳ, xem server console + `adb logcat`.

Expected:
```text
POST .../Login
POST .../CheckUser
POST .../GetUserInfo
[Form 13 hiện 3 nhân vật]
POST .../SelectStartNhanVat
[Home/Form 3]
```
Nếu fail: lấy request cuối + logcat/stack rồi reverse đúng chỗ fail.

Nếu chưa runtime được: static reverse Home startup/request tự động → GiangHo → BattleReplay.

## Mốc commit gần nhất
```text
364f5362 server SelectStartNhanVat
9483c920 cryptography
a6499192 unit tests
1a265ccf xóa dmc_crypto.py
2802d184 server README
5f5134f4 docs first-character
fd7b4de3 root README
```

## Quy tắc
Phân biệt `CONFIRMED STATIC`, `CONFIRMED RUNTIME`, `HYPOTHESIS`; không commit APK/full dump; ưu tiên flow nhỏ/testable; **sau mỗi mốc phải cập nhật HANDOFF**.
