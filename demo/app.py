"""Giao diện demo D3 – Chain Impact Propagation.  Chạy:  streamlit run app.py"""
from __future__ import annotations

from datetime import datetime, time, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from engine import (DAI_LUONG, DayChuyen, Nhieu, dong_thoi_gian, gio, khoang_trang_thai, phan_tich, phut,
                    thoi_luong)
from scenarios import chay, kich_ban

st.set_page_config(page_title="D3 – Chain Impact Propagation", page_icon="🏭", layout="wide")

MAU_MUC = {"Xanh": "#1e9e5a", "Vàng": "#e0a800", "Đỏ": "#d63c3c"}
MAU_TT = {"chạy": "#9ccc9c", "tăng tốc": "#2e7d32", "giảm năng lực": "#f2c94c", "đói hàng": "#f2994a",
          "bị chặn": "#bb6bd9", "dừng máy": "#d63c3c", "đổi mã": "#56a0d3", "thiếu linh kiện": "#eb5757",
          "xong": "#d0d0d0", "hỏng / dừng": "#d63c3c", "trên chuẩn": "#2e7d32", "cạn": "#eb5757",
          "đầy": "#bb6bd9", "hết": "#eb5757"}
NGAY = datetime(2026, 10, 5, 8, 0)


def dt(t: float) -> datetime:
    return NGAY + timedelta(minutes=float(t))


@st.cache_resource
def day_chuyen() -> DayChuyen:
    return DayChuyen.tai()


@st.cache_resource(show_spinner="Đang chạy mô phỏng…")
def chay_kich_ban(ma: str):
    return chay(ma, day_chuyen())


@st.cache_resource(show_spinner="Đang chạy mô phỏng…")
def chay_tu_nhap(khoa: tuple):
    nhieu = [Nhieu(**dict(k)) for k in khoa]
    return phan_tich(day_chuyen(), nhieu), {}


dc = day_chuyen()
kbs = kich_ban()

# ---------------------------------------------------------------- thanh bên
st.sidebar.title("🏭 D3 – Lan truyền sự cố")
nguon = st.sidebar.radio("Nguồn sự cố", ["Kịch bản có sẵn", "Tự nhập sự cố"], horizontal=True)

if nguon == "Kịch bản có sẵn":
    ma = st.sidebar.selectbox("Chọn kịch bản", list(kbs), format_func=lambda m: kbs[m].ten)
    kb = kbs[ma]
    pt, rieng = chay_kich_ban(ma)
    tieu_de, tinh_huong, tai_lieu = kb.ten, kb.tinh_huong, kb.tai_lieu
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
    if c1.button("➕ Thêm sự cố", use_container_width=True):
        st.session_state.tu_nhap.append(dict(
            diem=diem, dai_luong=dl, thay_doi=float(thay_doi), bat_dau=bat_dau.strftime("%H:%M"),
            thoi_luong_gio=(float(tl) if co_tl and tl > 0 else None),
            han=han.strftime("%H:%M") if dl == "nhu_cau" else None,
            ma=None))
    if c2.button("🗑 Xóa hết", use_container_width=True):
        st.session_state.tu_nhap = []
    if not st.session_state.tu_nhap:
        st.info("⬅ Mô tả sự cố ở thanh bên rồi bấm **Thêm sự cố**. Có thể thêm nhiều sự cố chồng nhau.")
        st.stop()
    khoa = tuple(tuple(sorted(x.items())) for x in st.session_state.tu_nhap)
    pt, rieng = chay_tu_nhap(khoa)
    tieu_de = "Sự cố tự nhập"
    tinh_huong = "Sự cố do người dùng mô tả theo mẫu chung – engine không có xử lý riêng cho loại sự cố này."
    tai_lieu = ""

st.sidebar.markdown("---")
st.sidebar.caption("Dây chuyền giả định (mục 6): Dập D1, D2 → B1 → Gia công M1–M3 → B2 → Lắp ráp (6 người) → "
                   "kho TP. Ca 08:00–16:00, kế hoạch 960 sp mã X.")

