# Protocol — First character / BeginCutsceneForm

> APK mục tiêu: **Đại Minh Chủ Việt Nam 8.0.2**.
>
> Trạng thái trong tài liệu này:
> - **CONFIRMED STATIC**: xác nhận trực tiếp từ IL/metadata/config nhúng trong APK.
> - **RUNTIME PENDING**: server/fixture đã dựng nhưng chưa test end-to-end trên Android thật/emulator.

## 1. Core config đã nằm sẵn trong APK — CONFIRMED STATIC

`GameManager.Awake()` load các `TextAsset` từ Unity `Resources` trước khi người dùng login.

Các resource đã xác nhận gồm:

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

Sau đó client gọi `ConfigManager.ReadAllCfg(...)`.

### Ý nghĩa

`LoginCfg = null` trong response `/Login` chỉ làm client **bỏ qua remote config update**. Nó không làm client mất toàn bộ config gameplay, vì core config đã được bundle sẵn trong APK và load từ `Resources`.

Đây là lý do hướng local/offline có khả năng khả thi hơn dự đoán ban đầu.

## 2. Form index 13 là `BeginCutsceneForm` — CONFIRMED STATIC

Sau `/GetUserInfo`, nếu:

```text
NhanVat == null hoặc NhanVat.Count == 0
```

client chuyển tới Form index `13`.

Static constructor của `BeginCutsceneForm` xác nhận 3 mã nhân vật khởi đầu:

```text
NhanVat1Name = "NV_PhongThanhDuong"
NhanVat2Name = "NV_LenhHoXung"
NhanVat3Name = "NV_SoLuuHuong"
```

`BeginCutsceneForm.OnActive()` lấy tên hiển thị/mô tả từ `ConfigManager.nhanVatCfgs`, tiếp tục xác nhận rằng config nhân vật nhúng trong APK được dùng ở flow này.

## 3. Ba nhân vật khởi đầu — CONFIRMED STATIC

Đã parse được TextAsset `ConfigFile/NhanVat` trong APK. Asset chứa khoảng `333` cấu hình nhân vật.

Không commit full asset/config gốc lên repository; dưới đây chỉ ghi các field tối thiểu cần cho compatibility fixture.

### `NV_PhongThanhDuong`

```text
Tên hiển thị: Phong Thanh Dương
Hạng: 1
VoCongMacDinh: VC_DocCoCuuKiem
MauCoSo: 260
CongCoSo: 284
ThuCoSo: 155
NoiLucCoSo: 234
```

### `NV_LenhHoXung`

```text
Tên hiển thị: Lệnh Hồ Xung
Hạng: 1
VoCongMacDinh: VC_DocCoCuuKiem
MauCoSo: 180
CongCoSo: 180
ThuCoSo: 60
NoiLucCoSo: 300
```

### `NV_SoLuuHuong`

```text
Tên hiển thị: Sở Lưu Hương
VoCongMacDinh: VC_DapTuyetLuuHuong
MauCoSo: 250
CongCoSo: 150
ThuCoSo: 160
NoiLucCoSo: 305
```

## 4. Click chọn nhân vật — CONFIRMED STATIC

Các click handler của `BeginCutsceneForm` cuối cùng gọi:

```text
SelectNhanVat(<code>)
```

và method này gọi:

```text
HTTP.SelectStartNhanVat(
    HTTP.WaitForSelectStartNhanVat,
    <code>
)
```

## 5. `/SelectStartNhanVat` — CONFIRMED STATIC

Endpoint:

```text
<LobbyURL>/SelectStartNhanVat
```

### Request type

`HTTPSelectStartNVRequest`:

```text
Aid         : int32
Token       : string
NhanVatCode : string
```

Client set:

```text
Aid         = HTTP.UserInfo.AID
Token       = HTTP.UserInfo.AccessToken
NhanVatCode = code người chơi chọn
```

Sau đó request được serialize/encrypt bằng cùng transport AES đã ghi trong `login.md`.

Ví dụ plaintext JSON về mặt cấu trúc:

```json
{
  "Aid": 1,
  "Token": "offline-token",
  "NhanVatCode": "NV_LenhHoXung"
}
```

## 6. Response type — CONFIRMED STATIC

`WaitForSelectStartNhanVat` deserialize response thành:

```text
HTTPGetUserInfoResponse
```

chứ không phải một response class riêng.

Success khi:

