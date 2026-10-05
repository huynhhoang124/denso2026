# Demo D3 – Chain Impact Propagation

Bản demo chạy trên máy local cho ý tưởng trong [`IDEA.md`](../IDEA.md). Người dùng chọn hoặc mô tả một sự cố,
hệ thống trả về:

- dòng thời gian tác động;
- sản lượng dự đoán;
- các phương án xử lý (số cứu được, chi phí, giờ tăng ca, mức xáo trộn);
- mức cảnh báo Xanh/Vàng/Đỏ;
- câu trả lời riêng cho Bảo trì, Kế hoạch và Giao hàng & Sales.

## Cách chạy

Cần Python 3.10 trở lên.

```bash
cd C:\denso2026\demo            # hoặc: cd denso2026/demo
python -m pip install pandas networkx streamlit plotly pyyaml pytest
python -m pytest -q             # 50 passed, 5 xfailed
streamlit run app.py            # mở http://localhost:8501
```

Nên dùng `python -m pytest` thay cho `pytest`, để chắc chắn test chạy đúng bộ Python đã cài thư viện.

## Các file

| File | Nội dung |
|---|---|
| `config.yaml` | Dây chuyền giả định ở mục 6: Dập D1, D2 → B1 → Gia công M1–M3 → B2 → Lắp ráp (6 người) → kho thành phẩm; linh kiện L-A/L-B; đơn D-101, D-102, D-201; xe giao; line 2; phân bố thời gian sửa; đơn giá. Những thông số tài liệu không nêu đều ghi "giả định demo". |
| `engine.py` | Lớp Logic (đồ thị networkx) và lớp Nghiệp vụ (mô phỏng bước 1 phút), cùng thang xử lý, mức cảnh báo, thời gian chịu đựng của đệm, thứ tự sửa máy, truy vết ngược, phân tích giao hàng và câu trả lời cho từng bộ phận. |
| `scenarios.py` | 8 kịch bản (ví dụ gốc và TH1–TH7) và bảng phả hệ sản phẩm tự tạo cho TH6. |
| `app.py` | Giao diện Streamlit một trang, tiếng Việt. |
| `tests/test_scenarios.py` | Mỗi assert ứng với một con số trong tài liệu. |

## Engine hoạt động thế nào

1. **Lớp Logic.** Đồ thị có hướng gồm máy, công đoạn, đệm, kho thành phẩm, linh kiện, nhà cung cấp, mã hàng, đơn hàng, khách hàng, chuyến xe và tổ người vận hành. Các cạnh mang tên quan hệ: *chạy trên*, *đưa vào*, *đệm cho*, *cấp cho*, *thành phần của*, *đáp ứng đơn*, *giao cho*, *chở bởi*, *vận hành*. Thứ tự dòng chảy lấy bằng sắp xếp topo trên đồ thị, nên thêm công đoạn hay đệm chỉ cần sửa `config.yaml`.
2. **Mẫu nhiễu chung** `Nhieu(điểm, đại lượng, thay đổi, bắt đầu, thời lượng)`, với 5 đại lượng:
   - năng lực: máy, hoặc cả công đoạn khi thiếu người;
   - nguồn cung: lô linh kiện;
   - nhu cầu: đơn gấp;
   - thời gian: chuyến giao;
   - chất lượng: giữ hàng nghi lỗi.

   Hành động khắc phục cũng dùng đúng mẫu này, ví dụ điều người (+16,7% năng lực Lắp ráp), tách lô hay đặt gấp linh kiện.
3. **Mô phỏng bước 1 phút**, đi từ cuối chuyền lên đầu chuyền. Sản lượng mỗi công đoạn = min(năng lực, đầu vào có trong đệm trước, linh kiện, chỗ trống ở đệm sau). Nhờ vậy sự cố lan cả hai chiều: xuôi (đói hàng) và ngược (bị chặn). Các quy tắc đã cài:
   - chạy trên chuẩn tối đa 6 giờ/ca;
   - tăng ca tối đa 4 giờ và chỉ chạy ở tốc độ chuẩn;
   - tiêu hao linh kiện theo BOM;
   - đổi mã mất 20 phút;
   - máy chạy chậm bất thường không được tăng tốc;
   - công đoạn thiếu người không chạy nhanh hơn nhịp của số người còn lại.
4. **Ba mức vận hành** đúng với thang xử lý:
   - 0 – không làm gì;
   - 1 – chia tải: giữ nhịp 120 sp/h; các máy còn lại gánh phần thiếu theo tỷ lệ công suất tối đa;
   - 2 – tăng tốc: chạy tới mức tối đa cho phép để đuổi kịp kế hoạch.

   Ngoài ra còn các lựa chọn đổi thứ tự, tăng ca, điều người, tách lô.
