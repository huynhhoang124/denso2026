"""Engine D3 – Chain Impact Propagation.

Hai lớp (IDEA.md mục 3):
- Lớp Logic: đồ thị networkx – cái gì nối với cái gì.
- Lớp Nghiệp vụ: mô phỏng dòng chảy theo bước 1 phút – nối như thế nào.

Ý tưởng cốt lõi (mục 2): mọi sự cố là một "nhiễu" theo mẫu chung; tác động = mô phỏng có
nhiễu − mô phỏng kế hoạch; hành động khắc phục cũng là nhiễu, chạy lại qua cùng engine.
"""
from __future__ import annotations

import copy
import itertools
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field, replace
from pathlib import Path

import networkx as nx
import pandas as pd
import yaml

EPS = 1e-6
DAI_LUONG = {
    "nang_luc": "năng lực",
    "nguon_cung": "nguồn cung",
    "nhu_cau": "nhu cầu",
    "thoi_gian": "thời gian",
    "chat_luong": "chất lượng",
}
TRANG_THAI_XAU = ("dừng máy", "đói hàng", "bị chặn", "thiếu linh kiện", "đổi mã", "giảm năng lực")


# ---------------------------------------------------------------- thời gian
def phut(gio: str | int | float | None) -> int | None:
    """'HH:MM' -> số phút kể từ đầu ca 08:00."""
    if gio is None:
        return None
    if isinstance(gio, (int, float)):
        return int(round(gio))
    h, m = str(gio).split(":")
    return (int(h) - 8) * 60 + int(m)


def gio(t: float | None) -> str:
    """Số phút kể từ 08:00 -> 'HH:MM'."""
    if t is None:
        return "–"
    t = int(round(t))
    return f"{8 + t // 60:02d}:{t % 60:02d}"


def thoi_luong(phut_: float | None) -> str:
    if phut_ is None:
        return "> giới hạn"
    phut_ = int(round(phut_))
    if phut_ < 60:
        return f"{phut_} phút"
    return f"{phut_ // 60} giờ {phut_ % 60:02d} phút" if phut_ % 60 else f"{phut_ // 60} giờ"


# ---------------------------------------------------------------- mẫu nhiễu
@dataclass
class Nhieu:
    """Mẫu mô tả chung: tại điểm X · đại lượng Y · thay đổi · từ t0 · trong T giờ.

    Ý nghĩa `thay_doi` theo đại lượng:
      nang_luc   – % (−100 = dừng hẳn; máy hoặc cả công đoạn, vd. thiếu người)
      nguon_cung – % lượng hàng về trong khung [t0, t0+T); phần bị giữ về ở cuối khung.
                   Có thể dùng `so_luong` thay cho % để thêm/bớt một chuyến hàng lúc t0.
      nhu_cau    – số sản phẩm thêm (đơn gấp), hạn `han`
      thoi_gian  – số giờ trễ (chuyến giao)
      chat_luong – số sản phẩm bị giữ lại lúc t0
    """

    diem: str
    dai_luong: str
    thay_doi: float = 0.0
    bat_dau: str | int = "08:00"
    thoi_luong_gio: float | None = None
    sai_so_gio: float = 0.0
    so_luong: float | None = None
    han: str | None = None
    ma: str | None = None
    mo_ta: str = ""

    @property
    def t0(self) -> int:
        return phut(self.bat_dau)

    def t1(self, mac_dinh: int) -> int:
        if self.thoi_luong_gio is None:
            return mac_dinh
        return self.t0 + int(round(self.thoi_luong_gio * 60))

    def mau(self) -> str:
        dl = DAI_LUONG.get(self.dai_luong, self.dai_luong)
        if self.dai_luong == "nang_luc" or (self.dai_luong == "nguon_cung" and self.so_luong is None):
            tri = f"{self.thay_doi:+.0f}%".replace("-", "−")
        elif self.dai_luong == "nguon_cung":
            tri = f"{self.so_luong:+.0f} sp".replace("-", "−")
        elif self.dai_luong == "thoi_gian":
            tri = f"+{self.thay_doi:g} giờ"
        else:
            tri = f"+{self.thay_doi:.0f} sp"
        ke = f"{self.diem} · {dl} · {tri} · từ {gio(self.t0)}"
        if self.thoi_luong_gio is not None:
            ke += f" · {self.thoi_luong_gio:g} giờ"
            if self.sai_so_gio:
                ke += f" ± {self.sai_so_gio:g} giờ"
        elif self.dai_luong == "nang_luc":
            ke += " · chưa rõ bao lâu"
        if self.han:
            ke += f" · hạn {self.han}"
        return ke


@dataclass
class ChinhSach:
    """Cách vận hành khi chạy mô phỏng.

    muc 0 – không làm gì: máy chạy chuẩn.
    muc 1 – chia tải: giữ nhịp kế hoạch, máy còn lại gánh theo tỷ lệ công suất tối đa.
    muc 2 – tăng tốc: chạy tới mức tối đa cho phép để đuổi kịp kế hoạch.
    tu – phút bắt đầu áp dụng (quyết định chậm, mục 7.3); trước đó dây chuyền chạy như "không làm gì".
    """

    muc: int = 1
    doi_thu_tu: bool = False
    hanh_dong: list[Nhieu] = field(default_factory=list)
    tu: int = 0


# ---------------------------------------------------------------- lớp Logic
class DayChuyen:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        ca = cfg["ca"]
        self.ca = phut(ca["ket_thuc"])
        self.tren_chuan_max = ca["gio_tren_chuan_toi_da"] * 60
        self.tang_ca_max = ca["tang_ca_toi_da_gio"] * 60
        self.doi_ma = ca["doi_ma_phut"]
        self.xuyen_chuyen = ca.get("thoi_gian_xuyen_chuyen_phut", 0)
        self.ke_hoach = cfg["ke_hoach"]["so_luong"]
        self.sp_chinh = cfg["ke_hoach"]["san_pham"]
        self.nhip = self.ke_hoach / (self.ca / 60)  # sp/h
        self.cong_doan = {c["id"]: c for c in cfg["cong_doan"]}
        self.may = {m["id"]: {**m, "cong_doan": c["id"]} for c in cfg["cong_doan"] for m in c["may"]}
        self.dem = {d["id"]: d for d in cfg["dem"]}
        self.fg = cfg["kho_thanh_pham"]
        self.san_pham = {s["id"]: s for s in cfg["san_pham"]}
        self.linh_kien = {lk["id"]: lk for lk in cfg["linh_kien"]}
        self.don_hang = cfg["don_hang"]
        self.chuyen = {c["id"]: c for c in cfg.get("chuyen_giao", [])}
        self.chi_phi = cfg.get("chi_phi", {})
        self.G = self._xay_do_thi()

        dong_chay = self.G.subgraph(
            [n for n, d in self.G.nodes(data=True) if d["loai"] in ("cong_doan", "dem", "kho")]
        )
        self.thu_tu = [n for n in nx.topological_sort(dong_chay) if self.G.nodes[n]["loai"] == "cong_doan"]
        self.dem_truoc = {s: next((u for u in self.G.predecessors(s) if self.G.nodes[u]["loai"] == "dem"), None)
                          for s in self.thu_tu}
        self.dem_sau = {s: next((v for v in self.G.successors(s) if self.G.nodes[v]["loai"] == "dem"), None)
                        for s in self.thu_tu}
        self.cd_lap = next(iter({lk["dung_tai"] for lk in self.linh_kien.values()}))
        self.so_nguoi = sum(c.get("so_nguoi", 0) for c in self.cong_doan.values())

    @classmethod
    def tai(cls, duong_dan: str | Path | None = None) -> "DayChuyen":
        duong_dan = duong_dan or Path(__file__).with_name("config.yaml")
        with open(duong_dan, encoding="utf-8") as f:
            return cls(yaml.safe_load(f))

    def _xay_do_thi(self) -> nx.DiGraph:
        G = nx.DiGraph()

        def canh(u, v, qh):
            G.add_edge(u, v, quan_he=qh)

        for c in self.cfg["cong_doan"]:
            G.add_node(c["id"], loai="cong_doan", ten=c["ten"])
            nhom = f"NG-{c['id']}"
            G.add_node(nhom, loai="nguoi", ten=f"Tổ {c['ten']} ({c.get('so_nguoi', '?')} người)")
            canh(nhom, c["id"], "vận hành")
            for m in c["may"]:
                G.add_node(m["id"], loai="may", ten=m.get("ten", m["id"]))
                canh(m["id"], c["id"], "chạy trên")
        for d in self.cfg["dem"]:
            G.add_node(d["id"], loai="dem", ten=d["ten"])
            canh(d["tu"], d["id"], "đưa vào")
            canh(d["id"], d["den"], "đệm cho")
        fg = self.fg["id"]
        G.add_node(fg, loai="kho", ten=self.fg["ten"])
        cuoi = [c["id"] for c in self.cfg["cong_doan"] if not any(d["tu"] == c["id"] for d in self.cfg["dem"])]
        for c in cuoi:
            canh(c, fg, "đưa vào")
        for lk in self.cfg["linh_kien"]:
            G.add_node(lk["id"], loai="linh_kien", ten=lk["id"])
            G.add_node(lk["nha_cung_cap"], loai="nha_cung_cap", ten=lk["nha_cung_cap"])
            canh(lk["nha_cung_cap"], lk["id"], "cấp cho")
            canh(lk["id"], lk["dung_tai"], "cấp cho")
        for sp in self.cfg["san_pham"]:
            G.add_node(sp["id"], loai="san_pham", ten=f"Mã {sp['id']}")
            canh(sp["linh_kien"], sp["id"], "thành phần của")
            canh(fg, sp["id"], "chứa")
        for d in self.cfg["don_hang"]:
            G.add_node(d["id"], loai="don_hang", ten=d["id"])
            kh = f"KH-{d['khach']}"
            G.add_node(kh, loai="khach_hang", ten=f"Khách {d['khach']}")
            canh(d["san_pham"], d["id"], "đáp ứng đơn")
            canh(d["id"], kh, "giao cho")
            if d.get("chuyen"):
                G.add_node(d["chuyen"], loai="chuyen_giao", ten=d["chuyen"])
                canh(d["id"], d["chuyen"], "chở bởi")
        for c in self.cfg.get("chuyen_giao", []):
            G.add_node(c["id"], loai="chuyen_giao", ten=c.get("ten", c["id"]))
        return G

    # tiện ích
    def loai(self, diem: str) -> str | None:
        return self.G.nodes[diem]["loai"] if diem in self.G else None

    def ten(self, diem: str) -> str:
        return self.G.nodes[diem]["ten"] if diem in self.G else diem

    def may_cua(self, cd: str) -> list[str]:
        return [m["id"] for m in self.cong_doan[cd]["may"]]

    def lk_cua(self, sp: str) -> str:
        return self.san_pham[sp]["linh_kien"]

    def nang_luc_chuan(self, cd: str) -> float:
        return sum(m["chuan"] for m in self.cong_doan[cd]["may"])

    def anh_huong_xuoi(self, diem: str) -> set[str]:
        return nx.descendants(self.G, diem)

    def nguon_goc(self, diem: str) -> set[str]:
        return nx.ancestors(self.G, diem)


