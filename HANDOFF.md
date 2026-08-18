# HANDOFF — DaiMinhChu-Offline

> **ĐỌC FILE NÀY TRƯỚC KHI TIẾP TỤC Ở CHAT MỚI.** Đây là nguồn trạng thái chính của dự án. Sau mỗi mốc kỹ thuật quan trọng phải cập nhật lại HANDOFF.

**Last updated:** 2026-08-18 (UTC+7)

## 1. Mục tiêu
Phục dựng **Đại Minh Chủ Việt Nam 8.0.2** chạy local/offline, giữ client/UI/assets gốc càng nhiều càng tốt. Hướng chính: clean-room local compatibility backend + client patch tối thiểu.

## 2. Client/runtime nền tảng
APK 8.0.2 Unity 4.x/Mono/ARMv7. Signed v2 đã patch direct login + no-op `SohaSDKManager.SetUserInfo`, signature v1/v2/v3 OK.

**CONFIRMED RUNTIME trên LDPlayer 32-bit:** Login -> CheckUser -> GetUserInfo -> starter -> Home. GM runtime-confirmed đổi VIP=8 và Vàng/KNB=10000.

## 3. Static endpoint audit
Đã extract trực tiếp `Assembly-CSharp.dll`: **277 endpoint exact**.

Repo:

```text
server/static_endpoints.py
tools/protocol_audit.py
```

User đã chạy và xác nhận:

```text
Client endpoints: 277
Static server coverage: 277
Missing from server allowlist: 0
Allowlist entries absent from this client: 0
```

## 4. DTO audit trực tiếp từ metadata
Tài liệu:

```text
docs/protocol/runtime-dto-audit.md
```

Các DTO chính đã đối soát static: `GetSystemHighLight`, `LayNhanVat`, `DanhNhanhGiangHo`, `GetInfoLienMinh`, `ChatGet`, `GetAnhHungBang`, `GetDongNhanInfo`, `GetHuyetChienInfo`, `GetNienThuInfo`, `GetVanTieuInfo`, `NguNhacGetInfo`, `GetTongKimInfo`, `GetInfoBangChien`, `FindLienMinh`, `GetThanhVienLienMinh`, `RefreshDiemLuanKiem` và một số nested DTO.

## 5. Server 0.11 — GET transport + lowercase error semantics
Runtime sweep 14:01 phát hiện:

- `ChatGet` được legacy client gọi bằng HTTP GET nên server 0.10 vẫn 404 dù route đã đăng ký.
- DTO family dùng `errorCode` chữ thường có convention `0 = success`, ngược với uppercase `ErrorCode` dùng `1 = success`.
- generic fallback 0.10 trả `errorCode=0`, vô tình thành success với lower-case family.

Server 0.11 đã sửa:

1. `do_GET()` route toàn bộ static endpoint inventory.
2. GET có `data=` thì decrypt; GET rỗng gọi handler với `{}`.
3. Lowercase success DTO dùng `errorCode=0`.
4. Lowercase controlled failure dùng `errorCode=1`.
5. Generic unsupported dùng `ErrorCode=0` + `errorCode=1` để fail đúng ở cả hai convention.
6. Server version: `DMCOffline/0.11`.

Commits chính:

```text
f498f51f  Fix GET transport and lowercase error semantics
4491654a  Test GET transport and lowercase error semantics
```

## 6. Unit-test regression sau khi user pull 0.11 — đã sửa trên repo
User chạy `python -m unittest -v` và có **5 failures**, nhưng cả 5 đều là **test cũ còn kỳ vọng convention 0.10**, không phải app handler hỏng.

Regression test mới đã pass, sau đó test cũ đã được đồng bộ ở:

```text
a579d845  Sửa test audit theo quy ước errorCode lowercase
7ee622b4  Đồng bộ test server với errorCode lowercase
```

Các expectation mới:
- lowercase read/recruit success => `errorCode == 0`;
- `CreateLienMinh` controlled failure => `errorCode == 1`;
- uppercase read success => `ErrorCode == 1`;
- `GetTongKimInfo` không có error-code field.

