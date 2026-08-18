# Runtime DTO audit — Đại Minh Chủ 8.0.2

Nguồn: metadata trực tiếp từ `Assembly-CSharp.dll` của APK mục tiêu 8.0.2.

Phân loại: **CONFIRMED STATIC**. Đây là tên field/type từ client; không đồng nghĩa gameplay server đã hoàn chỉnh.

## Các sửa sai quan trọng trước server 0.10

### GetSystemHighLight

`HTTPSystemHighLightRespone`:

```text
highLightQuery : List<HTTPHighLightUnit>
errorCode      : HTTP_ERROR_CODE
errorMsg       : string
```

Stub cũ dùng `SystemHighLightList/SystemHighLight` là sai DTO.

### LayNhanVat

`HTTPLayNhanVatRespone` chỉ có:

```text
errorCode
errorMsg
ListEventHon
GetIdx
UpdateUserInfo
```

Iterator `WaitForLayNhanVat` có local `nhanvat_str`, `tan_hon_count`, và runtime trước đó cho thấy callback truyền chuỗi nhận được vào `BigNhanVatAvatar.SetByName`. Server 0.10 dùng `errorMsg` làm valid embedded character code và bỏ các alias không tồn tại trong DTO.

### DanhNhanhGiangHo

`HTTPDanhNhanhGiangHoResponse`:

```text
Rewards        : List<BattleReward>
GiangHoIdx     : int
NhiemVuIdx     : int
UpdateUserInfo : HTTPGetUserInfoResponse
ErrorCode
ErrorMsg
```

`BattleReward`:

```text
Items
Bac
Vang
ExpMonPhai
ExpNhanVat
```

Stub cũ trả lowercase `giangHoIdx/nhiemVuIdx` và thêm `Count/Reward/ListReward`; server 0.10 đã đổi về exact DTO.

### GetInfoLienMinh

`HTTPGetInfoLienMinhResponse`:

```text
errorCode
errorMsg
lienMinhInfo : HTTPLienMinh
```

### CreateLienMinh

`HTTPCreateLienMinhRespone`:

```text
lienMinh
lienMinhAccount
info
errorCode
errorMsg
```

Chưa có alliance state thật, vì vậy server 0.10 trả controlled failure thay vì fake success + null data.

### ChatGet

`HTTPChatGetResponse`:

```text
chatQuery
errorCode
errorMsg
```

### GetAnhHungBang / Luận Kiếm

`HTTPLuanKiemBangResponse`:

```text
AnhHungBang
ThuHang
DiemTichLuy
LuotLuanKiem
lastTimeGetDiem
GetRewardTop1000
GetRewardTop500
GetRewardTop200
GetRewardTop100
GetRewardTop50
GetRewardTop10
GetRewardTop1
NPC1
NPC2
ErrorCode
ErrorMsg
```

`NPC1/NPC2` là `DoiDiemNPC` với `CodeName`, `DiemThuongCanDoi`, `BoiDuongDan`.

### GetDongNhanInfo

`HTTPDongNhanResponse` có các property chính:

```text
LevelDongNhan
MauDongNhan
MauDongNhanOrig
TopHits
TimeStartDongNhan
lastTop10
ServerTime
LuotDanh
TotalThuongTon
CostRespawn
DurationLastBattle
ErrorCode
ErrorMsg
```

Ngoài ra có queue/last-time nội bộ.

### GetHuyetChienInfo

`HTTPGetHuyetChienInfoResponse`:

```text
Profile : HuyetChienProfile
Top
PhanThuong : HTTPDanhSachPhanThuongResponse
ErrorCode
ErrorMsg
```

Server 0.10 trả non-null profile/reward containers để tránh success callback dereference null.

### GetNienThuInfo

`HTTPNienThuResponse` có:

```text
LevelNienThu
MauLong/MauLan/MauQuy/MauPhung
MauOrigLong/MauOrigLan/MauOrigQuy/MauOrigPhung
TopHits
TimeStartNienThu
lastTop10
ServerTime
LuotDanh
TotalThuongTon
CostRespawn
DurationLastBattle
ErrorCode
ErrorMsg
```

### GetVanTieuInfo

`HTTPGetVanTieuInfoResponse`:

```text
maxVanTieu
thoiGian
soLuotMienPhi
knb
vanTieu
cuopTieuLog
errorCode
errorMsg
```

### NguNhacGetInfo

`HTTPGetNguNhacInfoResponse`:

```text
errorCode
errorMsg
kiemTranInfo : NNKiemTranInfo
knbVuotNhanh
biBaoShopInfo : NNBiBaoShop
huongDan
```

Server 0.10 tạo nested containers non-null.

### GetTongKimInfo

`HTTPGetTongKimResponse`:

```text
huongDan
listBoss
```

## Kiến trúc fallback

Server 0.9 trả `ErrorCode=1` cho mọi endpoint tĩnh chưa reverse. Điều đó nguy hiểm: client đi vào success callback rồi dereference field không tồn tại, sinh NullReferenceException.

Từ server 0.10:

- endpoint exact đã reverse DTO: trả success DTO riêng;
- endpoint nằm trong inventory 277 nhưng chưa reverse: HTTP vẫn 200/AES đúng, nhưng logical `ErrorCode/errorCode = 0` với thông báo `endpoint recognised but DTO/gameplay is not reconstructed yet`;
- endpoint không có trong inventory client: vẫn HTTP 404.

Mục tiêu là loại 404 sai nhưng không giả thành công khi chưa có schema/data.