# ---------------------------------------------------------------- kết quả mô phỏng
@dataclass
class KetQua:
    dc: DayChuyen
    nhieu: list[Nhieu]
    cs: ChinhSach
    N: int
    ke_hoach_tong: float
    ke_hoach_sp: dict
    don_gap: list[dict]
    dem: dict          # id -> list mức đệm (N+1)
    lk: dict           # id -> list tồn linh kiện (N+1)
    cum: dict          # công đoạn -> sản lượng cộng dồn (N+1)
    cum_sp: dict       # mã -> sản lượng Lắp ráp cộng dồn (N+1)
    giu: dict          # mã -> số sp bị giữ cộng dồn (N+1)
    M: list            # sản lượng hiệu dụng (N+1)
    trang_thai: dict   # công đoạn -> list (N)
    nang_luc: dict     # công đoạn -> list sp/h (N)
    toc_do: dict       # máy -> list sp/h (N)
    sp_lr: list        # mã đang chạy ở Lắp ráp (N)
    tren_chuan: dict   # máy -> số phút chạy trên chuẩn trong ca
    so_lan_doi_ma: int
    tong_cung: dict    # linh kiện -> tổng lượng có trong ngày
    lich_ve: dict      # linh kiện -> {phút: số lượng}

    def san_luong(self, t: int | None = None) -> float:
        return self.M[self.dc.ca if t is None else t]

    def thieu(self) -> float:
        return max(0.0, self.ke_hoach_tong - self.san_luong())

    def tang_ca_can(self) -> int | None:
        """Số phút tăng ca để sản lượng hiệu dụng đạt kế hoạch (đệm đã trả về mục tiêu)."""
        return self.gio_dat(self.ke_hoach_tong, tu=self.dc.ca, tuong_doi=True)

    def gio_dat(self, muc: float, tu: int = 0, tuong_doi: bool = False) -> int | None:
        for t in range(tu, self.N + 1):
            if self.M[t] >= muc - 0.5:
                return t - tu if tuong_doi else t
        return None

    def bang(self) -> pd.DataFrame:
        df = pd.DataFrame({"phut": range(self.N + 1)})
        df["gio"] = df["phut"].map(gio)
        for k, v in self.dem.items():
            df[k] = v
        for k, v in self.lk.items():
            df[k] = v
        for k, v in self.cum.items():
            df[f"cong_don_{k}"] = v
        df["san_luong_hieu_dung"] = self.M
        return df


def _chia_tai(can: float, may: list[tuple[str, float, float]]) -> dict[str, float]:
    """Chia `can` sp/h cho các máy theo tỷ lệ công suất tối đa, mỗi máy không vượt trần của nó.

    may: (id, trần cho phép lúc này, trọng số = công suất tối đa).
    """
    kq, con = {}, list(may)
    while con:
        tong_w = sum(w for _, _, w in con)
        phan = {m: can * w / tong_w for m, _, w in con}
        vuot = [(m, tran) for m, tran, _ in con if phan[m] > tran + EPS]
        if not vuot:
            kq.update(phan)
            break
        for m, tran in vuot:
            kq[m] = tran
            can -= tran
        con = [x for x in con if x[0] not in kq]
    return kq


def mo_phong(dc: DayChuyen, nhieu: list[Nhieu] = (), cs: ChinhSach | None = None,
             den: int | None = None) -> KetQua:
    """Mô phỏng theo bước 1 phút từ 08:00 đến `den` (mặc định hết giới hạn tăng ca)."""
    cs = cs or ChinhSach()
    N = den or dc.ca + dc.tang_ca_max
    tat_ca = list(nhieu) + list(cs.hanh_dong)

    # --- hệ số năng lực theo phút
    hs_may = {m: [1.0] * N for m in dc.may}
    hs_cd = {c: [1.0] * N for c in dc.cong_doan}
    for n in tat_ca:
        if n.dai_luong != "nang_luc":
            continue
        bang = hs_may if n.diem in hs_may else hs_cd if n.diem in hs_cd else None
        if bang is None:
            raise ValueError(f"Không có điểm năng lực '{n.diem}'")
        for t in range(max(0, n.t0), min(N, n.t1(N))):
            bang[n.diem][t] += n.thay_doi / 100
    for bang in (hs_may, hs_cd):
        for k in bang:
            bang[k] = [max(0.0, x) for x in bang[k]]

    # --- lịch linh kiện về
    lich = {lk: defaultdict(float) for lk in dc.linh_kien}
    for lk, info in dc.linh_kien.items():
        for lo in info.get("lich_ve", []):
            lich[lk][phut(lo["gio"])] += lo["so_luong"]
    for n in tat_ca:
        if n.dai_luong == "nguon_cung" and n.so_luong is None:
            t1 = n.t1(N)
            for t in list(lich[n.diem]):
                if n.t0 <= t < t1:
                    giu = lich[n.diem][t] * (-n.thay_doi / 100)
                    lich[n.diem][t] -= giu
                    lich[n.diem][t1] += giu
    for n in tat_ca:
        if n.dai_luong == "nguon_cung" and n.so_luong is not None:
            lich[n.diem][n.t0] += n.so_luong
    tong_cung = {lk: dc.linh_kien[lk]["ton_kho"] + sum(v for v in lich[lk].values()) for lk in lich}

    # --- kế hoạch, đơn gấp, hàng bị giữ
    ke_hoach_sp = {sp: 0.0 for sp in dc.san_pham}
    ke_hoach_sp[dc.sp_chinh] = dc.ke_hoach
    kh_hien = dict(ke_hoach_sp)  # kế hoạch đã biết tại thời điểm t (đơn gấp chỉ biết từ lúc đến)
    nhu_cau_luc = defaultdict(lambda: defaultdict(float))
    don_gap, giu_luc = [], defaultdict(lambda: defaultdict(float))
    for n in tat_ca:
        if n.dai_luong == "nhu_cau":
            ke_hoach_sp[n.diem] += n.thay_doi
            nhu_cau_luc[n.t0][n.diem] += n.thay_doi
            don_gap.append({"id": n.ma or f"Đơn gấp {n.diem}", "san_pham": n.diem, "so_luong": n.thay_doi,
                            "han": phut(n.han) if n.han else N, "tu": n.t0})
        elif n.dai_luong == "chat_luong":
            giu_luc[n.t0][n.diem or dc.sp_chinh] += n.thay_doi
    ke_hoach_tong = sum(ke_hoach_sp.values())
    keo_som = {}
    if cs.doi_thu_tu:  # được kéo sớm mã khác cho đơn ngày mai
        for sp in dc.san_pham:
            if sp != dc.sp_chinh:
                can = sum(d["so_luong"] for d in dc.don_hang if d["san_pham"] == sp and d.get("ngay", 0) >= 1)
                keo_som[sp] = max(0.0, can - dc.fg["hien_tai"].get(sp, 0))

    # --- trạng thái
    B = {b: float(d["hien_tai"]) for b, d in dc.dem.items()}
    P = {lk: float(info["ton_kho"]) for lk, info in dc.linh_kien.items()}
    cum = {s: 0.0 for s in dc.thu_tu}
    cumsp = {sp: 0.0 for sp in dc.san_pham}
    giu = {sp: 0.0 for sp in dc.san_pham}
    tren = {m: 0 for m in dc.may}
    rec_B = {b: [v] for b, v in B.items()}
    rec_P = {lk: [v] for lk, v in P.items()}
    rec_cum = {s: [0.0] for s in cum}
    rec_sp = {sp: [0.0] for sp in cumsp}
    rec_giu = {sp: [0.0] for sp in giu}
    rec_tt = {s: [] for s in dc.thu_tu}
    rec_nl = {s: [] for s in dc.thu_tu}
    rec_td = {m: [] for m in dc.may}
    rec_sp_lr = []

    def m_hieu_dung():
        phat = sum(min(0.0, B[b] - dc.dem[b]["muc_tieu"]) for b in B)
        return cum[dc.thu_tu[-1]] - sum(giu.values()) + phat

    M = [m_hieu_dung()]
    hien, dang_doi, dich, so_doi = dc.sp_chinh, 0, None, 0

    def can_lam(sp):
        con = kh_hien[sp] + giu[sp] + keo_som.get(sp, 0) - cumsp[sp]
        return P[dc.lk_cua(sp)] > EPS and con > EPS

    for t in range(N):
        trong_ca = t < dc.ca
        muc = cs.muc if t >= cs.tu else 0
        doi_thu_tu = cs.doi_thu_tu and t >= cs.tu
        for lk in lich:
            P[lk] += lich[lk].get(t, 0.0)
        for sp, sl in giu_luc.get(t, {}).items():
            giu[sp] += sl
        for sp, sl in nhu_cau_luc.get(t, {}).items():
            kh_hien[sp] += sl
        # hàng kéo sớm cho ngày mai (đổi thứ tự) không chiếm chỗ của kế hoạch hôm nay ở các công đoạn trước
        yeu_cau = sum(kh_hien.values()) + sum(giu.values()) + sum(cumsp[sp] for sp in keo_som)

        # đổi mã ở Lắp ráp
        if dang_doi > 0:
            dang_doi -= 1
            if dang_doi == 0:
                hien = dich
        elif doi_thu_tu:
            if hien != dc.sp_chinh and can_lam(dc.sp_chinh):
                dang_doi, dich = dc.doi_ma, dc.sp_chinh
            elif not can_lam(hien):
                khac = next((sp for sp in dc.san_pham if sp != hien and can_lam(sp)), None)
                if khac:
                    dang_doi, dich = dc.doi_ma, khac
            if dang_doi:
                so_doi += 1
        rec_sp_lr.append(hien)

        for s in reversed(dc.thu_tu):
            g = hs_cd[s][t]
            toc, co_dinh, khoe = {}, 0.0, []
            for m in dc.may_cua(s):
                f = hs_may[m][t]
                info = dc.may[m]
                if f <= EPS:
                    toc[m] = 0.0
                elif f < 1 - EPS:  # máy bất thường: chạy cố định, không tăng tốc
                    toc[m] = info["chuan"] * f * g
                    co_dinh += toc[m]
                else:
                    chuan, toi_da = info["chuan"] * f * g, max(info["toi_da"] * g, info["chuan"] * f * g)
                    # công đoạn đang thiếu người (g < 1) không chạy nhanh hơn nhịp chuẩn của số người còn lại
                    duoc_tang = muc >= 1 and trong_ca and tren[m] < dc.tren_chuan_max and g >= 1 - EPS
                    khoe.append((m, chuan, toi_da if duoc_tang else chuan, toi_da))
            tong_chuan = sum(k[1] for k in khoe)
            if muc == 0 or not trong_ca:
                toc.update({m: chuan for m, chuan, _, _ in khoe})
            else:
                muc_tieu = dc.nhip
                if muc == 2:
                    muc_tieu = max(muc_tieu, (yeu_cau - cum[s]) / max(dc.ca - t, 1) * 60)
                can = muc_tieu - co_dinh
                if can <= tong_chuan + EPS:
                    toc.update({m: chuan for m, chuan, _, _ in khoe})
                else:
                    toc.update(_chia_tai(can, [(m, tran, w) for m, _, tran, w in khoe]))
            nang_luc = sum(toc.values())
            if s == dc.cd_lap and dang_doi > 0:
                nang_luc = 0.0

            vao = B[dc.dem_truoc[s]] if dc.dem_truoc[s] else float("inf")
            lk_vao = float("inf")
            if s == dc.cd_lap:
                lk_vao = P[dc.lk_cua(hien)] / dc.san_pham[hien]["dinh_muc"]
            sau = dc.dem_sau[s]
            cho = dc.dem[sau]["suc_chua"] - B[sau] if sau else float("inf")
            con = yeu_cau - cum[s]
            if s == dc.cd_lap:  # Lắp ráp giới hạn theo từng mã
                con = kh_hien[hien] + giu[hien] + keo_som.get(hien, 0) - cumsp[hien]
            ra = max(0.0, min(nang_luc / 60, vao, lk_vao, cho, con))

            if con <= EPS:
                tt = "xong"
            elif s == dc.cd_lap and dang_doi > 0:
                tt = "đổi mã"
            elif nang_luc <= EPS:
                tt = "dừng máy"
            elif ra < nang_luc / 60 - EPS:
                rang_buoc = min(vao, lk_vao, cho, con)
                tt = ("thiếu linh kiện" if rang_buoc == lk_vao else "đói hàng" if rang_buoc == vao
                      else "bị chặn" if rang_buoc == cho else "chạy")
            elif nang_luc < dc.nang_luc_chuan(s) - 0.5:
                tt = "giảm năng lực"
            elif nang_luc > dc.nang_luc_chuan(s) + 0.5:
                tt = "tăng tốc"
            else:
                tt = "chạy"

            if trong_ca and ra * 60 > co_dinh + tong_chuan + EPS:
                for m, chuan, _, _ in khoe:
                    if toc[m] > chuan + EPS:
                        tren[m] += 1

            if dc.dem_truoc[s]:
                B[dc.dem_truoc[s]] -= ra
            if sau:
                B[sau] += ra
            if s == dc.cd_lap:
                P[dc.lk_cua(hien)] -= ra * dc.san_pham[hien]["dinh_muc"]
                cumsp[hien] += ra
            cum[s] += ra
            rec_tt[s].append(tt)
            rec_nl[s].append(nang_luc)
            for m in dc.may_cua(s):
                rec_td[m].append(toc[m] if tt not in ("đổi mã",) else 0.0)

        for b in B:
            rec_B[b].append(B[b])
        for lk in P:
            rec_P[lk].append(P[lk])
        for s in cum:
            rec_cum[s].append(cum[s])
        for sp in cumsp:
            rec_sp[sp].append(cumsp[sp])
            rec_giu[sp].append(giu[sp])
        M.append(m_hieu_dung())

    return KetQua(dc=dc, nhieu=list(nhieu), cs=cs, N=N, ke_hoach_tong=ke_hoach_tong, ke_hoach_sp=ke_hoach_sp,
                  don_gap=don_gap, dem=rec_B, lk=rec_P, cum=rec_cum, cum_sp=rec_sp, giu=rec_giu, M=M,
                  trang_thai=rec_tt, nang_luc=rec_nl, toc_do=rec_td, sp_lr=rec_sp_lr, tren_chuan=tren,
                  so_lan_doi_ma=so_doi, tong_cung=tong_cung, lich_ve={k: dict(v) for k, v in lich.items()})


