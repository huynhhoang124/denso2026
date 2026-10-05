# D3 – CHAIN IMPACT PROPAGATION

Liên kết dữ liệu chuỗi sản xuất, dự đoán tác động lan truyền và gợi ý hành động cho từng bộ phận

DENSO Factory Hacks 2026 · Bản ý tưởng và giải pháp · 05/10/2026

Thông điệp: War Room cho biết bây giờ ra sao. Hệ thống này cho biết các giờ tới sẽ ra sao và nên làm gì – cho từng bộ phận, trên cùng một nguồn số liệu, trong vòng 1 phút.

## Tóm tắt ý tưởng

- Dựng nhà máy thành bản đồ dòng chảy có quy tắc: máy, công đoạn, tồn đệm, lô linh kiện, người, đơn hàng là các điểm nối với nhau theo quan hệ phụ thuộc.

- Mọi sự cố được quy về một mẫu chung: tại điểm nào, đại lượng nào (năng lực, nguồn cung, nhu cầu, thời gian) thay đổi bao nhiêu, trong bao lâu.

- Tác động = mô phỏng có sự cố − mô phỏng theo kế hoạch. Hành động khắc phục cũng là một "nhiễu" và được chạy thử để ra số sản phẩm cứu được, chi phí, mức xáo trộn.

- Mỗi máy có công suất chuẩn và công suất tối đa cho phép; khi có sự cố, hệ thống chia tải, tính giờ tăng ca, xếp thứ tự sửa máy, cảnh báo theo mức tác động và cảnh báo trước khi máy hỏng.

- Cùng bản đồ đi theo chiều ngược để truy vết nguồn gốc lỗi và nguyên nhân đơn trễ.

### 1. Bài toán

Nhà máy vận hành theo chuỗi bốn khâu phụ thuộc nhau: Kế hoạch sản xuất → Cấp linh kiện → Vận hành máy → Giao hàng. Mỗi công đoạn có nhiều máy chạy song song, giữa các công đoạn có tồn đệm để dòng chảy không đứt.

Khi có sự cố, ảnh hưởng lan dọc chuỗi. Nhưng dữ liệu các khâu rời rạc, nên Kế hoạch, Bảo trì và Giao hàng mỗi bên tự tính tay trên file riêng: chậm, dễ sai, và có thể ra ba con số khác nhau về cùng một sự cố. Đến khi thống nhất được thì thường đã muộn để xoay xở.

Tình huống BTC nêu: một máy trên chuyền dừng đột ngột, dự kiến phục hồi sau 8 giờ → nghẽn công đoạn sau, hụt sản lượng ca, nguy cơ trễ giao hàng. Bộ phận liên quan: Kế hoạch sản xuất, Bảo trì, Giao hàng & bán hàng.

Phòng điều hành (War Room) hiện đã hiển thị hiệu suất dây chuyền, trạng thái AGV, tồn kho có ngưỡng, hỏng hóc kèm thời gian xử lý. Phần còn thiếu là tính về phía trước và gợi ý hành động.

| Bộ phận | Cần biết gì khi có sự cố |
|---|---|
| Bảo trì | Máy nào cần sửa trước; máy nào sắp hỏng; khi nào bảo dưỡng mà không mất sản lượng |
| Kế hoạch sản xuất | Ca có cứu được không; chia tải, đổi thứ tự, tăng ca bao lâu, chuyển line hay không |
| Giao hàng & Sales | Đơn nào chắc chắn trễ, đơn nào còn cứu được; có cần báo khách sớm không; nhận đơn gấp được không |
| Chất lượng & Mua hàng (mở rộng) | Lỗi đến từ đâu; phải khoanh lại bao nhiêu sản phẩm |

### 2. Ý tưởng cốt lõi

Dựng nhà máy thành một bản đồ dòng chảy có quy tắc. Khi có sự cố, hệ thống tự "chạy thử tương lai" để biết thiếu bao nhiêu hàng, đơn nào trễ và nên xoay xở theo cách nào.

#### 2.1 Mọi sự cố là một "nhiễu" lên bốn đại lượng của dòng chảy

| Đại lượng bị thay đổi | Khâu | Ví dụ sự cố |
|---|---|---|
| Năng lực | Vận hành máy, con người | Máy hỏng, máy chạy chậm, thiếu người, đổi khuôn kéo dài |
| Nguồn cung | Cấp linh kiện | Lô linh kiện về trễ, lô bị giữ chờ kiểm tra, AGV hỏng |
| Nhu cầu | Kế hoạch | Khách chèn đơn gấp, tăng số lượng, đổi thứ tự ưu tiên |
| Thời gian | Giao hàng | Xe đến trễ, đổi lịch xuất, chuyển tuyến |

Mẫu mô tả chung: tại điểm X · đại lượng Y · tăng/giảm p% · từ t₀ trong T giờ · độ chắc chắn.

Ví dụ "máy dừng 8 giờ" → M2 · năng lực · −100% · từ 08:00 · 8 giờ ± 2 giờ. Gặp loại sự cố mới chỉ cần mô tả theo mẫu, không phải viết quy trình xử lý mới. Đây là cách tổng quát hóa mà DENSO yêu cầu.

#### 2.2 Tác động = mô phỏng có sự cố − mô phỏng theo kế hoạch

Hệ thống chạy hai lần trên cùng bản đồ: một lần theo kế hoạch, một lần có nhiễu. Phần chênh lệch chính là tác động (sản phẩm thiếu, giờ dừng, đơn trễ). Định nghĩa này không phụ thuộc loại sự cố và ai cũng kiểm tra lại được.

#### 2.3 Hành động khắc phục cũng là một nhiễu (tích cực)

Chia tải, tăng tốc, đổi thứ tự, tăng ca, chuyển line… đều được mô tả theo cùng mẫu và chạy lại mô phỏng. Mỗi phương án ra ba con số: sản phẩm cứu được, chi phí, mức xáo trộn kế hoạch. Con người chọn phương án.

### 3. Mô hình nhà máy hai lớp

Thẻ đề D3 yêu cầu liên kết dữ liệu qua hai lớp: Logic và Nghiệp vụ sản xuất. Cách hiểu dưới đây là đề xuất của nhóm.

#### 3.1 Lớp Logic – cái gì nối với cái gì

- Điểm: Đơn hàng, Kế hoạch ca, Lô linh kiện, Nhà cung cấp, Công đoạn, Máy, Tồn đệm, Người vận hành/ca, Chuyến giao, Khách hàng.

- Quan hệ: cấp cho, chạy trên, đệm cho, vận hành bởi, đáp ứng đơn, giao cho.

- Khóa nối: mã sản phẩm, mã linh kiện, mã lô, mã dây chuyền, mã nhà sản xuất – theo quan sát khi tham quan, phần lớn các khâu đã có sẵn.

- Lưu trữ: đồ thị lưu thành hai bảng (điểm, quan hệ) ngay trên lakehouse nhà máy đang dùng – không cần hạ tầng mới. Mỗi dây chuyền là một tệp cấu hình; thêm dây chuyền không phải sửa phần lõi.

#### 3.2 Lớp Nghiệp vụ sản xuất – nối như thế nào