```text
ErrorCode == 1
```

Khi success, client thực hiện:

```text
HTTP.UserInfo.UpdateData(response)
BeginCutsceneForm.OnSelectCharacterComplete()
```

Sau phần animation/cutscene, flow chuyển tới Home / Form index `3`.

## 7. `HTTPUserInfo.UpdateData()` — CONFIRMED STATIC

Các điều kiện merge quan trọng cho milestone này:

- nếu `response.NhanVat != null && response.NhanVat.Count > 0` → thay `Data.NhanVat`;
- nếu `response.DoiHinh != null && response.DoiHinh.Slot1 > -1` → thay `Data.DoiHinh`.

`doihinh::.ctor()` mặc định khởi tạo:

```text
Slot1..Slot8 = -1
```

Do đó response chọn nhân vật phải có ít nhất một hero và `Slot1` hợp lệ để Home tìm được hero đang đứng đội hình.

## 8. Schema `nhanvat` tối thiểu — CONFIRMED STATIC

Tên property đã thấy trong metadata:

```text
Id
Name
Level
Exp
ExpMax
Mau
Cong
Thu
Noicong
VoCong1Level
KyNgoCocLevel
```

Client có nhiều field hơn, nhưng chưa cần dựng tất cả cho milestone đầu.

## 9. Home form cần gì — CONFIRMED STATIC

`HomeForm.SyncWithNetworkData()` gọi các component sync dữ liệu user.

`BigNhanVatSlider` duyệt các slot `DoiHinh`. Với hero ID dương, nó gọi:

```text
HTTPUserInfo.GetNhanVatByID(id)
```

rồi dùng `nhanvat.Name` để resolve config/visual của nhân vật.

Do vậy fixture tối thiểu hợp lý:

```json
{
  "ErrorCode": 1,
  "ErrorMsg": "",
  "NhanVat": [
    {
      "Id": 1,
      "Name": "NV_LenhHoXung",
      "Level": 1,
      "Exp": 0,
      "ExpMax": 100,
      "Mau": 180,
      "Cong": 180,
      "Thu": 60,
      "Noicong": 300,
      "VoCong1Level": 1,
      "KyNgoCocLevel": 1
    }
  ],
  "DoiHinh": {
    "Slot1": 1
  }
}
```

`AccountInfoGUI` trên Home còn đọc các field như:

```text
Account.DisplayName
Account.Level
Account.Exp / ExpMax
Account.Vang
Account.Bac
GiaTriThoiGian.LuotNV / LuotNVMax
GiaTriThoiGian.LuotTD / LuotTDMax
```

Vì vậy prototype `/GetUserInfo` hiện cấp các giá trị cơ bản này trước khi bước vào flow chọn nhân vật.

## 10. Server local đã implement — RUNTIME PENDING

`server/app.py` hiện xử lý:

```text
/Login
/CheckUser
/GetUserInfo
/SelectStartNhanVat
```

`/GetUserInfo` ban đầu trả `NhanVat: []` để ép client vào `BeginCutsceneForm`.

`/SelectStartNhanVat` chấp nhận đúng 3 code đã xác nhận và trả:

```text
NhanVat[0].Id = 1
NhanVat[0].Name = selected code
DoiHinh.Slot1 = 1
```

cùng base stats tương ứng từ config nhúng.

## 11. Flow milestone hiện tại

```text
LoginForm
   |
   v
/Login
   |
   v
SelectServerForm
   |
   v
/CheckUser
   |
   v
/GetUserInfo (NhanVat=[])
   |
   v
BeginCutsceneForm (Form 13)
   |
   | chọn Phong Thanh Dương / Lệnh Hồ Xung / Sở Lưu Hương
   v
/SelectStartNhanVat
   |
   | HTTP.UserInfo.UpdateData
   v
BeginCutsceneForm.OnSelectCharacterComplete
   |
   v
Home (Form 3)
```

## 12. Blocker thật tiếp theo

Static reverse cho milestone này đã đủ để thử client thật.

Cần chạy APK đã patch trên Android/emulator với local server và quan sát:

```text
server console log
adb logcat
```

Expected request sequence:

```text
POST .../Login
POST .../CheckUser
POST .../GetUserInfo
POST .../SelectStartNhanVat
```

Nếu client crash hoặc phát sinh endpoint mới sau đó, lấy stack/log + request thực tế rồi reverse đúng điểm đó, không đoán trước.