# ---------------------------------------------------------------- đơn hàng
def danh_gia_don(kq: KetQua, tang_ca: int = 0) -> dict:
    """Kiểm tra từng đơn với lượng tăng ca `tang_ca` phút. Kho thành phẩm được dùng cho đơn."""
    dc = kq.dc
    te = min(dc.ca + tang_ca, kq.N)

    def co_san(sp, t):
        return dc.fg["hien_tai"].get(sp, 0) + kq.cum_sp[sp][t] - kq.giu[sp][t]

    hom_nay = [{**d, "han_p": phut(d["han"])} for d in dc.don_hang if d.get("ngay", 0) == 0]
    hom_nay += [{"id": g["id"], "khach": "–", "san_pham": g["san_pham"], "so_luong": g["so_luong"],
                 "han": gio(g["han"]), "han_p": g["han"]} for g in kq.don_gap]
    hom_nay.sort(key=lambda d: d["han_p"])
    da_dung, dong, ok_all = defaultdict(float), [], True
    for d in hom_nay:
        sp, sl = d["san_pham"], d["so_luong"]
        co = co_san(sp, min(d["han_p"], te)) - da_dung[sp]
        ok = co >= sl - 0.5
        ok_all &= ok
        da_dung[sp] += min(sl, max(co, 0.0))
        dong.append({"Đơn": d["id"], "Khách": d.get("khach", "–"), "Mã": sp, "Số lượng": sl,
                     "Hạn": f"hôm nay {d['han']}", "Trạng thái": "Kịp" if ok else "Trễ",
                     "Ghi chú": f"có {co:.0f}/{sl:.0f} sp lúc {gio(min(d['han_p'], te))}"
                     if not ok else f"đủ lúc {gio(min(d['han_p'], te))}"})

    con_lai = {sp: co_san(sp, te) - da_dung[sp] for sp in dc.san_pham}
    ngay_mai = [d for d in dc.don_hang if d.get("ngay", 0) == 1]
    can = defaultdict(float)
    for d in ngay_mai:
        lay = min(d["so_luong"], max(con_lai[d["san_pham"]], 0.0))
        con_lai[d["san_pham"]] -= lay
        can[d["san_pham"]] += d["so_luong"] - lay
    bat_dau = kq.sp_lr[te - 1]
    ma_can = [sp for sp in can if can[sp] > 0.5]
    so_doi = len(ma_can) - (1 if bat_dau in ma_can else 0)
    bu_dem = sum(max(0.0, dc.dem[b]["muc_tieu"] - kq.dem[b][te]) for b in dc.dem)
    phut_mai = (sum(can.values()) + bu_dem) / dc.nhip * 60 + so_doi * dc.doi_ma
    du_mai = phut_mai <= dc.ca + 0.5
    ok_all &= du_mai
    thieu_mai = max(0.0, (phut_mai - dc.ca) * dc.nhip / 60)
    # thứ tự làm ngày mai: mã đang chạy trước, đơn cuối cùng chịu phần thiếu
    thu_tu = sorted(ngay_mai, key=lambda d: (d["san_pham"] != bat_dau, ngay_mai.index(d)))
    for i, d in enumerate(thu_tu):
        cuoi = i == len(thu_tu) - 1
        ok = du_mai or not cuoi
        dong.append({"Đơn": d["id"], "Khách": d.get("khach", "–"), "Mã": d["san_pham"], "Số lượng": d["so_luong"],
                     "Hạn": "ngày mai", "Trạng thái": "Kịp" if ok else "Nguy cơ trễ",
                     "Ghi chú": (f"ngày mai còn phải làm {can[d['san_pham']]:.0f} sp"
                                 if ok else f"ca mai thiếu ~{thieu_mai:.0f} sp (cần ~{phut_mai - dc.ca:.0f} phút tăng ca)")})
    return {"ok": ok_all, "don": dong, "phut_ngay_mai": phut_mai, "bu_dem": bu_dem}


# ---------------------------------------------------------------- phương án
@dataclass
class PhuongAn:
    ten: str
    bac: int                      # bậc trên thang xử lý (0 = không làm gì)
    cs: ChinhSach
    mo_ta: str = ""
    chi_phi_them: float = 0.0
    xao_tron_them: int = 0
    kha_thi: bool = True
    ly_do: str = ""
    tang_ca: bool = True          # có được phép tăng ca không


BAC = {0: "Không làm gì", 1: "Chia tải", 2: "Tăng tốc", 3: "Đổi thứ tự", 4: "Tăng ca", 5: "Chuyển line / ca sau",
       6: "Báo khách"}


def _dat_gap_linh_kien(dc: DayChuyen, kq: KetQua) -> Nhieu | None:
    """Nếu tổng linh kiện trong ngày không đủ cho kế hoạch -> sinh hành động đặt gấp."""
    for lk in dc.linh_kien:
        can = sum((kq.ke_hoach_sp[sp] + kq.giu[sp][-1]) * info["dinh_muc"]
                  for sp, info in dc.san_pham.items() if info["linh_kien"] == lk)
        if kq.tong_cung[lk] < can - 0.5:
            t_het = next((t for t in range(kq.N) if kq.trang_thai[dc.cd_lap][t] == "thiếu linh kiện"), None)
            if t_het is None:
                continue
            return Nhieu(lk, "nguon_cung", so_luong=can - kq.tong_cung[lk], bat_dau=t_het,
                         mo_ta=f"Đặt gấp {can - kq.tong_cung[lk]:.0f} {lk}, về trước {gio(t_het)}")
    return None


def danh_gia(dc: DayChuyen, nhieu: list[Nhieu], pa: PhuongAn, kq_goc: KetQua | None = None) -> dict:
    kq = mo_phong(dc, nhieu, pa.cs)
    chi_phi_them, xao_tron, ghi_chu = pa.chi_phi_them, pa.xao_tron_them, [pa.mo_ta] if pa.mo_ta else []
    dat_gap = _dat_gap_linh_kien(dc, kq) if pa.bac >= 1 else None
    if dat_gap:
        pa = replace(pa, cs=replace(pa.cs, hanh_dong=pa.cs.hanh_dong + [dat_gap]))
        kq = mo_phong(dc, nhieu, pa.cs)
        chi_phi_them += dc.chi_phi.get("xe_nho_ncc", 0)
        xao_tron += 1
        ghi_chu.append(dat_gap.mo_ta)

    tc_ke_hoach = kq.tang_ca_can()
    don0 = danh_gia_don(kq, 0)
    if don0["ok"]:
        tc_de_xuat, don = 0, don0
    elif pa.tang_ca and tc_ke_hoach is not None:
        tc_de_xuat, don = tc_ke_hoach, danh_gia_don(kq, tc_ke_hoach)
    else:
        tc_de_xuat, don = None, don0
    giu_don = pa.kha_thi and don["ok"]

    gio_tren_chuan = sum(kq.tren_chuan.values()) / 60
    cp = dc.chi_phi
    chi_phi_ct = {"tăng ca": (tc_de_xuat or 0) / 60 * dc.so_nguoi * cp.get("tang_ca_nguoi_gio", 0),
                  "hao mòn chạy trên chuẩn": gio_tren_chuan * cp.get("hao_mon_may_gio_tren_chuan", 0),
                  "đổi mã": kq.so_lan_doi_ma * cp.get("doi_ma_lan", 0), "khác": chi_phi_them}
    chi_phi = sum(chi_phi_ct.values())
    xao_tron += kq.so_lan_doi_ma + (1 if tc_de_xuat else 0) + (1 if gio_tren_chuan > 0 else 0)
    muc_xt = "Không" if xao_tron == 0 else "Thấp" if xao_tron <= 2 else "Trung bình" if xao_tron <= 4 else "Cao"
    goc = kq_goc.san_luong() if kq_goc else kq.san_luong()
    return {"pa": pa, "kq": kq, "san_luong": kq.san_luong(), "cuu_duoc": kq.san_luong() - goc,
            "tang_ca_ke_hoach": tc_ke_hoach, "tang_ca_de_xuat": tc_de_xuat, "don": don, "giu_don": giu_don,
            "chi_phi": chi_phi, "chi_phi_ct": chi_phi_ct, "xao_tron": xao_tron, "muc_xao_tron": muc_xt, "gio_tren_chuan": gio_tren_chuan,
            "ghi_chu": "; ".join(g for g in ghi_chu if g)}


def phuong_an_chung(dc: DayChuyen, nhieu: list[Nhieu]) -> list[PhuongAn]:
    """Thang xử lý tổng quát: không làm gì → chia tải → tăng tốc → (đổi thứ tự nếu thiếu linh kiện)."""
    ds = [PhuongAn("Không làm gì", 0, ChinhSach(muc=0), tang_ca=False),
          PhuongAn("Chia tải", 1, ChinhSach(muc=1)),
          PhuongAn("Chia tải + tăng tốc", 2, ChinhSach(muc=2))]
    thu = mo_phong(dc, nhieu, ChinhSach(muc=1))
    thieu_lk = any("thiếu linh kiện" == x for x in thu.trang_thai[dc.cd_lap][: dc.ca])
    ma_khac = any(n.dai_luong == "nhu_cau" and n.diem != dc.sp_chinh for n in nhieu)
    if (thieu_lk or ma_khac) and len(dc.san_pham) > 1:
        ds += [PhuongAn("Đổi thứ tự sản xuất", 3, ChinhSach(muc=1, doi_thu_tu=True)),
               PhuongAn("Đổi thứ tự + tăng tốc", 3, ChinhSach(muc=2, doi_thu_tu=True))]
    return ds


