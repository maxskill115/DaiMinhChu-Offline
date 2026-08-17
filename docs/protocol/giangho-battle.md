# Protocol — Giang Hồ / Battle.asmx/GiangHo

> APK mục tiêu: Đại Minh Chủ Việt Nam 8.0.2.
>
> Phân loại:
> - **CONFIRMED STATIC**: đọc trực tiếp từ IL/metadata/config của client.
> - **SERVER TESTED**: local Python server/transport đã được smoke-test ngoài client.
> - **CLIENT RUNTIME PENDING**: chưa chạy end-to-end trên Android/emulator.

## 1. Mở Giang Hồ không gọi server — CONFIRMED STATIC

`MenuGroup.OnGiangHoBtnClick()` chuyển:

```text
GameManager.ActiveForm = 4
```

Form `4` là `GiangHoForm`.

`GiangHoForm.OnActive()` chủ yếu sync dữ liệu đã có trong `HTTP.UserInfo.Data` và config nhúng. Không cần request mạng chỉ để mở màn Giang Hồ.

`GiangHoSlider` tạo chapter/stage từ `ConfigManager.giangHoCfgs`; item đầu tiên được enable mặc định.

### User mới có `GiangHo=[]` vẫn được client hỗ trợ

`GH_NhiemVuSlider.SyncWithNetworkData()` có nhánh khi:

```text
currentGiangHoIdx == HTTP.UserInfo.Data.GiangHo.Count
```

Client tự tạo record nhiệm vụ tạm với:

```text
S = 0
T = 0
```

Do đó prototype `/GetUserInfo` không cần tạo progress Giang Hồ giả chỉ để hiển thị chapter đầu.

## 2. Click đánh nhiệm vụ — CONFIRMED STATIC

`GH_NhiemVu_Item.OnBattleClick()` kiểm tra lượt nhiệm vụ rồi gọi:

```text
HTTP.DanhGiangHo(
    HTTP.WaitForDanhGiangHo,
    giangHoIdx,
    nhiemVuIdx
)
```

Request type `HTTPBattleGiangHoRequest` dùng **public fields lowercase**:

```text
aid        int32
token      string
giangHoIdx uint8
nhiemVuIdx uint8
```

Request được gửi tới Battle URL:

```text
<BattleURL>/GiangHo
```

`BattleURL` được client tạo khi chọn server bằng:

```text
User.asmx -> Battle.asmx
```

Ví dụ local:

```text
http://10.0.2.2:8000/Server/Webservice/Battle.asmx/GiangHo
```

Transport vẫn là AES/JSON như `login.md`.

## 3. Response root — CONFIRMED STATIC

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

Success:

```text
ErrorCode == 1
```

`HTTP.WaitForDanhGiangHo()` lưu response rồi gọi:

```text
GiangHoForm.OnReceiveBattleResult(response.BattleReplay)
```

`OnReceiveBattleResult()`:

```text
BattleForm.environment = GiangHo  // numeric 0
GameManager.ActiveForm = 7        // Form 7 = BattleForm
BattleForm.PlayGame(replay, false)
```

## 4. Cấu trúc BattleReplay — CONFIRMED STATIC

### `KetQuaTranDau`

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

### `Team`

```text
Name      string
AccountID string
DanhVong  int
```

### `HiepDau`

```text
DoiHinh1 List<VoGia>
DoiHinh2 List<VoGia>
LuotDau  List<LuotDau>
```

### `VoGia`

```text
Name    string
Mau     int64
NoiLuc  float
Buffs   List<BuffValue>
BuaChu  List<BuffValue>
BiThuat List<BuffValue>
```

`VoGia.Name` phải là key tồn tại trong embedded `ConfigManager.nhanVatCfgs`; `SetDoiHinh()` index trực tiếp dictionary này để lấy tên/visual.

### `LuotDau`

```text
DoiTanCong          TeamEnum
NguoiTanCong        int
DanhSachThuongTon   List<ThuongTon>
VoCong               string
```

### `ThuongTon`

```text
Value                 int64
TrangThaiThuongTon    List<TrangThai>
```

## 5. TeamEnum và normal attack — CONFIRMED STATIC

Client branches show:

```text
Team1 = 0
Team2 = 1
```

`BattleReplayPanel.playLuotDau()`:

- `DoiTanCong == 0` → attacker lấy từ Team1;
- `DoiTanCong != 0` → attacker lấy từ Team2.

Nếu:

```text
VoCong == null hoặc ""
```

client đi nhánh **normal attack**, không lookup `ConfigManager.voCongCfgs`.

Normal attack dùng:

