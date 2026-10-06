"""Mỗi assert ứng với một con số trong IDEA.md (mục 5–6).

Con số trong tài liệu ban đầu là tính tay. Năm chỗ mô phỏng ra khác (TH2 ×2, TH3, TH6, TH7) KHÔNG sửa engine
cho khớp mà sửa IDEA.md (xem mục 10); các test đó nay kiểm số mới, lý do lệch ghi ở comment "Đã sửa trong IDEA.md".
"""
from functools import lru_cache

import pytest

from engine import ChinhSach, DayChuyen, Nhieu, gio, mo_phong, phut
from scenarios import chay, truy_vet_th6

SL = 2      # dung sai sản lượng (sp) do bước thời gian 1 phút
PHUT = 2    # dung sai thời gian (phút)

dc = DayChuyen.tai()
M2_HONG = [Nhieu("M2", "nang_luc", -100, "10:00", 4)]


@lru_cache(maxsize=None)
def kb(ma):
    return chay(ma, dc)


def pa(ma, ten_dau):
    return next(r for r in kb(ma)[0].phuong_an if r["pa"].ten.startswith(ten_dau))


# ---------------------------------------------------------------- Ví dụ gốc (mục 5)
def test_goc_khong_lam_gi_800():
    assert mo_phong(dc, M2_HONG, ChinhSach(muc=0)).san_luong() == pytest.approx(800, abs=SL)


def test_goc_chia_tai_tang_toc_884():
    assert mo_phong(dc, M2_HONG, ChinhSach(muc=2)).san_luong() == pytest.approx(884, abs=SL)


def test_goc_tang_ca_khoang_38_phut():
    assert mo_phong(dc, M2_HONG, ChinhSach(muc=2)).tang_ca_can() == pytest.approx(38, abs=PHUT)


@pytest.mark.parametrize("gio_sua, ky_vong", [(3, 930), (4, 884), (5, 838), (6, 792)])
def test_goc_san_luong_theo_thoi_gian_sua(gio_sua, ky_vong):
    q = kb("goc")[0].quet_sua.set_index("Sửa xong sau (giờ)")
    assert q.loc[gio_sua, "Sản lượng ca"] == pytest.approx(ky_vong, abs=SL)


@pytest.mark.parametrize("gio_sua, ky_vong", [(3, 15), (4, 38), (5, 61), (6, 84)])
def test_goc_tang_ca_theo_thoi_gian_sua(gio_sua, ky_vong):
    q = kb("goc")[0].quet_sua.set_index("Sửa xong sau (giờ)")
    assert q.loc[gio_sua, "Tăng ca (phút)"] == pytest.approx(ky_vong, abs=PHUT)


# ---------------------------------------------------------------- TH1
def test_th1_chia_tai_m1_46_m2_44():
    kq = mo_phong(dc, [Nhieu("M3", "nang_luc", -25, "09:00")], ChinhSach(muc=1))
    t = phut("10:00")
    assert round(kq.toc_do["M1"][t]) == 46
    assert round(kq.toc_do["M2"][t]) == 44


def test_th1_thieu_10_kho_bu():
    kq = mo_phong(dc, [Nhieu("M3", "nang_luc", -25, "09:00")], ChinhSach(muc=1))
    assert kq.thieu() == pytest.approx(10, abs=SL)


def test_th1_muc_xanh():
    assert kb("th1")[0].muc == "Xanh"


def test_th1_m3_hong_han_luc_12h_con_842():
    x = kb("th1")[0].xau
    assert gio(x["nhieu"].t0) == "12:00"
    assert x["san_luong"] == pytest.approx(842, abs=SL)


def test_th1_m3_hong_han_tang_ca_khoang_1_5_gio():
    assert kb("th1")[0].xau["tang_ca"] == pytest.approx(90, abs=5)


# ---------------------------------------------------------------- TH2
def _thu_tu(ten):
    df = kb("th2")[0].thu_tu_sua
    return df[df["Thứ tự sửa"] == ten].iloc[0]