5. **Sản lượng hiệu dụng** = sản lượng ra khỏi Lắp ráp − hàng bị giữ + Σ min(0, mức đệm − mục tiêu). Đây là cách viết tổng quát của quy ước "tính tại nút cổ chai, đệm phải trả về mức mục tiêu". Rút đệm không được tính là cứu sản lượng. Giao diện vẫn hiện riêng sản lượng từng công đoạn để đối chiếu.
6. **Tác động** = mô phỏng có nhiễu − mô phỏng theo kế hoạch.
7. **Giờ tăng ca** là số phút sau 16:00 để sản lượng hiệu dụng đạt kế hoạch. Kho thành phẩm cũng là một đệm, nên không dùng để giảm giờ tăng ca, nhưng được tính khi kiểm tra đơn.
8. **Kiểm tra đơn hàng.** D-101 phải đủ trước xe 17:00. Đơn ngày mai phải vừa một ca, có tính thời gian đổi mã và thời gian bù các đệm bị thiếu.
9. **Mức cảnh báo** theo mục 4.5:
   - Xanh: chỉ cần chia tải hoặc tăng tốc, không tăng ca, đơn vẫn đủ;
   - Vàng: cần tăng ca, đổi thứ tự hoặc điều người, đơn vẫn kịp;
   - Đỏ: không phương án nào giữ được đơn.

   Phương án đề xuất là phương án ít giờ tăng ca nhất, rồi đến bậc thang thấp nhất, rồi đến chi phí thấp nhất. Con người vẫn là bên chọn.

## Kết quả kiểm tra so với tài liệu

`python -m pytest -q` cho **50 passed, 5 xfailed**. Engine không được chỉnh cho khớp số tài liệu. Những chỗ lệch được đánh dấu `xfail(strict=True)` kèm lý do: suite vẫn xanh, chỗ lệch vẫn được ghi lại, và nếu engine tình cờ ra đúng số tài liệu thì test sẽ báo.

**Khớp tài liệu (mô phỏng bước 1 phút):**

| Trường hợp | Con số |
|---|---|
| Ví dụ gốc | Không làm gì 800; chia tải + tăng tốc 884; tăng ca 38 phút; sửa 3/4/5/6 giờ → 930/884/838/792 sp và tăng ca 15/38/61/84 phút; Vàng |
| TH1 | M1 = 45,96 ≈ 46, M2 = 44,04 ≈ 44; thiếu 10 sp, kho bù → Xanh; M3 hỏng hẳn 12:00 → 842 sp, tăng ca 89 phút ≈ 1,5 giờ |
| TH2 | Sửa M2 trước: Gia công 848 sp, B1 còn 12. Sửa D1 trước: 792 sp, B1 còn 218, tăng ca 104 phút ≈ 1 giờ 45 |
| TH3 | 11:20 L-A cạn, 12:05 B2 đầy, 12:55 B1 đầy; không làm gì mất 440; đổi thứ tự mất 80 (480 X + 400 Y); ngưỡng lô 16:05 |
| TH4 | Đơn C xong 18:00 (A), 18:30 (B); engine tự phát hiện thiếu 260 L-A |
| TH5 | 640 / 760 (tăng ca 2 giờ) / 880 (tăng ca 40 phút); B chỉ khả thi khi line 2 dư năng lực; cơ hội bảo dưỡng Gia công 08:00–10:00 |
| TH6 | Truy ngược ra M3 + lô S-77; hai giả thuyết 600 và 88 sp; lấy mẫu S-77 trên M1/M2 ra 0 lỗi → giữ 88 sp; tính xuôi 846 sp |
| TH7 | Hàng đến khách 20:30, trễ 1,5 giờ |

**Chỗ lệch (xfail) và lý do:**

1. **TH2: engine chọn sửa D1 trước, tài liệu chọn M2.** Sửa M2 trước cho Gia công 848 sp nhưng rút B1 từ 200 xuống 12. Áp đúng quy ước "đệm phải trả về mức mục tiêu" thì:
   - sửa M2 trước: sản lượng hiệu dụng khoảng 660, cần khoảng 180 phút tăng ca để vừa đủ kế hoạch vừa trả đệm;
   - sửa D1 trước: 792 sp, cần khoảng 104 phút.

   Nguyên nhân: dây chuyền cân bằng (mọi công đoạn chuẩn 120 sp/h). D1 hỏng làm Dập hụt 50 sp/h, M2 hỏng chỉ làm Gia công hụt 28 sp/h. Đệm B1 chỉ hoãn thiệt hại của D1 sang sau 16:00, không xóa được nó. Tài liệu chỉ so sản lượng Gia công lúc 16:00. Giao diện hiện cả hai thước đo để đội quyết định.