# ---------------------------------------------------------------- phân tích bổ trợ
def thoi_gian_chiu_dung(dc: DayChuyen, nhieu: list[Nhieu]) -> pd.DataFrame:
    """Time-to-Survive của đệm so với thời gian sửa (mục 4.7)."""
    dong = []
    for n in nhieu:
        if n.dai_luong != "nang_luc" or n.diem not in dc.may or n.thay_doi >= 0:
            continue
        cd = dc.may[n.diem]["cong_doan"]
        con = sum(dc.may[m]["toi_da"] for m in dc.may_cua(cd) if m != n.diem)
        con += dc.may[n.diem]["chuan"] * (1 + n.thay_doi / 100)
        hut = dc.nhip - con
        sua = n.thoi_luong_gio
        sau, truoc = dc.dem_sau[cd], dc.dem_truoc[cd]
        tts_sau = dc.dem[sau]["hien_tai"] / hut if sau and hut > 0 else None
        tts_truoc = (dc.dem[truoc]["suc_chua"] - dc.dem[truoc]["hien_tai"]) / hut if truoc and hut > 0 else None
        ngan = min([x for x in (tts_sau, tts_truoc) if x is not None], default=None)
        if sua is None or ngan is None:
            kl = "–"
        elif ngan >= sua:
            kl = "Đệm hấp thụ được – máy này chờ được"
        else:
            kl = "Đệm không đỡ nổi – thiệt hại chắc chắn"
        dong.append({"Máy": n.diem, "Công đoạn": dc.ten(cd), "Hụt (sp/h)": round(hut, 1),
                     "Thời gian sửa (giờ)": sua,
                     "Đệm sau": dc.ten(sau) if sau else "–",
                     "Đệm sau đỡ được (giờ)": round(tts_sau, 2) if tts_sau is not None else None,
                     "Đệm trước": dc.ten(truoc) if truoc else "–",
                     "Đệm trước đầy sau (giờ)": round(tts_truoc, 2) if tts_truoc is not None else None,
                     "Kết luận": kl})
    return pd.DataFrame(dong)


def so_sanh_thu_tu_sua(dc: DayChuyen, nhieu: list[Nhieu], cs: ChinhSach) -> pd.DataFrame | None:
    """Nhiều máy hỏng, một tổ bảo trì: thử mọi thứ tự sửa, chạy engine cho từng thứ tự."""
    hong = [n for n in nhieu if n.dai_luong == "nang_luc" and n.diem in dc.may and n.thay_doi <= -100
            and n.thoi_luong_gio]
    if len(hong) < 2:
        return None
    khac = [n for n in nhieu if n not in hong]
    dong = []
    for thu_tu in itertools.permutations(hong):
        t, lich = min(n.t0 for n in hong), []
        for n in thu_tu:
            bd = max(t, n.t0)
            ket = bd + int(n.thoi_luong_gio * 60)
            lich.append(replace(n, thoi_luong_gio=(ket - n.t0) / 60))
            t = ket
        kq = mo_phong(dc, khac + lich, cs)
        tc = kq.tang_ca_can()
        dong.append({
            "Thứ tự sửa": " → ".join(n.diem for n in thu_tu),
            "Lịch sửa": "; ".join(f"{n.diem}: {gio(n.t1(0) - int(o.thoi_luong_gio * 60))}–{gio(n.t1(0))}"
                                   for n, o in zip(lich, thu_tu)),
            "Sản lượng Gia công 16:00": round(kq.cum["GC"][dc.ca]) if "GC" in kq.cum else None,
            **{f"{b} lúc 16:00": round(kq.dem[b][dc.ca]) for b in dc.dem},
            "Sản lượng hiệu dụng 16:00": round(kq.san_luong()),
            "Tăng ca để đủ kế hoạch + trả đệm (phút)": tc,
            "_kq": kq,
            "_lich": khac + lich,
        })
    df = pd.DataFrame(dong)
    df["_xep"] = df["Tăng ca để đủ kế hoạch + trả đệm (phút)"].fillna(10 ** 6)
    df = df.sort_values(["_xep", "Sản lượng hiệu dụng 16:00"], ascending=[True, False]).drop(columns="_xep")
    return df.reset_index(drop=True)


def quet_thoi_gian_sua(dc: DayChuyen, nhieu: list[Nhieu], cs: ChinhSach) -> pd.DataFrame | None:
    """Một máy hỏng với thời gian sửa không chắc chắn -> bảng tăng ca theo từng khả năng (mục 4.3)."""
    hong = [n for n in nhieu if n.dai_luong == "nang_luc" and n.diem in dc.may and n.thay_doi <= -100
            and n.thoi_luong_gio]
    if len(hong) != 1:
        return None
    n = hong[0]
    dong = []
    for muc in dc.cfg.get("phan_bo_sua", []):
        h = n.thoi_luong_gio + muc["lech_gio"]
        if h <= 0:
            continue
        kq = mo_phong(dc, [x if x is not n else replace(n, thoi_luong_gio=h) for x in nhieu], cs)
        dong.append({"Sửa xong sau (giờ)": h, "Sản lượng ca": round(kq.san_luong()), "Thiếu": round(kq.thieu()),
                     "Tăng ca (phút)": kq.tang_ca_can(),
                     "Xác suất sửa xong trong thời gian này": muc["xac_suat_cong_don"]})
    return pd.DataFrame(dong)


def kich_ban_xau(dc: DayChuyen, nhieu: list[Nhieu], cs: ChinhSach, sau_gio: float = 3) -> dict | None:
    """Máy chạy chậm thường báo trước sắp hỏng: tự chạy thử 'nếu máy hỏng hẳn sau vài giờ'."""
    cham = [n for n in nhieu if n.dai_luong == "nang_luc" and n.diem in dc.may and -100 < n.thay_doi < 0]
    if not cham:
        return None
    n = cham[0]
    hong = Nhieu(n.diem, "nang_luc", -100, n.t0 + int(sau_gio * 60), None)
    kq = mo_phong(dc, [x for x in nhieu if x is not n] + [replace(n, thoi_luong_gio=sau_gio), hong], cs)
    return {"nhieu": hong, "kq": kq, "san_luong": kq.san_luong(), "thieu": kq.thieu(), "tang_ca": kq.tang_ca_can()}


def cua_so_bao_tri(dc: DayChuyen, kq: KetQua, toi_thieu: int = 30) -> list[dict]:
    """Khung giờ một công đoạn có thể dừng bớt 1 máy mà không mất sản lượng (công đoạn sau chạy chậm)."""
    ds = []
    for i, s in enumerate(dc.thu_tu[:-1]):
        if len(dc.may_cua(s)) < 2:
            continue
        sau = dc.thu_tu[i + 1]
        bot = dc.nang_luc_chuan(s) - max(dc.may[m]["chuan"] for m in dc.may_cua(s))
        bd = None
        for t in range(dc.ca + 1):
            ranh = t < dc.ca and kq.nang_luc[sau][t] <= bot + EPS and kq.trang_thai[sau][t] != "xong"
            if ranh and bd is None:
                bd = t
            elif not ranh and bd is not None:
                if t - bd >= toi_thieu:
                    ds.append({"cong_doan": s, "tu": bd, "den": t, "so_may_can": len(dc.may_cua(s)) - 1})
                bd = None
    return ds


def nguong_nguon_cung(dc: DayChuyen, nhieu: Nhieu, cs: ChinhSach, ma_don: str) -> int | None:
    """Lô linh kiện về muộn nhất lúc nào thì đơn `ma_don` vẫn kịp (tìm nhị phân trên engine)."""
    don = next(d for d in dc.don_hang if d["id"] == ma_don)
    han = phut(don["han"])

    def kip(t_ve):
        n = replace(nhieu, thoi_luong_gio=(t_ve - nhieu.t0) / 60)
        kq = mo_phong(dc, [n], cs, den=max(han, dc.ca) + 1)
        sp = don["san_pham"]
        co = dc.fg["hien_tai"].get(sp, 0) + kq.cum_sp[sp][han] - kq.giu[sp][han]
        return co >= don["so_luong"] - 0.5

    lo, hi = nhieu.t0, han
    if not kip(lo):
        return None
    if kip(hi):
        return hi
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if kip(mid) else (lo, mid)
    return lo


def truy_vet_nguoc(pha_he: pd.DataFrame, loi: list[str], kiem_mau) -> dict:
    """Sản phẩm lỗi → máy, lô vật liệu, nhà cung cấp, ca → khoanh vùng (mục 4.8, TH6).

    pha_he: bảng phả hệ (mỗi dòng 1 sp). kiem_mau(df) -> số sp lỗi khi lấy mẫu nhóm df.
    """
    l = pha_he[pha_he["ma_sp"].isin(loi)]
    thuoc_tinh = ["may_gia_cong", "lo_thep", "nha_cung_cap", "may_dap", "ca"]
    chung = {c: l[c].iloc[0] for c in thuoc_tinh if l[c].nunique() == 1}
    may = chung.get("may_gia_cong")
    gia_thuyet = []
    if "lo_thep" in chung:
        g = pha_he[pha_he["lo_thep"] == chung["lo_thep"]]
        gia_thuyet.append({"ten": f"Lỗi do vật liệu (cả lô {chung['lo_thep']})", "loai": "vat_lieu", "nhom": g})
    if may:
        # khung giờ: đoạn liên tục quanh các sp lỗi mà máy chạy cùng tốc độ như lúc sinh lỗi
        m = pha_he[pha_he["may_gia_cong"] == may].sort_values("phut")
        toc = l["toc_do_may"].mode().iloc[0]
        cung_toc = m[m["toc_do_may"] == toc]
        tu, den = cung_toc["phut"].min(), cung_toc["phut"].max() + 1
        g = m[(m["phut"] >= tu) & (m["phut"] < den)]
        gia_thuyet.append({"ten": f"Lỗi do máy ({may} {gio(round(tu / 30) * 30)}–{gio(round(den / 30) * 30)}, "
                                  f"chạy {toc:g} sp/h)",
                           "loai": "may", "nhom": g, "tu": tu, "den": den, "toc": toc})
    kiem = None
    vl = next((g for g in gia_thuyet if g["loai"] == "vat_lieu"), None)
    mm = next((g for g in gia_thuyet if g["loai"] == "may"), None)
    ket_luan = vl or mm
    if vl and mm:
        ngoai = vl["nhom"][~vl["nhom"]["ma_sp"].isin(mm["nhom"]["ma_sp"])]
        so_loi = kiem_mau(ngoai)
        kiem = {"nhom": f"cùng lô {chung['lo_thep']} nhưng không qua {may} trong khung trên",
                "so_mau": min(len(ngoai), 20), "so_loi": so_loi}
        ket_luan = mm if so_loi == 0 else vl
    return {"loi": l, "chung": chung, "gia_thuyet": gia_thuyet, "kiem_mau": kiem, "ket_luan": ket_luan,
            "so_giu": len(ket_luan["nhom"]) if ket_luan else 0}


