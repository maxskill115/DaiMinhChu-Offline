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
User chạy `python -m unittest -v` và có **5 failures**, nhưng cả 5 đều là **test cũ còn kỳ vọng convention 0.10**, không phải app handler hỏng:

```text
test_known_runtime_read_routes_have_specific_handlers
test_create_lien_minh_is_controlled_failure_not_fake_success
test_known_read_routes_return_success
test_lay_nhan_vat_exact_response_fields_and_adds_hero
test_system_highlight_exact_dto_shape
```

Trong cùng run, regression test mới đã pass:

```text
test_chat_get_legacy_http_get_returns_encrypted_success ... ok
test_generic_static_fallback_fails_both_error_conventions ... ok
test_lowercase_error_code_zero_is_success_for_recruit ... ok
test_lowercase_read_success_and_controlled_failure ... ok
```

=> implementation 0.11 phù hợp với convention mới; test suite cũ cần đồng bộ.

Đã sửa:

```text
a579d845  Sửa test audit theo quy ước errorCode lowercase
7ee622b4  Đồng bộ test server với errorCode lowercase
```

Các expectation mới:

- lowercase read/recruit success => `errorCode == 0`;
- `CreateLienMinh` controlled failure => `errorCode == 1`;
- uppercase read success => `ErrorCode == 1`;
- `GetTongKimInfo` không có error-code field.

User cần pull lại và chạy test lần nữa; mục tiêu là toàn bộ 33 tests `OK`.

## 7. Runtime lỗi còn lại từ log 14:01
### Kỳ Ngộ
Vẫn **CONFIRMED RUNTIME**:

```text
NullReferenceException
KyNgoForm.CreateDocCoPage
KyNgoForm.CreateNormalPage
KyNgoForm.CreateUI
KyNgoForm.SyncWithNetworkData
```

### Luyện Công
Logcat cũ có `/ChatGet` 404; 0.11 đã fix transport nhưng runtime retest pending.
Ngoài ra có 2 lần client hiển thị `Offline backend: endpoint recognised but DTO/gameplay is not reconstructed yet`; cần console server để lấy exact endpoint names.

### Mở tướng
0.10: không crash nhưng bấm Thu nhận không hiện gì. 0.11 đổi `LayNhanVat.errorCode` thành 0 success; runtime retest pending.

### Cửa hàng / Lễ bao
Ảnh runtime cho thấy popup `Mua lễ bao thành công` nhưng reward trống. `BuyLeBao` vẫn chưa reverse exact DTO/semantics.

## 8. Giang Hồ — PARTIAL
Minimal BattleReplay chạy runtime nhưng chưa phải nội dung gốc. Đã persist Bạc + account EXP + hero EXP. NPC fixture thay đổi theo ải, nhưng roster/item/combat script/reward gốc chưa map từ config.

Exact endpoints:

```text
/DanhNhanhGiangHo
/ResetTurnNhiemVuGH
```

`DanhNhanhGiangHo` đã có exact root DTO static; runtime retest pending.

## 9. Việc user cần làm tiếp

```bat
cd /d "F:\Downloads\img\đạiminhchủ\DaiMinhChu-Offline"
git pull
cd server
python -m unittest -v
```

Nếu toàn bộ 33 tests `OK`:

```bat
set DMC_BASE_URL=http://192.168.1.14:8000
python app.py
```

`/health` phải báo `DMCOffline/0.11`.

Sau đó runtime retest:

1. Mở tướng / Thu nhận.
2. Luyện Công — xác nhận `ChatGet` không còn FileNotFound.
3. Lấy console server `STATIC-KNOWN UNSUPPORTED` để xác định exact endpoint còn thiếu DTO.
4. Giang Hồ + Đánh nhanh 10 lần.
5. BuyLeBao.
6. Kỳ Ngộ.

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
