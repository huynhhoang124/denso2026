"""Phong cách "War Room" tối cho demo D3: màu, CSS, template Plotly và các thẻ HTML dùng chung."""
from __future__ import annotations

import html

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ---------------------------------------------------------------- màu (đã kiểm tra tương phản trên nền tối)
NEN = "#0b1020"
BE_MAT = "#131a2b"
BE_MAT_2 = "#1a2338"
VIEN = "rgba(255,255,255,0.09)"
CHU = "#e8ecf4"
CHU_2 = "#aab3c5"
CHU_MO = "#7d879c"
LUOI = "#232c40"
TRUC = "#38425a"
NHAN = "#3987e5"

# màu trạng thái – dành riêng cho mức cảnh báo, luôn kèm chữ + biểu tượng
MAU_MUC = {"Xanh": "#0ca30c", "Vàng": "#fab219", "Đỏ": "#d03b3b"}
BIEU_TUONG_MUC = {"Xanh": "●", "Vàng": "▲", "Đỏ": "◆"}

# màu danh mục (thứ tự cố định, bước cho nền tối)
DANH_MUC = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]

# trạng thái trên Gantt / bản đồ lan truyền: cùng nhóm nghĩa → cùng màu
TRUNG_TINH = "#3a4560"
MAU_TT = {
    "chạy": TRUNG_TINH, "xong": "#2c3448",
    "tăng tốc": "#199e70", "trên chuẩn": "#199e70",
    "đổi mã": "#3987e5",
    "giảm năng lực": "#d55181",
    "đói hàng": "#c98500",
    "bị chặn": "#9085e9", "đầy": "#9085e9",
    "thiếu linh kiện": "#d95926", "hết": "#d95926", "cạn": "#d95926",
    "dừng máy": "#e66767", "hỏng / dừng": "#e66767",
}
NHOM_TT = [("Dừng / hỏng", "#e66767"), ("Hết / cạn / thiếu linh kiện", "#d95926"), ("Đói hàng", "#c98500"),
           ("Bị chặn / đầy", "#9085e9"), ("Giảm năng lực", "#d55181"), ("Tăng tốc / trên chuẩn", "#199e70"),
           ("Đổi mã", "#3987e5"), ("Bình thường", TRUNG_TINH)]


def rgba(hex_: str, a: float) -> str:
    h = hex_.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


# ---------------------------------------------------------------- template Plotly
def _dang_ky_template() -> None:
    t = go.layout.Template(pio.templates["plotly_dark"])
    t.layout.update(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=DANH_MUC,
        font=dict(family="'Source Sans Pro', system-ui, -apple-system, 'Segoe UI', sans-serif", color=CHU_2, size=13),
        xaxis=dict(gridcolor=LUOI, linecolor=TRUC, zerolinecolor=TRUC, tickcolor=TRUC),
        yaxis=dict(gridcolor=LUOI, linecolor=TRUC, zerolinecolor=TRUC, tickcolor=TRUC),
        hoverlabel=dict(bgcolor=BE_MAT_2, bordercolor=TRUC, font=dict(color=CHU, size=13)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=CHU_2)),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    pio.templates["warroom"] = t
    pio.templates.default = "warroom"


_dang_ky_template()


def ve(fig: go.Figure, key: str | None = None) -> None:
    """Vẽ biểu đồ bằng template War Room (tắt theme của Streamlit để không bị ghi đè)."""
    st.plotly_chart(fig, theme=None, key=key, config={"displayModeBar": False, "displaylogo": False})