| Điểm | Thông số | Quy tắc |
|---|---|---|
| Máy | Công suất chuẩn; công suất tối đa cho phép. Tùy chọn: giờ tối đa chạy trên chuẩn, tỷ lệ lỗi khi chạy cao, mã hàng làm được | Mức tối đa chỉ dùng khi có sự cố làm hụt sản lượng |
| Công đoạn | Danh sách máy song song | Năng lực = tổng năng lực các máy đang chạy |
| Tồn đệm | Mức hiện tại, mức mục tiêu, sức chứa | Cạn → công đoạn sau đói hàng; đầy → công đoạn trước bị chặn |
| Linh kiện | Định mức BOM, tồn kho, lịch về | Cạn → công đoạn dùng linh kiện đó dừng |
| Người | Số người cần mỗi công đoạn, kỹ năng, giới hạn tăng ca | Thiếu người → năng lực giảm theo tỷ lệ |
| Đơn hàng | Số lượng, hạn giao, mức ưu tiên khách | Không đủ hàng trước hạn → trễ |

#### 3.3 Công suất chuẩn và công suất tối đa cho phép

Nhà máy chạy theo nhịp kế hoạch nên phần lớn máy chạy thấp hơn khả năng thật – phần dư đó chính là "đệm năng lực" để bù khi máy bên cạnh hỏng. Mô hình hóa như sau:

- Công suất chuẩn: tốc độ chạy hằng ngày theo nhịp kế hoạch.

- Công suất tối đa cho phép: tốc độ cao nhất đã được duyệt về chất lượng, không phải giới hạn vật lý của máy (trong ngành ô tô, thay đổi thông số công nghệ phải được phê duyệt).

- Kích hoạt khi có bất kỳ sự cố nào làm hụt sản lượng – không chỉ máy cùng công đoạn hỏng mà cả lô linh kiện trễ, thiếu người, đơn gấp.

- Giới hạn thời gian chạy trên chuẩn (giả định 6 giờ/ca) vì hao mòn, nhiệt và nguy cơ hỏng tiếp.

- Chất lượng: chạy cao có thể tăng tỷ lệ lỗi → sản lượng đạt = công suất × (1 − tỷ lệ lỗi).

- Máy có chu kỳ cố định (lò nhiệt luyện, máy ép giữ khuôn) thì tối đa = chuẩn.

- Giá trị tối đa ban đầu là giả định (khoảng 110–120% chuẩn) và được hiệu chỉnh dần theo dữ liệu thực (xem trường hợp 6).

### 4. Engine – các chức năng

#### 4.1 Dự đoán sản lượng và dòng thời gian

Mô phỏng theo bước thời gian (ví dụ 1 phút). Ở mỗi bước: sản lượng công đoạn = min(năng lực, đầu vào có sẵn, chỗ trống ở đệm sau) × hiệu suất thực. Nhờ vậy sự cố lan theo cả hai chiều: xuôi (công đoạn sau đói hàng) và ngược (công đoạn trước bị chặn).

Đầu ra là một dòng thời gian: công đoạn nào dừng lúc mấy giờ, đệm nào cạn/đầy khi nào, ca hụt bao nhiêu, đơn nào và khách nào bị trễ.

#### 4.2 Chia tải khi máy hỏng

- Năng lực còn lại = tổng công suất tối đa của các máy còn chạy.

- Nhu cầu ≤ năng lực còn lại: chia theo tỷ lệ công suất tối đa để các máy cùng mức tải (không chia đều, vì máy yếu có thể vượt giới hạn).

- Nhu cầu > năng lực còn lại: mọi máy chạy mức tối đa, phần thiếu chuyển sang bước tiếp theo của thang xử lý.

- Nhiều mã hàng: thêm ràng buộc máy nào làm được mã nào, ưu tiên mã có hạn gần → bài toán phân bổ (quy hoạch tuyến tính).

- Đi kèm: đổi lộ trình cấp phôi (AGV) sang các máy còn chạy.

#### 4.3 Dự báo giờ tăng ca

- Giờ tăng ca = sản lượng thiếu ÷ tốc độ trong giờ tăng ca + thời gian xuyên chuyền.

- Tốc độ tăng ca lấy theo mức chuẩn của các máy đang chạy được – máy chưa sửa xong thì không tính.

- Tính cho cả công đoạn phía sau (hàng làm bù phải đi hết chuyền) và phía trước (nếu đệm phía trước gần cạn).

- Thời gian sửa không chắc chắn → chạy nhiều kịch bản, trả về một khoảng kèm xác suất; tính lại mỗi khi Bảo trì cập nhật tiến độ.

- Kiểm tra giới hạn tăng ca theo luật (Bộ luật Lao động 2019: giờ làm thêm không quá 50% giờ làm bình thường trong ngày) và quy định nội bộ.

#### 4.4 Thang xử lý

| Bước | Hành động | Dùng khi |
|---|---|---|
| 1 | Chia tải cho máy còn lại | Luôn thử trước – chi phí gần như bằng 0 |
| 2 | Tăng tốc trong giới hạn cho phép | Chia tải chưa đủ |
| 3 | Đổi thứ tự sản xuất | Thiếu linh kiện hoặc thiếu máy cho một mã hàng |
| 4 | Tăng ca | Bước 1–3 chưa đủ |
| 5 | Chuyển line khác hoặc ca sau | Vượt giới hạn tăng ca |
| 6 | Báo khách, giao tách đợt | Bước 1–5 không đủ để kịp hạn |

Mỗi phương án được chấm theo ba tiêu chí: sản phẩm cứu được, chi phí, mức xáo trộn kế hoạch (càng ít thay đổi càng tốt).

#### 4.5 Cảnh báo theo mức tác động

| Mức | Điều kiện | Gửi cho |
|---|---|---|
| Xanh | Chia tải là bù đủ, không đơn nào ảnh hưởng | Bảo trì |
| Vàng | Cần tăng ca hoặc đổi thứ tự, đơn vẫn kịp | Bảo trì, Kế hoạch |
| Đỏ | Có đơn trễ dù đã dùng hết các bước | Bảo trì, Kế hoạch, Giao hàng & Sales |

Nội dung cảnh báo nói luôn hậu quả và hành động, ví dụ: "M2 hỏng 10:00. Sau chia tải, cuối ca thiếu 76 sp. Cần tăng ca khoảng 40–60 phút. Đơn D-101 vẫn kịp nếu tăng ca."

#### 4.6 Cảnh báo trước khi máy hỏng

- Dữ liệu dùng: lịch sử sự cố từng máy (khoảng cách giữa các lần hỏng, giờ chạy kể từ lần sửa gần nhất) và dấu hiệu xuống cấp (chu kỳ chậm dần, dừng ngắn tăng, tỷ lệ lỗi tăng). Không cần cảm biến; có cảm biến rung/nhiệt thì bổ sung sau.

- Phương pháp: phân tích Weibull trên lịch sử phiếu sửa chữa → xác suất hỏng trong 24 giờ tới. Tham số hình dạng β > 1 (hỏng do mòn) → bảo dưỡng định kỳ có ích; β ≈ 1 (hỏng ngẫu nhiên) → nên dồn vào rút ngắn thời gian sửa.

- Mức ưu tiên bảo trì = xác suất hỏng × số sản phẩm mất nếu hỏng (lấy từ engine).

| Máy | Xác suất hỏng 24 giờ tới | Mất nếu hỏng | Rủi ro | Ưu tiên |
|---|---|---|---|---|
| M2 | 30% | 160 sp (nằm ở nút cổ chai, đệm sau mỏng) | 48 sp | 1 |
| M5 | 40% | 15 sp (đệm phía sau dày) | 6 sp | 2 |

Máy dễ hỏng hơn chưa chắc phải lo trước; máy nào hỏng thì thiệt hại lan xa hơn mới được ưu tiên. (Số liệu minh họa.)

