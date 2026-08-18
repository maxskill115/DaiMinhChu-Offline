# GM Tool local

GM Tool được tích hợp thẳng vào compatibility server, không cần cài package Python mới.

Chạy server:

```bat
cd server
python app.py
```

Mở trên **chính máy PC chạy server**:

```text
http://127.0.0.1:8000/gm
```

GM route bị giới hạn localhost; LDPlayer/LAN vẫn dùng game API bình thường nhưng không được gọi GM API.

## Các phần đã có

### Account / tài nguyên

Chỉnh trực tiếp:

- `DisplayName`
- `Level`
- `Exp`, `ExpMax`
- `Bac`
- `Vang` — hiện dùng làm trường vàng/KNB theo account DTO đang có
- `Vip`

### Thể lực / lượt

Chỉnh:

- `LuotNV`, `LuotNVMax`
- `LuotTD`, `LuotTDMax`
- `LatTheBai`

### Nhân vật

- đặt starter chính: Phong Thanh Dương / Lệnh Hồ Xung / Sở Lưu Hương;
- chỉnh level/exp nhân vật chính;
- thêm record nhân vật raw JSON để test các hero code/schema đang reverse.

### Đồ / võ công / hệ thống

GM lưu được các user-info group mà client runtime đã yêu cầu:

```text
TrangBi
VoCong
Orb
VatPhamTieuThu
TanChuong
HonNhanVat
Mail
Banbe
DanhHieu
DanhSon
ServerInfo
LienMinh
KimCham
MoiRuou
LongChau
AmKhi
```

Có 2 cách:

1. **Ghi đè nguyên group bằng JSON** — phù hợp khi đã reverse đúng DTO.
2. **Add item nhanh** — append một record JSON vào group list.

Để không làm hỏng runtime đang chạy, các group còn ở giá trị mặc định rỗng **không tự động được nhét vào `/GetUserInfo`**. Chỉ group đã chỉnh khác mặc định mới được trả về client.

### Raw save editor

Có thể xem/sửa toàn bộ JSON save. Đây là chế độ mạnh nhất để test field mới trước khi viết UI riêng.

### Tạo/reset account test

Nút `Tạo/reset account local` tạo lại active save sạch với tên mới. Server hiện vẫn dùng **một active local account**; đây là test account, chưa phải hệ thống multi-account/login database hoàn chỉnh.

## Trạng thái schema

GM framework đã bao phủ các nhóm dữ liệu chính, nhưng không được coi mọi item DTO đã reverse hoàn chỉnh. Ví dụ record TrangBi/VoCong/KimCham/LongChau vẫn cần đối chiếu `Assembly-CSharp.dll` + runtime request/response trước khi có form chuyên biệt đầy đủ field.

Vì vậy UI có raw JSON editor để không chặn quá trình test: khi reverse thêm field/schema, có thể dùng ngay mà không phải chờ sửa GM UI.

## Save

GM sửa trực tiếp:

```text
server/local_data/save.json
```

Mọi thay đổi được persist ngay. Khi test game, nên thoát/re-enter form hoặc gọi lại `/GetUserInfo` để client refresh dữ liệu.
