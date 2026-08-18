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

User đã xác nhận đổi được ít nhất:

```text
VIP = 8
Vàng/KNB = 10000
```

=> GM -> save -> GetUserInfo -> client hoạt động thật.

## 4. Giang Hồ — CHỈ PARTIAL RUNTIME, KHÔNG ĐƯỢC GỌI LÀ HOÀN CHỈNH

User đã xác nhận 2026-08-18:

- vào được Giang Hồ và chạy được BattleForm;
- **mọi ải hiện chưa đúng nội dung gốc**;
- trước bản fix mới, mọi ải đều dùng cùng một NPC fixture, HP hiển thị sai/thấp, chỉ có đúng một NPC;
- phần thưởng chưa đầy đủ;
- EXP/Bạc hiển thị sau trận nhưng EXP nhân vật/Bạc state không cập nhật đúng như mong đợi;
- chức năng đánh nhanh 10 lần chưa hoạt động.

=> trạng thái đúng là:

```text
TRANSPORT + MINIMAL BATTLE REPLAY = CONFIRMED RUNTIME
GIANG HO FEATURE = PARTIAL / PROTOTYPE ONLY
```

Không được gọi Giang Hồ là feature duy nhất “hoàn chỉnh”.

### Fix server mới đã commit

`server/state.py`:

- thêm `apply_giangho_reward()`;
- persist Bạc;
- persist account EXP (`ExpMonPhai` prototype mapping);
- persist main hero EXP (`ExpNhanVat`);
- chưa invent level-up curve.

`server/app.py` 0.8:

- NPC fixture thay đổi theo chapter/mission thay vì luôn cùng một code;
- HP NPC lấy từ stat của starter embedded code đã biết, không hard-code `100`;
- reward Bạc/EXP scale nhẹ theo stage;
- `UpdateUserInfo` trả snapshot sau khi reward đã persist.

**Quan trọng:** roster NPC thật, item reward thật, nhiều NPC theo từng ải và combat script thật vẫn phải reverse từ config/Assembly. Không được coi fixture hiện tại là nội dung chính xác của game.

### Đánh nhanh 10 lần

Chưa có endpoint/callback exact trong log mới. Cần capture riêng thao tác **Đánh nhanh 10 lần** hoặc static reverse method tương ứng trước khi implement. Không đoán route.

## 5. Runtime full-menu sweep vòng 1 — CONFIRMED

Các endpoint 404/FileNotFound bắt được:

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

Server 0.7 đã có compatibility stubs cho các route này.

## 6. Runtime full-menu sweep vòng 2 13:04–13:07 — CONFIRMED

Log mới cho thấy thêm 404:

```text
User.asmx/BuyVatPhamTieuThu
User.asmx/BuyLeBao
Battle.asmx/RefreshDiemLuanKiem
Battle.asmx/GetInfoBangChien
User.asmx/FindLienMinh
User.asmx/GetThanhVienLienMinh
```

`ChatGet` vẫn xuất hiện 404 trong log vòng 2; khi retest phải xác nhận server đang thực sự chạy code mới/restart đúng process.

Server 0.8 đã đăng ký thêm 6 route trên với DTO/stub tối thiểu để lộ blocker tiếp theo.

## 7. Mở tướng / LayNhanVat — exact runtime blocker

Runtime log vòng 2 vẫn cho:

```text
KeyNotFoundException
Dictionary<string,NhanVatCfg>.get_Item
BigNhanVatAvatar.SetByName(...)
NhanVatPopup.CreateOnGetNewNhanVat(...)
HTTP.WaitForLayNhanVat
```

=> response vẫn chưa đưa đúng code/string vào callback.

Server 0.8 thay `/LayNhanVat` để:

- trả valid embedded starter code ở cả `ErrorMsg/errorMsg` và các alias candidate;
- nếu code chưa sở hữu thì thêm hero vào local save;
- trả `UpdateUserInfo` snapshot sau thay đổi.

**RUNTIME RETEST PENDING.**

## 8. Các NullReference mới từ sweep vòng 2

### Luận Kiếm

```text
NullReferenceException
LuanKiemBang.SyncWithNetworkData
LuanKiemForm.SyncWithNetworkData
HTTP.WaitForLuanKiemBang
```

=> cần reverse DTO LuanKiemBang.

### Linh Thưởng

```text
NullReferenceException
LinhThuongQuay.OnDoiThuongNPC1 / NPC2
```

=> data reward/exchange chưa được populate.

### Bang Chiến

Có 404 `/Battle.asmx/GetInfoBangChien`, sau đó:

```text
NullReferenceException
BangChienForm.SetupGUI(HTTPGetInfoBangChienResponse)
```

Server 0.8 đã thêm minimal `GetInfoBangChien` response; runtime retest pending.

### Kỳ Ngộ

Vẫn là lỗi riêng:

```text
NullReferenceException
KyNgoForm.CreateDocCoPage
KyNgoForm.CreateNormalPage
KyNgoForm.CreateUI
KyNgoForm.SyncWithNetworkData
```

## 9. Commits mới sau sweep vòng 2 / Giang Hồ correction

```text
b9b29f23  Persist EXP và phần thưởng Giang Hồ
86bfcc19  Sửa Giang Hồ và bổ sung route runtime vòng 2
279ceb19  Test reward Giang Hồ và route runtime vòng 2
```

Server version: `DMCOffline/0.8`.

## 10. Việc cần làm NGAY

User pull + restart server:

```bat
cd /d "F:\Downloads\img\đạiminhchủ\DaiMinhChu-Offline"
git pull
cd server
python -m unittest -v
set DMC_BASE_URL=http://192.168.1.14:8000
python app.py
```

Không cần rebuild APK.

Retest ưu tiên:

1. Mở tướng 1 lần;
2. Giang Hồ đánh 2 ải khác nhau, kiểm tra NPC/HP/Bạc/EXP trước-sau;
3. bấm **Đánh nhanh 10 lần** một lần và capture log riêng;
4. sau đó full-menu sweep tiếp.

Cần server console + logcat cho bước 3 để lấy exact route/request/response shape của đánh nhanh 10 lần.

## 11. APK workspace

`tools/apk_workspace.py` đã có unpack/scan/repack raw APK; Unity serialized assets vẫn cần AssetRipper/UABE/UnityPy khi muốn sửa texture/audio/animation/effect/prefab.

## 12. Quy tắc dự án

- Phân biệt rõ: `CONFIRMED STATIC`, `SERVER TESTED`, `CONFIRMED RUNTIME`, `HYPOTHESIS`.
- Không commit APK/full asset dump/keystore/credential.
- Không gọi stub là feature hoàn chỉnh.
- Không đoán schema/route rồi coi như confirmed.
- Full-menu sweep dùng để discover endpoint; sau đó sửa DTO từng feature.
- **Sau mỗi milestone phải cập nhật HANDOFF.md.**