# ---------------------------------------------------------------- tiêu đề + KPI
st.title(tieu_de)
st.write(tinh_huong)
st.markdown("**Hệ thống hiểu:** " + " &nbsp;|&nbsp; ".join(f"`{n.mau()}`" for n in pt.nhieu))
if tai_lieu:
    with st.expander("Con số trong tài liệu (IDEA.md) để đối chiếu"):
        st.write(tai_lieu)

dx, k0 = pt.de_xuat, pt.khong_lam_gi
chinh = dx or k0
ke_hoach = chinh["kq"].ke_hoach_tong
k1, k2, k3, k4 = st.columns(4)
k1.metric("Sản lượng dự đoán / kế hoạch", f"{chinh['san_luong']:.0f} / {ke_hoach:.0f}",
          f"{chinh['cuu_duoc']:+.0f} sp so với không làm gì" if dx and chinh["cuu_duoc"] else None)
k1.caption(f"Theo phương án đề xuất, lúc 16:00. Không làm gì: {k0['san_luong']:.0f} sp.")
k2.metric("Thiếu so với kế hoạch", f"{max(0, ke_hoach - chinh['san_luong']):.0f} sp")
k2.caption(f"Không làm gì: thiếu {max(0, ke_hoach - k0['san_luong']):.0f} sp.")
tc = chinh["tang_ca_de_xuat"]
k3.metric("Giờ tăng ca đề xuất", thoi_luong(tc) if tc is not None else "> 4 giờ")
if pt.quet_sua is not None and len(pt.quet_sua):
    k3.caption(f"Khoảng {thoi_luong(pt.quet_sua['Tăng ca (phút)'].min())} – "
               f"{thoi_luong(pt.quet_sua['Tăng ca (phút)'].max())} tùy thời gian sửa.")
k4.markdown(
    f"<div style='background:{MAU_MUC[pt.muc]};color:white;border-radius:10px;padding:10px 14px;'>"
    f"<div style='font-size:0.85rem;opacity:.9'>Mức cảnh báo</div>"
    f"<div style='font-size:1.9rem;font-weight:700;line-height:1.2'>{pt.muc.upper()}</div>"
    f"<div style='font-size:0.8rem'>Gửi cho: {', '.join(pt.gui_cho)}</div></div>", unsafe_allow_html=True)
st.success(f"**Đề xuất:** {dx['pa'].ten}" + (f" + tăng ca {thoi_luong(tc)}" if tc else "")
           if dx else "Không phương án nào giữ được tất cả đơn → chuyển line / ca sau, báo khách và giao tách đợt.",
           icon="✅" if dx else "⚠️")

# ---------------------------------------------------------------- diễn biến
ten_pa = [r["pa"].ten for r in pt.phuong_an]
chon = st.selectbox("Xem diễn biến theo phương án", ten_pa, index=0,
                    help="Mặc định 'Không làm gì' để thấy sự cố lan ra sao; chọn phương án khác để so sánh.")
r_chon = pt.phuong_an[ten_pa.index(chon)]
kq = r_chon["kq"]
den = dc.ca + (r_chon["tang_ca_de_xuat"] or 0) if r_chon["pa"].tang_ca else dc.ca
den = max(den, dc.ca)

