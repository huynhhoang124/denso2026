"""Đồng hồ quyết định (IDEA.md mục 7.3): mỗi assert ứng với một con số trong tài liệu."""
from functools import lru_cache

import pytest

from engine import DayChuyen, dong_ho_quyet_dinh, phut
from scenarios import chay

PHUT = 2    # dung sai thời gian (phút)

dc = DayChuyen.tai()


@lru_cache(maxsize=None)
def dong_ho(ma):
    return dong_ho_quyet_dinh(dc, chay(ma, dc)[0])


def hang(ma, ten_dau):
    d = dong_ho(ma)
    return d[d["Phương án"].str.startswith(ten_dau)].iloc[0]


def test_th3_doi_thu_tu_phai_quyet_truoc_1120():
    # "phải quyết đổi thứ tự trước 11:20 (kho L-A cạn)"
    assert hang("th3", "Đổi thứ tự sản xuất")["_moc"] == pytest.approx(phut("11:20"), abs=PHUT)


def test_th3_doi_thu_tu_moi_phut_cham_mat_2_sp():
    # "sau đó mỗi phút chậm mất 2 sp"
    assert hang("th3", "Đổi thứ tự sản xuất")["Mỗi phút chậm mất (sp)"] == pytest.approx(2, abs=0.3)


def test_th3_ncc_tach_lo_cung_moc_1120():
    assert hang("th3", "NCC tách lô")["_moc"] == pytest.approx(phut("11:20"), abs=PHUT)


def test_th4_phuong_an_a_phai_quyet_ngay_tu_1000():
    # "phương án A chỉ còn hiệu lực nếu tăng tốc từ 10:00"
    assert hang("th4", "A:")["_moc"] == pytest.approx(phut("10:00"), abs=PHUT)


def test_quyet_muon_khong_bao_gio_tot_hon():
    for ma in ("goc", "th3", "th4"):
        for _, r in dong_ho(ma).iterrows():
            if r["_moc"] is not None:
                assert r["_t_inc"] <= r["_moc"] <= dc.ca


def test_phuong_an_khong_kha_thi_duoc_ghi_ro():
    assert hang("th5", "B:")["Muộn nhất không mất gì"] == "không khả thi"
