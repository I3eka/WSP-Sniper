from src.ui.web.dashboard import render_dashboard
from src.ui.web.layout import apply_styles
from src.ui.web.logs import render_logs_widget, setup_web_logger
from src.ui.web.sidebar import render_sidebar

apply_styles()
setup_web_logger()

render_sidebar()
render_dashboard()
render_logs_widget()