cot_trai, cot_phai = st.columns([3, 2])
with cot_trai:
    st.subheader("Dòng thời gian tác động")
    k = khoang_trang_thai(kq)
    k = k[(k["Từ"] < den) & ~((k["Nhóm"] == "Công đoạn") & (k["Trạng thái"] == "chạy"))].copy()
    k["Đến"] = k["Đến"].clip(upper=den)
    thu_tu_hang = ([dc.ten(s) for s in dc.thu_tu] + list(dc.may) + [dc.ten(b) for b in dc.dem]
                   + list(dc.linh_kien))
    if len(k):
        k["Bắt đầu"], k["Kết thúc"] = k["Từ"].map(dt), k["Đến"].map(dt)
        k["Khoảng"] = k["Từ"].map(gio) + "–" + k["Đến"].map(gio)
        fig = px.timeline(k, x_start="Bắt đầu", x_end="Kết thúc", y="Đối tượng", color="Trạng thái",
                          color_discrete_map=MAU_TT, hover_data={"Khoảng": True, "Bắt đầu": False,
                                                                 "Kết thúc": False, "Nhóm": True},
                          category_orders={"Đối tượng": [x for x in thu_tu_hang if x in set(k["Đối tượng"])]})
        fig.add_vline(x=dt(dc.ca).timestamp() * 1000, line_dash="dash", line_color="grey")
        fig.add_annotation(x=dt(dc.ca), y=1, yref="paper", text="hết ca 16:00", showarrow=False, yshift=10)
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), legend_title_text="",
                          xaxis=dict(range=[dt(0), dt(den)], tickformat="%H:%M"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Không có công đoạn nào dừng, đói hàng hay bị chặn trong phương án này.")
with cot_phai:
    st.subheader("Diễn biến (nếu không làm gì)" if r_chon is k0 else f"Diễn biến – {chon}")
    for t, nd in dong_thoi_gian(kq):
        st.markdown(f"**{gio(t)}** – {nd}")

c1, c2 = st.columns(2)
with c1:
    st.subheader("Mức đệm theo thời gian")
    fig = go.Figure()
    xs = [dt(t) for t in range(den + 1)]
    for i, (b, info) in enumerate(dc.dem.items()):
        mau = px.colors.qualitative.Set1[i]
        fig.add_trace(go.Scatter(x=xs, y=kq.dem[b][: den + 1], name=dc.ten(b), line=dict(color=mau, width=2.5)))
        fig.add_trace(go.Scatter(x=[xs[0], xs[-1]], y=[info["suc_chua"]] * 2, name=f"Sức chứa {b}",
                                 line=dict(color=mau, dash="dot", width=1), showlegend=False,
                                 hovertemplate=f"Sức chứa {b}: {info['suc_chua']}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[xs[0], xs[-1]], y=[info["muc_tieu"]] * 2, name=f"Mục tiêu {b}",
                                 line=dict(color=mau, dash="dash", width=1), showlegend=False,
                                 hovertemplate=f"Mục tiêu {b}: {info['muc_tieu']}<extra></extra>"))
    if any(n.dai_luong == "nguon_cung" for n in pt.nhieu) or any(min(kq.lk[lk][: den + 1]) <= 1e-6 for lk in kq.lk):
        for lk in dc.linh_kien:
            fig.add_trace(go.Scatter(x=xs, y=kq.lk[lk][: den + 1], name=f"Tồn {lk}", line=dict(width=1.5, dash="dashdot"),
                                     yaxis="y2"))
        fig.update_layout(yaxis2=dict(title="Linh kiện", overlaying="y", side="right", showgrid=False))
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="sp",
                      xaxis=dict(tickformat="%H:%M"), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Nét chấm: sức chứa; nét gạch: mức mục tiêu. Đệm cạn → công đoạn sau đói hàng; đầy → công đoạn trước bị chặn.")
with c2:
    st.subheader("Sản lượng hiệu dụng cộng dồn")
    fig = go.Figure()
    xs_all = [dt(t) for t in range(dc.ca + 241)]
    fig.add_trace(go.Scatter(x=xs_all, y=[min(ke_hoach, dc.nhip * t / 60) if t <= dc.ca else ke_hoach
                                         for t in range(dc.ca + 241)],
                             name="Kế hoạch", line=dict(color="black", dash="dash")))
    for r in pt.phuong_an:
        ket = dc.ca + (r["tang_ca_de_xuat"] or 0) if r["pa"].tang_ca else dc.ca
        fig.add_trace(go.Scatter(x=xs_all[: ket + 1], y=r["kq"].M[: ket + 1], name=r["pa"].ten,
                                 line=dict(width=3 if r is dx else 1.5)))
    fig.add_vline(x=dt(dc.ca).timestamp() * 1000, line_dash="dot", line_color="grey")
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="sp",
                      xaxis=dict(tickformat="%H:%M"), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Sản lượng tại cuối chuyền, trừ phần đệm bị rút dưới mục tiêu và hàng bị giữ "
               "(quy ước: tính tại nút cổ chai, đệm phải trả về mục tiêu). Đường kéo dài sau 16:00 = tăng ca.")

