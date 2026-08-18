# HANDOFF — DaiMinhChu-Offline

> **ĐỌC FILE NÀY TRƯỚC KHI TIẾP TỤC Ở CHAT MỚI.** Đây là nguồn trạng thái chính của dự án. Sau mỗi mốc kỹ thuật quan trọng phải cập nhật lại HANDOFF.

**Last updated:** 2026-08-18 (UTC+7)

## 1. Mục tiêu
Phục dựng **Đại Minh Chủ Việt Nam 8.0.2** chạy local/offline, giữ client/UI/assets gốc càng nhiều càng tốt. Hướng chính: clean-room local compatibility backend + client patch tối thiểu.

## 2. Client/runtime nền tảng
APK 8.0.2 Unity 4.x/Mono/ARMv7. Signed v2 đã patch direct login + no-op `SohaSDKManager.SetUserInfo`, signature v1/v2/v3 OK.

**CONFIRMED RUNTIME trên LDPlayer 32-bit:** Login -> CheckUser -> GetUserInfo -> starter -> Home. GM đã runtime-confirmed đổi VIP=8 và Vàng/KNB=10000.

## 3. Static endpoint audit
Đã extract trực tiếp `Assembly-CSharp.dll`: **277 endpoint exact**.

Repo:

```text
server/static_endpoints.py
tools/protocol_audit.py
```

User đã chạy 2026-08-18 và xác nhận:

```text
Client endpoints: 277
Static server coverage: 277
Missing from server allowlist: 0
Allowlist entries absent from this client: 0
```

=> endpoint-name coverage hiện sạch cho client 8.0.2.

## 4. DTO audit trực tiếp từ metadata
Đã đối soát metadata `TypeDef/Field` trong `Assembly-CSharp.dll` để sửa nhiều response key trước đó bị đoán sai.

Tài liệu:

```text
docs/protocol/runtime-dto-audit.md
```

Các correction **CONFIRMED STATIC** chính:

### GetSystemHighLight
Exact `HTTPSystemHighLightRespone`:

```text
highLightQuery
errorCode
errorMsg
```

### LayNhanVat
Exact `HTTPLayNhanVatRespone`:

```text
errorCode
errorMsg
ListEventHon
GetIdx
UpdateUserInfo
```

Server 0.10 dùng `errorMsg` làm valid embedded hero code theo runtime callback đã quan sát.

### DanhNhanhGiangHo
Exact `HTTPDanhNhanhGiangHoResponse`:

```text
Rewards : List<BattleReward>
GiangHoIdx
NhiemVuIdx
UpdateUserInfo
ErrorCode
ErrorMsg
```

### GetTongKimInfo
Static metadata xác nhận `HTTPGetTongKimResponse` chỉ có:

```text
huongDan
listBoss
```

Không có `ErrorCode/errorCode`. Unit test cũ sai đã được sửa.

### Các read DTO đã có exact/minimal skeleton

```text
GetInfoLienMinh
ChatGet
GetAnhHungBang / LuanKiemBang
GetDongNhanInfo
GetHuyetChienInfo
GetNienThuInfo
GetVanTieuInfo
NguNhacGetInfo
GetTongKimInfo
GetInfoBangChien
FindLienMinh
GetThanhVienLienMinh
RefreshDiemLuanKiem
GetMiniBossInfo
```

Nested DTO quan trọng cũng đã đối soát cho `HuyetChienProfile`, `NNKiemTranInfo`, `NNBiBaoShop`, `DoiDiemNPC`, `BattleReward`, v.v.

## 5. Kiến trúc fallback
Từ **server 0.10**:

- route đã có exact/minimal DTO -> success handler riêng;
- endpoint thuộc 277 nhưng chưa reverse -> HTTP/AES hợp lệ nhưng logical `ErrorCode/errorCode=0` controlled unsupported;
- endpoint không tồn tại trong 277 -> HTTP 404.

=> tránh fake-success rồi NullReference.

## 6. Server 0.10 — SERVER TESTED CLEAN
User đã pull đến commit `2d866de` và chạy:

```text
python -m unittest -v
```

Kết quả **CONFIRMED SERVER TESTED**:

```text
Ran 29 tests in 0.091s
OK
```

Sau đó chạy server với:

```text
DMC_BASE_URL=http://192.168.1.14:8000
```

Console xác nhận:

```text
Starting Dai Minh Chu local compatibility server
Listen: http://0.0.0.0:8000
Advertised User.asmx: http://192.168.1.14:8000/Server/Webservice/User.asmx
Derived Battle.asmx: http://192.168.1.14:8000/Server/Webservice/Battle.asmx
Exact routes: 26; static client endpoints covered: 277
```

`GET http://127.0.0.1:8000/health` trả 200 và xác nhận:

```text
server_version = DMCOffline/0.10
static_endpoint_count = 277
exact_route_count = 26
has_character = true
```

=> server 0.10 hiện đủ điều kiện runtime test client, không cần sửa unit/server bootstrap trước.

## 7. Giang Hồ — PARTIAL
Minimal BattleReplay chạy runtime nhưng nội dung chưa phải game gốc.

Đã persist Bạc + account EXP + hero EXP. NPC fixture thay đổi theo ải nhưng roster/item/combat script/reward gốc chưa map từ config.

Exact endpoint:

```text
/DanhNhanhGiangHo
/ResetTurnNhiemVuGH
```

`DanhNhanhGiangHo` đã có exact root DTO static và thực hiện tối đa 10 clear. **Runtime retest pending trên server 0.10.**

## 8. Blocker runtime cần retest trên 0.10
- **Mở tướng:** runtime cũ `WaitForLayNhanVat -> SetByName -> KeyNotFoundException`; exact DTO đã sửa, retest pending.
- **Kỳ Ngộ:** `KyNgoForm.CreateDocCoPage -> NullReferenceException`; data issue.
- **Luận Kiếm:** `LuanKiemBang.SyncWithNetworkData -> NullReferenceException`; server 0.10 đã dựng response skeleton, retest pending.
- **Bang Chiến:** `BangChienForm.SetupGUI -> NullReferenceException`; exact root DTO đã dựng, nested semantics còn pending.
- **Linh Thưởng:** `LinhThuongQuay.OnDoiThuongNPC1/NPC2 -> NullReferenceException`; chưa reverse data source.

## 9. Việc cần làm NGAY
Không pull/build APK thêm. Server 0.10 đang chạy và test sạch.

Runtime test theo thứ tự:

1. Mở tướng / LayNhanVat.
2. Giang Hồ: đánh 2 ải khác nhau, kiểm Bạc/EXP; bấm Đánh nhanh 10 lần.
3. Luận Kiếm.
4. Bang Chiến.
5. Kỳ Ngộ.
6. Sau đó mới sweep các menu còn lại.

Khi test, ưu tiên capture `adb logcat` + console server từ lúc click chức năng đến lúc lỗi/thành công để xác nhận DTO runtime, không còn dùng log để discover endpoint-name.

## 10. APK workspace / GM
- `tools/apk_workspace.py`: unpack/scan/repack raw APK; Unity serialized assets vẫn cần AssetRipper/UABE/UnityPy cho texture/audio/animation/effect/prefab.
- GM: `http://127.0.0.1:8000/gm`.

## 11. Quy tắc dự án
- Phân biệt `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore/credential.
- Không gọi stub là feature hoàn chỉnh.
- Không đoán schema rồi coi như confirmed.
- Ưu tiên static reverse DTO từ Assembly trước khi bắt user test lại.
- **Sau mỗi milestone phải cập nhật HANDOFF.md.**
