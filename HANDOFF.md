# HANDOFF — DaiMinhChu-Offline

> **ĐỌC FILE NÀY TRƯỚC KHI TIẾP TỤC Ở CHAT MỚI.** Đây là nguồn trạng thái chính của dự án. Sau mỗi mốc kỹ thuật quan trọng phải cập nhật lại HANDOFF.

**Last updated:** 2026-08-18 (UTC+7)

## 1. Mục tiêu

Phục dựng **Đại Minh Chủ Việt Nam 8.0.2** chạy local/offline, giữ client/UI/assets gốc càng nhiều càng tốt. Hướng chính: clean-room local compatibility backend + client patch tối thiểu.

## 2. Client/runtime nền tảng

APK 8.0.2 Unity 4.x/Mono/ARMv7. Signed v2 đã patch direct login + no-op `SohaSDKManager.SetUserInfo`, signature v1/v2/v3 OK.

**CONFIRMED RUNTIME trên LDPlayer 32-bit:** Login -> CheckUser -> GetUserInfo -> starter -> Home -> GiangHo -> BattleForm -> BattleReplay chạy. Giang Hồ hiện là gameplay duy nhất chạy được thật.

## 3. GM TOOL — CONFIRMED RUNTIME

`http://127.0.0.1:8000/gm`

User đã xác nhận đổi được ít nhất:

```text
VIP = 8
Vàng/KNB = 10000
```

=> GM -> save -> GetUserInfo -> client hoạt động thật.

## 4. Runtime full-menu sweep 12:55–12:56 — CONFIRMED

User đã click gần như toàn bộ chức năng/menu trong một lần logcat. Kết luận: **ngoài Giang Hồ, các chức năng khác hiện đều lỗi/chưa hoàn chỉnh**.

Các endpoint 404/FileNotFound được bắt chính xác:

```text
User.asmx/GetInfoLienMinh
User.asmx/CreateLienMinh
User.asmx/ChatGet
User.asmx/GetVanTieuInfo
User.asmx/NguNhacGetInfo
Battle.asmx/GetAnhHungBang
Battle.asmx/GetDongNhanInfo
Battle.asmx/GetHuyetChienInfo
Battle.asmx/GetNienThuInfo
Battle.asmx/GetTongKimInfo
```

Luyện Công vào `LuyenCongForm` rồi đồng thời gọi `GetDongNhanInfo`, `GetHuyetChienInfo`, `GetNienThuInfo`, `ChatGet`.

Liên Minh/Home gọi `GetInfoLienMinh`; thao tác tạo liên minh gọi `CreateLienMinh`; một nhánh xếp hạng gọi `GetAnhHungBang`.

Vận Tiêu, Ngũ Nhạc, Tống Kim lần lượt gọi các endpoint tên tương ứng ở trên.

## 5. Mở tướng / LayNhanVat — exact blocker mới

`/LayNhanVat` không còn 404. Client đã chạy tới `HTTP.WaitForLayNhanVat`, nhưng lỗi:

```text
KeyNotFoundException: The given key was not present in the dictionary
at Dictionary<string,NhanVatCfg>.get_Item
at BigNhanVatAvatar.SetByName(...)
at NhanVatPopup.CreateOnGetNewNhanVat(code_name, tan_hon_count, listEventHon, GetIdx)
at HTTP.WaitForLayNhanVat
```

=> blocker chính xác: callback recruit nhận `code_name` không map được tới embedded `NhanVatCfg`. Stub cũ trả snapshot sai semantics.

Server 0.7 đã sửa `/LayNhanVat` theo hướng compatibility: luôn trả một code starter chắc chắn có trong embedded config (`NV_PhongThanhDuong`) và thêm candidate aliases `CodeName/code_name/NhanVatCode`, `TanHonCount`, `ListEventHon`, `GetIdx` để runtime xác định field DTO thật. **RUNTIME RETEST PENDING; chưa gọi recruit hoàn chỉnh.**

## 6. Kỳ Ngộ — exact blocker mới

Không phải 404. Khi mở `KyNgoForm`, client ném:

```text
NullReferenceException
at KyNgoForm.CreateDocCoPage
at KyNgoForm.CreateNormalPage
at KyNgoForm.CreateUI
at KyNgoForm.SyncWithNetworkData
at KyNgoForm.OnActive
```

=> cần reverse dữ liệu/network group mà `CreateDocCoPage` dereference; không được coi là endpoint 404.

## 7. Server 0.7 — compatibility routes implemented, runtime retest pending

Commit mới thêm route cho toàn bộ endpoint 404 bắt được trong sweep:

```text
10fbe114  Thêm compatibility route cho toàn bộ menu runtime đã bắt được
833f8ecb  Test các route menu runtime mới
```

Server version: `DMCOffline/0.7`.

Các route mới hiện là **compatibility stubs**: mục tiêu trước mắt loại 404/FileNotFound để lộ ra DTO/NullReference tiếp theo. Chưa gọi các feature này hoàn chỉnh.

Route mới:

```text
getinfolienminh
createlienminh
chatget
getanhhungbang
getdongnhaninfo
gethuyetchieninfo
getnienthuinfo
getvantieuinfo
ngunhacgetinfo
gettongkiminfo
```

Tests đã cập nhật để kiểm tra registration + success envelope và `/LayNhanVat` có valid embedded code.

## 8. Việc cần làm NGAY

User pull + test + restart server:

```bat
cd /d "F:\Downloads\img\đạiminhchủ\DaiMinhChu-Offline"
git pull
cd server
python -m unittest -v
set DMC_BASE_URL=http://192.168.1.14:8000
python app.py
```

Không cần rebuild APK.

Sau đó runtime retest **full menu một lượt nữa**. Mục tiêu vòng này:

1. xác nhận 10 endpoint trên không còn `FileNotFoundException`;
2. test Mở tướng xem `KeyNotFoundException` có hết không;
3. thu exact `NullReferenceException` / LitJson / field missing mới cho từng feature;
4. Kỳ Ngộ xử lý riêng theo `CreateDocCoPage`.

Nếu một stub trả HTTP 200 nhưng client lỗi DTO, reverse đúng DTO đó rồi thay stub bằng schema tối thiểu đúng; không đoán feature logic đầy đủ.

## 9. APK workspace

`tools/apk_workspace.py` đã có unpack/scan/repack raw APK; Unity serialized assets vẫn cần AssetRipper/UABE/UnityPy khi muốn sửa texture/audio/animation/effect/prefab.

## 10. Quy tắc dự án

- Phân biệt rõ: `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore/credential.
- Không gọi stub là feature hoàn chỉnh.
- Không đoán schema rồi coi như confirmed.
- Full-menu sweep dùng để discover endpoint; sau đó sửa DTO từng feature.
- **Sau mỗi milestone phải cập nhật HANDOFF.md.**
