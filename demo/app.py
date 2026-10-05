"""Giao diện demo D3 – Chain Impact Propagation.  Chạy (từ thư mục demo):  streamlit run app.py"""
from __future__ import annotations

import time as _time
from datetime import datetime, time, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from engine import (DAI_LUONG, EPS, DayChuyen, Nhieu, ban_do_rui_ro, de_xuat_muc_dem, dong_ho_quyet_dinh,
                    dong_thoi_gian, gio, khoang_trang_thai, phan_tich, thoi_luong, xac_suat_hoan_thanh)
from giao_dien import (BE_MAT, CHU, CHU_2, CHU_MO, DANH_MUC, LUOI, MAU_MUC, MAU_TT, NHAN, NHOM_TT, TRUC, TRUNG_TINH,
                       BIEU_TUONG_MUC, badge_muc, chu_giai, css, e, html_, md, rgba, the_kpi, tieu_de_muc, ve)
from scenarios import chay, kich_ban

st.set_page_config(page_title="D3 – Chain Impact Propagation", page_icon="🏭", layout="wide")
css()

NGAY = datetime(2026, 10, 5, 8, 0)
XANH_LA, DO = "#0ca30c", "#d03b3b"


def dt(t: float) -> datetime:
    return NGAY + timedelta(minutes=float(t))


# ---------------------------------------------------------------- tính toán (cache)
@st.cache_resource
def day_chuyen() -> DayChuyen:
    return DayChuyen.tai()


@st.cache_resource(show_spinner="Engine đang mô phỏng các phương án…")
def chay_kich_ban(ma: str):
    t = _time.perf_counter()
    pt, rieng = chay(ma, day_chuyen())
    return pt, rieng, _time.perf_counter() - t


@st.cache_resource(show_spinner="Engine đang mô phỏng các phương án…")
def chay_tu_nhap(khoa: tuple):
    t = _time.perf_counter()
    pt = phan_tich(day_chuyen(), [Nhieu(**dict(k)) for k in khoa])
    return pt, {}, _time.perf_counter() - t


@st.cache_resource(show_spinner="Đang tính đồng hồ quyết định (chạy lại mỗi phương án theo từng giờ quyết)…")
def dong_ho(khoa: str, _pt):
    t = _time.perf_counter()
    return dong_ho_quyet_dinh(day_chuyen(), _pt), _time.perf_counter() - t


@st.cache_resource(show_spinner="Đang diễn tập từng máy hỏng…")
def dien_tap_may(luc: str):
    return ban_do_rui_ro(day_chuyen(), luc), de_xuat_muc_dem(day_chuyen(), luc)


@st.cache_resource(show_spinner="Đang chạy kế hoạch ca qua nhiều kịch bản rủi ro…")
def dien_tap_ca(so_lan: int, seed: int):
    return xac_suat_hoan_thanh(day_chuyen(), so_lan, seed)


dc = day_chuyen()
kbs = kich_ban()


def ket_thuc(r: dict) -> int:
    """Phút cuối cùng của phương án: hết ca, hoặc hết giờ tăng ca đề xuất."""
    return dc.ca + (r["tang_ca_de_xuat"] or 0) if r["pa"].tang_ca else dc.ca


def nhan_kb(ma: str) -> tuple[str, str]:
    ten = kbs[ma].ten
    return tuple(ten.split(": ", 1)) if ": " in ten else ("", ten)


def pt_tram(p: float) -> str:
    """Phần trăm; giữ 1 chữ số lẻ khi làm tròn sẽ thành 0% hoặc 100% sai lệch."""
    return f"{p:.1%}" if 0 < p < 1 and f"{p:.0%}" in ("0%", "100%") else f"{p:.0%}"


# ---------------------------------------------------------------- bản đồ lan truyền (lớp Logic, có hoạt ảnh)
def vi_tri() -> dict:
    pos, G = {}, dc.G
    dong = [n for n in ["DAP", "B1", "GC", "B2", "LR", dc.fg["id"]] if n in G] or dc.thu_tu
    for i, n in enumerate(dong):
        pos[n] = (i * 1.6, 0)
    for s in dc.thu_tu:
        ms = dc.may_cua(s)
        for j, m in enumerate(ms):
            pos[m] = (pos[s][0] + (j - (len(ms) - 1) / 2) * 0.55, 1.1)
        pos[f"NG-{s}"] = (pos[s][0], -0.9)
    lks = list(dc.linh_kien)
    for j, lk in enumerate(lks):
        x = pos[dc.cd_lap][0] + (j - (len(lks) - 1) / 2) * 0.9
        pos[lk] = (x, -1.8)
        pos[dc.linh_kien[lk]["nha_cung_cap"]] = (x, -2.7)
    x0 = pos[dc.fg["id"]][0]
    for j, sp in enumerate(dc.san_pham):
        pos[sp] = (x0 + 1.4, 0.7 - j * 1.4)
    for j, d in enumerate(dc.don_hang):
        pos[d["id"]] = (x0 + 2.8, 1.1 - j * 1.1)
    kh = [n for n, a in G.nodes(data=True) if a["loai"] == "khach_hang"]
    for j, n in enumerate(kh):
        pos[n] = (x0 + 4.2, 0.6 - j * 1.4)
    xe = [n for n, a in G.nodes(data=True) if a["loai"] == "chuyen_giao"]
    for j, n in enumerate(xe):
        pos[n] = (x0 + 4.2, 1.6 + j * 0.8)
    for n in G:
        pos.setdefault(n, (0, -3.5))
    return pos


POS = vi_tri()
NUT = list(dc.G.nodes(data=True))
CANH = list(dc.G.edges())
HINH = {"cong_doan": "square", "may": "circle", "dem": "diamond", "kho": "square", "linh_kien": "triangle-up",
        "nha_cung_cap": "triangle-down", "san_pham": "hexagon", "don_hang": "star", "khach_hang": "pentagon",
        "chuyen_giao": "cross", "nguoi": "circle"}
XAU = set(MAU_TT) - {"chạy", "xong", "tăng tốc", "trên chuẩn"}


def trang_thai_nut(kq, t: int, t_inc: int, don_tre: set) -> dict[str, str]:
    """Trạng thái từng nút của đồ thị tại phút t (cùng quy tắc với khoang_trang_thai trong engine)."""
    s: dict[str, str] = {}
    t = min(t, kq.N - 1)
    for cd in dc.thu_tu:
        s[cd] = kq.trang_thai[cd][t] or "chạy"
    for m, c in dc.may.items():
        v, tt_cd = kq.toc_do[m][t], kq.trang_thai[c["cong_doan"]][t]
        s[m] = ("xong" if tt_cd == "xong" else "hỏng / dừng" if v <= EPS and tt_cd != "đổi mã"
                else "trên chuẩn" if v > c["chuan"] + EPS else "chạy")
    for b, info in dc.dem.items():
        v = kq.dem[b][t + 1]
        s[b] = "cạn" if v <= 0.5 else "đầy" if v >= info["suc_chua"] - 0.5 else "chạy"
    for lk in dc.linh_kien:
        s[lk] = "hết" if kq.lk[lk][t + 1] <= EPS else "chạy"
    for d in don_tre:
        if t >= t_inc:
            s[d] = "dừng máy"
            for v in dc.G.successors(d):
                s[v] = "dừng máy"
    return s