def test_th2_sua_m2_truoc_848():
    assert _thu_tu("M2 → D1")["Sản lượng Gia công 16:00"] == pytest.approx(848, abs=SL)


def test_th2_sua_d1_truoc_792():
    assert _thu_tu("D1 → M2")["Sản lượng Gia công 16:00"] == pytest.approx(792, abs=SL)


def test_th2_dem_b1_luc_16h_12_va_218():
    assert _thu_tu("M2 → D1")["B1 lúc 16:00"] == pytest.approx(12, abs=SL)
    assert _thu_tu("D1 → M2")["B1 lúc 16:00"] == pytest.approx(218, abs=SL)


# Đã sửa trong IDEA.md (bản tính tay chọn M2 trước): sửa M2 trước cho Gia công 848 nhưng rút B1 từ 200 xuống 12;
# theo quy ước "đệm phải trả về mức mục tiêu" sản lượng hiệu dụng chỉ còn ~660 (D1 trước: 792) và cần ~180 phút
# tăng ca để đủ kế hoạch + trả đệm (D1 trước: ~104 phút). Dây chuyền cân bằng (mọi công đoạn chuẩn 120):
# D1 hỏng làm Dập hụt 50 sp/h, còn M2 hỏng làm Gia công chỉ hụt 28 sp/h.
def test_th2_san_luong_hieu_dung_sau_tra_dem_660_va_792():
    assert _thu_tu("M2 → D1")["Sản lượng hiệu dụng 16:00"] == pytest.approx(660, abs=SL)
    assert _thu_tu("D1 → M2")["Sản lượng hiệu dụng 16:00"] == pytest.approx(792, abs=SL)


def test_th2_he_thong_chon_sua_d1_truoc():
    assert kb("th2")[0].thu_tu_sua.iloc[0]["Thứ tự sửa"].startswith("D1")


# Đã sửa trong IDEA.md (bản tính tay: 1 giờ 20 – chỉ bù 112 sp ở Gia công, chưa trả B1 thiếu 188 về mục tiêu).
def test_th2_sua_m2_truoc_tang_ca_khoang_3_gio():
    assert _thu_tu("M2 → D1")["Tăng ca để đủ kế hoạch + trả đệm (phút)"] == pytest.approx(180, abs=5)


def test_th2_sua_d1_truoc_tang_ca_1_gio_45():
    assert _thu_tu("D1 → M2")["Tăng ca để đủ kế hoạch + trả đệm (phút)"] == pytest.approx(105, abs=PHUT)


# ---------------------------------------------------------------- TH3
TH3 = [Nhieu("L-A", "nguon_cung", -100, "10:00", 5)]


def test_th3_khong_lam_gi_mat_440():
    assert mo_phong(dc, TH3, ChinhSach(muc=0)).thieu() == pytest.approx(440, abs=SL)


def test_th3_doi_thu_tu_chi_mat_80():
    kq = mo_phong(dc, TH3, ChinhSach(muc=1, doi_thu_tu=True))
    assert kq.thieu() == pytest.approx(80, abs=SL)
    assert kq.cum_sp["X"][dc.ca] == pytest.approx(480, abs=SL)
    assert kq.cum_sp["Y"][dc.ca] == pytest.approx(400, abs=SL)


def _lan_dau(ds, dk):
    return next(t for t, v in enumerate(ds) if dk(v))


@pytest.mark.parametrize("moc, ky_vong", [("L-A cạn", "11:20"), ("B2 đầy", "12:05"), ("B1 đầy", "12:55")])
def test_th3_dong_thoi_gian(moc, ky_vong):
    kq = mo_phong(dc, TH3, ChinhSach(muc=0))
    t = {"L-A cạn": _lan_dau(kq.lk["L-A"], lambda v: v <= 1e-6),
         "B2 đầy": _lan_dau(kq.dem["B2"], lambda v: v >= 150 - 1e-6),
         "B1 đầy": _lan_dau(kq.dem["B1"], lambda v: v >= 300 - 1e-6)}[moc]
    assert t == pytest.approx(phut(ky_vong), abs=PHUT)