#### 4.7 Thời gian chịu đựng và thời gian phục hồi

Thời gian chịu đựng của một đệm = mức đệm ÷ tốc độ thiếu hụt khi máy phía trước hỏng. So với thời gian sửa thường gặp của máy đó: nếu chịu đựng ≥ sửa, sự cố được đệm hấp thụ trong ca; ngược lại, thiệt hại chắc chắn xảy ra. Hai chỉ số này lấy từ phương pháp stress test chuỗi cung ứng (Time-to-Survive / Time-to-Recover) và dùng để sàng lọc nhanh thứ tự sửa máy (trường hợp 2) và đề xuất mức đệm (mục 7.1). Lưu ý: đệm hấp thụ chỉ là hoãn thiệt hại – phần đệm bị rút vẫn phải bù lại sau đó. Vì vậy thứ tự sửa cuối cùng được quyết định bằng mô phỏng, tính cả thời gian trả đệm về mức mục tiêu (xem trường hợp 2).

#### 4.8 Truy vết ngược

- Sản phẩm lỗi → lô linh kiện → nhà cung cấp → máy → ca → người vận hành. Từ đó khoanh vùng những sản phẩm khác có cùng nguy cơ.

- Đơn trễ → trễ vì sự cố nào. Khi nhiều sự cố chồng nhau, hệ thống bỏ lần lượt từng sự cố rồi chạy lại để tính phần góp của mỗi sự cố.

- Truy vết dùng chính bản đồ của phần dự đoán, chỉ đi theo chiều ngược – không phải xây hệ thống riêng.

#### 4.9 Kết hợp quy tắc và học máy

Học máy ước lượng tham số: thời gian sửa theo loại lỗi, xác suất hỏng, hiệu suất thực, tỷ lệ lỗi khi chạy cao. Quy tắc dòng chảy tính sự lan truyền. Nhờ vậy mọi con số đều giải thích được – điều mà một mô hình học máy thuần không làm được.

Ba nguyên tắc: luôn giải thích được (bấm vào con số thấy nguồn gốc); nói rõ chỗ không chắc (trả về khoảng và xác suất); con người quyết định (hệ thống không tự điều khiển máy hay đổi kế hoạch).

### 5. Ví dụ gốc: máy hỏng 4 giờ

Công đoạn Gia công có 3 máy song song. Ca 08:00–16:00, kế hoạch 960 sp (120 sp/h). Lắp ráp phía sau chạy tối đa 130 sp/h nên Gia công là nút cổ chai.

| Máy | Công suất chuẩn | Công suất tối đa cho phép |
|---|---|---|
| M1 | 40 sp/h | 48 sp/h |
| M2 | 40 sp/h | 46 sp/h |
| M3 | 40 sp/h | 44 sp/h (máy cũ) |

Sự cố: M2 hỏng lúc 10:00, Bảo trì dự kiến sửa 4 giờ (xong 14:00).

| Khoảng | Máy chạy | Tốc độ | Sản lượng | Cộng dồn |
|---|---|---|---|---|
| 08–10 | M1, M2, M3 (chuẩn) | 120 | 240 | 240 |
| 10–14 | M1, M3 (tối đa) | 92 | 368 | 608 |
| 14–16 | M1, M2, M3 (tối đa) | 138 | 276 | 884 |

- Không làm gì: 240 + 320 + 240 = 800 sp, thiếu 160.

- Chia tải và tăng tốc: 884 sp, cứu thêm 84, còn thiếu 76.

- Tăng ca ở tốc độ chuẩn 120 sp/h: 76 ÷ 120 ≈ 38 phút cho Gia công; Lắp ráp và Đóng gói chạy thêm khoảng 20 phút thời gian xuyên chuyền.

Thời gian sửa không chắc chắn nên hệ thống tính giờ tăng ca cho từng khả năng:

| M2 sửa xong sau | Sản lượng ca | Thiếu | Tăng ca Gia công | Khả năng (theo lịch sử, minh họa) |
|---|---|---|---|---|
| 3 giờ | 930 | 30 sp | 15 phút | 20% |
| 4 giờ | 884 | 76 sp | 38 phút | 50% |
| 5 giờ | 838 | 122 sp | 61 phút | 80% |
| 6 giờ | 792 | 168 sp | 84 phút | 95% |

Đề xuất: đăng ký trước khoảng 60 phút tăng ca (đủ trong 80% khả năng), tính lại mỗi khi Bảo trì cập nhật tiến độ. Mức cảnh báo: Vàng.

Quy ước tính: sản lượng tính tại công đoạn nút cổ chai (Gia công). Đệm phía sau có thể giúp Lắp ráp chạy đủ thêm một thời gian, nhưng phải được trả về mức mục tiêu để ca sau không hụt – vì vậy phần thiếu thực chất vẫn là phần thiếu của Gia công.

### 6. Bảy trường hợp mẫu

Các trường hợp chạy trên cùng một dây chuyền giả định. Số liệu minh họa, tính tay; sẽ được kiểm tra lại bằng mô phỏng.

| Điểm | Thông số |
|---|---|
| Dập: D1, D2 | Chuẩn 60 sp/h mỗi máy, tối đa 70 |
| Đệm B1 (Dập → Gia công) | Đang có 200 sp, sức chứa 300 |
| Gia công: M1, M2, M3 | Chuẩn 40 sp/h mỗi máy, tối đa 48 / 46 / 44 |
| Đệm B2 (Gia công → Lắp ráp) | Đang có 60 sp, sức chứa 150 |
| Lắp ráp: 1 chuyền, 6 người | Chuẩn 120 sp/h, tối đa 130. Mã X dùng linh kiện L-A, mã Y dùng L-B; X và Y dùng chung Dập và Gia công |
| Kho thành phẩm | 30 sp |

Quy tắc chung: ca 08:00–16:00, kế hoạch 960 sp; tăng ca sau 16:00. Máy chạy trên chuẩn tối đa 6 giờ/ca. Mỗi người tăng ca tối đa 4 giờ/ngày.

#### Trường hợp 1: Máy không hỏng hẳn mà chạy chậm

Tình huống: 09:00, M3 tụt từ 40 xuống 30 sp/h, chưa rõ nguyên nhân.

Hệ thống hiểu: M3 · năng lực · −25% · từ 09:00 · chưa rõ bao lâu.

- Chia tải: cần 120 sp/h, M3 còn 30 → M1 và M2 gánh 90, chia theo tỷ lệ công suất tối đa: M1 chạy 46, M2 chạy 44 (khoảng 96% mức tối đa).

- M1, M2 chỉ được chạy trên chuẩn 6 giờ (09:00–15:00). Giờ cuối về 40 → tổng 110 sp/h, thiếu 10 sp; kho thành phẩm 30 sp bù đủ.

- Mức: Xanh – không đơn nào ảnh hưởng.

Chạy trước kịch bản xấu: máy chạy chậm bất thường thường là dấu hiệu sắp hỏng. Hệ thống tự hỏi "nếu M3 hỏng hẳn lúc 12:00 thì sao?":

- 12:00–15:00 M1 + M2 chạy tối đa 94 sp/h; 15:00–16:00 hết giới hạn 6 giờ, về 80 sp/h → cả ca 842 sp, thiếu 118.

- Tăng ca chỉ còn M1, M2 ở 80 sp/h → khoảng 1,5 giờ. Mức Vàng.

Gợi ý Bảo trì: kiểm tra M3 trong giờ nghỉ trưa, không đợi đến khi máy hỏng hẳn. Điểm rút ra: sự cố nhẹ vẫn được dùng để cảnh báo sớm sự cố nặng.