def phan_tich_giao_hang(dc: DayChuyen, n: Nhieu, kq_kh: KetQua) -> dict:
    """Chuyến giao trễ: tính giờ đến, phương án, và kiểm tra kho thành phẩm có đầy không (TH7)."""
    xe = dc.chuyen[n.diem]
    di = phut(xe["gio_di"]) + int(n.thay_doi * 60)
    den = di + int(xe["duong_gio"] * 60)
    han = phut(xe["han_den"])
    don = next(d for d in dc.don_hang if d.get("chuyen") == n.diem)
    tre = den - han
    pa = []
    for x in dc.chuyen.values():
        if x["id"] == n.diem or "con_trong" not in x:
            continue
        cho = x["suc_chua"] * x["con_trong"]
        den_x = phut(x["gio_di"]) + int(x["duong_gio"] * 60)
        pa.append({"Phương án": f"Ghép vào {x.get('ten', x['id'])} (còn {x['con_trong']:.0%} chỗ ≈ {cho:.0f} sp)",
                   "Kết quả": f"{min(cho, don['so_luong']):.0f}/{don['so_luong']} sp đến {gio(den_x)}"
                              + (" – kịp phần hàng ưu tiên" if den_x <= han else " – vẫn trễ"),
                   "Kịp hạn": den_x <= han and cho >= don["so_luong"],
                   "Chi phí (VND)": 0})
    di_ngoai = phut(xe["gio_di"])
    den_ngoai = di_ngoai + int(xe["duong_gio"] * 60)
    pa.append({"Phương án": "Thuê xe ngoài chạy đúng giờ cũ",
               "Kết quả": f"đủ {don['so_luong']} sp đến {gio(den_ngoai)}",
               "Kịp hạn": den_ngoai <= han, "Chi phí (VND)": dc.chi_phi.get("thue_xe_ngoai", 0)})
    pa.append({"Phương án": "Báo khách ngay",
               "Kết quả": f"khách biết trước {thoi_luong(den - n.t0)} thay vì khi hàng đã trễ",
               "Kịp hạn": False, "Chi phí (VND)": 0})
    ton = [dc.fg["hien_tai"].get(sp, 0) + kq_kh.cum_sp[sp][t] for t in range(min(di, kq_kh.N) + 1)
           for sp in [don["san_pham"]]]
    tong_ton = [sum(dc.fg["hien_tai"].values()) + sum(kq_kh.cum_sp[sp][t] for sp in dc.san_pham)
                for t in range(min(di, kq_kh.N) + 1)]
    kip = [p for p in pa if p["Kịp hạn"]]
    de_xuat = min(kip, key=lambda p: p["Chi phí (VND)"]) if tre > 0 and kip else None
    return {"xe": xe, "don": don, "gio_di": di, "gio_den": den, "han": han, "tre": tre, "phuong_an": pa,
            "de_xuat": de_xuat,
            "ton_kho_dinh": max(tong_ton), "suc_chua_kho": dc.fg["suc_chua"],
            "kho_day": max(tong_ton) > dc.fg["suc_chua"], "ton_ma": max(ton)}


# ---------------------------------------------------------------- dòng thời gian
def khoang_trang_thai(kq: KetQua, chi_trong_ca: bool = False) -> pd.DataFrame:
    """Các khoảng trạng thái của công đoạn, máy và đệm – dùng cho Gantt và dòng thời gian."""
    dc, ket = kq.dc, kq.dc.ca if chi_trong_ca else kq.N
    dong = []

    def gop(doi_tuong, nhan, ds):
        bd, cu = 0, ds[0] if ds else None
        for t in range(1, len(ds) + 1):
            x = ds[t] if t < len(ds) else None
            if x != cu:
                if cu:
                    dong.append({"Đối tượng": doi_tuong, "Từ": bd, "Đến": t, "Trạng thái": cu, "Nhóm": nhan})
                bd, cu = t, x

    for s in dc.thu_tu:
        gop(dc.ten(s), "Công đoạn", kq.trang_thai[s][:ket])
    for m in dc.may:
        ds = []
        for t in range(ket):
            v, c = kq.toc_do[m][t], dc.may[m]
            ds.append("hỏng / dừng" if v <= EPS and kq.trang_thai[c["cong_doan"]][t] not in ("xong", "đổi mã")
                      else "trên chuẩn" if v > c["chuan"] + EPS else None)
        gop(m, "Máy", ds)
    for b, info in dc.dem.items():
        ds = ["cạn" if v <= 0.5 else "đầy" if v >= info["suc_chua"] - 0.5 else None for v in kq.dem[b][1:ket + 1]]
        gop(dc.ten(b), "Đệm", ds)
    for lk in dc.linh_kien:
        ds = ["hết" if v <= EPS else None for v in kq.lk[lk][1:ket + 1]]
        gop(lk, "Linh kiện", ds)
    return pd.DataFrame(dong, columns=["Đối tượng", "Từ", "Đến", "Trạng thái", "Nhóm"])


def dong_thoi_gian(kq: KetQua) -> list[tuple[int, str]]:
    """Diễn biến bằng lời, theo giờ."""
    dc, ev = kq.dc, []
    for n in kq.nhieu:
        ev.append((n.t0, f"Sự cố: {n.mau()}"))
    k = khoang_trang_thai(kq, chi_trong_ca=False)
    for _, r in k.iterrows():
        if r["Từ"] >= kq.N:
            continue
        if r["Nhóm"] == "Công đoạn" and r["Trạng thái"] in TRANG_THAI_XAU and r["Đến"] - r["Từ"] >= 1:
            ev.append((r["Từ"], f"{r['Đối tượng']}: {r['Trạng thái']} (đến {gio(r['Đến'])})"))
        elif r["Nhóm"] in ("Đệm", "Linh kiện"):
            ev.append((r["Từ"], f"{r['Đối tượng']} {r['Trạng thái']} (đến {gio(r['Đến'])})"))
    co_nguon_cung = any(n.dai_luong == "nguon_cung" for n in kq.nhieu)
    for lk, lich in (kq.lich_ve.items() if co_nguon_cung else ()):
        for t, sl in lich.items():
            if sl > 0.5 and t < kq.N:
                ev.append((t, f"Lô {lk} về: {sl:.0f} cái"))
    ev.append((dc.ca, f"Hết ca: sản lượng {kq.san_luong():.0f}/{kq.ke_hoach_tong:.0f}, thiếu {kq.thieu():.0f} sp"))
    ev = [e for e in ev if e[0] <= dc.ca]
    ev.sort(key=lambda e: e[0])
    return ev


def diem_bi_anh_huong(dc: DayChuyen, kq: KetQua, don: dict | None = None) -> set[str]:
    bi = set()
    for n in kq.nhieu:
        bi.add(n.diem)
    for s in dc.thu_tu:
        if any(x in TRANG_THAI_XAU for x in kq.trang_thai[s][: dc.ca]):
            bi.add(s)
    for m in dc.may:
        if any(v <= EPS for v in kq.toc_do[m][: dc.ca]):
            bi.add(m)
    for b, info in dc.dem.items():
        ds = kq.dem[b][: dc.ca + 1]
        if min(ds) <= 0.5 or max(ds) >= info["suc_chua"] - 0.5 or ds[-1] < info["muc_tieu"] - 0.5:
            bi.add(b)
    for lk in dc.linh_kien:
        if min(kq.lk[lk][: dc.ca + 1]) <= EPS:
            bi.add(lk)
    if kq.thieu() > 0.5:
        bi.add(dc.fg["id"])
    if don:
        for d in don["don"]:
            if d["Trạng thái"] != "Kịp" and d["Đơn"] in dc.G:
                bi.add(d["Đơn"])
                bi.update(v for v in dc.G.successors(d["Đơn"]))
    return {b for b in bi if b in dc.G}


# ---------------------------------------------------------------- diễn tập đầu ca (mục 7.1–7.2)
def lech_sua(dc: DayChuyen, muc: float | None = None) -> float:
    """Độ lệch thời gian sửa (giờ) so với dự kiến ở mức xác suất `muc` (mặc định mức đăng ký tăng ca)."""
    muc = dc.cfg.get("muc_dang_ky_tang_ca", 0.8) if muc is None else muc
    pb = dc.cfg.get("phan_bo_sua", [])
    for x in pb:
        if x["xac_suat_cong_don"] >= muc - EPS:
            return x["lech_gio"]
    return pb[-1]["lech_gio"] + 1 if pb else 0.0


def ban_do_rui_ro(dc: DayChuyen, luc: str | int = "10:00", cs: ChinhSach | None = None) -> pd.DataFrame:
    """Diễn tập "nếu máy này hỏng thì sao" cho từng máy: hỏng lúc `luc`, sửa trong thời gian ở mức 80%.

    Ưu tiên bảo trì = xác suất hỏng × số sản phẩm mất nếu hỏng (mục 4.6); số sau lấy từ engine.
    """
    cs = cs or ChinhSach(muc=2)
    lech = lech_sua(dc)
    dong = []
    for m, info in dc.may.items():
        if "sua_gio" not in info:
            continue
        h = info["sua_gio"] + lech
        kq = mo_phong(dc, [Nhieu(m, "nang_luc", -100, luc, h)], cs)
        mat = max(0.0, kq.ke_hoach_tong - kq.san_luong())
        p = info.get("hong_trong_ca", 0.0)
        dong.append({"Máy": m, "Công đoạn": dc.ten(info["cong_doan"]), "Sửa (giờ, mức 80%)": h,
                     "Mất nếu hỏng (sp)": round(mat), "Lắp ráp ra lúc 16:00": round(kq.cum[dc.thu_tu[-1]][dc.ca]),
                     "Tăng ca cần (phút)": kq.tang_ca_can(), "Số điểm bị ảnh hưởng": len(diem_bi_anh_huong(dc, kq)),
                     "Xác suất hỏng trong ca": p, "Rủi ro (sp)": round(p * mat, 1)})
    df = pd.DataFrame(dong).sort_values(["Rủi ro (sp)", "Mất nếu hỏng (sp)"], ascending=False)
    df.insert(0, "Ưu tiên", range(1, len(df) + 1))
    return df.reset_index(drop=True)


def muc_dem_toi_thieu(dc: DayChuyen, dem: str, may: str) -> dict:
    """Mức đệm tối thiểu để đỡ được máy `may` (ở công đoạn trước đệm) hỏng = hụt × thời gian sửa mức 80%."""
    cd = dc.dem[dem]["tu"]
    con = sum(dc.may[m]["toi_da"] for m in dc.may_cua(cd) if m != may)
    hut = max(0.0, dc.nhip - con)
    h = dc.may[may].get("sua_gio", 0) + lech_sua(dc)
    return {"hut": hut, "sua_gio": h, "can": hut * h}


def _voi_dem(dc: DayChuyen, dem: str, muc: float) -> DayChuyen:
    cfg = copy.deepcopy(dc.cfg)
    for d in cfg["dem"]:
        if d["id"] == dem:
            d["hien_tai"] = d["muc_tieu"] = muc
    return DayChuyen(cfg)


def de_xuat_muc_dem(dc: DayChuyen, luc: str | int = "10:00", cs: ChinhSach | None = None) -> pd.DataFrame:
    """Đề xuất mức đệm (mục 7.1) và kiểm chứng bằng mô phỏng: máy tệ nhất phía trước hỏng, mức đệm hiện tại vs đề xuất.

    Hai con số đặt cạnh nhau: đệm dày hơn giữ cho công đoạn sau không đói hàng (hàng ra cuối chuyền đủ hơn),
    đổi lại là thêm tồn bán thành phẩm – và phần đệm đã dùng vẫn phải bù lại sau đó (quy ước mục 10).
    """
    cs = cs or ChinhSach(muc=2)
    dong = []
    for b, info in dc.dem.items():
        ung_vien = [(m, muc_dem_toi_thieu(dc, b, m)) for m in dc.may_cua(info["tu"]) if "sua_gio" in dc.may[m]]
        if not ung_vien:
            continue
        m, x = max(ung_vien, key=lambda v: v[1]["can"])
        de_xuat = min(info["suc_chua"], math.ceil(x["can"]))
        nhieu = [Nhieu(m, "nang_luc", -100, luc, x["sua_gio"])]
        kq0, kq1 = mo_phong(dc, nhieu, cs), mo_phong(_voi_dem(dc, b, de_xuat), nhieu, cs)
        cuoi = dc.thu_tu[-1]
        dong.append({
            "Đệm": dc.ten(b), "Đỡ cho": dc.ten(info["den"]), "Máy tệ nhất phía trước": m,
            "Hụt khi hỏng (sp/h)": round(x["hut"], 1), "Sửa (giờ, mức 80%)": x["sua_gio"],
            "Theo từng máy (sp)": ", ".join(f"{mm}: {math.ceil(v['can'])}" for mm, v in ung_vien),
            "Mức hiện tại": info["muc_tieu"], "Đề xuất": de_xuat, "Sức chứa": info["suc_chua"],
            "Tồn thêm (sp)": max(0, de_xuat - info["muc_tieu"]),
            "Lắp ráp ra 16:00 – hiện tại": round(kq0.cum[cuoi][dc.ca]),
            "Lắp ráp ra 16:00 – đề xuất": round(kq1.cum[cuoi][dc.ca]),
            "Tăng ca cần – hiện tại (phút)": kq0.tang_ca_can(),
            "Tăng ca cần – đề xuất (phút)": kq1.tang_ca_can(),
        })
    return pd.DataFrame(dong)