# ---------------------------------------------------------------- phương án
st.subheader("So sánh phương án (thang xử lý)")
bang = pt.bang_phuong_an()
st.dataframe(bang.style.format({"Chi phí (VND)": "{:,.0f}"}).apply(
    lambda row: ["background-color: #e8f5e9" if dx and row["Phương án"] == dx["pa"].ten else "" for _ in row],
    axis=1), use_container_width=True, hide_index=True)
st.caption("Cứu được = so với không làm gì, tại 16:00. Tăng ca cần = phút sau 16:00 để giữ được mọi đơn "
           "(0 = không cần). Chi phí quy đổi theo đơn giá giả định trong config.yaml. Con người chọn phương án.")
if pt.giao_hang:
    st.markdown("**Phương án giao hàng**")
    st.dataframe(pd.DataFrame(pt.giao_hang["phuong_an"]).style.format({"Chi phí (VND)": "{:,.0f}"}),
                 use_container_width=True, hide_index=True)

# ---------------------------------------------------------------- 3 bộ phận
st.subheader("Câu trả lời cho từng bộ phận")
tab_bt, tab_kh, tab_gh = st.tabs(["🔧 Bảo trì", "📋 Kế hoạch", "🚚 Giao hàng & Sales"])
with tab_bt:
    for d in pt.thong_diep["Bảo trì"]:
        st.markdown(f"- {d}")
    if pt.thu_tu_sua is not None:
        st.markdown("**So sánh thứ tự sửa (một tổ bảo trì)** – chạy engine cho từng thứ tự:")
        st.dataframe(pt.thu_tu_sua.drop(columns=["_kq", "_lich"]), use_container_width=True, hide_index=True)
        st.caption("Tài liệu chọn theo sản lượng Gia công lúc 16:00. Engine chọn theo giờ tăng ca để vừa đủ kế hoạch "
                   "vừa trả các đệm về mục tiêu – hai thước đo có thể cho kết luận khác nhau (xem README).")
    if len(pt.tts):
        st.markdown("**Thời gian chịu đựng của đệm so với thời gian sửa** (mục 4.7)")
        st.dataframe(pt.tts, use_container_width=True, hide_index=True)
with tab_kh:
    for d in pt.thong_diep["Kế hoạch"]:
        st.markdown(f"- {d}")
    if pt.quet_sua is not None and len(pt.quet_sua):
        st.markdown("**Tăng ca theo từng khả năng thời gian sửa**")
        q = pt.quet_sua.copy()
        q["Xác suất sửa xong trong thời gian này"] = q["Xác suất sửa xong trong thời gian này"].map("{:.0%}".format)
        st.dataframe(q, use_container_width=True, hide_index=True)
with tab_gh:
    for d in pt.thong_diep["Giao hàng & Sales"]:
        st.markdown(f"- {d}")
    st.markdown("**Tình trạng đơn hàng** (theo phương án đề xuất)")
    st.dataframe(pd.DataFrame(chinh["don"]["don"]), use_container_width=True, hide_index=True)