def test_th3_nguong_lo_ve_truoc_16h05():
    assert kb("th3")[1]["nguong_lo"] == pytest.approx(phut("16:05"), abs=PHUT)


# Đã sửa trong IDEA.md (bản tính tay: ngày mai 450 X + 500 Y = 950 sp "vừa một ca"): làm 2 mã cần 1 lần đổi mã
# 20 phút (≈ 40 sp) → 990 > 960 → đổi thứ tự cần ~40 phút tăng ca hôm nay; kết hợp tăng tốc thì không cần.
def test_th3_doi_thu_tu_tang_ca_khoang_40_phut():
    assert pa("th3", "Đổi thứ tự sản xuất")["tang_ca_de_xuat"] == pytest.approx(40, abs=PHUT)


def test_th3_doi_thu_tu_ket_hop_tang_toc_khong_can_tang_ca():
    assert pa("th3", "Đổi thứ tự + tăng tốc")["tang_ca_de_xuat"] == 0


def test_th3_muc_vang():
    assert kb("th3")[0].muc == "Vàng"


# ---------------------------------------------------------------- TH4
def _gio_xong_don_c(ten):
    r = pa("th4", ten)
    return r["kq"].gio_dat(r["kq"].ke_hoach_tong)


def test_th4_phuong_an_A_xong_18h():
    assert _gio_xong_don_c("A:") == pytest.approx(phut("18:00"), abs=PHUT)


def test_th4_phuong_an_B_xong_18h30():
    assert _gio_xong_don_c("B:") == pytest.approx(phut("18:30"), abs=PHUT)


def test_th4_kiem_tra_cheo_phat_hien_thieu_linh_kien_LA():
    # tài liệu: "đơn C cần thêm 300 L-A; nếu kho không đủ, sự cố này tự sinh ra trường hợp 3"
    assert "Đặt gấp 260 L-A" in pa("th4", "A:")["ghi_chu"]


# ---------------------------------------------------------------- TH5
def test_th5_khong_lam_gi_640():
    assert pa("th5", "Không làm gì")["san_luong"] == pytest.approx(640, abs=SL)


def test_th5_A_760_tang_ca_2_gio():
    r = pa("th5", "A:")
    assert r["san_luong"] == pytest.approx(760, abs=SL)
    assert r["tang_ca_de_xuat"] == pytest.approx(120, abs=PHUT)


def test_th5_B_880_tang_ca_40_phut():
    r = pa("th5", "B:")
    assert r["san_luong"] == pytest.approx(880, abs=SL)
    assert r["tang_ca_ke_hoach"] == pytest.approx(40, abs=PHUT)


def test_th5_B_chi_chon_khi_line_2_du_nang_luc():
    assert not pa("th5", "B:")["pa"].kha_thi
    assert kb("th5")[0].de_xuat["pa"].ten.startswith("A:")


def test_th5_co_hoi_bao_tri_08_10_gia_cong_chi_can_2_may():
    w = kb("th5")[0].bao_tri[0]
    assert (w["cong_doan"], gio(w["tu"]), gio(w["den"]), w["so_may_can"]) == ("GC", "08:00", "10:00", 2)


# ---------------------------------------------------------------- TH6
def test_th6_khoanh_vung_88_sp():
    assert truy_vet_th6()["so_giu"] == 88


def test_th6_ca_lo_S77_khoang_600_va_mau_khong_loi():
    tv = truy_vet_th6()
    assert len(tv["gia_thuyet"][0]["nhom"]) == 600
    assert tv["kiem_mau"]["so_loi"] == 0
    assert tv["chung"]["may_gia_cong"] == "M3" and tv["chung"]["lo_thep"] == "S-77"


def test_th6_m3_dung_1_gio_thieu_them_26():
    assert pa("th6", "Chia tải")["san_luong"] == pytest.approx(960 - 88 - 26, abs=SL)


