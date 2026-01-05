from src.ui.web.layout import apply_styles
from src.ui.web.logs import setup_web_logger, render_logs_widget
from src.ui.web.sidebar import render_sidebar
from src.ui.web.dashboard import render_dashboard

apply_styles()
setup_web_logger()

render_sidebar()
render_dashboard()
render_logs_widget()
