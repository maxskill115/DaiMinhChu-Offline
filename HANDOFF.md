# HANDOFF — DaiMinhChu-Offline

> **ĐỌC FILE NÀY TRƯỚC KHI TIẾP TỤC Ở CHAT MỚI.** Đây là nguồn trạng thái chính của dự án. Sau mỗi mốc kỹ thuật quan trọng phải cập nhật lại HANDOFF.

**Last updated:** 2026-08-18 (UTC+7)

## 1. Mục tiêu
Phục dựng **Đại Minh Chủ Việt Nam 8.0.2** chạy local/offline, giữ client/UI/assets gốc càng nhiều càng tốt. Hướng chính: clean-room local compatibility backend + client patch tối thiểu.

## 2. Client/runtime nền tảng
APK 8.0.2 Unity 4.x/Mono/ARMv7. Signed v2 đã patch direct login + no-op `SohaSDKManager.SetUserInfo`, signature v1/v2/v3 OK.

**CONFIRMED RUNTIME trên LDPlayer 32-bit:** Login -> CheckUser -> GetUserInfo -> starter -> Home. Nhiều form/menu mở được, nhưng gameplay/data backend còn thiếu.

## 3. GM TOOL — CONFIRMED RUNTIME
`http://127.0.0.1:8000/gm`

User đã xác nhận đổi được ít nhất VIP=8 và Vàng/KNB=10000. GM -> save -> GetUserInfo -> client hoạt động thật.

## 4. Giang Hồ — PARTIAL, KHÔNG HOÀN CHỈNH
Transport + minimal BattleReplay đã chạy runtime, nhưng roster NPC, số lượng địch, reward/item, combat script và level curve chưa phải dữ liệu gốc.

Server đã persist Bạc + account EXP + main hero EXP và thay đổi NPC fixture theo ải. **Không gọi đây là nội dung Giang Hồ hoàn chỉnh.**

### Static correction mới
Đã đối soát trực tiếp `Assembly-CSharp.dll` của APK gốc. Exact endpoint trong client là:

```text
/DanhNhanhGiangHo
/ResetTurnNhiemVuGH
```

Không dùng tên đoán `ResetTurnNhiemVuGiangHo`.

Server 0.9 đã có explicit handler cho `DanhNhanhGiangHo`: mặc định 10 lượt, persist progress + Bạc + account EXP + hero EXP, trả aggregate/per-run reward aliases. `ResetTurnNhiemVuGH` cũng đã register exact name.

## 5. FULL STATIC ENDPOINT AUDIT — MỐC QUAN TRỌNG
Từ APK gốc đã extract toàn bộ UTF-16 endpoint literals dạng `/PascalCase` trong `Assembly-CSharp.dll`.

**CONFIRMED STATIC:** tìm được **277 endpoint names**.

Repo mới có:

```text
server/static_endpoints.py
```

chứa toàn bộ 277 endpoint exact của client.

Server 0.9 behavior:
- route đã reverse/implement -> handler cụ thể;
- route chưa reverse DTO nhưng nằm trong 277 endpoint tĩnh -> **không trả 404 nữa**, trả encrypted compatibility envelope và log `STATIC-COMPAT STUB`;
- chỉ route không tồn tại trong inventory tĩnh mới 404.

=> giảm mạnh vòng test chỉ để discover endpoint. Từ nay runtime test chủ yếu dùng để xác định **DTO/semantics**, không còn phải bắt từng endpoint name thủ công.

## 6. Tool protocol audit
Mới thêm:

```text
tools/protocol_audit.py
```

Chạy trực tiếp APK hoặc `Assembly-CSharp.dll`:

```bat
python tools\protocol_audit.py daiminhchu.apk
```

Tool extract endpoint tĩnh và so với `server/static_endpoints.py`; exit code 1 nếu client có endpoint chưa được allowlist.

Mục tiêu hiện tại với APK 8.0.2: `Client endpoints = 277`, `Missing from server allowlist = 0`.

## 7. Runtime sweep đã biết
404 trước đây gồm GetInfoLienMinh/CreateLienMinh/ChatGet/GetVanTieuInfo/NguNhacGetInfo/GetAnhHungBang/GetDongNhanInfo/GetHuyetChienInfo/GetNienThuInfo/GetTongKimInfo và vòng 2 BuyVatPhamTieuThu/BuyLeBao/RefreshDiemLuanKiem/GetInfoBangChien/FindLienMinh/GetThanhVienLienMinh.

Tất cả tên này nay đều thuộc static coverage; không còn lý do để 404 nếu process đang chạy server 0.9.

Nếu runtime vẫn thấy `FileNotFoundException` cho một endpoint thuộc 277 list => gần như chắc chắn máy đang chạy process/server code cũ hoặc chưa restart.

## 8. Blocker DTO/runtime còn thật sự tồn tại
### Mở tướng
Runtime cũ: `WaitForLayNhanVat -> NhanVatPopup.CreateOnGetNewNhanVat -> BigNhanVatAvatar.SetByName -> KeyNotFoundException`.
Server đã trả valid starter code + aliases và persist hero, nhưng cần runtime retest trên server mới để xác nhận exact DTO mapping.

### Kỳ Ngộ
`KyNgoForm.CreateDocCoPage -> NullReferenceException`. Đây là DTO/data issue, không phải endpoint-name issue.

### Luận Kiếm
`LuanKiemBang.SyncWithNetworkData -> NullReferenceException`. Cần reverse DTO.

### Bang Chiến
`BangChienForm.SetupGUI(HTTPGetInfoBangChienResponse) -> NullReferenceException` sau endpoint call. Cần exact DTO.

### Linh Thưởng
`LinhThuongQuay.OnDoiThuongNPC1/NPC2 -> NullReferenceException`. Cần populate data/reward tables.

## 9. Server version / commits mới
Server hiện: `DMCOffline/0.9`.

Các mốc mới:

```text
b960c1ee  Thêm danh sách 277 endpoint tĩnh từ client 8.0.2
f9b20df3  Đối soát endpoint tĩnh và loại 404 toàn client
2e380346  Thêm tool đối soát endpoint trực tiếp từ APK
415b3105  Test độ phủ endpoint tĩnh và đánh nhanh Giang Hồ
```

## 10. Bước tiếp theo
User chỉ cần pull một lần, chạy tests + protocol audit, restart server 0.9. Không cần rebuild APK.

```bat
cd /d "F:\Downloads\img\đạiminhchủ\DaiMinhChu-Offline"
git pull
python tools\protocol_audit.py daiminhchu.apk
cd server
python -m unittest -v
set DMC_BASE_URL=http://192.168.1.14:8000
python app.py
```

`/health` phải báo server 0.9, `static_endpoint_count=277`.

Sau mốc này không cần full-menu sweep chỉ để tìm tên endpoint nữa. Tập trung reverse exact DTO cho các feature NullReference và map dữ liệu gốc GiangHo/config.

## 11. APK workspace
`tools/apk_workspace.py` có unpack/scan/repack raw APK; Unity serialized assets vẫn cần AssetRipper/UABE/UnityPy khi sửa texture/audio/animation/effect/prefab.

## 12. Quy tắc dự án
- Phân biệt rõ: `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore/credential.
- Không gọi stub là feature hoàn chỉnh.
- Không đoán schema rồi coi như confirmed.
- **Sau mỗi milestone phải cập nhật HANDOFF.md.**