```text
DanhSachThuongTon[0]
```

nên list damage phải có ít nhất 1 phần tử.

`BattleNhanVat.BiTanCong()` và `HeroBattleAvatar.PlayImpact()` gọi `.Contains(...)` trên `TrangThaiThuongTon`, vì vậy list status **không được null**. Fixture an toàn nhất cho đòn thường là:

```json
{
  "DoiTanCong": 0,
  "NguoiTanCong": 0,
  "DanhSachThuongTon": [
    {"Value": 100, "TrangThaiThuongTon": []}
  ],
  "VoCong": ""
}
```

Một số enum status đã suy ra trực tiếp từ branch client:

```text
1 = BaoKich
2 = NeDon
3 = PhanKich
5 = HoThe
```

Fixture đầu tiên không cần status đặc biệt nên dùng `[]`.

## 6. Điều kiện tối thiểu để replay không null-crash — CONFIRMED STATIC

Client dereference trực tiếp các field sau:

```text
Team1 != null
Team2 != null
Hiep1 != null
Hiep1.DoiHinh1 != null và có fighter
Hiep1.DoiHinh2 != null và có fighter
Hiep1.LuotDau != null và Count >= 1
VoGia.Buffs != null
DanhSachThuongTon != null và Count >= 1
TrangThaiThuongTon != null
```

`Hiep2` và `Hiep3` có thể `null`; `PlayGameVisual()` kiểm tra trước khi chạy hai hiệp này.

`PlayBuffs()` gọi `.Count` trên `VoGia.Buffs` không có null-check, do đó server gửi `Buffs: []` cho từng fighter.

Top-level `BuaChuBiThuatMP1/MP2` có null-check, nhưng prototype gửi `[]` để fixture rõ ràng/deterministic.

## 7. Kết quả trận / Reward — CONFIRMED STATIC

`BattleGiangHoResultPanel.SetResult()` coi:

```text
DoiThang == 0
```

là Team1/player và dùng `star` để hiển thị:

```text
0 = thua
1 = thắng 1 sao
2 = thắng 2 sao
3 = thắng 3 sao
```

Result panel dereference trực tiếp:

```text
Reward.ExpMonPhai
Reward.Bac
UpdateUserInfo.NhanVat
```

Vì vậy `Reward` và `UpdateUserInfo` phải non-null.

`BattleForm.UpdateGiangHoResult()` khi đóng result gọi:

```text
HTTP.UserInfo.UpdateData(response.UpdateUserInfo)
```

và kiểm tra `Reward.Items`.

Prototype hiện trả:

```json
"Reward": {
  "Bac": 100,
  "Vang": 0,
  "ExpMonPhai": 10,
  "ExpNhanVat": 10,
  "Items": []
}
```

`UpdateUserInfo.NhanVat` chứa lại hero ID 1 để result panel tìm được nhân vật đang ở `DoiHinh.Slot1`.

## 8. Fixture server hiện tại — SERVER TESTED

`server/app.py` đã có route suffix:

```text
POST /Server/Webservice/Battle.asmx/GiangHo
```

Fixture hiện là trận 1v1, 1 hiệp, 1 đòn thường:

```text
player Team1
 -> normal attack
 -> enemy nhận damage bằng toàn bộ HP
 -> DoiThang = Team1
 -> star = 3
```

Hero player lấy từ lựa chọn `/SelectStartNhanVat` đang giữ trong state RAM của process. Enemy dùng một code nhân vật khởi đầu khác để chắc chắn tồn tại trong config nhúng.

Tiến trình Giang Hồ **chưa được lưu/cập nhật** ở milestone này, nên trận đầu có thể đánh lại. Đây là chủ ý để test compatibility trước.

## 9. Smoke test local — SERVER TESTED, không phải client runtime

Đã test trực tiếp server bằng request AES thực tới:

```text
/Server/Webservice/Battle.asmx/GiangHo
```

và decrypt response thành công với:

```text
ErrorCode = 1
star = 3
DoiThang = 0
Hiep1.LuotDau.Count = 1
```

Repo có `server/smoke_client.py` để test cả chuỗi:

```text
Login -> CheckUser -> GetUserInfo -> SelectStartNhanVat -> GiangHo
```

## 10. Trạng thái cần ghi đúng

Hiện tại:

- **static reverse:** đủ để dựng replay 1v1 tối thiểu;
- **local server smoke test:** pass;
- **Android/client runtime:** vẫn **PENDING**.

Chưa được kết luận rằng Unity client đã phát trận thành công cho tới khi có test APK thật + server console + `adb logcat`.
