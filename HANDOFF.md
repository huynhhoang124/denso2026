# HANDOFF – Demo D3 Chain Impact Propagation

File này để chuyển việc sang phiên Claude Code mới khi context đầy (~500k token).
Phiên mới: đọc file này + `IDEA.md` (mục 2–6) rồi làm tiếp từ mục "Tiến độ".

## Prompt mở đầu cho phiên mới

> Tiếp tục làm demo D3 trong repo `huynhhoang124/denso2026`, nhánh `claude/stoic-maxwell-8m9yp6` (PR draft https://github.com/huynhhoang124/denso2026/pull/1).
> Đọc `HANDOFF.md` (yêu cầu, quyết định thiết kế, tiến độ, việc còn lại) và `IDEA.md` mục 2–6 + mục 10.
> Cài thư viện: `pip install pandas networkx streamlit plotly pyyaml pytest`; chạy test bằng `python3 -m pytest -q demo`.
> Gọi `subscribe_pr_activity` cho PR #1. Làm các việc trong mục "Việc còn lại" của HANDOFF.md, commit + push.
> Giữ đúng các quyết định thiết kế; không sửa code để khớp số – chỗ nào lệch thì báo lại.
> Khi context chạm ~500k token: dừng, cập nhật HANDOFF.md, commit + push, đưa lại prompt này.

## Yêu cầu gốc của người dùng (tóm tắt trung thành)

- App web local, Python 3.10+, CHỈ dùng: pandas, networkx, streamlit, plotly, pyyaml, pytest. Không DB, không Neo4j, không LLM.
- Code trong `demo/` (người dùng ghi `C:\denso2026\demo\` – trên máy họ là repo clone ở C:\denso2026).
- Ít file: `config.yaml`, `engine.py`, `scenarios.py`, `app.py`, `tests/`, `README.md` (cách chạy + hướng mở rộng: dữ liệu thật, Weibull, LLM, Neo4j).
- config.yaml = bảng "Dây chuyền giả định" mục 6 (D1,D2 / B1 / M1–M3 / B2 / Lắp ráp 6 người / kho TP; L-A→X, L-B→Y; đơn D-101, D-102, D-201).
- Lớp Logic = đồ thị networkx (máy, công đoạn, đệm, linh kiện, đơn hàng…, cạnh = quan hệ phụ thuộc).
- Engine bước 1 phút, ca 08:00–16:00 + tăng ca. Sản lượng công đoạn = min(năng lực, đầu vào, chỗ trống đệm sau). Lan xuôi (đói hàng) + lan ngược (bị chặn). Quy tắc: trên chuẩn ≤ 6h/ca; tăng ca ≤ 4h/người/ngày; BOM; đổi mã 20 phút.
- Sự cố = mẫu chung {điểm, đại lượng (năng lực/nguồn cung/nhu cầu/thời gian), thay đổi %, bắt đầu, thời lượng}. Tác động = mô phỏng có sự cố − mô phỏng kế hoạch.
- Hành động = nhiễu tích cực, chạy lại engine. Thang: chia tải (theo tỷ lệ công suất tối đa) → tăng tốc → đổi thứ tự → tăng ca → chuyển line → báo khách. Tăng ca là khoảng theo thời gian sửa 3/4/5/6 giờ.
- Mức Xanh/Vàng/Đỏ; thứ tự sửa máy theo thời gian chịu đựng đệm vs thời gian sửa; truy vết ngược trên bảng phả hệ tự tạo (TH6).
- tests/test_scenarios.py – mỗi assert = 1 con số tài liệu:
  - Ví dụ gốc: không làm gì 800; chia tải 884; tăng ca ~38'; sửa 3/4/5/6h → 930/884/838/792.
  - TH1: M1=46, M2=44, Xanh; M3 hỏng hẳn 12:00 → 842.
  - TH2: sửa M2 trước 848, D1 trước 792 → chọn M2.
  - TH3: không làm gì mất 440; đổi thứ tự mất 80; ngưỡng lô 16:05.
  - TH4: đơn C xong 18:00 (A), 18:30 (B).
  - TH5: 760 và 880.
  - TH6: khoanh vùng 88; tăng ca ~42'.
  - Quy ước: sản lượng tính tại nút cổ chai, đệm phải trả về mức mục tiêu.
  - **Nếu mô phỏng ra khác: KHÔNG sửa code cho khớp; báo chỗ lệch + giải thích.** (Cách làm: đánh dấu `pytest.mark.xfail(strict=True, reason=...)` để suite xanh nhưng vẫn ghi lại chỗ lệch.)
- UI Streamlit 1 trang tiếng Việt: sidebar chọn 1 trong 8 kịch bản (ví dụ gốc + 7 TH) hoặc tự nhập sự cố; KPI (sản lượng/kế hoạch, thiếu, giờ tăng ca, mức cảnh báo có màu); Gantt (công đoạn dừng, đệm cạn/đầy); biểu đồ mức đệm; bảng so sánh phương án (cứu được, chi phí, xáo trộn); 3 tab Bảo trì / Kế hoạch / Giao hàng & Sales; sơ đồ dây chuyền tô đỏ điểm bị ảnh hưởng.
- Thứ tự: engine + test trước, pytest xanh, rồi UI. Cuối cùng chạy `streamlit run app.py`, kiểm tra trên trình duyệt (Playwright/Chromium có sẵn ở /opt/pw-browsers), báo kết quả test + chỗ lệch.
- Git: commit + push nhánh `claude/stoic-maxwell-8m9yp6`, tạo draft PR, subscribe PR.

## Quyết định thiết kế (đã chốt)

1. **Thước đo sản lượng M (sản lượng hiệu dụng)** = tổng sản lượng ra khỏi Lắp ráp − hàng bị giữ (chất lượng) + Σ_đệm min(0, mức đệm − mục tiêu).
   Đây là cách viết tổng quát của quy ước "tính tại nút cổ chai + đệm phải trả về mục tiêu": phần đệm bị rút không được tính là sản lượng.
   Kiểm tay: ví dụ gốc 884 ✓, TH3 520/880 ✓, TH5 640/760/880 ✓. Ngoài ra vẫn xuất sản lượng riêng từng công đoạn (vd. Gia công) để đối chiếu.
2. **Mức chính sách (policy)**: 0 = không làm gì (máy chuẩn); 1 = chia tải (mục tiêu công đoạn = nhịp kế hoạch 120, máy còn lại chia theo tỷ lệ công suất tối đa, chỉ khi cần > tổng chuẩn; cắt ở max, water-filling); 2 = tăng tốc (mục tiêu = max(nhịp kế hoạch, cần còn lại / thời gian ca còn lại)).
   Tài liệu dùng lẫn: mục 5 (884) là mức 2; TH1 (46/44) và TH2 (848/792, B1 còn 12/218) là mức 1. Test kiểm số ở đúng mức tài liệu dùng.
3. Máy bị giảm năng lực một phần (TH1 M3=30) chạy cố định, không được tăng tốc. Máy hỏng = 0.
4. Đếm giờ trên chuẩn: phút nào máy được lệnh > chuẩn VÀ công đoạn thực ra > tổng chuẩn các máy đang chạy. Giới hạn 360 phút/ca. Trong giờ tăng ca chỉ chạy chuẩn.
5. Mỗi công đoạn dừng khi sản lượng cộng dồn ≥ kế hoạch ngày (+ phần bị giữ) → không sản xuất thừa, đệm tự trở về mục tiêu khi xong.
6. Thứ tự tính trong 1 phút: từ cuối chuyền lên đầu (Lắp ráp lấy từ B2 trước, rồi Gia công đẩy vào chỗ trống).
7. Đổi thứ tự (TH3): khi hết linh kiện mã đang chạy → đổi sang mã khác có linh kiện (20'); khi linh kiện mã chính về → đổi lại (20'). Y được kéo sớm cho D-201.
8. Tăng ca: mô phỏng tiếp sau 16:00 ở tốc độ chuẩn (máy đang sửa vẫn dừng), tối đa 4h; giờ tăng ca = lúc M ≥ kế hoạch. **Không dùng kho TP để giảm giờ tăng ca** (kho TP cũng là đệm phải trả về mục tiêu) – nhưng kho TP được tính khi kiểm tra đơn hàng.
9. Kiểm tra đơn: D-101 (hôm nay 17:00) = kho X + X làm được đến min(17:00, 16:00+OT) − hàng giữ ≥ 500. Đơn ngày mai: phần còn thiếu / 120 sp/h + 20' mỗi lần đổi mã (bắt đầu bằng mã cuối hôm nay) + thời gian bù đệm thiếu ≤ 480'.
10. Mức cảnh báo: Xanh = mức 1 (chia tải) không tăng ca mà đơn vẫn đủ; Vàng = có phương án (tăng tốc/đổi thứ tự/tăng ca ≤4h/chuyển người) giữ được đơn; Đỏ = không phương án nào giữ được.
11. Chọn phương án: trong các phương án giữ được đơn, ít giờ tăng ca nhất → bậc thang thấp hơn → chi phí thấp hơn.
12. Nhu cầu gấp (TH4) = tăng kế hoạch ngày thêm 300, hạn 20:00; đơn C xong khi M ≥ 1260. Phương án A = mức 2 + tăng ca; B = mức 1 + tăng ca.
13. TH6: bảng phả hệ tự tạo (seed cố định): 08–09 thép S-76, 09–14 S-77 (600 sp); 10–12 M1, M2 chạy 38 (thay dao luân phiên), M3 chạy 44 (tối đa) → tổng vẫn 120. Lỗi ẩn: chỉ M3 lúc chạy tối đa. Truy vết: thuộc tính chung → 2 giả thuyết (cả lô S-77 ≈600; M3 10–12 = 88) → lấy mẫu S-77 trên M1/M2 → 0 lỗi → giữ 88. Tính xuôi: giữ 88 lúc 14:00 + M3 dừng 14:00–15:00.
14. TH7: tính riêng phần giao hàng (XE-A trễ +2h → đến 20:30, trễ 1,5h; ghép XE-GAN 40% chỗ = 200 sp; thuê xe ngoài; kiểm tra kho TP đầy).
15. Sự cố nguồn cung: −100% trong [t0, t0+T) = các lô về trong khung bị dời tới cuối khung.

## Chỗ lệch (ĐÃ xác nhận bằng mô phỏng – 5 test xfail strict)

Số khớp tài liệu: 800/884/38'/930-884-838-792/15-38-61-84'; TH1 46/44, thiếu 10, Xanh, 842, ~89'; TH2 848/792, B1 12/218,
D1 trước 104' (≈1h45 ✓); TH3 440/80, 480X+400Y, 11:20/12:05/12:55, ngưỡng 16:05; TH4 18:00/18:30 (+ tự phát hiện thiếu 260 L-A,
đặt trước 15:50 / 16:20); TH5 640/760 (OT 120')/880 (OT 40'), B không khả thi vì line 2, cửa sổ bảo trì 08–10;
TH6 88 sp, lô S-77 600, mẫu 0 lỗi, 846 sp; TH7 đến 20:30 trễ 90'.
Phát hiện thêm: TH6 giữ 88 sp làm tổng nhu cầu L-A 1048 > 1000 → engine đề xuất đặt gấp 48 L-A.

Ghi chú tính tay ban đầu (đã khớp mô phỏng):

- **TH2 – đảo kết luận**: theo quy ước "đệm phải trả về mục tiêu", sửa M2 trước làm B1 cạn còn 12 (thiếu 188 so với mục tiêu 200) → M ≈ 660 vs sửa D1 trước 792; tăng ca để hoàn thành kế hoạch + trả đệm: M2 trước ≈ 3h, D1 trước ≈ 1h44. Engine sẽ chọn D1. Lý do: dây chuyền cân bằng (mọi công đoạn chuẩn 120), D1 hỏng làm Dập hụt 50 sp/h, M2 hỏng làm Gia công hụt 28 sp/h; tài liệu chỉ nhìn sản lượng Gia công đến 16:00. Sản lượng Gia công 848/792 và B1 12/218 vẫn khớp tài liệu.
- **TH6**: tăng ca 57' (114 sp ÷ 120) thay vì 42' – tài liệu trừ kho TP 30 ở TH6 nhưng không trừ ở mục 5 (38'). Hai số không thể cùng đúng.
- **TH3**: ngày mai 450 X + 500 Y = 950 sp + 1 lần đổi mã 20' (40 sp) → 990 > 960, không "vừa một ca" → cần ~40' tăng ca hôm nay.
- **TH4**: kho L-A (400 + lô 600) = 1000 < 960 + 300 → engine tự phát hiện thiếu L-A (đúng như tài liệu dự báo); cần đặt gấp ~260 L-A trước ~15:51 (A) / ~16:20 (B). Test 18:00/18:30 chạy kèm hành động "đặt gấp L-A" do engine tự sinh.
- **TH7**: có phương án giữ đơn đúng hạn → theo định nghĩa mục 4.5 là Vàng, tài liệu ghi Đỏ.
- Mục 5: Gia công chạy 138 khung 14–16 > Lắp ráp max 130 (dư dồn vào B2) – không đổi M.

## Tiến độ

- [x] Cài thư viện (pip install pandas networkx streamlit plotly pyyaml pytest).
- [x] `demo/config.yaml`
- [x] `demo/engine.py` (đồ thị, mô phỏng, phương án, mức cảnh báo, TTS, thứ tự sửa, truy vết, giao hàng, thông điệp từng bộ phận)
- [x] `demo/scenarios.py` (8 kịch bản + bảng phả hệ TH6; `chay(ma)` -> (PhanTich, phần riêng))
- [x] `demo/tests/test_scenarios.py` → `python3 -m pytest -q demo`: 50 passed, 5 xfailed (5 chỗ lệch dưới đây)
  (lưu ý: lệnh `pytest` trần trong container trỏ Python hệ thống thiếu thư viện → dùng `python3 -m pytest`)
- [x] `demo/app.py`
- [x] `demo/README.md` (bảng khớp + 5 chỗ lệch)
- [x] Chạy streamlit + Playwright (node, /opt/node22/lib/node_modules/playwright): 8 kịch bản + tự nhập, 0 exception, 0 lỗi JS; ảnh `demo/screenshot_th3.png`
- [x] Cập nhật "Chỗ lệch" theo số mô phỏng thật
- Quyết định thêm: Xanh = chỉ chia tải/tăng tốc (bậc ≤ 2), không tăng ca/đổi thứ tự; đơn gấp mã khác mã đang chạy → sinh phương án đổi thứ tự.
- [x] Commit, push, draft PR https://github.com/huynhhoang124/denso2026/pull/1 (đã subscribe), báo cáo người dùng

## Cập nhật phiên 1 (cuối)

- [x] IDEA.md đã sửa theo 5 chỗ lệch (TH2 → sửa D1 trước, tăng ca M2 trước ≈ 3h; TH3 ngày mai 990 > 960 → tăng ca ~40' hoặc đổi thứ tự + tăng tốc;
  TH6 → ~57' (48' nếu tăng tốc) + đặt gấp 48 L-A; TH7 → Vàng; mục 4.7, 9.1, 10, bảng tổng hợp). Thêm ghi chú TH4 đặt gấp 260 L-A.
- Đã hủy lần tự kiểm tra PR (send_later) của phiên 1; phiên mới tự subscribe lại PR #1.

## Cập nhật phiên 2

- [x] 5 test xfail → test thường theo số mới IDEA.md (lý do giữ ở comment "Đã sửa trong IDEA.md"): TH2 chọn D1 trước,
  TH2 M2 trước tăng ca 180', TH3 đổi thứ tự 40' + "đổi thứ tự + tăng tốc" 0', TH6 57' (chia tải) / 48' (tăng tốc), TH7 Vàng
  (thêm vào `test_muc_canh_bao`). Thêm test TH2 sản lượng hiệu dụng 660/792. `python3 -m pytest -q demo` → **58 passed**.
  Không đổi engine; mọi số mô phỏng = số IDEA.md mới (TH2: 660/792, 180'/104'; TH3: 40'/0'; TH6: 57'/48').
- [x] `scenarios.py`: chuỗi `tai_lieu` của th2, th3, th4 (260 L-A), th6, th7 theo IDEA.md mới.
- [x] `README.md`: "Chỗ lệch (xfail)" → "Đã sửa trong IDEA.md sau khi mô phỏng"; kết quả test 58 passed.
- [x] Thêm `.gitignore`, bỏ `__pycache__` khỏi git.
- [x] Streamlit + Playwright: 8 kịch bản, 0 exception, 0 lỗi JS; chuỗi "Con số trong tài liệu" mới hiển thị đúng.
- [x] Cập nhật mô tả PR #1.

- [x] Người dùng đồng ý → `D3_Y_tuong_va_giai_phap.docx` đã sửa theo IDEA.md (cùng các thay đổi của commit d4f5f49:
  mục 4.7, TH2 bảng + kết luận, TH3, TH4, TH6, TH7 thêm dòng Mức Vàng, bảng tổng hợp, 9.1, 10). Sửa trực tiếp XML, giữ định dạng;
  mục lục cập nhật số trang theo độ dời (LibreOffice render: 15 → 16 trang). Kiểm tra: validate.py PASSED, mọi dòng mới của IDEA.md có trong docx.
  (Container cần `apt-get install libreoffice-writer` + `pip install defusedxml lxml` mới render/validate được.)

## Cập nhật phiên 2 (tiếp) – người dùng duyệt đề xuất "làm 3 rồi 1"

- [x] Việc 3: `.github/workflows/tests.yml` (pytest, Python 3.10 + 3.12) và `demo/run.bat` (Windows; CRLF qua `.gitattributes`).
- [x] Việc 1 – Diễn tập đầu ca (IDEA.md 7.1–7.2), chế độ thứ 3 ở thanh bên:
  - `engine.py`: `lech_sua`, `ban_do_rui_ro`, `muc_dem_toi_thieu`, `de_xuat_muc_dem`, `sinh_rui_ro`, `xac_suat_hoan_thanh`.
  - `config.yaml`: mỗi máy thêm `sua_gio`, `hong_trong_ca`; thêm `dung_ngan` (giả định demo). Không đổi số cũ.
  - `tests/test_dau_ca.py` (14 test; số tài liệu: 7.1 B2/M2 = 28 × 5 = 140, thêm 80). Tổng **72 passed**.
  - Kết quả (seed 7, 300 kịch bản): trong ca 42%, đăng ký 38', ≤4h 99,7%, D-101 100%. Ưu tiên bảo trì: M3 > LR-1 > M1 > D1 = D2 > M2.
  - Phát hiện (đã ghi README, CHƯA sửa quy ước): đệm B2 150 giữ Lắp ráp ra 960 khi M1 hỏng 5h (thay vì 878) nhưng
    giờ tăng ca không đổi (66') vì đệm phải trả về mục tiêu. Muốn đệm "có lợi" phải tính bù đệm bằng năng lực dư ca sau – cần người dùng quyết.
  - Giao diện: Playwright 0 exception. Lưu ý: Chromium headless trong container có locale `en-US@posix` không hợp lệ
    → `st.time_input` báo RangeError (cả chế độ Tự nhập cũ); dùng `newContext({locale: 'vi-VN'})` khi kiểm tra.

## Cập nhật phiên 2 (cuối)

- CI GitHub Actions lần đầu: xanh (3.10 + 3.12). PR #1 chưa có review.
- Người dùng: **KHÔNG đổi quy ước** "đệm phải trả về mục tiêu" (không tính bù đệm bằng năng lực dư ca sau). Chưa trả lời
  việc cập nhật IDEA.md/docx mục 7.1–7.2 bằng số mô phỏng → hỏi lại.
- Đang làm việc 2 – Đồng hồ quyết định (IDEA.md 7.3). ĐÃ XONG bước 1: `ChinhSach.tu` (phút bắt đầu áp dụng phương án;
  trước `tu` chạy như muc 0, không đổi thứ tự). Mặc định 0 → 72 test cũ vẫn xanh.

## Cập nhật phiên 3 – nâng cấp giao diện "War Room" + Đồng hồ quyết định

Nhánh phiên 3: `claude/kind-albattani-rwc6p2` (tạo từ `claude/stoic-maxwell-8m9yp6`), draft PR base = `claude/stoic-maxwell-8m9yp6`.
Người dùng chốt: trình chiếu trên laptop cho giám khảo xem gần; phong cách War Room tối; gộp Việc 2; KHÔNG thêm thư viện.

- [x] Việc 2 – `engine.dong_ho_quyet_dinh(dc, pt)` (hàm riêng, không gọi trong `phan_tich`) + `tests/test_dong_ho.py` (6 test).
  Số mô phỏng = số tài liệu: TH3 đổi thứ tự 11:20, ~2 sp/phút (thêm ~1 phút tăng ca/phút); NCC tách lô 11:20; TH4 A 10:02.
  Tổng **78 passed**. Mọi phương án mẫu vẫn giữ đơn nếu quyết trước 16:00 (bằng tăng ca ≤ 4h) → "hết hiệu lực" = "còn cả ca".
- [x] `demo/.streamlit/config.toml` (theme tối), `demo/giao_dien.py` (màu đã chạy validator dataviz trên nền #131a2b, CSS,
  template Plotly "warroom", thẻ HTML), `demo/app.py` viết lại: chế độ Tổng quan; trang sự cố = hero + 4 KPI (có đồng hồ) +
  thẻ đề xuất + 01 bản đồ lan truyền có hoạt ảnh (Plotly frames, mở ở lúc tệ nhất, ▶ phát từ lúc sự cố, chuyển không làm gì ↔
  đề xuất) + 02 thẻ phương án / biểu đồ cứu được / thanh đồng hồ + 03 bộ phận + truy vết (TH6) + 04 chi tiết kỹ thuật.
  Diễn tập đầu ca: gauge + thẻ KPI, cùng phong cách.
- [x] Playwright (viewport 1440×900, `locale: 'vi-VN'`): Tổng quan, 8 kịch bản, ▶ bản đồ, chuyển đề xuất, Diễn tập đầu ca,
  Tự nhập → 0 exception, 0 lỗi JS. Ảnh: `demo/screenshot_tong_quan.png`, `screenshot_th3.png`, `screenshot_dau_ca.png`.
  Lưu ý kiểm tra: ảnh "full page" phải nới viewport (Streamlit cuộn trong `stMain`); sửa `giao_dien.py` cần khởi động lại server.

## Việc còn lại (cho phiên mới)

1. Người dùng duyệt giao diện mới (ảnh chụp) và PR phiên 3; chỉnh theo góp ý.
2. Việc 4: kịch bản demo 5 phút + slide pitch (hỏi người dùng trước; có thể đang làm ở tab khác).
3. Hỏi người dùng: có cập nhật IDEA.md/docx mục 7.1–7.3 bằng số mô phỏng không.
4. Theo dõi PR #1 và PR phiên 3 (CI / review).
