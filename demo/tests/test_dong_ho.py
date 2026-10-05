"""Đồng hồ quyết định (IDEA.md mục 7.3): mỗi phương án phải quyết muộn nhất lúc nào.

Số tài liệu: TH3 phải quyết đổi thứ tự trước 11:20 (kho L-A cạn), sau đó mỗi phút chậm mất 2 sp;
TH4 phương án A chỉ còn hiệu lực nếu tăng tốc từ 10:00.
"""
from functools import lru_cache

import pandas as pd
import pytest

from engine import DayChuyen, dong_ho_quyet_dinh, phut, quyet_luc
from scenarios import chay

PHUT = 2    # dung sai thời gian (phút)

dc = DayChuyen.tai()


@lru_cache(maxsize=None)
def kb(ma):
    return chay(ma, dc)[0]


@lru_cache(maxsize=None)
def dong_ho(ma):
    return dong_ho_quyet_dinh(dc, kb(ma)).set_index("Phương án")


def hang(ma, ten_dau):
    df = dong_ho(ma)
    return df.loc[next(t for t in df.index if t.startswith(ten_dau))]


# ---------------------------------------------------------------- số tài liệu
def test_th3_doi_thu_tu_phai_quyet_truoc_11h20():
    assert hang("th3", "Đổi thứ tự sản xuất")["Muộn nhất không mất gì"] == pytest.approx(phut("11:20"), abs=PHUT)


def test_th3_doi_thu_tu_moi_phut_cham_mat_2_sp():
    assert hang("th3", "Đổi thứ tự sản xuất")["Mỗi phút chậm mất (sp)"] == pytest.approx(2, abs=0.2)


def test_th3_ncc_tach_lo_cung_moc_11h20():
    assert hang("th3", "NCC tách lô")["Muộn nhất không mất gì"] == pytest.approx(phut("11:20"), abs=PHUT)


def test_th4_phuong_an_a_phai_quyet_ngay_10h00():
    r = hang("th4", "A:")
    assert r["Phát hiện lúc"] == phut("10:00")
    assert r["Muộn nhất không mất gì"] == pytest.approx(phut("10:00"), abs=PHUT)


# ---------------------------------------------------------------- tính chất của cách tính
def test_quyet_ngay_tu_dau_ca_trung_danh_gia_goc():
    """tu = 0 nghĩa là áp dụng từ đầu – phải ra đúng kết quả của bảng phương án."""
    for r in kb("th3").phuong_an:
        x = quyet_luc(dc, r["kq"].nhieu, r["pa"], 0)
        assert x["san_luong"] == pytest.approx(r["san_luong"], abs=0.01)
        assert x["tang_ca_de_xuat"] == r["tang_ca_de_xuat"]


def test_quyet_luc_phat_hien_trung_bang_phuong_an():
    """Trước lúc phát hiện chưa có sự cố nên chạy như kế hoạch: quyết ngay lúc phát hiện = bảng phương án."""
    for ma in ("goc", "th3", "th4"):
        for r in kb(ma).phuong_an:
            if r["pa"].bac == 0:
                continue
            t_inc = min(n.t0 for n in r["kq"].nhieu)
            assert quyet_luc(dc, r["kq"].nhieu, r["pa"], t_inc)["san_luong"] == pytest.approx(r["san_luong"], abs=0.01)


def test_hanh_dong_truoc_luc_quyet_bi_doi_toi_luc_quyet():
    """TH3 tách lô: 450 L-A lẽ ra về 11:00; quyết lúc 12:00 thì về 12:00 → Lắp ráp đói L-A 11:20–12:00."""
    r = next(r for r in kb("th3").phuong_an if r["pa"].ten.startswith("NCC tách lô"))
    x = quyet_luc(dc, r["kq"].nhieu, r["pa"], phut("12:00"))
    lr = x["kq"].trang_thai["LR"]
    assert lr[phut("11:30")] == "thiếu linh kiện"
    assert lr[phut("12:05")] != "thiếu linh kiện"


def test_quyet_cang_muon_cang_mat():
    for ma, ten in (("th3", "Đổi thứ tự sản xuất"), ("goc", "Chia tải + tăng tốc")):
        r = hang(ma, ten)
        assert r["Mỗi phút chậm mất (sp)"] > 0
        assert r["Muộn nhất không mất gì"] >= r["Phát hiện lúc"]


def test_doi_thu_tu_qua_muon_hai_hon_loi():
    """TH3: quyết đổi thứ tự sau ~14:40 thì vừa đổi sang Y lại phải đổi về X khi lô 15:00 về → cần > 4 giờ tăng ca."""
    r = hang("th3", "Đổi thứ tự sản xuất")
    assert phut("14:00") <= r["Hết hiệu lực (giữ đơn)"] < phut("15:00")


def test_phuong_an_khong_kha_thi_khong_co_moc():
    r = hang("th5", "B:")
    assert "không khả thi" in r["Ghi chú"]
    assert pd.isna(r["Muộn nhất không mất gì"])


def test_quyet_luc_nao_cung_nhu_nhau():
    r = hang("th4", "B:")
    assert r["Muộn nhất không mất gì"] == dc.ca
    assert "như nhau" in r["Ghi chú"]


def test_th7_chi_giao_hang_khong_co_dong_ho_san_xuat():
    assert dong_ho("th7").empty