## 7. Runtime sweep 14:30 — dữ liệu mới
User gửi logcat mới 749 dòng.

### 7.1 ChatGet vẫn FileNotFound
**CONFIRMED RUNTIME trong log 14:30:**

```text
Form LuyenCongForm is active
java.io.FileNotFoundException:
http://192.168.1.14:8000/Server/Webservice/User.asmx/ChatGet
```

Xuất hiện ít nhất 2 lần (14:30:46 và 14:30:57).

Điều này **mâu thuẫn trực tiếp** với regression test 0.11 (`GET /ChatGet` trả 200 encrypted). Khả năng cao nhất: process server đang phục vụ runtime vẫn là **server 0.10/cũ** hoặc chưa restart sau pull. Trước khi sửa app.py thêm, phải xác nhận `GET /health` đúng process đang chạy báo `DMCOffline/0.11` và console startup của chính process đó.

### 7.2 NienThu có blocker data thật
**CONFIRMED RUNTIME:** mở `NienThuForm` gây:

```text
KeyNotFoundException
Dictionary<string,int>.get_Item
NienThuItem.SetGUI(HTTPNienThuResponse)
NienThuForm.SetGUI
NienThuForm.SyncWithNetworkData
```

Sau đó `NienThuItem.Update()` lặp lại KeyNotFoundException nhiều lần.

`AutoTuLinhPopup -> StartAutoNienThu -> StartGame` cũng bị `Dictionary<string,int>.get_Item` KeyNotFound.

=> `HTTPNienThuResponse` root DTO đúng tên field nhưng **giá trị semantic hiện không hợp lệ với dictionary/config client**. Cần reverse IL `NienThuItem.SetGUI` / `AutoTuLinhPopup.StartGame` để biết exact dictionary key/value, không nên đoán.

### 7.3 Unsupported endpoint vẫn xuất hiện
Logcat có 2 lần:

```text
Offline backend: endpoint recognised but DTO/gameplay is not reconstructed yet
```

quanh lúc NienThu đang active. Logcat không cho biết endpoint name; cần console server dòng `STATIC-KNOWN UNSUPPORTED ...` để xác định chính xác.

### 7.4 Mở tướng chưa được đánh giá trong log này
Không tìm thấy chuỗi `LayNhanVat` trong logcat 14:30, nên chưa được phép kết luận recruit 0.11 đã thành công hay thất bại từ file này.

### 7.5 Không có NullReference trong log 14:30
Không tìm thấy `NullReferenceException`; blocker nổi bật của vòng này là FileNotFound ChatGet + KeyNotFound NienThu.

## 8. Giang Hồ — PARTIAL
Minimal BattleReplay chạy runtime nhưng chưa phải nội dung gốc. Đã persist Bạc + account EXP + hero EXP. NPC fixture thay đổi theo ải, nhưng roster/item/combat script/reward gốc chưa map từ config.

Exact endpoints:

```text
/DanhNhanhGiangHo
/ResetTurnNhiemVuGH
```

`DanhNhanhGiangHo` đã có exact root DTO static; runtime retest pending.

## 9. Việc cần làm NGAY
Trước khi sửa tiếp server vì `ChatGet`, xác nhận process runtime thực sự là 0.11:

```text
http://127.0.0.1:8000/health
```

phải báo `server_version = DMCOffline/0.11`.

Nếu không phải: tắt process cũ và restart server sau pull.

Nếu health đúng 0.11 mà client vẫn ChatGet 404, lúc đó lấy **console server** đúng thời điểm mở Luyện Công để xem request method/path thực tế và sửa transport tiếp.

Đồng thời cần reverse static IL cho:

```text
NienThuItem.SetGUI
AutoTuLinhPopup.StartGame / StartAutoNienThu
```

để dựng giá trị NienThu hợp lệ thay vì placeholder `1`/rỗng.

Runtime retest tiếp theo chỉ cần:
1. xác nhận `/health` version;
2. Mở tướng / Thu nhận;
3. Luyện Công;
4. NienThu;
5. gửi logcat + console server cùng thời điểm.

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
