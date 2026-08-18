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

## 5. Mốc server 0.10 trước runtime sweep mới
User đã chạy:

```text
Ran 29 tests in 0.091s
OK
```

`/health` xác nhận:

```text
server_version = DMCOffline/0.10
static_endpoint_count = 277
exact_route_count = 26
has_character = true
```

## 6. Runtime sweep 14:01 — phát hiện 2 lỗi nền tảng mới
User test nhiều menu trên server 0.10 và gửi logcat + ảnh.

### 6.1 ChatGet vẫn 404 dù route đã đăng ký
Logcat **CONFIRMED RUNTIME**:

```text
java.io.FileNotFoundException:
http://192.168.1.14:8000/Server/Webservice/User.asmx/ChatGet
```

Xuất hiện khi mở `LuyenCongForm`.

Nguyên nhân server-side: `DMCHandler.do_GET()` chỉ phục vụ `/health` và `/gm`, trong khi legacy client gọi `ChatGet` bằng **HTTP GET**, không phải POST encrypted form. Vì vậy route có trong `ROUTES` nhưng vẫn bị 404.

### 6.2 Lower-case `errorCode` dùng convention ngược uppercase `ErrorCode`
Runtime cũ của `LayNhanVat` rất quan trọng: khi DTO lower-case `errorCode` không được map (default enum = 0), client đã đi vào success callback rồi crash ở `BigNhanVatAvatar.SetByName` do `errorMsg/code_name` rỗng.

Server 0.10 lại trả:

```text
errorCode = 1
errorMsg = valid NV_ code
```

Kết quả runtime mới: **Mở tướng không còn crash nhưng bấm Thu nhận không hiện kết quả gì**. Đây là bằng chứng mạnh rằng lower-case family dùng:

```text
errorCode = 0  => success
errorCode != 0 => error
```

trong khi uppercase family đã confirmed:

```text
ErrorCode = 1 => success
ErrorCode = 0 => error
```

### 6.3 Generic fallback 0.10 cũng có bug
0.10 trả đồng thời:

```text
ErrorCode = 0
errorCode = 0
```

cho endpoint chưa reverse. Điều này là failure với uppercase convention nhưng **success với lower-case convention**, có thể vẫn đẩy client vào success callback thiếu DTO.

## 7. Server 0.11 — FIXED, RUNTIME RETEST PENDING
Commits:

```text
f498f51f  Fix GET transport and lowercase error semantics
4491654a  Test GET transport and lowercase error semantics
```

Các fix:

1. `do_GET()` giờ route cả 277 endpoint client, không chỉ `/health`/`/gm`.
2. GET route có `data=` thì decrypt như POST; GET không body/query vẫn gọi handler với `{}`.
3. `ChatGet` GET sẽ trả AES encrypted response thay vì 404.
4. Lower-case success DTO đổi sang `errorCode=0` cho `LayNhanVat`, `ChatGet`, `GetSystemHighLight`, `GetInfoLienMinh`, `GetVanTieuInfo`, `NguNhacGetInfo`, `FindLienMinh`, `GetThanhVienLienMinh` và nested reward lower-case.
5. `CreateLienMinh` controlled failure đổi thành `errorCode=1`.
6. Generic static unsupported trả:

```text
ErrorCode = 0
errorCode = 1
```

=> failure ở cả hai error-code conventions.
7. Server version nâng lên `DMCOffline/0.11`.
8. Test mới `server/test_runtime_transport.py` kiểm lower-case semantics + GET `/ChatGet` trả HTTP 200 encrypted.

## 8. Runtime lỗi còn lại từ log 14:01
### Kỳ Ngộ
Vẫn **CONFIRMED RUNTIME**:

```text
NullReferenceException
KyNgoForm.CreateDocCoPage
KyNgoForm.CreateNormalPage
KyNgoForm.CreateUI
KyNgoForm.SyncWithNetworkData
```

Đây là data/DTO issue riêng, không phải endpoint-name.

### Unsupported endpoints
Trong `LuyenCongForm` có 2 lần client hiển thị:

```text
Offline backend: endpoint recognised but DTO/gameplay is not reconstructed yet
```

Tên endpoint cụ thể cần lấy từ console server `STATIC-KNOWN UNSUPPORTED ...`; logcat chỉ có message, không có URL.

### Cửa hàng / Lễ bao
Ảnh runtime cho thấy popup `Mua lễ bao thành công` nhưng danh sách phần thưởng trống. Handler `BuyLeBao` hiện vẫn dùng generic `GetUserInfo` response, nên feature này **chưa đúng DTO/semantics** dù không crash.

## 9. Giang Hồ — PARTIAL
Minimal BattleReplay chạy runtime nhưng nội dung chưa phải game gốc. Đã persist Bạc + account EXP + hero EXP. NPC fixture thay đổi theo ải nhưng roster/item/combat script/reward gốc chưa map từ config.

Exact endpoint:

```text
/DanhNhanhGiangHo
/ResetTurnNhiemVuGH
```

`DanhNhanhGiangHo` đã có exact root DTO static; runtime retest vẫn pending.

## 10. Việc cần làm NGAY
User cần pull server 0.11, chạy tests, restart server; **không cần rebuild APK**.

```bat
cd /d "F:\Downloads\img\đạiminhchủ\DaiMinhChu-Offline"
git pull
cd server
python -m unittest -v
set DMC_BASE_URL=http://192.168.1.14:8000
python app.py
```

`/health` phải báo `DMCOffline/0.11`.

Runtime retest ưu tiên:

1. Mở tướng — bấm Thu nhận; kỳ vọng popup/tướng xuất hiện vì `errorCode=0`.
2. Luyện Công — xác nhận `ChatGet` không còn FileNotFound.
3. Gửi console server quanh các dòng `STATIC-KNOWN UNSUPPORTED` để biết chính xác 2 endpoint còn thiếu DTO trong Luyện Công.
4. Test BuyLeBao; phần thưởng hiện vẫn pending exact DTO.
5. Sau đó Giang Hồ / Đánh nhanh 10 lần và Kỳ Ngộ.

## 11. APK workspace / GM
- `tools/apk_workspace.py`: unpack/scan/repack raw APK; Unity serialized assets vẫn cần AssetRipper/UABE/UnityPy cho texture/audio/animation/effect/prefab.
- GM: `http://127.0.0.1:8000/gm`.

## 12. Quy tắc dự án
- Phân biệt `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore/credential.
- Không gọi stub là feature hoàn chỉnh.
- Không đoán schema rồi coi như confirmed.
- Ưu tiên static reverse DTO từ Assembly trước khi bắt user test lại.
- **Sau mỗi milestone phải cập nhật HANDOFF.md.**