2. **TH2: tăng ca khi sửa M2 trước.** Tài liệu ghi 1 giờ 20, chỉ bù 112 sp ở Gia công và chưa trả B1 (thiếu 188). Engine ra khoảng 180 phút.
3. **TH3: ngày mai "vừa một ca".** 450 X + 500 Y = 950 sp, nhưng hai mã cần một lần đổi mã 20 phút (bằng 40 sp) nên thành 990 > 960. Engine đề xuất khoảng 40 phút tăng ca hôm nay cho phương án đổi thứ tự. Phương án đổi thứ tự kết hợp tăng tốc thì không cần tăng ca.
4. **TH6: tăng ca 42 phút.** Tài liệu trừ 30 sp kho thành phẩm ở TH6 (84 sp → 42 phút) nhưng không trừ ở mục 5 (76 sp → 38 phút); hai số này không thể cùng đúng. Engine dùng một quy ước cho mọi trường hợp (không trừ kho), nên ra 114 sp → 57 phút ở mức chia tải, 48 phút nếu có tăng tốc. Engine còn phát hiện thêm: giữ 88 sp làm nhu cầu L-A thành 1048 > 1000, nên phải đặt gấp 48 L-A.
5. **TH7: mức Đỏ.** Có phương án giữ đơn đúng hạn (thuê xe ngoài, đến 18:30), nên theo định nghĩa ở mục 4.5 là Vàng. Bảng tổng hợp của tài liệu ghi Đỏ.

Hai lưu ý không làm đổi kết quả:

- Ở mục 5, khung 14:00–16:00 Gia công chạy 138 sp/h, cao hơn mức tối đa 130 của Lắp ráp. Phần dư dồn vào B2, nên sản lượng hiệu dụng không đổi.
- TH4 chỉ đạt 18:00/18:30 khi đặt gấp 260 L-A, về trước 15:50 (A) hoặc 16:20 (B). Engine tự sinh hành động này, đúng như câu "sự cố này tự sinh ra trường hợp 3" trong tài liệu.

## Giả định của bản demo

- Toàn bộ dữ liệu là tự tạo, theo đúng bảng ở mục 6. Đơn giá chi phí, sức chứa kho thành phẩm, số người ở Dập và Gia công, năng suất line 2 và giờ xe báo trễ (15:00) là giả định demo, đặt trong `config.yaml`.
- X và Y dùng chung Dập và Gia công; đệm không phân biệt mã. Định mức 1 linh kiện cho mỗi sản phẩm.
- Thời gian xuyên chuyền (20 phút) chỉ dùng để diễn giải. Mô hình coi việc chuyển hàng qua đệm là tức thời.
- Bảng phả hệ TH6 có cơ chế lỗi ẩn mà engine không biết trước: chỉ M3 khi chạy 44 sp/h mới sinh lỗi. Truy vết phải tự tìm ra điều này bằng điểm chung và lấy mẫu.

## Hướng mở rộng (ngoài phạm vi demo)

- **Dữ liệu thật:** nối lakehouse của nhà máy (tình trạng máy, tồn đệm, MES theo lô hoặc sản phẩm, đơn hàng, lịch xe) vào hai bảng điểm và quan hệ; hiệu chỉnh hiệu suất thực và công suất tối đa theo dữ liệu (mục 7.4).
- **Weibull và cảnh báo trước khi hỏng (mục 4.6):** ước lượng xác suất hỏng trong 24 giờ từ lịch sử phiếu sửa; ưu tiên bảo trì = xác suất hỏng × số sản phẩm mất nếu hỏng, con số sau lấy từ chính engine này.
- **LLM (mục 7.6):** dịch câu hỏi bằng lời thành mẫu nhiễu và dịch kết quả ra lời. Engine vẫn là bên tính số.
- **Neo4j hoặc graph database:** khi số dây chuyền, lô và đơn lớn. Bản demo dùng networkx trong bộ nhớ.
- Mô phỏng theo sự kiện cho nhiều sự cố chồng nhau, quy đổi mọi phương án ra tiền (mục 7.7), diễn tập rủi ro đầu ca và đề xuất mức đệm (mục 7.1–7.2), kho tri thức sự cố (mục 7.5).