#### Trường hợp 2: Hai máy hỏng cùng lúc, chỉ có một tổ bảo trì

Tình huống: 10:00, M2 (Gia công) hỏng, cần 4 giờ sửa. Cùng lúc D1 (Dập) hỏng, cần 3 giờ. Chỉ có một tổ bảo trì. Sửa máy nào trước? Theo cảm tính, nhiều người chọn D1 vì sửa nhanh hơn và nằm đầu chuyền.

|  | Sửa M2 trước | Sửa D1 trước |
|---|---|---|
| Lịch sửa | M2: 10–14; D1: 14–17 | D1: 10–13; M2: 13–17 |
| Gia công | 10–14: 92 sp/h; 14–16: 120 sp/h | 10–16: 92 sp/h |
| Sản lượng Gia công lúc 16:00 | 848 (thiếu 112) | 792 (thiếu 168) |
| Đệm B1 lúc 16:00 | Còn 12 sp – thiếu 188 so với mức mục tiêu 200 | Còn 218 sp (trên mục tiêu) |
| Sản lượng ca sau khi trả đệm về mục tiêu | ≈ 660 | 792 |
| Tăng ca để đủ kế hoạch và trả đệm về mục tiêu | ≈ 3 giờ: D1 sửa xong 17:00, giờ đầu Dập chỉ còn D2 60 sp/h; sau đó Dập chạy chuẩn 120 = nhịp chuyền nên B1 chỉ đầy lại được trong giờ tăng ca | ≈ 1 giờ 45 phút: giờ đầu M2 chưa sửa xong, Gia công chỉ chạy 80 sp/h |

→ Sửa D1 trước: ít hơn khoảng 1 giờ 15 phút tăng ca. Nếu chỉ nhìn sản lượng Gia công lúc 16:00 thì sửa M2 trước có vẻ hơn (848 so với 792), nhưng phần hơn đó lấy từ đệm B1 (rút từ 200 xuống 12) và phải trả lại sau ca.

Vì sao:

- Thời gian chịu đựng cho thấy D1 chờ được *trong ca*: D1 hỏng, Dập còn 70 sp/h; đệm B1 200 sp đỡ được khoảng 9 giờ (Gia công chạy 92) hoặc 4 giờ (Gia công chạy 120) – lâu hơn 3 giờ sửa D1. Còn M2 thì không chờ được: Gia công thiếu 28 sp/h, đệm B2 60 sp chỉ đỡ khoảng 2 giờ, ngắn hơn 4 giờ sửa.

- Nhưng dây chuyền cân bằng (mọi công đoạn chuẩn 120 sp/h): mỗi giờ D1 hỏng, Dập hụt 50 sp; mỗi giờ M2 hỏng, Gia công chỉ hụt 28 sp. Đệm B1 chỉ dời thiệt hại của D1 sang sau 16:00. Khi tính cả việc trả đệm, máy hụt nhiều hơn mỗi giờ và sửa nhanh hơn (D1) nên được sửa trước.

- Nếu ca sau Dập có thể chạy trên chuẩn (tối đa 140) để tự bù B1 mà không cần tăng ca thì khoảng cách giữa hai phương án hẹp lại. Hệ thống hiển thị cả hai thước đo để Bảo trì và Kế hoạch quyết định.

Điểm rút ra: thứ tự sửa quyết định bởi thiệt hại lan truyền tính đến khi các đệm được trả về mức mục tiêu – không phải thứ tự báo hỏng, cảm tính, hay chỉ sản lượng cuối ca. (Kiểm chứng bằng mô phỏng ở bản demo; bản nháp tính tay trước đây chọn M2 vì chưa tính phần trả đệm B1.)

#### Trường hợp 3: Lô linh kiện về trễ – sự cố lan ngược

Tình huống: lô 600 linh kiện L-A dự kiến về 10:00, nhà cung cấp báo trễ đến 15:00. Kho L-A đang có 400. Kế hoạch ca: 960 sp mã X. Đơn liên quan: D-101 (khách A) 500 sp X, xe lấy hàng 17:00 hôm nay; D-102: 460 sp X, hạn ngày mai; D-201 (khách B): 900 sp Y, hạn ngày mai.

Hệ thống hiểu: nguồn cung L-A · chậm 5 giờ.

| Giờ | Diễn biến nếu không làm gì |
|---|---|
| 11:20 | Kho L-A cạn → Lắp ráp dừng |
| 12:05 | Đệm B2 đầy → Gia công bị chặn (lan ngược) |
| 12:55 | Đệm B1 đầy → Dập bị chặn. Toàn chuyền đứng |
| 15:00 | Lô về. Mất 440 sp; phần bù dồn sang ngày mai, đe dọa D-102 và D-201 |

Xử lý – đổi thứ tự sản xuất:

- 11:20: Lắp ráp chuyển sang mã Y (dùng L-B, kho có 500), mất 20 phút đổi khuôn; chạy Y đến 15:00 được 400 sp Y.

- 15:00: lô về, đổi lại sang X (20 phút), chạy đến 16:00 được 80 sp X.

- Cả ca: 480 X + 400 Y = 880 sp. Chỉ mất 80 sp (2 lần đổi khuôn) thay vì 440.

| Bộ phận | Câu trả lời |
|---|---|
| Kế hoạch | Đổi thứ tự như trên. Ngày mai còn 450 X (D-102) + 500 Y (D-201) = 950 sp, cộng 1 lần đổi mã X → Y (20 phút ≈ 40 sp) = 990 sp > 960 → không vừa một ca. Hai cách: tăng ca khoảng 40 phút hôm nay để bù 80 sp, hoặc đổi thứ tự kết hợp tăng tốc Lắp ráp trong giới hạn cho phép (ca hôm nay đạt khoảng 920 sp, ngày mai vừa một ca, không cần tăng ca). |
| Bảo trì | Làm bảo dưỡng định kỳ chuyền Lắp ráp ngay trong 2 lần đổi khuôn, không mất thêm giờ máy. |
| Giao hàng & Sales | D-101 đủ: 480 X + 30 trong kho = 510 ≥ 500. Ngưỡng: D-101 cần thêm 70 sp X sau khi lô về (20 phút đổi khuôn + 35 phút chạy) → lô phải về trước 16:05. Lô đang báo 15:00, dư khoảng 1 giờ; nếu nhà cung cấp báo trễ thêm quá 16:05 → chuyển Đỏ. |
| Phương án thay thế | Nhà cung cấp tách lô, gửi trước 450 cái bằng xe nhỏ trước 11:20 → không phải đổi thứ tự, nhưng tốn phí xe. Hệ thống đặt hai phương án cạnh nhau để chọn. |

Mức: Vàng. Điểm rút ra: sự cố ở khâu cấp linh kiện lan ngược làm đứng cả chuyền; hệ thống tính được cả ngưỡng thời gian để biết còn bao nhiêu khoảng an toàn.

#### Trường hợp 4: Khách chèn đơn gấp – nhận được không?

Tình huống: 10:00, khách C đặt thêm 300 sp mã X, cần trước 20:00 hôm nay. Kế hoạch ca đã kín 960 sp cho các đơn hiện có.

Hệ thống hiểu: nhu cầu · +300 sp · hạn 20:00.

