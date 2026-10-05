"""8 kịch bản có sẵn (ví dụ gốc mục 5 + 7 trường hợp mục 6) và bảng phả hệ tự tạo cho TH6.

Mỗi kịch bản chỉ là một danh sách nhiễu theo mẫu chung (+ vài phương án riêng của tình huống).
Cả 8 kịch bản dùng chung một dây chuyền (config.yaml) và một engine.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace
from fractions import Fraction

import pandas as pd

from engine import (ChinhSach, DayChuyen, Nhieu, PhanTich, PhuongAn, gio, nguong_nguon_cung, phan_tich,
                    truy_vet_nguoc)


@dataclass
class KichBan:
    ma: str
    ten: str
    tinh_huong: str
    nhieu: list[Nhieu]
    phuong_an_them: list[PhuongAn] = field(default_factory=list)
    bo_chung: bool = False
    tai_lieu: str = ""  # con số kỳ vọng trong IDEA.md, để đối chiếu trên giao diện


# ---------------------------------------------------------------- TH6: bảng phả hệ tự tạo
def tao_pha_he(seed: int = 7) -> pd.DataFrame:
    """Phả hệ Gia công 08:00–14:00: mỗi dòng là 1 sản phẩm, đã qua máy nào, giờ nào, lô thép nào.

    Dữ liệu tự tạo: 10:00–12:00 M1, M2 thay dao luân phiên (38 sp/h), M3 chạy tối đa 44 sp/h để bù.
    Cơ chế lỗi ẩn (engine không biết): chỉ M3 khi chạy 44 sp/h mới sinh lỗi kích thước lỗ.
    """
    rnd = random.Random(seed)
    toc = {"M1": 40, "M2": 40, "M3": 40}
    dong, tich = [], {m: Fraction(0) for m in toc}
    nguoi = {"M1": "NV-11", "M2": "NV-12", "M3": "NV-13"}
    so = 0
    for t in range(6 * 60):
        cao_diem = 120 <= t < 240
        for m in toc:
            v = (38 if m != "M3" else 44) if cao_diem else 40
            truoc = tich[m]
            tich[m] += Fraction(v, 60)
            for _ in range(int(tich[m]) - int(truoc)):
                so += 1
                lo = "S-76" if t < 60 else "S-77"
                dong.append({
                    "ma_sp": f"SP{so:04d}", "phut": t, "gio": gio(t), "may_gia_cong": m, "toc_do_may": v,
                    "lo_thep": lo, "nha_cung_cap": "NCC-Y" if lo == "S-76" else "NCC-Z",
                    "may_dap": rnd.choice(["D1", "D2"]), "ca": "Ca 1", "nguoi_van_hanh": nguoi[m],
                    "loi_an": m == "M3" and v == 44 and rnd.random() < 0.15,
                })
    df = pd.DataFrame(dong)
    # Kiểm tra cuối phát hiện 5 sp lỗi (lúc 14:00)
    loi = df[df["loi_an"]].sample(5, random_state=seed)["ma_sp"].tolist()
    df["phat_hien_loi"] = df["ma_sp"].isin(loi)
    return df


def kiem_mau(nhom: pd.DataFrame, n: int = 20, seed: int = 1) -> int:
    """Lấy mẫu n sp trong nhóm và kiểm tra lại (dùng cơ chế lỗi ẩn của dữ liệu tự tạo)."""
    if nhom.empty:
        return 0
    return int(nhom.sample(min(n, len(nhom)), random_state=seed)["loi_an"].sum())


def truy_vet_th6(pha_he: pd.DataFrame | None = None) -> dict:
    pha_he = tao_pha_he() if pha_he is None else pha_he
    loi = pha_he.loc[pha_he["phat_hien_loi"], "ma_sp"].tolist()
    return truy_vet_nguoc(pha_he, loi, kiem_mau)


# ---------------------------------------------------------------- 8 kịch bản
def kich_ban() -> dict[str, KichBan]:
    ds = [
        KichBan(
            "goc", "Ví dụ gốc: M2 hỏng 4 giờ",
            "Gia công có 3 máy song song. M2 hỏng lúc 10:00, Bảo trì dự kiến sửa 4 giờ (xong 14:00).",
            [Nhieu("M2", "nang_luc", -100, "10:00", 4, mo_ta="M2 hỏng")],
            tai_lieu="Không làm gì 800 sp; chia tải + tăng tốc 884 sp; tăng ca ~38 phút; "
                     "sửa 3/4/5/6 giờ → 930/884/838/792 sp; mức Vàng.",
        ),
        KichBan(
            "th1", "TH1: Máy chạy chậm (M3 40 → 30 sp/h)",
            "09:00, M3 tụt từ 40 xuống 30 sp/h, chưa rõ nguyên nhân.",
            [Nhieu("M3", "nang_luc", -25, "09:00", None, mo_ta="M3 chạy chậm")],
            tai_lieu="Chia tải: M1 ≈ 46, M2 ≈ 44 sp/h; thiếu 10 sp, kho TP bù → Xanh. "
                     "Nếu M3 hỏng hẳn 12:00: 842 sp, tăng ca ~1,5 giờ.",
        ),
        KichBan(
            "th2", "TH2: Hai máy hỏng, một tổ bảo trì",
            "10:00, M2 (Gia công) hỏng cần 4 giờ sửa; cùng lúc D1 (Dập) hỏng cần 3 giờ. Chỉ có một tổ bảo trì.",
            [Nhieu("M2", "nang_luc", -100, "10:00", 4, mo_ta="M2 hỏng"),
             Nhieu("D1", "nang_luc", -100, "10:00", 3, mo_ta="D1 hỏng")],
            tai_lieu="Gia công lúc 16:00: sửa M2 trước 848 sp (B1 còn 12), sửa D1 trước 792 sp (B1 còn 218). "
                     "Sau khi trả đệm về mục tiêu: ≈ 660 vs 792 → chọn sửa D1 trước; "
                     "tăng ca ≈ 3 giờ (M2 trước) vs ≈ 1 giờ 45 (D1 trước); mức Vàng.",
        ),
        KichBan(
            "th3", "TH3: Lô linh kiện L-A về trễ 5 giờ",
            "Lô 600 L-A dự kiến về 10:00, nhà cung cấp báo trễ đến 15:00. Kho L-A đang có 400.",
            [Nhieu("L-A", "nguon_cung", -100, "10:00", 5, mo_ta="Lô L-A trễ")],
            phuong_an_them=[PhuongAn(
                "NCC tách lô: gửi trước 450 L-A bằng xe nhỏ", 3,
                ChinhSach(muc=1, hanh_dong=[Nhieu("L-A", "nguon_cung", so_luong=450, bat_dau="11:00"),
                                            Nhieu("L-A", "nguon_cung", so_luong=-450, bat_dau="15:00")]),
                mo_ta="450 L-A về 11:00 (trước 11:20), 150 còn lại về 15:00",
                chi_phi_them=0, xao_tron_them=1)],
            tai_lieu="11:20 kho L-A cạn, 12:05 B2 đầy, 12:55 B1 đầy; không làm gì mất 440; "
                     "đổi thứ tự chỉ mất 80 (480 X + 400 Y); lô phải về trước 16:05. Ngày mai 950 sp + 1 lần đổi mã "
                     "(≈ 40 sp) = 990 > 960 → tăng ca ~40 phút hôm nay, hoặc đổi thứ tự + tăng tốc (không cần tăng ca); "
                     "mức Vàng.",
        ),
        KichBan(
            "th4", "TH4: Khách chèn đơn gấp 300 sp",
            "10:00, khách C đặt thêm 300 sp mã X, cần trước 20:00 hôm nay. Kế hoạch ca đã kín 960 sp.",
            [Nhieu("X", "nhu_cau", 300, "10:00", han="20:00", ma="Đơn C", mo_ta="Đơn gấp khách C")],
            phuong_an_them=[
                PhuongAn("A: Tăng tốc ca chính + tăng ca", 2, ChinhSach(muc=2),
                         mo_ta="Cả chuyền chạy tối đa từ 10:00 (tối đa 6 giờ), phần còn lại tăng ca"),
                PhuongAn("B: Chỉ tăng ca", 4, ChinhSach(muc=1), mo_ta="Ca chính theo kế hoạch, làm 300 sp trong tăng ca"),
            ],
            bo_chung=True,
            tai_lieu="A: đơn C xong 18:00 (2 giờ tăng ca + 6 giờ cao tải); B: xong 18:30 (2,5 giờ tăng ca); "
                     "kho L-A 1000 < 1260 → đặt gấp 260 L-A (trước 15:50 / 16:20); mức Vàng.",
        ),
        KichBan(
            "th5", "TH5: Lắp ráp thiếu 2/6 người",
            "08:00, Lắp ráp chỉ có 4/6 người do nghỉ đột xuất.",
            [Nhieu("LR", "nang_luc", -100 / 3, "08:00", None, mo_ta="Lắp ráp thiếu 2 người")],
            tai_lieu="Không làm gì 640 (B2 đầy ~10:15); A (điều 1 người): 760, tăng ca 2 giờ; "
                     "B (điều 2 người): 880, tăng ca 40 phút – chỉ khi line 2 dư năng lực; mức Vàng.",
        ),
        KichBan(
            "th6", "TH6: Phát hiện hàng lỗi – truy ngược rồi tính xuôi",
            "14:00, Kiểm tra cuối phát hiện 5 sp lỗi kích thước lỗ. Truy ngược trên bảng phả hệ tự tạo, "
            "khoanh vùng, rồi tính tác động: giữ hàng nghi lỗi + M3 dừng 1 giờ để kiểm tra.",
            [],  # điền sau khi truy vết (xem chay())
            tai_lieu="Khoanh vùng 88 sp (thay vì ~600 cả lô S-77); thiếu 88 + 26 = 114 sp (kho TP không dùng để giảm "
                     "giờ tăng ca) → tăng ca ~57 phút, ~48 phút nếu tăng tốc; đặt gấp 48 L-A; "
                     "gợi ý hạ công suất tối đa M3 44 → 42; mức Vàng.",
        ),
        KichBan(
            "th7", "TH7: Xe giao hàng đến trễ 2 giờ",
            "Chuyến xe 17:00 chở D-101 cho khách A báo trễ đến 19:00. Đường đi 1,5 giờ, khách cần hàng trước 19:00.",
            [Nhieu("XE-A", "thoi_gian", 2, "15:00", mo_ta="Xe XE-A báo trễ")],
            phuong_an_them=[PhuongAn("Giữ kế hoạch sản xuất", 1, ChinhSach(muc=1))],
            bo_chung=True,
            tai_lieu="Hàng đến khách 20:30, trễ 1,5 giờ; ghép chuyến 17:30 / thuê xe ngoài / báo khách; "
                     "kiểm tra kho TP đầy; mức Vàng (thuê xe ngoài vẫn giữ đơn đúng hạn).",
        ),
    ]
    return {kb.ma: kb for kb in ds}


def _phuong_an_th5(dc: DayChuyen) -> list[PhuongAn]:
    l2 = dc.cfg["line_2"]
    ds = []
    for so, nhan in ((1, "A"), (2, "B")):
        con = (l2["so_nguoi"] - so) * l2["nang_suat_moi_nguoi"]
        du = con >= l2["ke_hoach_sp_gio"] and so <= l2["nguoi_da_ky_nang"]
        ds.append(PhuongAn(
            f"{nhan}: Điều {so} người đa kỹ năng từ line 2", 5,
            ChinhSach(muc=1, hanh_dong=[Nhieu("LR", "nang_luc", 100 * so / 6, "10:00")]),
            mo_ta=f"Từ 10:00 Lắp ráp có {4 + so} người",
            xao_tron_them=so, kha_thi=du,
            ly_do=(f"Line 2 còn {con} sp/h ≥ kế hoạch {l2['ke_hoach_sp_gio']} ✓" if du
                   else f"Line 2 chỉ còn {con} sp/h < kế hoạch {l2['ke_hoach_sp_gio']} ✗ – chỉ chọn nếu line 2 dư năng lực"),
        ))
    return ds


def chay(ma: str, dc: DayChuyen | None = None) -> tuple[PhanTich, dict]:
    """Chạy một kịch bản: trả về phân tích của engine + phần riêng của tình huống."""
    dc = dc or DayChuyen.tai()
    kb = kich_ban()[ma]
    them, rieng = list(kb.phuong_an_them), {}
    nhieu = list(kb.nhieu)
    if ma == "th3":
        them = [replace(pa, chi_phi_them=dc.chi_phi.get("xe_nho_ncc", 0)) for pa in them]
    if ma == "th5":
        them += _phuong_an_th5(dc)
    if ma == "th6":
        tv = truy_vet_th6()
        rieng["truy_vet"] = tv
        nhieu = [Nhieu("X", "chat_luong", tv["so_giu"], "14:00", mo_ta=f"Giữ {tv['so_giu']} sp nghi lỗi"),
                 Nhieu("M3", "nang_luc", -100, "14:00", 1, mo_ta="M3 dừng 1 giờ kiểm tra dao cụ")]
    pt = phan_tich(dc, nhieu, them, kb.bo_chung)
    if ma == "th3":
        t = nguong_nguon_cung(dc, kb.nhieu[0], ChinhSach(muc=1, doi_thu_tu=True), "D-101")
        rieng["nguong_lo"] = t
        pt.thong_diep["Giao hàng & Sales"].append(
            f"Ngưỡng: lô L-A phải về trước **{gio(t)}** thì D-101 vẫn đủ (đổi thứ tự + chạy đến 17:00). "
            f"Lô đang báo {gio(kb.nhieu[0].t1(0))}, dư {t - kb.nhieu[0].t1(0)} phút; nếu NCC báo trễ quá {gio(t)} → chuyển Đỏ.")
        pt.thong_diep["Bảo trì"].append(
            "Làm bảo dưỡng định kỳ chuyền Lắp ráp ngay trong các lần đổi mã, không mất thêm giờ máy.")
    if ma == "th6":
        tv = rieng["truy_vet"]
        kl = tv["ket_luan"]
        pt.thong_diep["Bảo trì"].insert(0, (
            f"Lỗi xuất hiện đúng lúc {kl['nhom']['may_gia_cong'].iloc[0]} chạy {kl.get('toc', 0):g} sp/h (mức tối đa) → "
            f"gợi ý hạ công suất tối đa cho phép của M3 từ 44 xuống 42 và kiểm tra dao cụ; "
            f"ghi nhận tỷ lệ lỗi khi chạy cao vào thông số máy."))
        pt.thong_diep["Giao hàng & Sales"].insert(0, (
            f"Chất lượng: giữ lại {tv['so_giu']} sp ({kl['ten']}) thay vì {len(tv['gia_thuyet'][0]['nhom'])} sp cả lô."))
    return pt, rieng