if "truy_vet" in rieng:
    tv = rieng["truy_vet"]
    with st.expander("🔎 Truy vết ngược (Chất lượng) – sản phẩm lỗi → máy → lô vật liệu → khoanh vùng", expanded=True):
        a, b = st.columns(2)
        a.markdown("**5 sản phẩm lỗi phát hiện ở Kiểm tra cuối**")
        a.dataframe(tv["loi"][["ma_sp", "gio", "may_gia_cong", "toc_do_may", "lo_thep", "nha_cung_cap", "may_dap"]],
                    hide_index=True, use_container_width=True)
        b.markdown("**Điểm chung:** " + ", ".join(f"{k} = `{v}`" for k, v in tv["chung"].items()))
        for g in tv["gia_thuyet"]:
            b.markdown(f"- Giả thuyết: {g['ten']} → **{len(g['nhom'])} sp**")
        if tv["kiem_mau"]:
            km = tv["kiem_mau"]
            b.markdown(f"- Lấy mẫu {km['so_mau']} sp {km['nhom']}: **{km['so_loi']} lỗi**")
        b.success(f"Kết luận: {tv['ket_luan']['ten']} → chỉ giữ lại **{tv['so_giu']} sp**.")

# ---------------------------------------------------------------- sơ đồ
st.subheader("Sơ đồ dây chuyền (lớp Logic) – điểm bị ảnh hưởng tô đỏ")


def vi_tri(dc: DayChuyen) -> dict:
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


pos = vi_tri(dc)
bi = pt.bi_anh_huong
goc_su_co = {n.diem for n in pt.nhieu}
fig = go.Figure()
for u, v, a in dc.G.edges(data=True):
    do = u in bi and v in bi
    fig.add_trace(go.Scatter(x=[pos[u][0], pos[v][0]], y=[pos[u][1], pos[v][1]], mode="lines",
                             line=dict(color="#d63c3c" if do else "#c7c7c7", width=2.5 if do else 1),
                             hoverinfo="skip", showlegend=False))
    fig.add_annotation(x=pos[v][0], y=pos[v][1], ax=pos[u][0], ay=pos[u][1], xref="x", yref="y", axref="x",
                       ayref="y", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, standoff=14,
                       arrowcolor="#d63c3c" if do else "#c7c7c7", text="")
HINH = {"cong_doan": "square", "may": "circle", "dem": "diamond", "kho": "square", "linh_kien": "triangle-up",
        "nha_cung_cap": "triangle-down", "san_pham": "hexagon", "don_hang": "star", "khach_hang": "pentagon",
        "chuyen_giao": "cross", "nguoi": "circle-open"}
nodes = list(dc.G.nodes(data=True))
fig.add_trace(go.Scatter(
    x=[pos[n][0] for n, _ in nodes], y=[pos[n][1] for n, _ in nodes], mode="markers+text",
    text=[n if a["loai"] != "nguoi" else a["ten"].split(" (")[0] for n, a in nodes], textposition="bottom center",
    marker=dict(size=[30 if a["loai"] in ("cong_doan", "kho") else 22 for _, a in nodes],
                symbol=[HINH.get(a["loai"], "circle") for _, a in nodes],
                color=["#8b0000" if n in goc_su_co else "#d63c3c" if n in bi else "#9bb7d4" for n, _ in nodes],
                line=dict(color="white", width=1)),
    hovertext=[f"{a['ten']} ({a['loai']})" + (" – ĐIỂM SỰ CỐ" if n in goc_su_co else " – bị ảnh hưởng" if n in bi else "")
               for n, a in nodes], hoverinfo="text", showlegend=False))
fig.update_layout(height=430, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white",
                  xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"))
st.plotly_chart(fig, use_container_width=True)
st.caption("Đỏ sẫm: điểm xảy ra sự cố. Đỏ: điểm bị ảnh hưởng khi không làm gì (công đoạn dừng/đói/chặn, đệm cạn/đầy, "
           "linh kiện hết, đơn trễ). Đồ thị networkx: máy –chạy trên→ công đoạn –đưa vào→ đệm –đệm cho→ công đoạn; "
           "NCC –cấp cho→ linh kiện –thành phần của→ mã hàng –đáp ứng đơn→ đơn hàng –giao cho→ khách.")