def sinh_rui_ro(dc: DayChuyen, rnd: random.Random) -> list[Nhieu]:
    """Rút ngẫu nhiên các sự cố của một ca từ thông số rủi ro – mỗi rủi ro vẫn là một nhiễu theo mẫu chung.

    Engine không biết trước: máy nào hỏng, lúc nào, sửa lệch dự kiến bao nhiêu, các lần dừng ngắn.
    """
    pb = dc.cfg.get("phan_bo_sua", [])
    dn = dc.cfg.get("dung_ngan")
    ds = []
    for m, info in dc.may.items():
        if rnd.random() < info.get("hong_trong_ca", 0.0):
            u = rnd.random()
            lech = next((x["lech_gio"] for x in pb if u <= x["xac_suat_cong_don"]), pb[-1]["lech_gio"] + 1 if pb else 0)
            ds.append(Nhieu(m, "nang_luc", -100, rnd.randrange(0, dc.ca, 5), max(0.5, info.get("sua_gio", 1) + lech),
                            mo_ta=f"{m} hỏng"))
        if dn and rnd.random() < dn["xac_suat_moi_may"]:
            ds.append(Nhieu(m, "nang_luc", -100, rnd.randrange(0, dc.ca, 5),
                            rnd.randint(dn["phut_min"], dn["phut_max"]) / 60, mo_ta=f"{m} dừng ngắn"))
    return ds


def xac_suat_hoan_thanh(dc: DayChuyen, so_lan: int = 300, seed: int = 7, cs: ChinhSach | None = None) -> dict:
    """Xác suất hoàn thành kế hoạch hôm nay (mục 7.2): chạy kế hoạch ca qua engine `so_lan` lần với rủi ro rút ngẫu nhiên.

    Giản lược: các máy hỏng cùng lúc được sửa song song (chưa xét giới hạn một tổ bảo trì như TH2).
    """
    cs = cs or ChinhSach(muc=2)
    rnd = random.Random(seed)
    goc = mo_phong(dc, [], cs)
    dong = []
    for i in range(so_lan):
        nhieu = sinh_rui_ro(dc, rnd)
        kq = mo_phong(dc, nhieu, cs) if nhieu else goc
        tc = kq.tang_ca_can()
        don = danh_gia_don(kq, dc.tang_ca_max if tc is None else tc)
        dong.append({"Lần": i + 1, "Sự cố": "; ".join(n.mo_ta for n in nhieu) or "–",
                     "Máy hỏng": [n.diem for n in nhieu if n.mo_ta.endswith("hỏng")],
                     "Sản lượng 16:00": round(kq.san_luong()), "Tăng ca cần (phút)": tc,
                     "Đơn hôm nay kịp": all(d["Trạng thái"] == "Kịp" for d in don["don"] if d["Hạn"].startswith("hôm nay"))})
    df = pd.DataFrame(dong)
    tc = df["Tăng ca cần (phút)"]
    muc = dc.cfg.get("muc_dang_ky_tang_ca", 0.8)
    xep = sorted(math.inf if pd.isna(v) else v for v in tc)
    dang_ky = xep[min(len(xep) - 1, math.ceil(muc * len(xep)) - 1)]
    theo_may = []
    for m in dc.may:
        co = df[df["Máy hỏng"].map(lambda ds: m in ds)]
        if len(co):
            theo_may.append({"Máy": m, "Số lần hỏng": len(co),
                             "Tăng ca TB khi hỏng (phút)": round(co["Tăng ca cần (phút)"].fillna(dc.tang_ca_max).mean()),
                             "Đủ kế hoạch trong ca khi hỏng": (co["Tăng ca cần (phút)"] == 0).mean()})
    return {"bang": df, "so_lan": so_lan, "seed": seed,
            "p_trong_ca": float((tc == 0).mean()),
            "p_trong_gioi_han": float(tc.notna().mean()),
            "p_don_hom_nay": float(df["Đơn hôm nay kịp"].mean()),
            "muc_dang_ky": muc, "dang_ky_tang_ca": None if math.isinf(dang_ky) else int(dang_ky),
            "theo_may": pd.DataFrame(theo_may)}


# ---------------------------------------------------------------- phân tích tổng hợp
@dataclass
class PhanTich:
    nhieu: list[Nhieu]
    ke_hoach: KetQua
    phuong_an: list[dict]
    de_xuat: dict | None
    muc: str
    gui_cho: list[str]
    khong_lam_gi: dict
    tts: pd.DataFrame
    thu_tu_sua: pd.DataFrame | None
    quet_sua: pd.DataFrame | None
    xau: dict | None
    bao_tri: list[dict]
    giao_hang: dict | None
    bi_anh_huong: set
    dong_thoi_gian: list
    thong_diep: dict = field(default_factory=dict)

    def bang_phuong_an(self) -> pd.DataFrame:
        dong = []
        for r in self.phuong_an:
            pa = r["pa"]
            dong.append({
                "Phương án": pa.ten,
                "Bậc": BAC.get(pa.bac, ""),
                "Sản lượng ca (16:00)": round(r["san_luong"]),
                "Cứu được (sp)": round(r["cuu_duoc"]),
                "Tăng ca cần (phút)": r["tang_ca_de_xuat"] if r["tang_ca_de_xuat"] is not None else "> giới hạn",
                "Chi phí (VND)": round(r["chi_phi"], -3),
                "Xáo trộn kế hoạch": r["muc_xao_tron"],
                "Giữ được đơn": "✔" if r["giu_don"] else "✘",
                "Ghi chú": (r["ghi_chu"] + ("; " if r["ghi_chu"] and pa.ly_do else "") + pa.ly_do),
            })
        return pd.DataFrame(dong)


def chon_de_xuat(ket_qua: list[dict]) -> dict | None:
    kha_thi = [r for r in ket_qua if r["giu_don"] and r["pa"].bac >= 1]
    if not kha_thi:
        return None
    return min(kha_thi, key=lambda r: (r["tang_ca_de_xuat"], r["pa"].bac, r["chi_phi"]))


def phan_tich(dc: DayChuyen, nhieu: list[Nhieu], phuong_an_them: list[PhuongAn] = (),
              bo_chung: bool = False) -> PhanTich:
    kh = mo_phong(dc, [], ChinhSach(muc=1))
    luong = [n for n in nhieu if n.dai_luong != "thoi_gian"]
    tts = thoi_gian_chiu_dung(dc, luong)
    thu_tu_sua = so_sanh_thu_tu_sua(dc, luong, ChinhSach(muc=1))
    if thu_tu_sua is not None:  # một tổ bảo trì: các phương án chạy theo thứ tự sửa tốt nhất
        luong = thu_tu_sua.iloc[0]["_lich"]
    ds = ([] if bo_chung else phuong_an_chung(dc, luong))
    if bo_chung:
        ds.append(PhuongAn("Không làm gì", 0, ChinhSach(muc=0), tang_ca=False))
    ds += list(phuong_an_them)
    goc = mo_phong(dc, luong, ChinhSach(muc=0))
    ket_qua = [danh_gia(dc, luong, pa, goc) for pa in ds]
    khong_lam_gi = next(r for r in ket_qua if r["pa"].bac == 0)

    giao_hang = None
    for n in nhieu:
        if n.dai_luong == "thoi_gian" and n.diem in dc.chuyen:
            giao_hang = phan_tich_giao_hang(dc, n, kh)

    de_xuat = chon_de_xuat(ket_qua)
    if giao_hang:
        kip_xe = [p for p in giao_hang["phuong_an"] if p["Kịp hạn"]]
        if giao_hang["tre"] <= 0:
            muc = "Xanh"
        elif kip_xe:
            muc = "Vàng"
        else:
            muc = "Đỏ"
    else:
        # Xanh: chỉ cần chia tải / tăng tốc trong giới hạn (gần như không tốn), không tăng ca, không đổi thứ tự
        xanh = any(r["giu_don"] and r["pa"].bac <= 2 and r["tang_ca_de_xuat"] == 0 for r in ket_qua)
        muc = "Xanh" if xanh else "Vàng" if de_xuat else "Đỏ"
    gui_cho = {"Xanh": ["Bảo trì"], "Vàng": ["Bảo trì", "Kế hoạch"],
               "Đỏ": ["Bảo trì", "Kế hoạch", "Giao hàng & Sales"]}[muc]
    if giao_hang and giao_hang["tre"] > 0 and "Giao hàng & Sales" not in gui_cho:
        gui_cho.append("Giao hàng & Sales")  # sự cố giao hàng: Giao hàng luôn phải biết, dù sản xuất không đổi

    cs_dx = de_xuat["pa"].cs if de_xuat else ChinhSach(muc=2)
    kq_dx = de_xuat["kq"] if de_xuat else khong_lam_gi["kq"]
    pt = PhanTich(
        nhieu=list(nhieu), ke_hoach=kh, phuong_an=ket_qua, de_xuat=de_xuat, muc=muc, gui_cho=gui_cho,
        khong_lam_gi=khong_lam_gi, tts=tts, thu_tu_sua=thu_tu_sua,
        quet_sua=quet_thoi_gian_sua(dc, luong, cs_dx), xau=kich_ban_xau(dc, luong, cs_dx),
        bao_tri=cua_so_bao_tri(dc, kq_dx), giao_hang=giao_hang,
        bi_anh_huong=diem_bi_anh_huong(dc, khong_lam_gi["kq"], khong_lam_gi["don"]),
        dong_thoi_gian=dong_thoi_gian(khong_lam_gi["kq"]),
    )
    pt.thong_diep = thong_diep(dc, pt)
    return pt


# ---------------------------------------------------------------- đồng hồ quyết định (mục 7.3)
def quyet_luc(dc: DayChuyen, nhieu: list[Nhieu], pa: PhuongAn, t_d: int) -> dict:
    """Đánh giá phương án `pa` khi được quyết lúc `t_d`: trước đó dây chuyền chạy như không làm gì,
    hành động lẽ ra bắt đầu trước `t_d` dời tới `t_d` (giữ giờ kết thúc). Đặt gấp linh kiện do `danh_gia` tự sinh."""
    hd = []
    for n in pa.cs.hanh_dong:
        if n.t0 >= t_d:
            hd.append(n)
        elif n.thoi_luong_gio is None:
            hd.append(replace(n, bat_dau=t_d))
        elif n.t1(0) > t_d:
            hd.append(replace(n, bat_dau=t_d, thoi_luong_gio=(n.t1(0) - t_d) / 60))
    return danh_gia(dc, nhieu, replace(pa, cs=replace(pa.cs, tu=t_d, hanh_dong=hd)))


def _muon_nhat(dung, lo: int, hi: int, buoc: int = 15) -> int:
    """t lớn nhất trong [lo, hi] trước lần đầu dung(t) sai, biết dung(lo) đúng.

    Quét thô mỗi `buoc` phút tìm khoảng đầu tiên bị sai rồi tìm nhị phân trong khoảng đó (giả định đơn điệu
    trong khoảng `buoc` phút). Không tìm nhị phân trên cả ca vì có thể không đơn điệu: vd. TH3 quyết đổi thứ tự
    lúc 15:00 tốt hơn 14:50 (lô L-A về đúng 15:00, khỏi đổi mã hai lần)."""
    t = lo
    while t < hi:
        t2 = min(t + buoc, hi)
        if not dung(t2):
            while t2 - t > 1:
                mid = (t + t2) // 2
                t, t2 = (mid, t2) if dung(mid) else (t, mid)
            return t
        t = t2
    return hi