|  | A: Tăng tốc ca chính + tăng ca | B: Chỉ tăng ca |
|---|---|---|
| Ca chính | Lắp ráp chạy tối đa 130 sp/h từ 10:00 (6 giờ) → dư thêm 60 sp cho đơn C | Theo kế hoạch |
| Tăng ca | 16:00–18:00 làm 240 sp còn lại | 16:00–18:30 làm cả 300 sp |
| Đơn C xong lúc | 18:00 ✓ | 18:30 ✓ |
| Cái giá | 2 giờ tăng ca + 6 giờ chạy cao tải | 2,5 giờ tăng ca |

- Sales: nhận được, có số liệu để trả lời khách ngay; còn dư 1,5–2 giờ so với hạn 20:00.

- Kế hoạch: chọn A hay B là đổi hao mòn máy lấy 30 phút tăng ca.

- Bảo trì: không xếp bảo dưỡng chuyền Lắp ráp trong khung 10:00–18:30.

- Kiểm tra chéo tự động: đơn C cần thêm 300 linh kiện L-A. Nếu kho không đủ, sự cố này tự sinh ra trường hợp 3 – hệ thống phát hiện được vì mọi thứ nằm trên cùng một bản đồ. Với số liệu của dây chuyền này (kho 400 + lô 600 = 1000 L-A, cần 960 + 300 = 1260) thì kho không đủ: phải đặt gấp 260 L-A, về trước 15:50 (phương án A) hoặc 16:20 (phương án B). Hai mốc 18:00 và 18:30 ở trên đều đã giả định có lô bổ sung này.

Mức: Vàng. Điểm rút ra: hệ thống trả lời câu hỏi kinh doanh "nhận được không" kèm cái giá cụ thể, thay vì Sales phải hỏi vòng qua Kế hoạch.

#### Trường hợp 5: Thiếu người – biến sự cố thành cơ hội

Tình huống: 08:00, Lắp ráp chỉ có 4/6 người do nghỉ đột xuất.

Hệ thống hiểu: Lắp ráp · năng lực · −33% · cả ca. Cùng một mẫu mô tả như máy hỏng, dù nguyên nhân là con người.

- Không làm gì: Lắp ráp còn 80 sp/h → cả ca 640 sp, thiếu 320. Lan ngược: đệm B2 đầy lúc khoảng 10:15, Gia công buộc phải chạy chậm.

|  | A: Điều 1 người đa kỹ năng từ line 2 | B: Điều 2 người từ line 2 |
|---|---|---|
| Từ 10:00 | Lắp ráp 5 người → 100 sp/h | Lắp ráp 6 người → 120 sp/h |
| Sản lượng ca | 160 + 600 = 760 (thiếu 200) | 160 + 720 = 880 (thiếu 80) |
| Tăng ca | 2 giờ ở 100 sp/h (≤ 4 giờ ✓) | 40 phút ở 120 sp/h |
| Điều kiện | Line 2 thiếu 1 người vẫn đủ kế hoạch | Hệ thống chạy kiểm tra line 2: chỉ chọn B nếu line 2 dư năng lực |

- Cơ hội cho Bảo trì: trong 08:00–10:00 Lắp ráp chỉ chạy 80 sp/h → Gia công chỉ cần 2 máy → bảo dưỡng ngắn M3 ngay trong khung này, không mất sản lượng.

- Sales: đơn vẫn kịp nếu tăng ca được. Nếu không ai tăng ca được → Đỏ, đề xuất giao tách đợt và báo khách trước.

Mức: Vàng. Điểm rút ra: hệ thống không chỉ báo thiệt hại mà còn tìm ra năng lực nhàn rỗi do sự cố tạo ra để dùng vào việc khác; tài nguyên dùng chung giữa các line (người đa kỹ năng) cũng là một quan hệ trên bản đồ.

#### Trường hợp 6: Phát hiện hàng lỗi – truy ngược rồi tính xuôi

Tình huống: 14:00, khâu Kiểm tra cuối phát hiện 5 sp lỗi kích thước lỗ.

- Truy ngược: cả 5 sp đều được gia công trên M3 trong khung 10:00–12:00 (lúc M3 đang chạy tối đa 44 sp/h để bù cho máy khác), dùng phôi từ lô thép S-77 (nhà cung cấp Z).

- Khoanh vùng: hai giả thuyết – lỗi do vật liệu (cả lô S-77, khoảng 600 sp trên cả 3 máy) hoặc lỗi do máy (M3 trong 10:00–12:00, 88 sp). Hệ thống gợi ý lấy mẫu sản phẩm cùng lô S-77 nhưng chạy trên M1, M2 → 0 lỗi → nguyên nhân ở M3. Chỉ giữ lại 88 sp thay vì 600.

- Tính xuôi: giữ 88 sp → đơn đang chạy thiếu 88. M3 dừng 1 giờ để kiểm tra → M1, M2 chạy tối đa 94 sp/h → thiếu thêm 26. Tổng thiếu 114 sp. Kho thành phẩm (30 sp) cũng là một đệm phải trả về mức mục tiêu nên không dùng để giảm giờ tăng ca (cùng quy ước với mục 5) → tăng ca khoảng 57 phút; nếu sau 15:00 cả ba máy chạy tăng tốc để đuổi kịp kế hoạch thì còn khoảng 48 phút. Kho thành phẩm vẫn được tính khi kiểm tra đơn: D-101 vẫn đủ.

- Kiểm tra chéo linh kiện: làm bù 88 sp X nghĩa là cần 960 + 88 = 1048 L-A, trong khi cả ngày chỉ có 1000 → phải đặt gấp 48 L-A, về trước khoảng 16:20.

- Vòng phản hồi: lỗi xuất hiện đúng lúc M3 chạy ở mức tối đa → gợi ý hạ công suất tối đa cho phép của M3 từ 44 xuống 42 và kiểm tra dao cụ; ghi nhận tỷ lệ lỗi khi chạy cao vào thông số máy.

Mức: Vàng. Điểm rút ra: truy ngược và dự đoán xuôi chạy trên cùng một bản đồ; thông số "công suất tối đa" được chỉnh dần theo dữ liệu thật. Điều kiện: dữ liệu phải ghi được mỗi sản phẩm hoặc mỗi lô đã đi qua máy nào, giờ nào, dùng lô vật liệu nào.

#### Trường hợp 7: Xe giao hàng đến trễ

Tình huống: chuyến xe 17:00 chở đơn D-101 cho khách A báo trễ đến 19:00. Đường đi mất 1,5 giờ, khách cần hàng trước 19:00.

Hệ thống hiểu: chuyến giao · thời gian · +2 giờ → hàng đến khách 20:30, trễ 1,5 giờ.

| Phương án | Kết quả | Chi phí |
|---|---|---|
| Ghép vào chuyến 17:30 của tuyến gần (còn chỗ 40%) | Kịp phần hàng ưu tiên | Không phát sinh |
| Thuê xe ngoài | Kịp toàn bộ | Phí thuê xe |
| Báo khách | Khách biết trước 1,5 giờ thay vì biết khi hàng đã trễ | – |

Kiểm tra thêm: hàng chờ xe có làm kho thành phẩm đầy trước khi xe đến không? Nếu đầy, chuyền phải dừng – sự cố cuối chuỗi lan ngược vào tận nhà máy.

Mức: Vàng – còn phương án giữ đơn đúng hạn (thuê xe ngoài chạy đúng giờ cũ, hàng đến 18:30). Chuyến 17:30 tuyến gần đến đúng 19:00, chỉ chở được khoảng 200/500 sp. Chỉ chuyển Đỏ nếu không có xe nào kịp, khi đó báo khách ngay và giao tách đợt.

#### Tổng hợp: bảy trường hợp, một mô hình

