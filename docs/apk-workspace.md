# APK Workspace Tool

Tool: `tools/apk_workspace.py`

Mục tiêu: bung toàn bộ APK thành workspace có thể sửa file, sau đó đóng lại thành APK **unsigned** để zipalign + sign lại.

## 1. Unpack toàn bộ APK

```bat
python tools\apk_workspace.py unpack daiminhchu.apk apk_workspace --clean
```

Tool sẽ:

- giải nén toàn bộ entry trong APK;
- giữ `assets/`, `res/`, `lib/`, `META-INF/`, `classes*.dex`, `AndroidManifest.xml`...;
- tạo `.dmc_apk_manifest.json` lưu compression/timestamp/metadata gốc;
- phân loại sơ bộ image/audio/video/config/Unity data/native lib/Managed DLL;
- chặn zip-slip/path traversal.

Quét nhanh workspace:

```bat
python tools\apk_workspace.py scan apk_workspace
```

## 2. Những gì chỉnh trực tiếp được

Các file ảnh/âm thanh/config vốn đã là file rời có thể sửa/thay trực tiếp trong workspace.

Đại Minh Chủ là Unity 4.x nên rất nhiều texture, animation, prefab, material, effect và audio có thể nằm trong **Unity serialized assets / bundles** dưới `assets/bin/Data/...`. Các file này vẫn là binary sau unzip. Python/ZIP không thể tự biến chúng thành PNG/FBX/WAV riêng lẻ.

Để chỉnh sâu Unity asset, dùng AssetRipper/UABE/UnityPy bên ngoài để export/import object, sau đó đặt file binary đã sửa trở lại đúng vị trí trong workspace. Tool này cố tình không đóng gói asset proprietary vào repo.

`Assembly-CSharp.dll` nằm tại:

```text
assets/bin/Data/Managed/Assembly-CSharp.dll
```

## 3. Android resources decoded bằng apktool (tuỳ chọn)

Nếu đã cài `apktool` và có trong PATH:

```bat
python tools\apk_workspace.py apktool-decode daiminhchu.apk apktool_out
```

Sau khi sửa resource/manifest decoded:

```bat
python tools\apk_workspace.py apktool-build apktool_out DMC_apktool_unsigned.apk
```

## 4. Repack workspace raw

```bat
python tools\apk_workspace.py repack apk_workspace DMC_mod_unsigned.apk
```

Tool giữ compression metadata cũ khi có thể và loại chữ ký cũ trong `META-INF/*.RSA/*.SF/*.MF` vì chữ ký đó chắc chắn không còn hợp lệ sau chỉnh sửa.

## 5. Zipalign + ký

```bat
"%LOCALAPPDATA%\Android\Sdk\build-tools\35.0.0\zipalign.exe" -f -p 4 DMC_mod_unsigned.apk DMC_mod_aligned.apk
```

Trên máy hiện tại `apksigner.bat` từng không tạo output, nên dùng trực tiếp jar:

```bat
java -jar "%LOCALAPPDATA%\Android\Sdk\build-tools\35.0.0\lib\apksigner.jar" sign --verbose --ks dmc-test.jks --ks-key-alias dmc --out DMC_mod_signed.apk DMC_mod_aligned.apk
```

Verify:

```bat
java -jar "%LOCALAPPDATA%\Android\Sdk\build-tools\35.0.0\lib\apksigner.jar" verify --verbose DMC_mod_signed.apk
```

## Lưu ý

- Workspace/APK output đều bị `.gitignore`, không commit game asset lên repo.
- Với Unity asset, nên thay đúng object/file và giữ format tương thích Unity 4.x.
- Nếu thay file làm game crash, so sánh kích thước/hash và test từng nhóm nhỏ để khoanh vùng.
