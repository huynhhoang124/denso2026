"""Diễn tập đầu ca (IDEA.md mục 7.1–7.2): bản đồ rủi ro, mức đệm đề xuất, xác suất hoàn thành kế hoạch.

Số tài liệu chỉ có ở mục 7.1 (B2 khi M2 hỏng → 140 sp, thêm ~80 sp tồn); phần còn lại là tính chất của engine.
"""
import copy
import random
from functools import lru_cache

import pytest

from engine import (DayChuyen, ban_do_rui_ro, de_xuat_muc_dem, lech_sua, muc_dem_toi_thieu, sinh_rui_ro,
                    xac_suat_hoan_thanh)

dc = DayChuyen.tai()


@lru_cache(maxsize=None)
def ban_do():
    return ban_do_rui_ro(dc)


@lru_cache(maxsize=None)
def dem():
    return de_xuat_muc_dem(dc).set_index("Đệm")


def _khong_rui_ro() -> DayChuyen:
    cfg = copy.deepcopy(dc.cfg)
    for c in cfg["cong_doan"]:
        for m in c["may"]:
            m["hong_trong_ca"] = 0.0
    cfg["dung_ngan"]["xac_suat_moi_may"] = 0.0
    return DayChuyen(cfg)


# ---------------------------------------------------------------- 7.1 mức đệm (số tài liệu)
def test_7_1_thoi_gian_sua_muc_80_phan_tram_la_du_kien_cong_1_gio():
    assert lech_sua(dc) == 1


def test_7_1_dem_B2_khi_M2_hong_can_140_sp():
    x = muc_dem_toi_thieu(dc, "B2", "M2")
    assert x["hut"] == pytest.approx(28)
    assert x["sua_gio"] == 5
    assert x["can"] == pytest.approx(140)


def test_7_1_dem_B2_them_khoang_80_sp_ton_so_voi_60_hien_tai():
    assert muc_dem_toi_thieu(dc, "B2", "M2")["can"] - dc.dem["B2"]["muc_tieu"] == pytest.approx(80)


def test_de_xuat_lay_may_te_nhat_va_khong_vuot_suc_chua():
    b2 = dem().loc["Đệm B2"]
    assert b2["Máy tệ nhất phía trước"] == "M1"           # M1 có công suất tối đa lớn nhất → hỏng thì hụt nhiều nhất
    assert b2["Đề xuất"] == min(150, 30 * 5) == b2["Sức chứa"]


def test_dem_day_hon_giu_cuoi_chuyen_khong_doi_hang_nhung_khong_giam_tang_ca():
    # Đệm dày → Lắp ráp ra đủ 960 lúc 16:00; nhưng phần đệm đã dùng vẫn phải bù về mục tiêu (quy ước mục 10)
    b2 = dem().loc["Đệm B2"]
    assert b2["Lắp ráp ra 16:00 – hiện tại"] < b2["Lắp ráp ra 16:00 – đề xuất"] == dc.ke_hoach
    assert b2["Tăng ca cần – đề xuất (phút)"] == b2["Tăng ca cần – hiện tại (phút)"]


# ---------------------------------------------------------------- 7.1 bản đồ rủi ro
def test_ban_do_rui_ro_co_moi_may_mot_dong_xep_theo_rui_ro():
    bd = ban_do()
    assert sorted(bd["Máy"]) == sorted(dc.may)
    assert list(bd["Ưu tiên"]) == list(range(1, len(dc.may) + 1))
    assert bd["Rủi ro (sp)"].is_monotonic_decreasing


def test_rui_ro_bang_xac_suat_nhan_so_san_pham_mat():
    for _, r in ban_do().iterrows():
        assert r["Rủi ro (sp)"] == pytest.approx(r["Xác suất hỏng trong ca"] * r["Mất nếu hỏng (sp)"], abs=0.1)


def test_cong_doan_khong_co_may_du_phong_mat_nhieu_nhat():
    bd = ban_do().set_index("Máy")
    assert bd["Mất nếu hỏng (sp)"].idxmax() == "LR-1"


def test_may_de_hong_hon_chua_chac_phai_lo_truoc():
    # mục 4.6: M3 (máy cũ) hỏng nhiều gấp đôi M1, M2 nhưng mất ít hơn nếu hỏng
    bd = ban_do().set_index("Máy")
    assert bd.loc["M3", "Mất nếu hỏng (sp)"] < bd.loc["M1", "Mất nếu hỏng (sp)"]
    assert bd.loc["M3", "Xác suất hỏng trong ca"] > bd.loc["M1", "Xác suất hỏng trong ca"]


# ---------------------------------------------------------------- 7.2 xác suất hoàn thành kế hoạch
def test_sinh_rui_ro_trong_ca_va_theo_mau_nhieu_chung():
    rnd = random.Random(1)
    for _ in range(200):
        for n in sinh_rui_ro(dc, rnd):
            assert n.dai_luong == "nang_luc" and n.thay_doi == -100 and n.diem in dc.may
            assert 0 <= n.t0 < dc.ca
            assert n.thoi_luong_gio >= (0.5 if n.mo_ta.endswith("hỏng") else 5 / 60)


def test_khong_co_rui_ro_thi_chac_chan_hoan_thanh():
    r = xac_suat_hoan_thanh(_khong_rui_ro(), so_lan=20)
    assert r["p_trong_ca"] == 1 and r["dang_ky_tang_ca"] == 0 and r["p_don_hom_nay"] == 1


def test_cung_seed_cung_ket_qua():
    a, b = xac_suat_hoan_thanh(dc, so_lan=40, seed=3), xac_suat_hoan_thanh(dc, so_lan=40, seed=3)
    assert a["p_trong_ca"] == b["p_trong_ca"] and a["dang_ky_tang_ca"] == b["dang_ky_tang_ca"]


def test_rui_ro_cao_hon_thi_xac_suat_hoan_thanh_thap_hon():
    cfg = copy.deepcopy(dc.cfg)
    for c in cfg["cong_doan"]:
        for m in c["may"]:
            m["hong_trong_ca"] = min(1.0, m["hong_trong_ca"] * 5)
    cao = xac_suat_hoan_thanh(DayChuyen(cfg), so_lan=80, seed=5)
    thuong = xac_suat_hoan_thanh(dc, so_lan=80, seed=5)
    assert cao["p_trong_ca"] < thuong["p_trong_ca"]
    assert (cao["dang_ky_tang_ca"] or 10 ** 6) > thuong["dang_ky_tang_ca"]


def test_xac_suat_hop_le_va_muc_dang_ky_80_phan_tram():
    r = xac_suat_hoan_thanh(dc, so_lan=60)
    for k in ("p_trong_ca", "p_trong_gioi_han", "p_don_hom_nay"):
        assert 0 <= r[k] <= 1
    tc = r["bang"]["Tăng ca cần (phút)"].fillna(10 ** 6)
    assert (tc <= r["dang_ky_tang_ca"]).mean() >= r["muc_dang_ky"]
