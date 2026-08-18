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

`protocol_audit.py` phải cho:

```text
Client endpoints: 277
Missing from server allowlist: 0
```

User đã chạy 2026-08-18 và xác nhận:

```text
Client endpoints: 277
Static server coverage: 277
Missing from server allowlist: 0
Allowlist entries absent from this client: 0
```

## 4. Mốc mới: DTO audit trực tiếp từ metadata
Trước khi user pull, đã làm thêm một lượt đối soát metadata `TypeDef/Field` trong `Assembly-CSharp.dll` và phát hiện server 0.9 còn nhiều response key đoán sai dù endpoint đã đúng.

Tài liệu mới:

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

Stub cũ `SystemHighLightList/SystemHighLight` sai.

### LayNhanVat
Exact `HTTPLayNhanVatRespone`:

```text
errorCode
errorMsg
ListEventHon
GetIdx
UpdateUserInfo
```

Server 0.10 bỏ alias đoán, dùng `errorMsg` làm valid embedded hero code theo runtime callback đã quan sát.

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

Server 0.9 sai casing `giangHoIdx/nhiemVuIdx` và thêm field đoán. Server 0.10 đã sửa exact DTO.

### GetTongKimInfo — correction test quan trọng
Static metadata xác nhận `HTTPGetTongKimResponse` chỉ có:

```text
huongDan
listBoss
```

Không có `ErrorCode/errorCode`. Unit test cũ dùng generic success-envelope nên fail dù handler đúng. Đã sửa test để kiểm exact DTO `{huongDan:"", listBoss:[]}` thay vì ép phải có ErrorCode.

Commit fix:

```text
dee43935  Sửa test DTO GetTongKimInfo theo schema tĩnh
```

### Các read DTO đã sửa exact/skeleton non-null

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

## 5. Kiến trúc fallback sửa lại — quan trọng
Server 0.9 có lỗi thiết kế: endpoint nằm trong 277 list nhưng chưa reverse DTO được trả **fake success `ErrorCode=1`**. Điều này loại 404 nhưng khiến client đi vào success callback và dễ NullReference vì thiếu data.

Từ **server 0.10**:

- route đã có exact/minimal DTO -> success handler riêng;
- endpoint thuộc 277 nhưng chưa reverse -> HTTP/AES vẫn hợp lệ nhưng logical `ErrorCode/errorCode=0` với thông báo controlled unsupported;
- endpoint không tồn tại trong 277 -> HTTP 404.

=> không còn biến `404` thành `fake success + NullReference` một cách mù quáng.

## 6. Giang Hồ — PARTIAL
Minimal BattleReplay chạy runtime nhưng nội dung chưa phải game gốc.

Đã persist Bạc + account EXP + hero EXP. NPC fixture thay đổi theo ải nhưng roster/item/combat script/reward gốc chưa map từ config.

Exact endpoint:

```text
/DanhNhanhGiangHo
/ResetTurnNhiemVuGH
```

`DanhNhanhGiangHo` hiện thực hiện tối đa 10 clear và response đã sửa theo exact DTO static. Runtime retest pending.

## 7. Blocker runtime đã biết
- **Mở tướng:** runtime cũ `WaitForLayNhanVat -> SetByName -> KeyNotFoundException`; server 0.10 đã sửa theo exact DTO, retest pending.
- **Kỳ Ngộ:** `KyNgoForm.CreateDocCoPage -> NullReferenceException`; data issue.
- **Luận Kiếm:** `LuanKiemBang.SyncWithNetworkData -> NullReferenceException`; server 0.10 đã dựng exact response skeleton, retest pending.
- **Bang Chiến:** `BangChienForm.SetupGUI -> NullReferenceException`; exact root DTO đã dựng, nested semantics còn pending.
- **Linh Thưởng:** `LinhThuongQuay.OnDoiThuongNPC1/NPC2 -> NullReferenceException`; chưa reverse data source.

## 8. Server / tests mới
Server hiện: `DMCOffline/0.10`.

Mốc commit mới:

```text
8f099ba5  Đối soát DTO runtime trước khi test
e69ca07b  Cập nhật test theo DTO đã đối soát
a6cc341b  Đồng bộ test server với DTO runtime mới
4c933d48  Ghi lại đối soát DTO runtime từ Assembly
dee43935  Sửa test DTO GetTongKimInfo theo schema tĩnh
```

User đã chạy test sau khi pull và có đúng 1 failure:

```text
test_known_read_routes_return_success
AssertionError: None != 1 : gettongkiminfo
```

Nguyên nhân là test sai, không phải handler sai. Đã fix trên repo; user cần `git pull` lại và chạy `python -m unittest -v`.

## 9. Bước user cần làm tiếp

```bat
cd /d "F:\Downloads\img\đạiminhchủ\DaiMinhChu-Offline"
git pull
cd server
python -m unittest -v
```

Nếu toàn bộ test `OK`, chạy:

```bat
set DMC_BASE_URL=http://192.168.1.14:8000
python app.py
```

`/health` phải báo:

```text
server_version = DMCOffline/0.10
static_endpoint_count = 277
```

Sau đó mới runtime test client.

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