# ---------------------------------------------------------------- CSS
CSS = f"""
<style>
:root {{ --nen:{NEN}; --be-mat:{BE_MAT}; --be-mat-2:{BE_MAT_2}; --vien:{VIEN}; --chu:{CHU}; --chu-2:{CHU_2};
        --chu-mo:{CHU_MO}; --nhan:{NHAN}; }}
.stApp {{ background: radial-gradient(1200px 500px at 70% -10%, #15223f 0%, var(--nen) 60%) fixed; color: var(--chu); }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{ background: #0e1426; }}
.block-container {{ padding-top: 2.2rem; max-width: 1500px; }}
h1, h2, h3 {{ letter-spacing: -0.01em; }}
h3 {{ font-size: 1.25rem !important; margin-top: 0.4rem; }}
footer, #MainMenu {{ visibility: hidden; }}

.wr-eyebrow {{ color: var(--chu-mo); font-size: .78rem; letter-spacing: .14em; text-transform: uppercase; font-weight: 600; }}
.wr-title {{ font-size: 2.1rem; font-weight: 700; line-height: 1.15; margin: .2rem 0 .35rem; color: var(--chu); }}
.wr-sub {{ color: var(--chu-2); font-size: 1rem; margin-bottom: .55rem; }}
.wr-chips {{ display: flex; flex-wrap: wrap; gap: .4rem; }}
.wr-chip {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: .8rem; color: var(--chu);
           background: var(--be-mat-2); border: 1px solid var(--vien); border-radius: 999px; padding: .18rem .7rem; }}
.wr-chip b {{ color: var(--nhan); font-weight: 600; }}
.wr-meta {{ color: var(--chu-mo); font-size: .8rem; margin-top: .5rem; }}

.wr-card {{ background: var(--be-mat); border: 1px solid var(--vien); border-radius: 14px; padding: 14px 16px;
           height: 100%; box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset; }}
.wr-kpi-label {{ color: var(--chu-2); font-size: .82rem; font-weight: 600; }}
.wr-kpi-value {{ color: var(--chu); font-size: 2.05rem; font-weight: 700; line-height: 1.15; margin: .25rem 0 .15rem; }}
.wr-kpi-value small {{ color: var(--chu-mo); font-size: 1.05rem; font-weight: 600; }}
.wr-kpi-sub {{ color: var(--chu-mo); font-size: .8rem; line-height: 1.35; }}
.wr-up {{ color: #3ccf6b; font-weight: 700; }}
.wr-down {{ color: #f07c7c; font-weight: 700; }}

.wr-badge {{ border-radius: 14px; padding: 12px 16px; height: 100%; border: 1px solid; }}
.wr-badge .lv {{ font-size: 1.9rem; font-weight: 800; letter-spacing: .04em; line-height: 1.1; }}
.wr-badge .to {{ color: var(--chu-2); font-size: .8rem; margin-top: .2rem; }}
@keyframes wr-pulse {{ 0% {{ box-shadow: 0 0 0 0 var(--glow); }} 70% {{ box-shadow: 0 0 0 12px rgba(0,0,0,0); }}
                      100% {{ box-shadow: 0 0 0 0 rgba(0,0,0,0); }} }}
.wr-pulse {{ animation: wr-pulse 2s infinite; }}

.wr-clock {{ background: linear-gradient(135deg, #1b2a4a, var(--be-mat)); border: 1px solid rgba(57,135,229,.45); }}
.wr-clock .wr-kpi-value {{ font-variant-numeric: tabular-nums; }}

.wr-reco {{ display: flex; gap: 18px; align-items: center; background: linear-gradient(90deg, rgba(12,163,12,.16), var(--be-mat) 55%);
           border: 1px solid rgba(12,163,12,.45); border-radius: 14px; padding: 14px 18px; margin: 10px 0 4px; }}
.wr-reco.no {{ background: linear-gradient(90deg, rgba(208,59,59,.18), var(--be-mat) 55%); border-color: rgba(208,59,59,.5); }}
.wr-reco .ic {{ font-size: 1.7rem; }}
.wr-reco .t {{ font-size: 1.15rem; font-weight: 700; color: var(--chu); }}
.wr-reco .d {{ color: var(--chu-2); font-size: .9rem; margin-top: 2px; }}

.wr-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(215px, 1fr)); gap: 12px; }}
.wr-opt {{ background: var(--be-mat); border: 1px solid var(--vien); border-radius: 12px; padding: 12px 14px; }}
.wr-opt.best {{ border: 1.5px solid #0ca30c; box-shadow: 0 0 0 3px rgba(12,163,12,.15); }}
.wr-opt.off {{ opacity: .55; }}
.wr-opt .n {{ font-weight: 700; color: var(--chu); font-size: .95rem; line-height: 1.25; min-height: 2.4em; }}
.wr-opt .b {{ color: var(--chu-mo); font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; }}
.wr-opt .row {{ display: flex; justify-content: space-between; font-size: .84rem; color: var(--chu-2); padding: 2px 0;
               border-top: 1px dashed rgba(255,255,255,.06); }}
.wr-opt .row span:last-child {{ color: var(--chu); font-weight: 600; font-variant-numeric: tabular-nums; }}
.wr-tag {{ display: inline-block; font-size: .7rem; font-weight: 700; border-radius: 6px; padding: 1px 7px; margin-left: 4px; }}

.wr-legend {{ display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: .78rem; color: var(--chu-2); margin: 2px 0 6px; }}
.wr-legend i {{ display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 5px; vertical-align: -1px; }}

.wr-answer {{ background: var(--be-mat); border-left: 4px solid var(--nhan); border-radius: 8px; padding: 10px 14px;
             margin: 6px 0 10px; color: var(--chu); font-size: 1rem; }}
.wr-sc {{ background: var(--be-mat); border: 1px solid var(--vien); border-radius: 14px; padding: 14px 16px 10px; margin-bottom: 8px; }}
.wr-sc .h {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; }}
.wr-sc .h .k {{ color: var(--chu-mo); font-size: .72rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 600; }}
.wr-sc .n {{ font-weight: 700; font-size: 1.02rem; color: var(--chu); margin: 4px 0 6px; line-height: 1.3; height: 2.6em; overflow: hidden; }}
.wr-sc .m {{ font-family: ui-monospace, Menlo, Consolas, monospace; font-size: .72rem; color: var(--chu-2);
            background: var(--be-mat-2); border-radius: 6px; padding: 4px 6px; margin-bottom: 8px; height: 6.4em; line-height: 1.55; }}
.wr-sc .s {{ display: flex; gap: 14px; }}
.wr-sc .s div {{ font-size: .75rem; color: var(--chu-mo); }}
.wr-sc .s b {{ display: block; font-size: 1.25rem; color: var(--chu); font-variant-numeric: tabular-nums; }}
.wr-hr {{ height: 1px; background: var(--vien); margin: 18px 0 8px; }}
.wr-sec {{ display: flex; align-items: baseline; gap: 10px; margin: 22px 0 4px; }}
.wr-sec .no {{ color: var(--nhan); font-weight: 800; font-size: .85rem; }}
.wr-sec .tt {{ color: var(--chu); font-weight: 700; font-size: 1.3rem; }}
.wr-sec .gc {{ color: var(--chu-mo); font-size: .88rem; }}
</style>
"""