| # | Trường hợp | Loại thay đổi | Điều trường hợp này cho thấy | Mức |
|---|---|---|---|---|
| 1 | Máy chạy chậm | Năng lực −25% | Chia tải; chạy trước kịch bản xấu để cảnh báo sớm | Xanh |
| 2 | Hai máy hỏng, một tổ bảo trì | Năng lực, 2 điểm | Ưu tiên sửa theo thiệt hại lan truyền, tính cả việc trả đệm về mục tiêu | Vàng |
| 3 | Lô linh kiện trễ | Nguồn cung | Lan ngược; đổi thứ tự; ngưỡng thời gian an toàn; tính cả thời gian đổi mã ngày mai | Vàng |
| 4 | Đơn gấp | Nhu cầu | Trả lời "nhận được không" kèm cái giá | Vàng |
| 5 | Thiếu người | Năng lực (con người) | Giới hạn tăng ca; tài nguyên dùng chung; tận dụng năng lực nhàn rỗi | Vàng |
| 6 | Hàng lỗi | Chất lượng → năng lực | Truy ngược khoanh vùng hẹp; tự chỉnh thông số | Vàng |
| 7 | Xe trễ | Thời gian giao | Sự cố cuối chuỗi lan ngược về nhà máy | Vàng |

Cả bảy trường hợp dùng cùng một bản đồ và cùng một cách tính, chỉ khác dòng mô tả sự cố – đó là bằng chứng cho khả năng tổng quát hóa.

### 7. Ý tưởng bổ sung để hoàn thiện

#### 7.1 Diễn tập rủi ro đầu ca và đề xuất mức đệm

Mỗi sáng, trước khi vào ca, hệ thống thử lần lượt "nếu máy này hỏng thì sao" cho từng máy và xếp hạng máy nào hỏng thì lan xa nhất (bản đồ rủi ro). Kết quả dùng cho bảo trì phòng ngừa: ưu tiên = xác suất hỏng trong ca × số sản phẩm mất nếu hỏng (mục 4.6). Mô phỏng với thông số giả định (máy hỏng lúc 10:00, sửa ở mức 80%): M3 (máy cũ, 10%/ca) xếp đầu dù mất ít nhất khi hỏng (112 sp); LR-1 mất nhiều nhất (330 sp) vì Lắp ráp không có máy dự phòng.

Từ đó đề xuất mức đệm tối thiểu = tốc độ thiếu hụt × thời gian sửa thường gặp. Ví dụ đệm B2: khi M2 hỏng thiếu 28 sp/h, thời gian sửa ở mức 80% là 5 giờ → B2 nên giữ khoảng 140 sp (sức chứa 150), thay vì 60 hiện tại. Máy tệ nhất trước B2 là M1 (thiếu 30 sp/h) → 150 sp, bằng sức chứa. Đổi lại là thêm 80–90 sp bán thành phẩm tồn kho – hệ thống đặt hai con số cạnh nhau để quyết định. Đệm B1 hiện 200 sp đã đủ cho D1 hỏng 4 giờ.

Mô phỏng cho thấy đệm dày giữ cho cuối chuyền không bị đói hàng nhưng không giảm giờ tăng ca: B2 = 150 giúp Lắp ráp ra đủ 960 sp lúc 16:00 khi M1 hỏng 5 giờ (thay vì 878), nhưng vẫn cần 66 phút tăng ca vì phần đệm đã dùng phải bù lại (quy ước ở mục 10).

#### 7.2 Xác suất hoàn thành kế hoạch trước khi vào ca

Mỗi kế hoạch ca được chạy qua engine nhiều lần với rủi ro lấy từ lịch sử (máy nào hỏng, lúc nào, sửa lệch dự kiến bao lâu, các lần dừng ngắn) → xác suất hoàn thành kế hoạch hôm nay và giờ tăng ca nên đăng ký trước. Nếu thấp, Kế hoạch có thể đăng ký tăng ca dự phòng hoặc tăng đệm trước khi có sự cố.

Mô phỏng 300 ca với thông số giả định: đủ kế hoạch trong ca 42%; đăng ký trước 38 phút tăng ca là đủ cho 80% số ca; đủ kế hoạch nếu tăng ca tối đa 4 giờ: 99,7%; đơn D-101 kịp 100%. Con số 42% thấp vì kế hoạch kín 100% công suất chuẩn (960 = 120 sp/h × 8 giờ): sự cố sớm trong ca được tăng tốc bù kịp, nhưng một lần dừng ngắn sát 16:00 thì không còn thời gian bù.

#### 7.3 "Đồng hồ quyết định"

Mỗi phương án có thời điểm muộn nhất còn hiệu lực. Hệ thống tính bằng cách chạy lại engine như thể phương án được quyết muộn hơn: trước lúc quyết, dây chuyền chạy như không làm gì. Ví dụ trường hợp 3: phải quyết đổi thứ tự chậm nhất 11:20 (kho L-A cạn); sau đó mỗi phút chậm mất 2 sp và thêm 1 phút tăng ca. Quyết sau 14:20 thì đổi thứ tự còn kém hơn không làm gì (vừa đổi sang Y thì lô L-A về lúc 15:00, lại phải đổi về X, mất thêm 40 phút đổi mã); sau khoảng 14:40 thì mất đơn D-101. Phương án nhà cung cấp tách lô cũng có mốc 11:20. Trường hợp 4: phương án A chỉ còn hiệu lực nếu tăng tốc từ 10:00 – phải quyết ngay; phương án B (chỉ tăng ca) quyết lúc nào trong ca cũng như nhau. Màn hình hiển thị đồng hồ đếm ngược để ba bộ phận biết còn bao lâu để thống nhất.

Mốc trên chưa tính thời gian chuẩn bị (gọi nhà cung cấp, điều người, họp thống nhất); thực tế phải quyết sớm hơn mốc một khoảng bằng thời gian đó.

#### 7.4 Tự hiệu chỉnh sau mỗi sự cố

Sau mỗi sự cố, hệ thống so dự đoán với thực tế và cập nhật tham số: hiệu suất thực, phân bố thời gian sửa theo loại lỗi, công suất tối đa và tỷ lệ lỗi khi chạy cao (như trường hợp 6). Sai lệch được báo cáo theo từng loại sự cố – mô hình càng dùng càng sát thực tế.

#### 7.5 Kho tri thức xử lý sự cố

Lưu nhật ký: sự cố, phương án được chọn, kết quả thực tế. Lần sau gặp sự cố tương tự, hệ thống gợi ý "lần trước làm X, cứu được Y sp" và thống kê phương án nào thực sự hiệu quả. Đây là phần Knowledge AI của giải pháp, khớp với chủ đề Predictive & Knowledge AI của cuộc thi.

#### 7.6 Trợ lý hỏi đáp bằng lời

Người dùng hỏi: "Nếu M2 hỏng đến 15 giờ thì đơn khách A có kịp không?". Mô hình ngôn ngữ chỉ dịch câu hỏi thành mẫu nhiễu và dịch kết quả ra lời; engine mới là bên tính số. Cách này tránh rủi ro AI tự bịa con số. Làm sau khi lõi mô phỏng đã ổn định.

#### 7.7 Quy đổi mọi phương án ra tiền

Để so các phương án trên cùng một thước đo: giờ công tăng ca, phạt trễ giao, cước vận chuyển gấp, hao mòn khi chạy cao tải, và điện năng tăng khi máy chạy ở mức tối đa (gắn với dòng chảy Năng lượng trong định hướng nhà máy tương lai của DENSO).