def nhan_nut(n: str, a: dict, kq, t: int) -> str:
    if a["loai"] == "dem":
        return f"{n} · {kq.dem[n][min(t + 1, kq.N)]:.0f}"
    if a["loai"] == "linh_kien":
        return f"{n} · {kq.lk[n][min(t + 1, kq.N)]:.0f}"
    if a["loai"] == "kho":
        return f"TP · {kq.M[min(t, kq.N)]:.0f}"
    if a["loai"] == "nguoi":
        return a["ten"].split(" (")[0]
    return n


def ban_do_lan_truyen(r: dict, nhieu: list[Nhieu], buoc: int = 10) -> go.Figure:
    kq = r["kq"]
    den = ket_thuc(r)
    t_inc = min((n.t0 for n in nhieu), default=0)
    goc = {n.diem for n in nhieu}
    don_tre = {d["Đơn"] for d in r["don"]["don"] if d["Trạng thái"] != "Kịp" and d["Đơn"] in dc.G}

    def du_lieu(t):
        s = trang_thai_nut(kq, t, t_inc, don_tre)
        mau = [MAU_TT.get(s.get(n, "chạy"), TRUNG_TINH) for n, _ in NUT]
        vien = ["#ffffff" if n in goc and t >= t_inc else rgba("#ffffff", .25) for n, _ in NUT]
        rong = [3 if n in goc and t >= t_inc else 1 for n, _ in NUT]
        chu = [nhan_nut(n, a, kq, t) for n, a in NUT]
        hover = [f"<b>{e(a['ten'])}</b><br>{e(s.get(n, 'bình thường'))}" +
                 ("<br><b>ĐIỂM SỰ CỐ</b>" if n in goc else "") for n, a in NUT]
        xau = [(u, v) for u, v in CANH if s.get(u) in XAU and s.get(v) in XAU or
               (u in goc and t >= t_inc and s.get(v) in XAU) or (v in goc and t >= t_inc and s.get(u) in XAU)]
        ex, ey = [], []
        for u, v in xau:
            ex += [POS[u][0], POS[v][0], None]
            ey += [POS[u][1], POS[v][1], None]
        so_xau = sum(1 for n, _ in NUT if s.get(n) in XAU)
        canh_do = go.Scatter(x=ex or [None], y=ey or [None], mode="lines", hoverinfo="skip", showlegend=False,
                             line=dict(color=rgba("#e66767", .85), width=4))
        nut = go.Scatter(
            x=[POS[n][0] for n, _ in NUT], y=[POS[n][1] for n, _ in NUT], mode="markers+text", text=chu,
            textposition="bottom center", textfont=dict(color=CHU_2, size=11), hovertext=hover, hoverinfo="text",
            showlegend=False,
            marker=dict(size=[34 if a["loai"] in ("cong_doan", "kho") else 18 if a["loai"] == "nguoi" else 24
                              for _, a in NUT],
                        symbol=[HINH.get(a["loai"], "circle") for _, a in NUT], color=mau,
                        line=dict(color=vien, width=rong)))
        tieu = (f"<b>{gio(t)}</b>  <span style='color:{CHU_MO}'>"
                + ("trước sự cố" if t < t_inc else f"{so_xau} điểm bị ảnh hưởng") + "</span>")
        return [canh_do, nut], tieu, so_xau

    # nền: mọi cạnh xám + mũi tên
    nen = go.Scatter(x=sum(([POS[u][0], POS[v][0], None] for u, v in CANH), []),
                     y=sum(([POS[u][1], POS[v][1], None] for u, v in CANH), []), mode="lines",
                     line=dict(color=TRUC, width=1.2), hoverinfo="skip", showlegend=False)
    moc = list(range(0, den + 1, buoc))
    if moc[-1] != den:
        moc.append(den)
    bat_dau = max(0, (t_inc // buoc) * buoc - buoc)
    frames, so = [], {}
    for t in moc:
        d, tieu, so[t] = du_lieu(t)
        frames.append(go.Frame(data=d, traces=[1, 2], name=gio(t), layout=dict(title=dict(text=tieu))))
    # mở sẵn ở lúc tệ nhất (nhiều điểm bị ảnh hưởng nhất); nút ▶ phát lại từ ngay trước sự cố
    te_nhat = max(moc, key=lambda t: (so[t], -t))
    data0, tieu0, _ = du_lieu(te_nhat)
    fig = go.Figure(data=[nen] + data0)
    fig.frames = frames
    phat = [gio(t) for t in moc if t >= bat_dau]
    for u, v in CANH:
        fig.add_annotation(x=POS[v][0], y=POS[v][1], ax=POS[u][0], ay=POS[u][1], xref="x", yref="y", axref="x",
                           ayref="y", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, standoff=13,
                           arrowcolor=TRUC, text="")
    fig.update_layout(
        height=470, margin=dict(l=10, r=10, t=46, b=10), title=dict(text=tieu0, x=0.01, font=dict(size=20, color=CHU)),
        xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"),
        updatemenus=[dict(type="buttons", direction="left", showactive=False, x=0.99, y=1.13, xanchor="right", yanchor="top",
                          bgcolor=BE_MAT, bordercolor=TRUC, font=dict(color=CHU),
                          buttons=[dict(label="▶  Phát từ lúc sự cố", method="animate",
                                        args=[phat, dict(frame=dict(duration=260, redraw=True), mode="immediate",
                                                         transition=dict(duration=0))]),
                                   dict(label="❚❚", method="animate",
                                        args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])])],
        sliders=[dict(active=moc.index(te_nhat), x=0.02, len=0.96, y=-0.02, pad=dict(t=8),
                      currentvalue=dict(visible=False), bgcolor=BE_MAT, bordercolor=TRUC, tickcolor=TRUC,
                      font=dict(color=CHU_MO, size=10), activebgcolor=NHAN,
                      steps=[dict(method="animate", label=gio(t) if t % 60 == 0 else "",
                                  args=[[gio(t)], dict(mode="immediate", frame=dict(duration=0, redraw=True),
                                                       transition=dict(duration=0))]) for t in moc])],
    )
    return fig


# ---------------------------------------------------------------- biểu đồ
def bieu_do_cuu_duoc(pt, moc_quyet: int | None) -> go.Figure:
    dx, k0 = pt.de_xuat, pt.khong_lam_gi
    ke_hoach = (dx or k0)["kq"].ke_hoach_tong
    het = max(ket_thuc(r) for r in pt.phuong_an)
    fig = go.Figure()
    xs = [dt(t) for t in range(het + 1)]
    fig.add_trace(go.Scatter(x=xs, y=[min(ke_hoach, dc.nhip * t / 60) if t <= dc.ca else ke_hoach
                                      for t in range(het + 1)],
                             name="Kế hoạch", line=dict(color=CHU_MO, dash="dash", width=1.5),
                             hovertemplate="Kế hoạch %{y:.0f} sp<extra></extra>"))
    for r in pt.phuong_an:
        if r is dx or r is k0:
            continue
        k = ket_thuc(r)
        fig.add_trace(go.Scatter(x=xs[: k + 1], y=r["kq"].M[: k + 1], name=r["pa"].ten,
                                 line=dict(color="#56607a", width=1.2),
                                 hovertemplate=f"{e(r['pa'].ten)}: %{{y:.0f}} sp<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs[: dc.ca + 1], y=k0["kq"].M[: dc.ca + 1], name="Không làm gì",
                             line=dict(color="#e66767", width=2.2),
                             hovertemplate="Không làm gì: %{y:.0f} sp<extra></extra>"))
    if dx:
        fig.add_trace(go.Scatter(x=xs[: dc.ca + 1], y=dx["kq"].M[: dc.ca + 1], fill="tonexty",
                                 fillcolor=rgba(NHAN, .18), line=dict(width=0), hoverinfo="skip", showlegend=False))
        k = ket_thuc(dx)
        fig.add_trace(go.Scatter(x=xs[: k + 1], y=dx["kq"].M[: k + 1], name=f"Đề xuất: {dx['pa'].ten}",
                                 line=dict(color=NHAN, width=3.2),
                                 hovertemplate="Đề xuất: %{y:.0f} sp<extra></extra>"))
        if dx["cuu_duoc"] > 0.5:
            fig.add_annotation(x=dt(dc.ca), y=(dx["san_luong"] + k0["san_luong"]) / 2, text=f"<b>+{dx['cuu_duoc']:.0f} sp</b>",
                               showarrow=False, xanchor="right", xshift=-8, font=dict(color=CHU, size=15),
                               bgcolor=rgba(NHAN, .35), borderpad=4)
    fig.add_vline(x=dt(dc.ca).timestamp() * 1000, line_dash="dot", line_color=TRUC)
    fig.add_annotation(x=dt(dc.ca), y=1, yref="paper", text="hết ca 16:00", showarrow=False, yshift=8,
                       font=dict(color=CHU_MO, size=11))
    if moc_quyet is not None:
        fig.add_vline(x=dt(moc_quyet).timestamp() * 1000, line_dash="dash", line_color=NHAN)
        fig.add_annotation(x=dt(moc_quyet), y=0.02, yref="paper", text=f"⏱ quyết trước {gio(moc_quyet)}",
                           showarrow=False, xanchor="left", xshift=4, font=dict(color=NHAN, size=12))
    fig.update_layout(height=360, yaxis_title="sp (hiệu dụng)", xaxis=dict(tickformat="%H:%M"), hovermode="x unified",
                      legend=dict(orientation="h", y=-0.18, font=dict(size=11)))
    return fig


def bieu_do_dong_ho(bang: pd.DataFrame, de_xuat: str | None) -> go.Figure | None:
    b = bang[bang["_moc"].notna()]
    if not len(b):
        return None
    fig = go.Figure()
    ten = [("★ " if r["Phương án"] == de_xuat else "") + r["Phương án"] for _, r in b.iterrows()]
    t0 = int(b["_t_inc"].min())

    def doan(nhan, mau, tu, den, chu, hover):
        fig.add_trace(go.Bar(y=ten, x=[max(0, d - a) for a, d in zip(tu, den)], base=tu, orientation="h", name=nhan,
                             marker=dict(color=mau, line=dict(color=BE_MAT, width=2), cornerradius=4),
                             text=chu, textposition="inside", insidetextanchor="middle",
                             textfont=dict(color="#0b1020", size=12), hovertext=hover, hoverinfo="text"))

    tu = [int(x) for x in b["_t_inc"]]
    khong_giu = [pd.isna(x) for x in b["_het"]]
    moc = [a if k else int(m) for a, m, k in zip(tu, b["_moc"], khong_giu)]
    het = [a if k else max(int(h), m) for a, h, m, k in zip(tu, b["_het"], moc, khong_giu)]
    doan("Không mất gì", XANH_LA, tu, moc, [f"quyết trước {gio(m)}" if m - a >= 40 else "" for a, m in zip(tu, moc)],
         [f"{gio(a)}–{gio(m)}: quyết lúc nào trong khoảng này cũng như nhau" for a, m in zip(tu, moc)])
    chu_vang = []
    for (_, r), a, d in zip(b.iterrows(), moc, het):
        mat, tc = r["Mỗi phút chậm mất (sp)"], r["Mỗi phút chậm thêm tăng ca (phút)"]
        ok = d - a >= 120 and pd.notna(mat) and mat > 0
        chu_vang.append((f"chậm 1 phút: −{mat:g} sp" + (f", +{tc:g}′ tăng ca" if pd.notna(tc) and tc > 0 else ""))
                        if ok else "")
    doan("Vẫn giữ đơn, nhưng mất thêm", "#fab219", moc, het, chu_vang,
         [f"{gio(a)}–{gio(d)}: vẫn giữ được đơn (bằng tăng ca), mỗi phút chậm mất thêm" for a, d in zip(moc, het)])
    doan("Hết hiệu lực", DO, het, [dc.ca] * len(het),
         ["không giữ được đơn" if k else "hết hiệu lực" if dc.ca - h >= 60 else "" for h, k in zip(het, khong_giu)],
         [f"sau {gio(h)}: phương án không còn giữ được đơn" for h in het])
    fig.add_vline(x=t0, line_color=CHU, line_width=1.5, line_dash="dot")
    fig.add_annotation(x=t0, y=1, yref="paper", text=f"phát hiện {gio(t0)}", showarrow=False, yshift=10,
                       font=dict(color=CHU_2, size=11), xanchor="left")
    tick = list(range((t0 // 60) * 60, dc.ca + 1, 60))
    fig.update_layout(barmode="overlay", height=90 + 46 * len(b), showlegend=False, bargap=0.35,
                      xaxis=dict(range=[t0 - 5, dc.ca + 2], tickvals=tick, ticktext=[gio(t) for t in tick],
                                 gridcolor=LUOI),
                      yaxis=dict(autorange="reversed", tickfont=dict(color=CHU, size=12)),
                      margin=dict(l=10, r=10, t=28, b=10))
    return fig


def bieu_do_gantt(kq, den: int) -> go.Figure | None:
    k = khoang_trang_thai(kq)
    k = k[(k["Từ"] < den) & ~((k["Nhóm"] == "Công đoạn") & (k["Trạng thái"] == "chạy"))].copy()
    if not len(k):
        return None
    k["Đến"] = k["Đến"].clip(upper=den)
    thu_tu_hang = [dc.ten(s) for s in dc.thu_tu] + list(dc.may) + [dc.ten(b) for b in dc.dem] + list(dc.linh_kien)
    k["Bắt đầu"], k["Kết thúc"] = k["Từ"].map(dt), k["Đến"].map(dt)
    k["Khoảng"] = k["Từ"].map(gio) + "–" + k["Đến"].map(gio)
    fig = px.timeline(k, x_start="Bắt đầu", x_end="Kết thúc", y="Đối tượng", color="Trạng thái",
                      color_discrete_map=MAU_TT, hover_data={"Khoảng": True, "Bắt đầu": False, "Kết thúc": False,
                                                             "Nhóm": True},
                      category_orders={"Đối tượng": [x for x in thu_tu_hang if x in set(k["Đối tượng"])]})
    fig.update_traces(marker_line_color=BE_MAT, marker_line_width=1.5)
    fig.add_vline(x=dt(dc.ca).timestamp() * 1000, line_dash="dash", line_color=TRUC)
    fig.update_layout(height=400, legend_title_text="", xaxis=dict(range=[dt(0), dt(den)], tickformat="%H:%M"),
                      legend=dict(orientation="h", y=-0.15))
    return fig


def bieu_do_dem(pt, kq, den: int) -> go.Figure:
    fig = go.Figure()
    xs = [dt(t) for t in range(den + 1)]
    for i, (b, info) in enumerate(dc.dem.items()):
        mau = DANH_MUC[i]
        fig.add_trace(go.Scatter(x=xs, y=kq.dem[b][: den + 1], name=dc.ten(b), line=dict(color=mau, width=2.2)))
        for nhan, gt, gach in (("Sức chứa", info["suc_chua"], "dot"), ("Mục tiêu", info["muc_tieu"], "dash")):
            fig.add_trace(go.Scatter(x=[xs[0], xs[-1]], y=[gt] * 2, line=dict(color=mau, dash=gach, width=1),
                                     showlegend=False, hovertemplate=f"{nhan} {b}: {gt}<extra></extra>"))
    fig.update_layout(height=330, yaxis_title="sp trong đệm", xaxis=dict(tickformat="%H:%M"),
                      legend=dict(orientation="h", y=-0.2))
    return fig


def bieu_do_linh_kien(kq, den: int) -> go.Figure:
    fig = go.Figure()
    xs = [dt(t) for t in range(den + 1)]
    for i, lk in enumerate(dc.linh_kien):
        fig.add_trace(go.Scatter(x=xs, y=kq.lk[lk][: den + 1], name=f"Tồn {lk}",
                                 line=dict(color=DANH_MUC[i + 2], width=2.2)))
    fig.update_layout(height=330, yaxis_title="cái", xaxis=dict(tickformat="%H:%M"), legend=dict(orientation="h", y=-0.2))
    return fig


# ---------------------------------------------------------------- trang: tổng quan
def mo_kich_ban(ma: str) -> None:
    st.session_state.che_do = "Kịch bản có sẵn"
    st.session_state.ma_kb = ma


def trang_tong_quan() -> None:
    html_("<div class='wr-eyebrow'>DENSO Factory Hacks 2026 · D3 Chain Impact Propagation</div>"
          "<div class='wr-title'>Bảy trường hợp – một mô hình</div>"
          "<div class='wr-sub'>War Room cho biết <b>bây giờ</b> ra sao. Hệ thống này cho biết <b>các giờ tới</b> sẽ ra sao "
          "và nên làm gì – cho từng bộ phận, trên cùng một nguồn số liệu. Mọi sự cố đều được quy về một mẫu chung "
          "<span class='wr-chip'><b>điểm</b> · đại lượng · thay đổi · từ lúc · trong bao lâu</span>, rồi engine "
          "chạy thử tương lai theo từng phút.</div>")
    ket_qua = {ma: chay_kich_ban(ma) for ma in kbs}
    tong = sum(x[2] for x in ket_qua.values())
    so_pa = sum(len(x[0].phuong_an) for x in ket_qua.values())
    k = st.columns(4)
    the_kpi("Kịch bản", f"{len(kbs)}", "Ví dụ gốc + 7 trường hợp mẫu (IDEA.md mục 5–6)", noi=k[0])
    the_kpi("Phương án đã mô phỏng", f"{so_pa}", "Mỗi phương án = một lần chạy engine bước 1 phút", noi=k[1])
    the_kpi("Thời gian engine", f"{tong:.1f}<small> giây</small>",
            f"Cho cả {len(kbs)} kịch bản (lần tính đầu; sau đó dùng lại)", noi=k[2])
    dem_muc = {m: sum(1 for x in ket_qua.values() if x[0].muc == m) for m in MAU_MUC}
    the_kpi("Mức cảnh báo", " ".join(f"<span style='color:{MAU_MUC[m]}'>{BIEU_TUONG_MUC[m]} {dem_muc[m]}</span>"
                                      for m in MAU_MUC), "Xanh · Vàng · Đỏ theo mức tác động (mục 4.5)", noi=k[3])
    html_("<div class='wr-hr'></div>")
    ds = list(kbs)
    for i in range(0, len(ds), 4):
        cot = st.columns(4)
        for c, ma in zip(cot, ds[i:i + 4]):
            pt, _, _ = ket_qua[ma]
            ky, ten = nhan_kb(ma)
            dx, k0 = pt.de_xuat, pt.khong_lam_gi
            mau = MAU_MUC[pt.muc]
            mau_nhieu = "<br>".join(e(n.mau()) for n in pt.nhieu[:2])
            tc = dx["tang_ca_de_xuat"] if dx else None
            so = [("Không làm gì", f"{k0['san_luong']:.0f}"), ("Đề xuất", f"{dx['san_luong']:.0f}" if dx else "–"),
                  ("Tăng ca", f"{tc}′" if tc else "0′" if dx else "–")]
            with c:
                html_(f"<div class='wr-sc'><div class='h'><span class='k'>{e(ky or 'Ví dụ gốc')}</span>"
                      f"<span class='wr-tag' style='color:{mau};background:{rgba(mau, .14)};"
                      f"border:1px solid {rgba(mau, .5)}'>{BIEU_TUONG_MUC[pt.muc]} {e(pt.muc.upper())}</span></div>"
                      f"<div class='n'>{e(ten)}</div><div class='m'>{mau_nhieu}</div><div class='s'>"
                      + "".join(f"<div>{e(a)}<b>{e(b)}</b></div>" for a, b in so) + "</div></div>")
                st.button(f"Mở {ky or 'ví dụ gốc'} →", key=f"mo_{ma}", on_click=mo_kich_ban, args=(ma,),
                          width="stretch", type="primary" if ma == "goc" else "secondary")
    st.caption("Dây chuyền giả định ở IDEA.md mục 6; mọi con số trên trang được engine tính, không nhập tay.")


# ---------------------------------------------------------------- trang: một sự cố
def trang_su_co(pt, rieng: dict, giay: float, tieu_de: str, tinh_huong: str, tai_lieu: str, khoa: str) -> None:
    dx, k0 = pt.de_xuat, pt.khong_lam_gi
    chinh = dx or k0
    ke_hoach = chinh["kq"].ke_hoach_tong
    t_inc = min((n.t0 for n in pt.nhieu), default=0)
    bang_dh, giay_dh = dong_ho(khoa, pt)
    hang_dx = bang_dh[bang_dh["Phương án"] == dx["pa"].ten] if dx is not None and len(bang_dh) else bang_dh.iloc[0:0]
    hang_dx = hang_dx.iloc[0] if len(hang_dx) else None

    # ---- hero
    c1, c2 = st.columns([3.3, 1], vertical_alignment="center")
    with c1:
        html_(f"<div class='wr-eyebrow'>Sự cố · phát hiện lúc {gio(t_inc)}</div>"
              f"<div class='wr-title'>{e(tieu_de)}</div><div class='wr-sub'>{e(tinh_huong)}</div>"
              "<div class='wr-chips'><span class='wr-chip' style='background:transparent;border:none;padding-left:0'>"
              "Hệ thống hiểu:</span>"
              + "".join(f"<span class='wr-chip'><b>{e(n.diem)}</b>{e(n.mau()[len(n.diem):])}</span>" for n in pt.nhieu)
              + f"</div><div class='wr-meta'>⚙ Engine mô phỏng {len(pt.phuong_an)} phương án (bước 1 phút) trong "
              f"{giay:.2f} giây · đồng hồ quyết định {giay_dh:.1f} giây</div>")
    badge_muc(pt.muc, pt.gui_cho, noi=c2)

    # ---- KPI
    st.write("")
    k = st.columns(4)
    cuu = (f"<span class='wr-up'>+{chinh['cuu_duoc']:.0f} sp</span> so với không làm gì ({k0['san_luong']:.0f})"
           if dx and chinh["cuu_duoc"] > 0.5 else f"Không làm gì: {k0['san_luong']:.0f} sp")
    the_kpi("Sản lượng dự đoán lúc 16:00", f"{chinh['san_luong']:.0f}<small> / {ke_hoach:.0f}</small>", cuu, noi=k[0])
    thieu, thieu0 = max(0, ke_hoach - chinh["san_luong"]), max(0, ke_hoach - k0["san_luong"])
    the_kpi("Thiếu so với kế hoạch", f"{thieu:.0f}<small> sp</small>",
            f"Không làm gì: <span class='wr-down'>thiếu {thieu0:.0f} sp</span>", noi=k[1])
    tc = chinh["tang_ca_de_xuat"]
    khoang = ""
    if pt.quet_sua is not None and len(pt.quet_sua):
        khoang = (f"Khoảng {thoi_luong(pt.quet_sua['Tăng ca (phút)'].min())} – "
                  f"{thoi_luong(pt.quet_sua['Tăng ca (phút)'].max())} tùy thời gian sửa.")
    the_kpi("Tăng ca đề xuất", e(thoi_luong(tc) if tc is not None else "> 4 giờ"),
            khoang or "Để giữ mọi đơn và trả các đệm về mục tiêu.", noi=k[2])
    if hang_dx is not None and pd.notna(hang_dx["_moc"]):
        moc = int(hang_dx["_moc"])
        mat, tcp = hang_dx["Mỗi phút chậm mất (sp)"], hang_dx["Mỗi phút chậm thêm tăng ca (phút)"]
        sau = []
        if mat is not None and not pd.isna(mat) and mat > 0:
            sau.append(f"−{round(mat, 1):g} sp")
        if tcp is not None and not pd.isna(tcp) and tcp > 0:
            sau.append(f"+{round(tcp, 1):g} phút tăng ca")
        phu = (f"Còn <b>{moc - t_inc} phút</b> kể từ lúc phát hiện để 3 bộ phận thống nhất."
               + (f" Sau đó mỗi phút chậm: {', '.join(sau)}." if sau else " Quyết muộn hơn cũng không mất thêm."))
        the_kpi("⏱ Đồng hồ quyết định", f"Trước {gio(moc)}", phu, lop="wr-clock", noi=k[3])
    else:
        the_kpi("⏱ Đồng hồ quyết định", "–", "Không có phương án đề xuất để đếm ngược.", lop="wr-clock", noi=k[3])

    # ---- đề xuất
    if dx:
        tc_txt = f" + tăng ca {thoi_luong(tc)}" if tc else ""
        html_(f"<div class='wr-reco'><div class='ic'>✅</div><div><div class='t'>Đề xuất: {e(dx['pa'].ten)}{e(tc_txt)}</div>"
              f"<div class='d'>Cứu thêm <b>{dx['cuu_duoc']:+.0f} sp</b> · chi phí ~{dx['chi_phi']:,.0f} VND · "
              f"xáo trộn kế hoạch: {e(dx['muc_xao_tron'].lower())} · giữ được mọi đơn · "
              f"bậc {dx['pa'].bac} trên thang xử lý. Con người quyết định cuối cùng.</div></div></div>")
    else:
        html_("<div class='wr-reco no'><div class='ic'>⚠️</div><div><div class='t'>Không phương án nào giữ được tất cả đơn"
              "</div><div class='d'>Chuyển line / ca sau, báo khách sớm và giao tách đợt.</div></div></div>")

    # ---- 01 lan truyền
    tieu_de_muc("01", "Sự cố lan ra sao", "Lớp Logic (đồ thị networkx) – đang hiện lúc tệ nhất; bấm ▶ để xem lan từng 10 phút")
    lua = ["Nếu không làm gì"] + (["Nếu làm theo đề xuất"] if dx else [])
    chon = st.segmented_control("Kịch bản trên bản đồ", lua, default=lua[0], key=f"bd_{khoa}",
                                label_visibility="collapsed") or lua[0]
    r_bd = dx if chon != lua[0] and dx else k0
    c1, c2 = st.columns([2.4, 1])
    with c1:
        ve(ban_do_lan_truyen(r_bd, pt.nhieu), key=f"map_{khoa}_{chon}")
        chu_giai([("Viền trắng = điểm xảy ra sự cố", "#ffffff")] + NHOM_TT)
    with c2:
        html_(f"<div class='wr-kpi-label' style='margin:.2rem 0 .4rem'>Diễn biến – {e(chon.lower())}</div>")
        dong = [(t, nd) for t, nd in dong_thoi_gian(r_bd["kq"])]
        html_("<div class='wr-card' style='max-height:470px;overflow:auto'>" + "".join(
            f"<div style='display:flex;gap:10px;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.05)'>"
            f"<span style='color:{NHAN};font-weight:700;font-variant-numeric:tabular-nums'>{gio(t)}</span>"
            f"<span style='color:{CHU_2};font-size:.88rem'>{e(nd)}</span></div>" for t, nd in dong) + "</div>")

    # ---- 02 phương án
    tieu_de_muc("02", "Thang xử lý – mỗi phương án là một lần chạy thử tương lai",
                "Cứu được tính tại 16:00 so với không làm gì")
    the = []
    for r in pt.phuong_an:
        pa = r["pa"]
        lop = "best" if dx is not None and r is dx else "off" if not r["giu_don"] else ""
        giu = (f"<span class='wr-tag' style='color:{XANH_LA};background:{rgba(XANH_LA, .14)}'>✔ giữ đơn</span>"
               if r["giu_don"] else f"<span class='wr-tag' style='color:#f07c7c;background:{rgba(DO, .16)}'>✘ trễ đơn</span>")
        nhan_dx = (f"<span class='wr-tag' style='color:#0b1020;background:{XANH_LA}'>ĐỀ XUẤT</span>"
                   if dx is not None and r is dx else "")
        tc_r = r["tang_ca_de_xuat"]
        the.append(
            f"<div class='wr-opt {lop}'><div class='b'>Bậc {pa.bac}{nhan_dx}</div><div class='n'>{e(pa.ten)}</div>"
            f"<div class='row'><span>Sản lượng 16:00</span><span>{r['san_luong']:.0f}</span></div>"
            f"<div class='row'><span>Cứu được</span><span>{r['cuu_duoc']:+.0f} sp</span></div>"
            f"<div class='row'><span>Tăng ca</span><span>{e(thoi_luong(tc_r) if tc_r is not None else '> giới hạn')}</span></div>"
            f"<div class='row'><span>Chi phí</span><span>{r['chi_phi'] / 1e6:,.2f} tr</span></div>"
            f"<div class='row'><span>Xáo trộn</span><span>{e(r['muc_xao_tron'])}</span></div>"
            f"<div style='margin-top:6px'>{giu}</div></div>")
    html_("<div class='wr-grid'>" + "".join(the) + "</div>")
    st.write("")
    c1, c2 = st.columns([1.15, 1])
    with c1:
        html_("<div class='wr-kpi-label'>Sản lượng hiệu dụng cộng dồn – vùng tô là phần cứu được</div>")
        moc_dx = int(hang_dx["_moc"]) if hang_dx is not None and pd.notna(hang_dx["_moc"]) else None
        ve(bieu_do_cuu_duoc(pt, moc_dx), key=f"cum_{khoa}")
        st.caption("Tính tại cuối chuyền, trừ phần đệm bị rút dưới mục tiêu và hàng bị giữ (quy ước: tính tại nút cổ "
                   "chai, đệm phải trả về mục tiêu). Đường kéo dài sau 16:00 = tăng ca.")
    with c2:
        html_("<div class='wr-kpi-label'>⏱ Đồng hồ quyết định – quyết muộn đến đâu thì còn kịp (mục 7.3)</div>")
        fig = bieu_do_dong_ho(bang_dh, dx["pa"].ten if dx else None) if len(bang_dh) else None
        if fig is not None:
            ve(fig, key=f"dh_{khoa}")
            chu_giai([("Quyết lúc nào cũng như nhau", XANH_LA), ("Vẫn giữ đơn, mỗi phút chậm mất thêm", "#fab219"),
                      ("Hết hiệu lực", DO)])
        else:
            st.info("Không có phương án nào cần quyết định theo thời gian.")
        st.caption("Engine chạy lại từng phương án với giờ quyết khác nhau: trước giờ quyết dây chuyền chạy như không "
                   "làm gì. Mốc xanh = giờ muộn nhất mà sản lượng và giờ tăng ca chưa xấu đi.")

    # ---- 03 bộ phận
    tieu_de_muc("03", "Câu trả lời cho từng bộ phận", "Cùng một nguồn số liệu, mỗi bộ phận một câu hỏi")
    tab_bt, tab_kh, tab_gh = st.tabs(["🔧 Bảo trì", "📋 Kế hoạch sản xuất", "🚚 Giao hàng & Sales"])
    for tab, bp in ((tab_bt, "Bảo trì"), (tab_kh, "Kế hoạch"), (tab_gh, "Giao hàng & Sales")):
        with tab:
            ds = pt.thong_diep[bp]
            if ds:
                html_(f"<div class='wr-answer'>{md(ds[0])}</div>")
                for d in ds[1:]:
                    st.markdown(f"- {d}")
    with tab_bt:
        if pt.thu_tu_sua is not None:
            st.markdown("**So sánh thứ tự sửa (một tổ bảo trì)** – chạy engine cho từng thứ tự:")
            st.dataframe(pt.thu_tu_sua.drop(columns=["_kq", "_lich"]), hide_index=True)
        if len(pt.tts):
            st.markdown("**Thời gian chịu đựng của đệm so với thời gian sửa** (mục 4.7)")
            st.dataframe(pt.tts, hide_index=True)
    with tab_kh:
        if pt.quet_sua is not None and len(pt.quet_sua):
            st.markdown("**Tăng ca theo từng khả năng thời gian sửa**")
            q = pt.quet_sua.copy()
            q["Xác suất sửa xong trong thời gian này"] = q["Xác suất sửa xong trong thời gian này"].map("{:.0%}".format)
            st.dataframe(q, hide_index=True)
    with tab_gh:
        st.markdown("**Tình trạng đơn hàng** (theo phương án đề xuất)")
        st.dataframe(pd.DataFrame(chinh["don"]["don"]), hide_index=True)
        if pt.giao_hang:
            st.markdown("**Phương án giao hàng**")
            st.dataframe(pd.DataFrame(pt.giao_hang["phuong_an"]).style.format({"Chi phí (VND)": "{:,.0f}"}),
                         hide_index=True)

    if "truy_vet" in rieng:
        tv = rieng["truy_vet"]
        tieu_de_muc("↺", "Truy vết ngược (Chất lượng)", "sản phẩm lỗi → máy → lô vật liệu → khoanh vùng")
        a, b = st.columns([1.3, 1])
        a.dataframe(tv["loi"][["ma_sp", "gio", "may_gia_cong", "toc_do_may", "lo_thep", "nha_cung_cap", "may_dap"]],
                    hide_index=True)
        buoc = ["Điểm chung của 5 sp lỗi: " + ", ".join(f"{k} = <b>{e(v)}</b>" for k, v in tv["chung"].items())]
        buoc += [f"Giả thuyết: {e(g['ten'])} → <b>{len(g['nhom'])} sp</b>" for g in tv["gia_thuyet"]]
        if tv["kiem_mau"]:
            km = tv["kiem_mau"]
            buoc.append(f"Lấy mẫu {km['so_mau']} sp {e(km['nhom'])}: <b>{km['so_loi']} lỗi</b>")
        with b:
            html_("<div class='wr-card'>" + "".join(
                f"<div style='padding:5px 0;color:{CHU_2};font-size:.92rem'><span style='color:{NHAN};font-weight:700'>"
                f"{i + 1}.</span> {x}</div>" for i, x in enumerate(buoc)) +
                  f"<div class='wr-answer' style='border-color:{XANH_LA};margin-top:8px'>Kết luận: "
                  f"{e(tv['ket_luan']['ten'])} → chỉ giữ lại <b>{tv['so_giu']} sp</b></div></div>")

    # ---- 04 chi tiết
    tieu_de_muc("04", "Chi tiết kỹ thuật", "Cho người muốn kiểm tra từng con số")
    ten_pa = [r["pa"].ten for r in pt.phuong_an]
    chon_ct = st.selectbox("Xem chi tiết theo phương án", ten_pa,
                           index=ten_pa.index(dx["pa"].ten) if dx else 0, key=f"ct_{khoa}")
    r_ct = pt.phuong_an[ten_pa.index(chon_ct)]
    den = ket_thuc(r_ct)
    t1, t2, t3, t4 = st.tabs(["Dòng thời gian (Gantt)", "Đệm & linh kiện", "Bảng phương án & đồng hồ",
                              "Đối chiếu tài liệu"])
    with t1:
        fig = bieu_do_gantt(r_ct["kq"], den)
        if fig is None:
            st.info("Không có công đoạn nào dừng, đói hàng hay bị chặn trong phương án này.")
        else:
            ve(fig, key=f"gantt_{khoa}_{chon_ct}")
    with t2:
        a, b = st.columns(2)
        with a:
            html_("<div class='wr-kpi-label'>Mức đệm (nét chấm: sức chứa; nét gạch: mục tiêu)</div>")
            ve(bieu_do_dem(pt, r_ct["kq"], den), key=f"dem_{khoa}_{chon_ct}")
        with b:
            html_("<div class='wr-kpi-label'>Tồn linh kiện ở Lắp ráp</div>")
            ve(bieu_do_linh_kien(r_ct["kq"], den), key=f"lk_{khoa}_{chon_ct}")
        st.caption("Đệm cạn → công đoạn sau đói hàng; đệm đầy → công đoạn trước bị chặn.")
    with t3:
        st.dataframe(pt.bang_phuong_an().style.format({"Chi phí (VND)": "{:,.0f}"}), hide_index=True)
        if len(bang_dh):
            st.dataframe(bang_dh.drop(columns=["_moc", "_het", "_t_inc"]), hide_index=True)
        st.caption("Đồng hồ: tìm nhị phân theo phút, giả định quyết càng muộn kết quả càng không tốt hơn.")
    with t4:
        if tai_lieu:
            st.markdown(f"**Con số trong IDEA.md:** {tai_lieu}")
            st.caption("Các test trong demo/tests kiểm từng con số này (python -m pytest -q).")
        else:
            st.info("Sự cố tự nhập – không có số tài liệu để đối chiếu. Engine không có xử lý riêng cho loại sự cố này.")


# ---------------------------------------------------------------- trang: diễn tập đầu ca
NHOM_TC = [("0 (trong ca)", 0, 0), ("1–15", 1, 15), ("16–30", 16, 30), ("31–60", 31, 60), ("61–120", 61, 120),
           ("121–240", 121, 240)]


def trang_dau_ca() -> None:
    """Diễn tập đầu ca (IDEA.md mục 7.1–7.2): chạy trước khi có sự cố."""
    st.sidebar.caption("Mỗi sáng, trước 08:00: thử lần lượt từng máy hỏng, rồi chạy kế hoạch ca qua nhiều kịch bản "
                       "rủi ro rút ngẫu nhiên (hỏng máy, sửa lệch dự kiến, dừng ngắn).")
    luc = st.sidebar.time_input("Giả định máy hỏng lúc (bản đồ rủi ro)", time(10, 0), step=timedelta(minutes=30))
    so_lan = st.sidebar.select_slider("Số kịch bản rủi ro", [100, 300, 500, 1000], value=300)
    seed = int(st.sidebar.number_input("Hạt giống ngẫu nhiên", 1, 9999, 7))
    bd, dem = dien_tap_may(luc.strftime("%H:%M"))
    mc = dien_tap_ca(so_lan, seed)

    html_(f"<div class='wr-eyebrow'>Trước khi vào ca · 07:30</div>"
          f"<div class='wr-title'>Diễn tập đầu ca</div>"
          f"<div class='wr-sub'>Kế hoạch ca {dc.ke_hoach} sp mã {dc.sp_chinh}. Engine chạy kế hoạch qua {mc['so_lan']} "
          "kịch bản rủi ro (mỗi rủi ro là một nhiễu theo mẫu chung) với cách phản ứng chia tải + tăng tốc, rồi thử "
          "riêng từng máy hỏng.</div>")
    c_g, c_k = st.columns([1, 2.2], vertical_alignment="center")
    with c_g:
        p = mc["p_trong_ca"]
        mau = XANH_LA if p >= 0.8 else "#fab219" if p >= 0.5 else DO
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=p * 100, number=dict(suffix="%", font=dict(size=44, color=CHU)),
            title=dict(text="Xác suất đủ kế hoạch trong ca", font=dict(size=14, color=CHU_2)),
            gauge=dict(axis=dict(range=[0, 100], tickcolor=TRUC, tickfont=dict(color=CHU_MO)), bar=dict(color=mau),
                       bgcolor=BE_MAT, borderwidth=0,
                       steps=[dict(range=[0, 50], color=rgba(DO, .12)), dict(range=[50, 80], color=rgba("#fab219", .10)),
                              dict(range=[80, 100], color=rgba(XANH_LA, .10))])))
        fig.update_layout(height=250, margin=dict(l=40, r=40, t=50, b=0))
        ve(fig, key="gauge")
    with c_k:
        dk = mc["dang_ky_tang_ca"]
        k = st.columns(3)
        the_kpi("Nên đăng ký tăng ca dự phòng", e(thoi_luong(dk) if dk is not None else "> 4 giờ"),
                f"Đủ cho {mc['muc_dang_ky']:.0%} số kịch bản.", noi=k[0])
        the_kpi("Đủ kế hoạch nếu tăng ca ≤ 4 giờ", pt_tram(mc["p_trong_gioi_han"]),
                "Phần còn lại phải chuyển ca sau / line khác.", noi=k[1])
        the_kpi("Đơn hôm nay kịp hạn", pt_tram(mc["p_don_hom_nay"]), "D-101 (xe 17:00), có tính kho thành phẩm.",
                noi=k[2])
        if mc["p_trong_ca"] < 0.8:
            st.info(f"Kế hoạch {dc.ke_hoach} sp bằng đúng 100% công suất chuẩn ({dc.nhip:.0f} sp/h × 8 giờ): sự cố hay "
                    "dừng ngắn sát cuối ca không còn thời gian để tăng tốc bù, nên nhiều kịch bản cần vài phút tăng ca.",
                    icon="ℹ️")

    tc = mc["bang"]["Tăng ca cần (phút)"]
    nhan = [n for n, _, _ in NHOM_TC] + ["> 4 giờ"]
    ti_le = [((tc >= a) & (tc <= b)).mean() for _, a, b in NHOM_TC] + [tc.isna().mean()]
    c1, c2 = st.columns(2)
    with c1:
        tieu_de_muc("01", "Cần tăng ca bao lâu?")
        fig = go.Figure(go.Bar(x=nhan, y=ti_le, marker=dict(color=NHAN, cornerradius=4),
                               hovertemplate="%{x} phút: %{y:.0%} số kịch bản<extra></extra>"))
        fig.update_layout(height=320, bargap=0.25, yaxis=dict(tickformat=".0%", title="Tỷ lệ kịch bản"),
                          xaxis=dict(title="Tăng ca cần (phút)"))
        ve(fig, key="tc_hist")
        st.caption(f"Đăng ký trước {thoi_luong(dk) if dk is not None else '> 4 giờ'} tăng ca là đủ cho "
                   f"{mc['muc_dang_ky']:.0%} khả năng (mức đăng ký trong config.yaml).")
    with c2:
        tieu_de_muc("02", "Bản đồ rủi ro – ưu tiên bảo trì phòng ngừa")
        v = bd.iloc[::-1]
        fig = go.Figure(go.Bar(
            x=v["Rủi ro (sp)"], y=v["Máy"] + " · " + v["Công đoạn"], orientation="h",
            marker=dict(color=NHAN, cornerradius=4),
            customdata=v[["Xác suất hỏng trong ca", "Mất nếu hỏng (sp)", "Tăng ca cần (phút)"]].values,
            hovertemplate="%{y}<br>Xác suất hỏng trong ca: %{customdata[0]:.0%}<br>Mất nếu hỏng: %{customdata[1]} sp"
                          "<br>Tăng ca cần: %{customdata[2]} phút<br>Rủi ro: %{x} sp<extra></extra>"))
        fig.update_layout(height=320, xaxis=dict(title="Rủi ro = xác suất hỏng × sp mất nếu hỏng"),
                          yaxis=dict(tickfont=dict(color=CHU)))
        ve(fig, key="rui_ro")
        st.caption(f"Mỗi máy được thử hỏng lúc {luc.strftime('%H:%M')}, sửa trong thời gian ở mức 80%. "
                   "Máy dễ hỏng hơn chưa chắc phải lo trước – máy hỏng thì thiệt hại lan xa hơn mới được ưu tiên (mục 4.6).")

    tieu_de_muc("03", "Câu trả lời cho từng bộ phận")
    top = bd.head(2)
    ds = [f"🔧 <b>Bảo trì:</b> ưu tiên bảo dưỡng phòng ngừa {e(', '.join(top['Máy']))} (rủi ro "
          f"{e(', '.join(f'{x:g}' for x in top['Rủi ro (sp)']))} sp/ca). Máy mất nhiều nhất nếu hỏng: "
          f"{e(bd.loc[bd['Mất nếu hỏng (sp)'].idxmax(), 'Máy'])} – nên có sẵn phụ tùng để rút ngắn thời gian sửa.",
          f"📋 <b>Kế hoạch:</b> xác suất đủ kế hoạch trong ca {pt_tram(mc['p_trong_ca'])}; đăng ký trước "
          f"{e(thoi_luong(dk) if dk is not None else '> 4 giờ')} tăng ca dự phòng (đủ cho {mc['muc_dang_ky']:.0%} khả năng).",
          f"🚚 <b>Giao hàng & Sales:</b> đơn hôm nay kịp trong {pt_tram(mc['p_don_hom_nay'])} kịch bản."]
    k = st.columns(3)
    for c, d in zip(k, ds):
        html_(f"<div class='wr-answer' style='height:100%'>{d}</div>", c)

    tieu_de_muc("04", "Đề xuất mức đệm", "mục 7.1")
    st.dataframe(dem.drop(columns=["Đỡ cho", "Theo từng máy (sp)", "Sức chứa"]), hide_index=True)
    for _, r in dem.iterrows():
        if r["Tồn thêm (sp)"] <= 0:
            st.markdown(f"- **{r['Đệm']}**: mức hiện tại {r['Mức hiện tại']} sp đã đỡ được {r['Máy tệ nhất phía trước']} "
                        f"hỏng {r['Sửa (giờ, mức 80%)']:g} giờ – giữ nguyên.")
            continue
        tc0, tc1 = r["Tăng ca cần – hiện tại (phút)"], r["Tăng ca cần – đề xuất (phút)"]
        st.markdown(
            f"- **{r['Đệm']}**: nâng từ {r['Mức hiện tại']} lên {r['Đề xuất']} sp (thêm {r['Tồn thêm (sp)']} sp bán thành "
            f"phẩm; sức chứa {r['Sức chứa']}; cần theo từng máy hỏng – {r['Theo từng máy (sp)']}). Khi "
            f"{r['Máy tệ nhất phía trước']} hỏng {r['Sửa (giờ, mức 80%)']:g} giờ, Lắp ráp ra lúc 16:00 tăng "
            f"từ {r['Lắp ráp ra 16:00 – hiện tại']} lên {r['Lắp ráp ra 16:00 – đề xuất']} sp, giữ {r['Đỡ cho']} không "
            f"đói hàng. Nhưng giờ tăng ca để trả đệm về mục tiêu " +
            ("không đổi" if tc0 == tc1 else f"đổi từ {tc0} thành {tc1} phút") +
            f" ({tc1} phút): đệm dày hơn chỉ dời việc làm bù sang sau, không xóa được nó. "
            "Hai con số đặt cạnh nhau để Kế hoạch quyết định.")

    with st.expander("Bản đồ rủi ro chi tiết, tác động theo máy và từng kịch bản"):
        cot = ["Ưu tiên", "Máy", "Công đoạn", "Xác suất hỏng trong ca", "Mất nếu hỏng (sp)", "Rủi ro (sp)",
               "Sửa (giờ, mức 80%)", "Tăng ca cần (phút)", "Lắp ráp ra lúc 16:00", "Số điểm bị ảnh hưởng"]
        st.dataframe(bd[cot].style.format({"Xác suất hỏng trong ca": "{:.0%}", "Rủi ro (sp)": "{:g}"}), hide_index=True)
        if len(mc["theo_may"]):
            st.dataframe(mc["theo_may"].style.format({"Đủ kế hoạch trong ca khi hỏng": "{:.0%}"}), hide_index=True)
        st.dataframe(mc["bang"].drop(columns=["Máy hỏng"]), hide_index=True)
    st.caption("Thông số rủi ro (xác suất hỏng, thời gian sửa, dừng ngắn) là giả định demo trong config.yaml – thay bằng "
               "thống kê phiếu sửa chữa khi có dữ liệu thật. Giản lược: các máy hỏng cùng lúc được sửa song song.")


# ---------------------------------------------------------------- thanh bên + điều hướng
st.sidebar.markdown(
    f"<div style='font-size:1.35rem;font-weight:800;color:{CHU};line-height:1.2'>🏭 D3 · War Room+</div>"
    f"<div style='color:{CHU_MO};font-size:.8rem;margin-bottom:.6rem'>Lan truyền sự cố dọc chuỗi sản xuất</div>",
    unsafe_allow_html=True)
CHE_DO = ["Tổng quan", "Kịch bản có sẵn", "Tự nhập sự cố", "Diễn tập đầu ca"]
nguon = st.sidebar.radio("Chế độ", CHE_DO, key="che_do")

if nguon == "Tổng quan":
    trang_tong_quan()
elif nguon == "Diễn tập đầu ca":
    trang_dau_ca()
elif nguon == "Kịch bản có sẵn":
    def ten_kb(m):
        pt_m = chay_kich_ban(m)[0]
        return f"{BIEU_TUONG_MUC[pt_m.muc]} {kbs[m].ten}"

    ma = st.sidebar.selectbox("Chọn kịch bản", list(kbs), format_func=ten_kb, key="ma_kb")
    pt, rieng, giay = chay_kich_ban(ma)
    kb = kbs[ma]
    trang_su_co(pt, rieng, giay, kb.ten, kb.tinh_huong, kb.tai_lieu, ma)
else:
    if "tu_nhap" not in st.session_state:
        st.session_state.tu_nhap = []
    st.sidebar.caption("Mẫu chung: **tại điểm · đại lượng · thay đổi · từ lúc · trong bao lâu**")
    dl = st.sidebar.selectbox("Đại lượng", list(DAI_LUONG), format_func=lambda k: DAI_LUONG[k].capitalize())
    lua_chon = {
        "nang_luc": list(dc.may) + list(dc.cong_doan),
        "nguon_cung": list(dc.linh_kien),
        "nhu_cau": list(dc.san_pham),
        "thoi_gian": list(dc.chuyen)[:1],
        "chat_luong": list(dc.san_pham),
    }[dl]
    diem = st.sidebar.selectbox("Tại điểm", lua_chon, format_func=lambda d: f"{d} – {dc.ten(d)}")
    nhan = {"nang_luc": "Thay đổi năng lực (%)", "nguon_cung": "Thay đổi lượng hàng về (%)",
            "nhu_cau": "Số sản phẩm thêm", "thoi_gian": "Trễ (giờ)", "chat_luong": "Số sản phẩm bị giữ"}[dl]
    mac_dinh = {"nang_luc": -100.0, "nguon_cung": -100.0, "nhu_cau": 200.0, "thoi_gian": 2.0, "chat_luong": 50.0}[dl]
    thay_doi = st.sidebar.number_input(nhan, value=mac_dinh, step=5.0 if dl in ("nang_luc", "nguon_cung") else 1.0)
    bat_dau = st.sidebar.time_input("Từ lúc", time(10, 0), step=timedelta(minutes=10))
    co_tl = dl in ("nang_luc", "nguon_cung")
    tl = st.sidebar.number_input("Trong bao lâu (giờ, 0 = chưa rõ / đến hết ca)", 0.0, 12.0, 4.0, 0.5,
                                 disabled=not co_tl)
    han = st.sidebar.time_input("Hạn giao", time(20, 0), disabled=dl != "nhu_cau")
    c1, c2 = st.sidebar.columns(2)
    if c1.button("➕ Thêm", width="stretch", type="primary", help="Thêm sự cố theo mẫu chung"):
        st.session_state.tu_nhap.append(dict(
            diem=diem, dai_luong=dl, thay_doi=float(thay_doi), bat_dau=bat_dau.strftime("%H:%M"),
            thoi_luong_gio=(float(tl) if co_tl and tl > 0 else None),
            han=han.strftime("%H:%M") if dl == "nhu_cau" else None,
            ma=None))
    if c2.button("🗑 Xóa hết", width="stretch"):
        st.session_state.tu_nhap = []
    if not st.session_state.tu_nhap:
        html_("<div class='wr-eyebrow'>Tự nhập sự cố</div><div class='wr-title'>Mô tả một sự cố bất kỳ</div>"
              "<div class='wr-sub'>⬅ Điền mẫu chung ở thanh bên rồi bấm <b>Thêm sự cố</b>. Có thể thêm nhiều sự cố "
              "chồng nhau. Engine không có xử lý riêng cho từng loại – cùng một mô hình tính tất cả.</div>")
        st.stop()
    khoa_tn = tuple(tuple(sorted(x.items())) for x in st.session_state.tu_nhap)
    pt, rieng, giay = chay_tu_nhap(khoa_tn)
    trang_su_co(pt, rieng, giay, "Sự cố tự nhập",
                "Sự cố do người dùng mô tả theo mẫu chung – engine không có xử lý riêng cho loại sự cố này.", "",
                "tn_" + str(abs(hash(khoa_tn))))

st.sidebar.markdown("---")
st.sidebar.caption("Dây chuyền giả định (mục 6): Dập D1, D2 → B1 → Gia công M1–M3 → B2 → Lắp ráp (6 người) → "
                   "kho TP. Ca 08:00–16:00, kế hoạch 960 sp mã X.")