def css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- thẻ HTML
def e(x) -> str:
    return html.escape(str(x))


def md(s: str) -> str:
    """Escape rồi đổi **đậm** (markdown của thông điệp engine) sang <b>."""
    s, ra, mo = e(s), [], True
    for i, p in enumerate(s.split("**")):
        ra.append(p if i == 0 else (("<b>" if mo else "</b>") + p))
        if i:
            mo = not mo
    return "".join(ra)


def html_(s: str, noi: st.delta_generator.DeltaGenerator | None = None) -> None:
    (noi or st).markdown(s, unsafe_allow_html=True)


def tieu_de_muc(so: str, tieu_de: str, ghi_chu: str = "") -> None:
    html_(f"<div class='wr-sec'><span class='no'>{e(so)}</span><span class='tt'>{e(tieu_de)}</span>"
          f"<span class='gc'>{e(ghi_chu)}</span></div>")


def the_kpi(nhan: str, gia_tri: str, phu: str = "", lop: str = "", noi=None) -> None:
    html_(f"<div class='wr-card {lop}'><div class='wr-kpi-label'>{e(nhan)}</div>"
          f"<div class='wr-kpi-value'>{gia_tri}</div><div class='wr-kpi-sub'>{phu}</div></div>", noi)


def badge_muc(muc: str, gui_cho: list[str], noi=None) -> None:
    mau = MAU_MUC[muc]
    nhip = " wr-pulse" if muc != "Xanh" else ""
    html_(f"<div class='wr-badge{nhip}' style='--glow:{rgba(mau, .55)};border-color:{rgba(mau, .7)};"
          f"background:linear-gradient(135deg,{rgba(mau, .22)},{BE_MAT})'>"
          f"<div class='wr-kpi-label'>Mức cảnh báo</div>"
          f"<div class='lv' style='color:{mau}'>{BIEU_TUONG_MUC[muc]} {e(muc.upper())}</div>"
          f"<div class='to'>Gửi cho: {e(', '.join(gui_cho))}</div></div>", noi)


def chu_giai(ds: list[tuple[str, str]], noi=None) -> None:
    html_("<div class='wr-legend'>" + "".join(f"<span><i style='background:{m}'></i>{e(n)}</span>" for n, m in ds)
          + "</div>", noi)