#### 7.8 Tài nguyên dùng chung giữa nhiều line

Người đa kỹ năng, AGV, khuôn, tổ bảo trì phục vụ nhiều line được mô hình hóa thành quan hệ trên bản đồ. Khi điều tài nguyên từ line này sang line khác (trường hợp 5), hệ thống tự kiểm tra tác động lên line cho mượn. Ma trận kỹ năng người vận hành giúp gợi ý điều ai.

#### 7.9 Nhiều sự cố chồng nhau

Dùng mô phỏng theo sự kiện trên cùng bản đồ: mỗi sự cố là một sự kiện có thời điểm bắt đầu và kết thúc; hệ thống xử lý lần lượt theo thời gian thay vì cộng dồn tác động. Đây là điểm yếu đã biết của bản hiện tại (độ chính xác giảm khi nhiều sự cố chồng nhau).

#### 7.10 An toàn khi thiếu dữ liệu

Khi một nguồn dữ liệu bị thiếu hoặc cũ (ví dụ thông số máy gia công bị ghi đè, tồn đệm cập nhật chậm), hệ thống hạ độ tin cậy và hiển thị rõ vùng chưa có dữ liệu thay vì đoán. Bảng dưới cho biết thiếu dữ liệu nào thì mất gì:

| Dữ liệu | Cụ thể | Nếu thiếu |
|---|---|---|
| Cấu trúc dây chuyền | Công đoạn, thứ tự, số máy, công suất chuẩn/tối đa | Bắt buộc |
| Ghi nhận sự cố | Máy, thời điểm bắt đầu, dự kiến bao lâu, người báo | Bắt buộc |
| Tồn đệm | Vị trí, mức hiện tại, tần suất cập nhật | Vẫn tính được sản lượng thiếu, không biết chính xác lúc nào dừng |
| Kế hoạch ca | Số sản phẩm dự kiến mỗi ca | Không quy ra được số sản phẩm thiếu |
| Đơn hàng | Mã đơn, số lượng, hạn giao, khách | Dừng ở mức sản lượng, không nói được đơn nào trễ |
| Khóa nối theo lô/sản phẩm | Sản phẩm/lô đi qua máy nào, giờ nào, lô vật liệu nào | Không truy vết được |
| Lịch sử sửa chữa | Các lần hỏng và thời gian sửa từng máy | Không cảnh báo sớm được, thời gian sửa chỉ là số ước lượng |

### 8. Cơ sở của giải pháp

Mỗi thành phần đều dựa trên nguyên lý hoặc tiền lệ đã có – đây là "cơ sở" để DENSO hình dung khả năng áp dụng vào thực tế.

| Thành phần | Cơ sở |
|---|---|
| Bản đồ đồ thị và chạy thử sự cố | Phương pháp stress test chuỗi cung ứng của GS. David Simchi-Levi (MIT): mô hình đồ thị, điểm là cơ sở sản xuất, cạnh là dòng vật tư; đã triển khai tại Ford để định lượng tác động của sự cố. Giải pháp này đưa cách làm đó xuống cấp dây chuyền, ca và đơn hàng. |
| Thời gian chịu đựng / phục hồi | Hai chỉ số Time-to-Survive và Time-to-Recover của chính phương pháp trên. |
| Lan truyền xuôi và ngược | Nguyên lý sản xuất kinh điển DENSO đang dùng (TPS/TOC): bảo toàn dòng chảy, nút cổ chai quyết định sản lượng, định luật Little, tính nhu cầu linh kiện theo BOM, đường găng cho đơn hàng. |
| Phân loại sự cố theo đại lượng dòng chảy | Nghiên cứu đồ thị tri thức cho kiểm soát nhiễu loạn sản xuất phân loại sự cố theo vật lý nhà máy, nút cổ chai và yếu tố sản xuất; GRASPER (DFKI) biến dữ liệu BOM thành đồ thị tri thức để tìm linh kiện, nhà cung cấp quan trọng. |
| Công suất chuẩn/tối đa, chia tải, tăng ca | Lý thuyết lập lại lịch cho máy song song có thời gian gia công điều chỉnh được (nén được, đổi lại có chi phí); khi máy hỏng, việc được chuyển sang máy khác hoặc dời lại; tăng ca và thuê ngoài là chiến lược phổ biến; mục tiêu gồm thời gian hoàn thành, độ ổn định kế hoạch và chi phí. |
| Ưu tiên bảo trì theo tác động | Nghiên cứu của Chalmers: ưu tiên bảo trì máy ở nút cổ chai làm tăng sản lượng toàn hệ thống, trong khi phần lớn công ty vẫn ưu tiên theo kinh nghiệm, đánh giá mức quan trọng tĩnh và chủ quan. |
| Nút cổ chai thay đổi khi có sự cố | Active Period Method (Roser và cộng sự, 2002); đã có thư viện Python mã nguồn mở. |
| Cảnh báo sớm không cần cảm biến | Phân tích Weibull trên lịch sử phiếu sửa chữa; tham số β cho biết kiểu hỏng (sớm, ngẫu nhiên, do mòn). |
| Truy vết và tri thức sự cố | Đồ thị tri thức sản xuất kết hợp mô hình ngôn ngữ để phân tích nguyên nhân dựa trên FMEA (nghiên cứu arXiv, 10/2025). |
| Phù hợp hạ tầng DENSO | DENSO đã có Factory-IoT Platform kết nối 130 nhà máy về một đám mây; nhà máy tại Việt Nam lưu dữ liệu theo mô hình lakehouse. Giải pháp bổ sung lớp liên kết và tính toán, không đòi hạ tầng mới. Hướng digital twin 3D (ví dụ dự án akaVerse/FPT với DENSO Nhật Bản) mạnh về hình ảnh; giải pháp này là "bản sao logic" tính tác động – hai hướng bổ sung cho nhau. |

Mức độ phù hợp chủ đề: Data Utilization (nối dữ liệu bốn khâu thành nền chung) và Predictive & Knowledge AI (dự báo thời gian sửa, xác suất hỏng, lan truyền; kho tri thức sự cố). Giải pháp mô hình hóa trực tiếp ba trong năm dòng chảy của "nhà máy tương lai" DENSO: Dữ liệu, Hàng hóa, Con người; mục 7.7 mở rộng sang Năng lượng.

### 9. Giả định, giới hạn và câu hỏi cần xác nhận

#### 9.1 Giả định

- Công suất tối đa cho phép của từng máy (~110–120% chuẩn) và giới hạn 6 giờ/ca chạy trên chuẩn là giả định, cần DENSO xác nhận; sẽ chạy phân tích độ nhạy (ví dụ nếu thực tế chỉ 105%).

- Giới hạn tăng ca lấy theo Bộ luật Lao động 2019; cần đối chiếu quy định nội bộ của DENSO.

- Mọi số liệu trong tài liệu là minh họa. Đã chạy lại bằng engine mô phỏng của bản demo (`demo/`, bước 1 phút): các con số khớp, trừ 5 chỗ đã sửa (xem mục 10).

#### 9.2 Giới hạn đã biết

- Hiện chạy trên dữ liệu tự tạo theo cấu trúc quan sát khi tham quan nhà máy; BTC xác nhận giai đoạn này làm ở mức mô phỏng.

- Kiểm chứng trên dữ liệu tự tạo dễ bị coi là "tự chứng minh": bộ sinh dữ liệu cần có cơ chế mà engine không biết trước (thời gian sửa lệch dự kiến, công suất dao động, sự cố phụ), và kết quả cần so với cách tính tay hiện tại.

