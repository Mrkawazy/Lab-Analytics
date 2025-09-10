import streamlit as st
from datetime import datetime

def page_header(title: str, subtitle: str | None = None):
    st.markdown(
        f"""
        <div style="padding:.25rem 0 0.75rem 0;">
          <h1 style="margin:0;">{title}</h1>
          {'<p style="margin:.25rem 0 0 0; color:#6b7280;">'+subtitle+'</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

def hide_streamlit_footer():
    st.markdown("""<style>footer, [data-testid="stFooter"]{visibility:hidden;}</style>""", unsafe_allow_html=True)

def render_footer(brand="Your Org", author="OJ", links: dict | None = None):
    year = datetime.now().year
    links_html = ""
    if links:
        links_html = " · " + " ".join(
            [f'<a href="{v}" target="_blank" style="margin-left:12px;">{k}</a>' for k, v in links.items()]
        )
    st.markdown(
        f"""
        <hr/>
        <div style="display:flex;flex-wrap:wrap;gap:.5rem;justify-content:space-between;
                    align-items:center;font-size:0.9rem;color:#6b7280;padding:.25rem 0;">
          <span>© {year} {brand}. All rights reserved.</span>
          <span>Built with ❤️ by {author}{links_html}</span>
        </div>
        """, unsafe_allow_html=True
    )


def app_header_with_logo(logo_path: str | None, title: str, subtitle: str | None = None):
    cols = st.columns([1, 5])
    with cols[0]:
        if logo_path:
            try:
                st.image(logo_path, use_container_width=True)
            except Exception:
                st.write("🧪")
        else:
            st.write("🧪")
    with cols[1]:
        page_header(title, subtitle)

def left_menu(links: list[tuple]):
    """Render a vertical menu: list of (label, target) where target is a page path or URL.

    Uses st.page_link when possible to navigate Streamlit pages.

    Example: [("📊 Dashboard", "pages/1_📊_Dashboard.py"), ("ℹ️ About", "pages/2_ℹ️_About.py")]

    """
    st.subheader("Menu")
    for label, target in links:
        try:
            st.page_link(target, label=label)
        except Exception:
            st.markdown(f"- [{label}]({target})")

def sticky_right_panel_start():
    st.markdown(
        """<style>
        .right-panel { position: sticky; top: 4rem; }
        </style>""", unsafe_allow_html=True
    )
    return st.container()