def dong_ho_quyet_dinh(dc: DayChuyen, pt: PhanTich, buoc_cham: int = 30, dung_sai: float = 0.05) -> pd.DataFrame:
    """Mỗi phương án: phải quyết muộn nhất lúc nào để không mất gì, và đến lúc nào thì hết giữ được đơn.

    "Không mất gì" = sản lượng 16:00 không giảm (quá `dung_sai` sp), tăng ca đề xuất không tăng và vẫn giữ đơn
    như khi quyết ngay lúc phát hiện; mốc = phút cuối cùng trước lần đầu bị mất (xem `_muon_nhat`).
    "Mỗi phút chậm" = độ dốc trung bình trong `buoc_cham` phút sau mốc.
    Thời điểm tính trong phút kể từ 08:00; <NA> = không có mốc (vd. ngay lúc phát hiện đã không giữ được đơn).
    """
    vo_cung = 10 ** 9
    dong = []
    for r in pt.phuong_an:
        pa, nhieu = r["pa"], r["kq"].nhieu
        if pa.bac == 0 or not nhieu:
            continue
        t_inc = min(max(0, min(n.t0 for n in nhieu)), dc.ca)
        hang = {"Phương án": pa.ten, "Phát hiện lúc": t_inc, "Muộn nhất không mất gì": None, "Còn (phút)": None,
                "Mỗi phút chậm mất (sp)": None, "Mỗi phút chậm thêm tăng ca (phút)": None,
                "Hết hiệu lực (giữ đơn)": None, "Ghi chú": ""}
        if not pa.kha_thi:
            hang["Ghi chú"] = "không khả thi" + (f" – {pa.ly_do}" if pa.ly_do else "")
            dong.append(hang)
            continue
        nho: dict[int, dict] = {}

        def kq_luc(t):
            if t not in nho:
                nho[t] = quyet_luc(dc, nhieu, pa, t)
            return nho[t]

        def tc(x):
            return vo_cung if x["tang_ca_de_xuat"] is None else x["tang_ca_de_xuat"]

        goc = kq_luc(t_inc)

        def khong_mat(t):
            x = kq_luc(t)
            return (x["san_luong"] >= goc["san_luong"] - dung_sai and tc(x) <= tc(goc)
                    and (x["giu_don"] or not goc["giu_don"]))

        moc = _muon_nhat(khong_mat, t_inc, dc.ca)
        hang["Muộn nhất không mất gì"], hang["Còn (phút)"] = moc, moc - t_inc
        t2 = min(moc + buoc_cham, dc.ca)
        if t2 > moc:
            a, b = kq_luc(moc), kq_luc(t2)
            hang["Mỗi phút chậm mất (sp)"] = round((a["san_luong"] - b["san_luong"]) / (t2 - moc), 2)
            if tc(a) < vo_cung and tc(b) < vo_cung:
                hang["Mỗi phút chậm thêm tăng ca (phút)"] = round((tc(b) - tc(a)) / (t2 - moc), 2)
        else:
            hang["Ghi chú"] = "quyết lúc nào trong ca cũng như nhau"
        if goc["giu_don"]:
            hang["Hết hiệu lực (giữ đơn)"] = _muon_nhat(lambda t: kq_luc(t)["giu_don"], t_inc, dc.ca)
        else:
            hang["Ghi chú"] = "ngay lúc phát hiện đã không giữ được đơn"
        dong.append(hang)
    df = pd.DataFrame(dong, columns=["Phương án", "Phát hiện lúc", "Muộn nhất không mất gì", "Còn (phút)",
                                     "Mỗi phút chậm mất (sp)", "Mỗi phút chậm thêm tăng ca (phút)",
                                     "Hết hiệu lực (giữ đơn)", "Ghi chú"])
    phut_cot = ["Phát hiện lúc", "Muộn nhất không mất gì", "Còn (phút)", "Hết hiệu lực (giữ đơn)"]
    return df.astype({c: "Int64" for c in phut_cot})


# ---------------------------------------------------------------- câu trả lời cho từng bộ phận
def thong_diep(dc: DayChuyen, pt: PhanTich) -> dict[str, list[str]]:
    bt, kh, gh = [], [], []
    dx, k0 = pt.de_xuat, pt.khong_lam_gi
    hong = [n for n in pt.nhieu if n.dai_luong == "nang_luc" and n.diem in dc.may]

    # Bảo trì
    if pt.thu_tu_sua is not None:
        tot = pt.thu_tu_sua.iloc[0]
        bt.append(f"Một tổ bảo trì, nhiều máy hỏng → sửa theo thứ tự **{tot['Thứ tự sửa']}** "
                  f"(ít giờ tăng ca nhất để đủ kế hoạch và trả đệm về mục tiêu: "
                  f"{thoi_luong(tot['Tăng ca để đủ kế hoạch + trả đệm (phút)'])}).")
    elif hong:
        for n in hong:
            if n.thay_doi <= -100:
                du_kien = f"dự kiến {n.thoi_luong_gio:g} giờ" if n.thoi_luong_gio else "chưa có thời gian sửa dự kiến"
                bt.append(f"Ưu tiên sửa {n.diem}: {du_kien}. Cập nhật tiến độ để hệ thống tính lại.")
    for _, r in pt.tts.iterrows():
        if r["Kết luận"] != "–" and r["Thời gian sửa (giờ)"] is not None:
            bt.append(f"{r['Máy']}: hụt {r['Hụt (sp/h)']:g} sp/h; {r['Đệm sau']} đỡ được "
                      f"{r['Đệm sau đỡ được (giờ)'] if r['Đệm sau đỡ được (giờ)'] is not None else '–'} giờ "
                      f"so với {r['Thời gian sửa (giờ)']:g} giờ sửa → {r['Kết luận'].lower()}.")
    if pt.xau:
        x = pt.xau
        bt.append(f"Cảnh báo sớm: máy chạy chậm bất thường thường là dấu hiệu sắp hỏng. Nếu {x['nhieu'].diem} hỏng hẳn "
                  f"lúc {gio(x['nhieu'].t0)}: ca còn {x['san_luong']:.0f} sp (thiếu {x['thieu']:.0f}), "
                  f"tăng ca {thoi_luong(x['tang_ca'])}. → Kiểm tra {x['nhieu'].diem} trong giờ nghỉ trưa, "
                  f"không đợi máy hỏng hẳn.")
    for w in pt.bao_tri:
        bt.append(f"Cơ hội bảo dưỡng: {gio(w['tu'])}–{gio(w['den'])} {dc.ten(w['cong_doan'])} chỉ cần "
                  f"{w['so_may_can']} máy → bảo dưỡng ngắn 1 máy trong khung này, không mất sản lượng.")
    if dx:
        kq = dx["kq"]
        for s in dc.thu_tu:
            ds = [t for t in range(dc.ca) if kq.trang_thai[s][t] == "tăng tốc"]
            if ds:
                ket = dc.ca + (dx["tang_ca_de_xuat"] or 0)
                bt.append(f"Không xếp bảo dưỡng {dc.ten(s)} trong khung {gio(ds[0])}–{gio(ket)} "
                          f"(đang chạy cao tải / tăng ca).")
        tren = {m: v for m, v in kq.tren_chuan.items() if v > 0}
        if tren:
            bt.append("Máy chạy trên chuẩn hôm nay (theo dõi hao mòn, nhiệt): "
                      + ", ".join(f"{m} {thoi_luong(v)}" for m, v in tren.items()) + ".")
    if not bt:
        bt.append("Không có việc gấp cho Bảo trì từ sự cố này.")

    # Kế hoạch
    if dx:
        pa = dx["pa"]
        kh.append(f"Phương án đề xuất: **{pa.ten}** – sản lượng ca {dx['san_luong']:.0f}/{dx['kq'].ke_hoach_tong:.0f} "
                  f"(cứu thêm {dx['cuu_duoc']:.0f} sp so với không làm gì).")
        if pa.mo_ta:
            kh.append(pa.mo_ta)
        if dx["ghi_chu"] and dx["ghi_chu"] != pa.mo_ta:
            kh.append(f"Kèm theo: {dx['ghi_chu']}.")
        tc = dx["tang_ca_de_xuat"]
        if tc:
            kh.append(f"Tăng ca **{thoi_luong(tc)}** sau 16:00 (công đoạn đầu), các công đoạn sau chạy thêm "
                      f"~{dc.xuyen_chuyen} phút xuyên chuyền. Giới hạn: {dc.tang_ca_max // 60} giờ/người/ngày ✓.")
        elif dx["tang_ca_ke_hoach"]:
            kh.append(f"Không bắt buộc tăng ca: thiếu {dx['kq'].thieu():.0f} sp so với kế hoạch được kho thành phẩm bù. "
                      f"Muốn trả kho về mức cũ cần thêm {thoi_luong(dx['tang_ca_ke_hoach'])}.")
        else:
            kh.append("Không cần tăng ca.")
        if dx["kq"].so_lan_doi_ma:
            sp = dx["kq"].sp_lr
            doi = [t for t in range(1, dc.ca) if sp[t] != sp[t - 1]]
            kh.append("Đổi mã ở Lắp ráp: " + "; ".join(f"{gio(t - dc.doi_ma)} bắt đầu đổi sang {sp[t]}"
                                                      for t in doi) + f" (mỗi lần {dc.doi_ma} phút).")
    else:
        kh.append("Không phương án nào trong thang xử lý giữ được tất cả đơn → chuyển line/ca sau hoặc báo khách.")
    if pt.quet_sua is not None and len(pt.quet_sua):
        q = pt.quet_sua
        nguong = dc.cfg.get("muc_dang_ky_tang_ca", 0.8)
        hang = q[q["Xác suất sửa xong trong thời gian này"] >= nguong]
        if len(hang):
            r = hang.iloc[0]
            kh.append(f"Thời gian sửa không chắc chắn: tăng ca từ {thoi_luong(q['Tăng ca (phút)'].min())} đến "
                      f"{thoi_luong(q['Tăng ca (phút)'].max())}. Đề xuất đăng ký trước "
                      f"**{thoi_luong(r['Tăng ca (phút)'])}** (đủ trong {r['Xác suất sửa xong trong thời gian này']:.0%} "
                      f"khả năng), tính lại khi Bảo trì cập nhật tiến độ.")
    mai = (dx or k0)["don"]
    kh.append(f"Ngày mai cần {mai['phut_ngay_mai']:.0f}/{dc.ca} phút để làm nốt đơn"
              + (f" (gồm bù {mai['bu_dem']:.0f} sp đệm)" if mai["bu_dem"] > 0.5 else "") + ".")

    # Giao hàng & Sales
    x = pt.giao_hang if pt.giao_hang and pt.giao_hang["tre"] > 0 else None
    if x:
        p = x["de_xuat"]
        gh.append(f"Đề xuất giao hàng: **{p['Phương án']}** – {p['Kết quả']}, hạn {gio(x['han'])}; chi phí "
                  f"~{p['Chi phí (VND)']:,.0f} VND. Sản xuất giữ nguyên kế hoạch." if p else
                  f"Không phương án giao hàng nào kịp hạn {gio(x['han'])}: báo khách ngay, giao tách đợt.")
    for d in (dx or k0)["don"]["don"]:
        xe_tre = x and d["Đơn"] == x["don"]["id"]
        gh.append(f"{d['Đơn']} (khách {d['Khách']}, {d['Số lượng']:.0f} {d['Mã']}, {d['Hạn']}): "
                  + (f"**hàng đủ nhưng xe {x['xe']['id']} trễ** – {d['Ghi chú']}, cần phương án giao hàng."
                     if xe_tre else f"**{d['Trạng thái']}** – {d['Ghi chú']}."))
    tre0 = [d["Đơn"] for d in k0["don"]["don"] if d["Trạng thái"] != "Kịp"]
    if tre0:
        gh.append(f"Nếu không làm gì: {', '.join(tre0)} có nguy cơ trễ.")
    for g in (dx or k0)["kq"].don_gap:
        t = (dx or k0)["kq"].gio_dat((dx or k0)["kq"].ke_hoach_tong)
        gh.append(f"{g['id']}: {'NHẬN ĐƯỢC' if dx else 'chưa nhận được'} – xong lúc {gio(t)}, "
                  f"hạn {gio(g['han'])} (dư {thoi_luong(g['han'] - t) if t is not None else '–'}).")
    if pt.giao_hang:
        x = pt.giao_hang
        gh.append(f"Chuyến {x['xe']['id']} đi {gio(x['gio_di'])} → đến khách {gio(x['gio_den'])}, hạn {gio(x['han'])}"
                  f" → {'trễ ' + thoi_luong(x['tre']) if x['tre'] > 0 else 'kịp'}.")
        gh.append(f"Kho thành phẩm cao nhất {x['ton_kho_dinh']:.0f}/{x['suc_chua_kho']} sp trước khi xe đến → "
                  + ("ĐẦY: chuyền phải dừng (sự cố cuối chuỗi lan ngược)." if x["kho_day"] else "chưa đầy, chuyền không bị chặn."))
    if pt.muc == "Đỏ":
        gh.append("Mức Đỏ: báo khách sớm, đề xuất giao tách đợt.")
    return {"Bảo trì": bt, "Kế hoạch": kh, "Giao hàng & Sales": gh}