- Độ chính xác giảm khi nhiều sự cố chồng nhau (hướng xử lý ở mục 7.9).

- Thông số máy ở khâu gia công chưa lấy ra được (nằm trong máy và bị ghi đè).

- Truy vết phụ thuộc dữ liệu có ghi theo lô/sản phẩm qua các khâu hay không.

#### 9.3 Câu hỏi cần hỏi BTC / DENSO

- 4 ví dụ BTC đã đưa ra là gì? (để đối chiếu với các trường hợp ở mục 6)

- BTC hiểu "hai lớp Logic và Nghiệp vụ sản xuất" và chữ "Cause" trong tên đề như thế nào?

- Ba bộ phận hiện mất bao lâu và dùng công cụ gì để tính tay một sự cố? (để có số "hiện tại" đo thật)

- Máy có công suất tối đa được duyệt hay không; quy định tăng ca nội bộ ra sao?

- Dữ liệu ghi theo từng sản phẩm hay theo lô; khóa nào nối giữa các khâu?

### 10. Ghi chú rà soát

Các điểm đã được kiểm tra và chỉnh lại so với các bản nháp trước:

- Thống nhất mô hình ca: các trường hợp dùng chung một ca 08:00–16:00 và tăng ca sau 16:00. Bản nháp trước dùng hai ca ở trường hợp 4 và 5, mâu thuẫn với việc tăng ca ngay sau ca 1 – đã viết lại.

- Tốc độ tăng ca khi máy chưa sửa xong: trường hợp 1 (kịch bản M3 hỏng hẳn) tăng ca chỉ còn 2 máy ở 80 sp/h → khoảng 1,5 giờ, không phải 1 giờ như bản nháp.

- Giới hạn 6 giờ chạy trên chuẩn áp dụng cho mọi máy, kể cả Dập (ảnh hưởng giờ tăng ca ở trường hợp 2).

- Quy ước sản lượng: tính tại công đoạn nút cổ chai; đệm phải được trả về mức mục tiêu nên không tính phần đệm đã dùng là sản lượng cứu được.

- Trường hợp 3: phương án nhà cung cấp gửi trước phải đủ 450 cái (200 cái chỉ kéo dài đến 13:00, vẫn hụt) – đã sửa; bổ sung ngưỡng 16:05.

- Số bộ phận: bảng hành động giữ 3 bộ phận như BTC nêu; Chất lượng & Mua hàng đặt ở phần truy vết như phần mở rộng.

- Trích dẫn BTC: hai bản nháp ghi hai câu trích "nguyên văn" khác nhau – cần lấy lại đúng câu trên website trước khi dùng.

- Số "sửa M3 cứu 200, sửa M7 cứu 40" trong tài liệu cũ là minh họa không cùng dây chuyền với tài liệu này – đã thay bằng ví dụ M2/M5 thống nhất.

Kiểm chứng bằng mô phỏng (bản demo trong `demo/`, mỗi con số có một test). Năm chỗ sửa so với bản tính tay:

- Trường hợp 2: đổi kết luận từ "sửa M2 trước" sang "sửa D1 trước". Sửa M2 trước rút đệm B1 xuống 12 (thiếu 188 so với mục tiêu), nên sau khi trả đệm chỉ còn khoảng 660 sp và cần khoảng 3 giờ tăng ca, so với 792 sp và 1 giờ 45 phút khi sửa D1 trước.
- Trường hợp 2: giờ tăng ca khi sửa M2 trước đổi từ 1 giờ 20 thành khoảng 3 giờ. Bản cũ chỉ bù 112 sp ở Gia công, chưa bù B1.
- Trường hợp 3: ngày mai 950 sp cộng 1 lần đổi mã (≈ 40 sp) = 990 > 960, không vừa một ca. Thêm hai cách xử lý: tăng ca khoảng 40 phút hôm nay, hoặc đổi thứ tự kết hợp tăng tốc.
- Trường hợp 6: tăng ca đổi từ 42 phút thành khoảng 57 phút. Bản cũ trừ kho thành phẩm 30 sp ở đây nhưng không trừ ở mục 5; nay thống nhất không trừ (kho thành phẩm cũng là đệm phải trả về mục tiêu). Thêm kiểm tra chéo: phải đặt gấp 48 L-A.
- Trường hợp 7: mức Đỏ đổi thành Vàng, vì vẫn còn phương án giữ đơn đúng hạn (thuê xe ngoài), đúng theo định nghĩa ở mục 4.5.
- Bổ sung (không đổi con số): trường hợp 4 với kho L-A của dây chuyền này phải đặt gấp 260 L-A thì mới đạt 18:00 / 18:30.
- Quy ước sản lượng áp dụng cho mọi đệm, kể cả kho thành phẩm: phần đệm bị rút dưới mục tiêu không được tính là sản lượng cứu được. Kho thành phẩm vẫn được dùng khi kiểm tra đơn hàng.
- Mục 7.1–7.3 bổ sung số mô phỏng: 7.1 khớp (B2 cần 140 sp khi M2 hỏng); thêm máy tệ nhất M1 → 150 sp và nhận xét đệm dày không giảm giờ tăng ca. 7.2: con số minh họa 87% thay bằng kết quả mô phỏng 42% đủ kế hoạch trong ca (kế hoạch kín 100% công suất chuẩn). 7.3 khớp (trường hợp 3: 11:20, 2 sp/phút; trường hợp 4: 10:00); thêm mốc 14:20 / 14:40 của trường hợp 3.

### Nguồn tham khảo

- Báo Tin tức – DENSO Factory Hacks 2026: baotintuc.vn/co-hoi-de-sinh-vien-viet-nam-ung-dung-ai-robot-du-lieu-chinh-phuc-bai-toan-san-xuat-post1257511.html

- MIT Data Science Lab – Impact on Practice (Ford): dsl.mit.edu/?p=123

- Databricks – Stress testing supply chain networks at scale: databricks.com/en/blog/stress-testing-supply-chain-networks-scale-databricks

- Knowledge graph enhanced disturbance control in manufacturing systems: pure.bit.edu.cn

- DFKI – GRASPER: dfki.de/web/forschung/projekte-publikationen/publikation/15306

- MIT – Assessing the Impact of Changes and their Knock-on Effects in Manufacturing Systems: dspace.mit.edu/handle/1721.1/115508

- Bilkent – Rescheduling parallel machines with controllable processing times: repository.bilkent.edu.tr

- KAIST – Rescheduling of unrelated parallel machines under forecasted machine breakdown: dspace.kaist.ac.kr/handle/10203/287552

- Fabrication runtime decision with probabilistic breakdowns, scrap and overtime: researchwith.montclair.edu

- Chalmers – Data-Driven Decision Support for Maintenance Prioritisation: research.chalmers.se/publication/504263

- Chalmers – Diagnosing throughput bottlenecks from a maintenance perspective: research.chalmers.se/publication/520068

- Roser et al. – Detecting Shifting Bottlenecks (2002): allaboutlean.com; thư viện pypi.org/project/active-period-method

- Weibull analysis for maintenance: fabrico.io/blog/weibull

- FMEA knowledge graph with LLM (arXiv 2510.15428): arxiv.org/abs/2510.15428

- DENSO Factory-IoT Platform linking 130 factories: nasdaq.com (press release 05/10/2020)

- akaVerse (FPT IS) x DENSO Japan digital twin: fpt-is.com

- Bộ luật Lao động 2019, Điều 107 – Làm thêm giờ