# Đã sửa trong IDEA.md (bản tính tay: 42 phút – trừ 30 sp kho thành phẩm ở TH6 nhưng không trừ ở mục 5).
# Một quy ước cho mọi trường hợp: kho TP cũng là đệm phải trả về mục tiêu → 114 sp → ~57 phút; có tăng tốc ~48 phút.
def test_th6_tang_ca_chia_tai_khoang_57_phut():
    assert pa("th6", "Chia tải")["tang_ca_ke_hoach"] == pytest.approx(57, abs=PHUT)


def test_th6_tang_ca_tang_toc_khoang_48_phut():
    assert pa("th6", "Chia tải + tăng tốc")["tang_ca_ke_hoach"] == pytest.approx(48, abs=PHUT)


# ---------------------------------------------------------------- TH7
def test_th7_hang_den_khach_20h30_tre_1_5_gio():
    g = kb("th7")[0].giao_hang
    assert gio(g["gio_den"]) == "20:30"
    assert g["tre"] == 90


# Đã sửa trong IDEA.md (bản tính tay ghi Đỏ): còn phương án giữ đơn đúng hạn (thuê xe ngoài đến 18:30) nên theo
# định nghĩa mục 4.5 ("Đỏ = có đơn trễ dù đã dùng hết các bước") là Vàng – kiểm ở test_muc_canh_bao bên dưới.


# ---------------------------------------------------------------- mức cảnh báo (bảng tổng hợp mục 6)
@pytest.mark.parametrize("ma, muc", [("goc", "Vàng"), ("th1", "Xanh"), ("th2", "Vàng"), ("th3", "Vàng"),
                                     ("th4", "Vàng"), ("th5", "Vàng"), ("th6", "Vàng"),
                                     ("th7", "Vàng")])
def test_muc_canh_bao(ma, muc):
    assert kb(ma)[0].muc == muc


# ---------------------------------------------------------------- tính chất chung của engine
def test_ke_hoach_khong_su_co_du_960_khong_tang_ca():
    kq = mo_phong(dc, [], ChinhSach(muc=1))
    assert kq.san_luong() == pytest.approx(960, abs=0.5) and kq.tang_ca_can() == 0


def test_lan_nguoc_cong_doan_truoc_bi_chan():
    kq = mo_phong(dc, TH3, ChinhSach(muc=0))
    assert "bị chặn" in kq.trang_thai["GC"] and "bị chặn" in kq.trang_thai["DAP"]


def test_lan_xuoi_cong_doan_sau_doi_hang():
    kq = mo_phong(dc, M2_HONG, ChinhSach(muc=0))
    assert "đói hàng" in kq.trang_thai["LR"]


def test_gioi_han_6_gio_tren_chuan():
    kq = mo_phong(dc, M2_HONG, ChinhSach(muc=2))
    assert max(kq.tren_chuan.values()) <= 6 * 60


def test_th7_de_xuat_giao_hang_thue_xe_ngoai_va_bao_giao_hang():
    pt = kb("th7")[0]
    assert pt.giao_hang["de_xuat"]["Phương án"].startswith("Thuê xe ngoài")
    assert "Giao hàng & Sales" in pt.gui_cho
    assert pt.thong_diep["Giao hàng & Sales"][0].startswith("Đề xuất giao hàng: **Thuê xe ngoài")


@pytest.mark.parametrize("ma", ["goc", "th1", "th2", "th3", "th4", "th5", "th6", "th7"])
def test_giai_thich_khop_phuong_an_de_xuat(ma):
    from engine import giai_thich_de_xuat
    pt = kb(ma)[0]
    g = giai_thich_de_xuat(dc, pt)
    ten = pt.giao_hang["de_xuat"]["Phương án"] if ma == "th7" else pt.de_xuat["pa"].ten
    assert g["ten"] == ten and g["vi_sao"] and g["toi_uu"]
    assert all(t != ten for t, _ in g["loai"])  # phương án được chọn không nằm trong danh sách bị loại