# ---------------------------------------------------------------- giải thích phương án đề xuất
CACH_LAM = {1: "dồn việc của điểm bị sự cố sang các máy còn chạy, chia theo tỷ lệ công suất tối đa để các máy cùng mức tải",
            2: "cho máy còn chạy lên trên chuẩn, tới công suất tối đa cho phép",
            3: "đổi thứ tự sản xuất: chạy mã còn đủ điều kiện trước, quay lại mã bị thiếu khi có hàng",
            4: "tăng ca sau giờ ca chính", 5: "chuyển sang line khác / ca sau", 6: "báo khách, giao tách đợt"}


def giai_thich_de_xuat(dc: DayChuyen, pt: PhanTich) -> dict:
    """Vì sao chọn phương án đề xuất (so với từng phương án khác) và nó tối ưu thế nào – sinh từ chính các con số
    engine đã tính, theo đúng luật của chon_de_xuat: giữ mọi đơn → ít tăng ca nhất → bậc thấp nhất → rẻ nhất."""
    gh = pt.giao_hang if pt.giao_hang and pt.giao_hang["tre"] > 0 else None
    if gh:
        p, kip = gh["de_xuat"], [x for x in gh["phuong_an"] if x["Kịp hạn"]]
        k0 = pt.khong_lam_gi
        vi_sao = [f"Sản xuất không bị ảnh hưởng ({k0['san_luong']:.0f}/{dc.ke_hoach} sp, không cần tăng ca) – vấn đề "
                  f"nằm ở xe {gh['xe']['id']}: hàng đến khách {gio(gh['gio_den'])}, trễ {thoi_luong(gh['tre'])} so "
                  f"với hạn {gio(gh['han'])}. Đổi kế hoạch sản xuất không giải quyết được.",
                  "Luật chọn: chỉ xét phương án giao **kịp hạn**, trong đó lấy phương án **rẻ nhất**."]
        if p:
            vi_sao.append(f"Có {len(kip)} phương án kịp hạn; **{p['Phương án']}** rẻ nhất "
                          f"(~{p['Chi phí (VND)']:,.0f} VND).")
        loai = [(x["Phương án"], f"{x['Kết quả']} – " + ("đắt hơn" if x["Kịp hạn"] else "không kịp hạn cho đủ đơn")
                 + ("; vẫn nên làm song song để khách chủ động" if x["Phương án"].startswith("Báo khách") else ""))
                for x in gh["phuong_an"] if x is not p]
        du = gh["han"] - phut(gh["xe"]["gio_di"]) - int(gh["xe"]["duong_gio"] * 60)
        toi_uu = ([f"Giữ nguyên giờ đi cũ {gh['xe']['gio_di']} bằng xe ngoài → {p['Kết quả']}, dư {thoi_luong(du)} "
                   f"so với hạn."] if p else ["Không có cách giao kịp: báo khách ngay, thỏa thuận giao tách đợt."])
        toi_uu += ["Không tốn tăng ca, không xáo trộn kế hoạch sản xuất.",
                   f"Đã kiểm tra lan ngược: kho thành phẩm cao nhất {gh['ton_kho_dinh']:.0f}/{gh['suc_chua_kho']} sp "
                   + ("→ đầy, chuyền sẽ bị chặn – cần xử lý kho." if gh["kho_day"] else "→ chưa đầy, chuyền không bị chặn.")]
        return {"ten": p["Phương án"] if p else None, "vi_sao": vi_sao, "loai": loai, "toi_uu": toi_uu}

    dx, k0 = pt.de_xuat, pt.khong_lam_gi
    tc = lambda r: thoi_luong(r["tang_ca_de_xuat"]) if r["tang_ca_de_xuat"] is not None else "> giới hạn"
    if dx is None:
        return {"ten": None,
                "vi_sao": ["Không phương án nào giữ được mọi đơn, kể cả khi tăng ca tới giới hạn."],
                "loai": [(r["pa"].ten, r["pa"].ly_do or "vẫn trễ đơn") for r in pt.phuong_an if r["pa"].bac >= 1],
                "toi_uu": ["Chuyển line / ca sau, báo khách sớm và giao tách đợt."]}

    khoa = lambda r: (r["tang_ca_de_xuat"], r["pa"].bac, r["chi_phi"])
    kha_thi = sorted((r for r in pt.phuong_an if r["giu_don"] and r["pa"].bac >= 1), key=khoa)
    vi_sao = [f"So với không làm gì: sản lượng ca {k0['san_luong']:.0f} → **{dx['san_luong']:.0f} sp** "
              f"(cứu {dx['cuu_duoc']:+.0f})" + ("; không làm gì thì trễ đơn." if not k0["giu_don"] else "."),
              "Luật chọn: trong các phương án **giữ được mọi đơn**, lấy phương án **ít tăng ca nhất**; bằng nhau thì "
              "lấy **bậc thấp nhất** trên thang xử lý (ít xáo trộn); vẫn bằng thì lấy **rẻ nhất**."]
    ke = kha_thi[1] if len(kha_thi) > 1 else None
    if ke is None:
        vi_sao.append("Đây là phương án **duy nhất** giữ được mọi đơn.")
    elif ke["tang_ca_de_xuat"] > dx["tang_ca_de_xuat"]:
        vi_sao.append(f"Quyết định ở bước 1: tăng ca **{tc(dx)}**, ít nhất trong {len(kha_thi)} phương án giữ đơn "
                      f"(kế tiếp là {ke['pa'].ten}: {tc(ke)}).")
    elif ke["pa"].bac > dx["pa"].bac:
        vi_sao.append(f"Quyết định ở bước 2: cùng tăng ca {tc(dx)} với {ke['pa'].ten} nhưng ở bậc thấp hơn "
                      f"({BAC[dx['pa'].bac]}) – dùng bước nhẹ nhất là đủ.")
    else:
        vi_sao.append(f"Quyết định ở bước 3: cùng tăng ca và cùng bậc với {ke['pa'].ten} nhưng rẻ hơn "
                      f"~{ke['chi_phi'] - dx['chi_phi']:,.0f} VND.")

    loai = []
    for r in pt.phuong_an:
        p = r["pa"]
        if r is dx or p.bac == 0:
            continue
        if not r["giu_don"]:
            ly = p.ly_do or "vẫn trễ đơn"
        elif r["tang_ca_de_xuat"] > dx["tang_ca_de_xuat"]:
            ly = f"cần tăng ca {tc(r)}" + (f", nhiều hơn {thoi_luong(r['tang_ca_de_xuat'] - dx['tang_ca_de_xuat'])}"
                                           if dx["tang_ca_de_xuat"] else " – đề xuất không cần tăng ca")
            if r["chi_phi"] < dx["chi_phi"] - 0.5:
                ly += f" (dù rẻ hơn ~{dx['chi_phi'] - r['chi_phi']:,.0f} VND)"
        elif p.bac > dx["pa"].bac:
            ly = f"cùng tăng ca nhưng dùng bước nặng hơn ({BAC.get(p.bac, p.bac)}) – không cần thiết"
        elif r["chi_phi"] > dx["chi_phi"] + 0.5:
            ly = f"cùng tăng ca, cùng bậc nhưng đắt hơn ~{r['chi_phi'] - dx['chi_phi']:,.0f} VND"
        else:
            ly = "kết quả tương đương"
        if r["giu_don"] and r["san_luong"] > dx["san_luong"] + 0.5:
            ly += f"; làm được nhiều hơn {r['san_luong'] - dx['san_luong']:.0f} sp trong ca nhưng không cần cho đơn"
        loai.append((p.ten, ly))

    p, kq = dx["pa"], dx["kq"]
    # phương án riêng của kịch bản tự mô tả cách làm; phương án chung dùng mô tả theo bậc
    toi_uu = [f"Cách làm: {p.ten} – {p.mo_ta}." if p.mo_ta else f"Cách làm: {CACH_LAM.get(p.bac, BAC.get(p.bac, ''))}."]
    if dx["gio_tren_chuan"] > 0:
        toi_uu.append(f"Máy chạy trên chuẩn tổng {dx['gio_tren_chuan']:.1f} giờ-máy, mỗi máy không quá "
                      f"{dc.tren_chuan_max // 60} giờ/ca (giới hạn hao mòn).")
    if kq.so_lan_doi_ma:
        toi_uu.append(f"{kq.so_lan_doi_ma} lần đổi mã ({kq.so_lan_doi_ma * dc.doi_ma} phút mất máy) – đổi lấy việc "
                      "chuyền không phải đứng chờ.")
    if pt.thu_tu_sua is not None and len(pt.thu_tu_sua) > 1:
        a, b = pt.thu_tu_sua.iloc[0], pt.thu_tu_sua.iloc[1]
        cot = next(c for c in pt.thu_tu_sua.columns if c.startswith("Tăng ca"))
        toi_uu.append(f"Một tổ bảo trì: sửa theo thứ tự **{a['Thứ tự sửa']}** – tăng ca {a[cot]} phút, so với "
                      f"{b[cot]} phút nếu sửa {b['Thứ tự sửa']}.")
    toi_uu.append(f"Tăng ca **{tc(dx)}** – vừa đủ để giữ mọi đơn và trả các đệm về mục tiêu, không dư."
                  if dx["tang_ca_de_xuat"] else "Không cần tăng ca.")
    kem = [g for g in dx["ghi_chu"].split("; ") if g and g != p.mo_ta]
    if kem:
        toi_uu.append(f"Kèm theo: {'; '.join(kem)}.")
    ct = [f"{k} {v:,.0f}" for k, v in dx["chi_phi_ct"].items() if v > 0.5]
    toi_uu.append(f"Chi phí ~{dx['chi_phi']:,.0f} VND" + (f" = {' + '.join(ct)}." if ct else "."))
    return {"ten": p.ten, "vi_sao": vi_sao, "loai": loai, "toi_uu": toi_uu}
