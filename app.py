import dash
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
from flask import Flask, make_response
from dash import callback_context
from pages.mdt import generate_pdf_mdt

flask_server = Flask(__name__)


# Inisialisasi aplikasi Dash
app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    server=Flask(__name__),
)

# Navbar untuk navigasi
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("HOME", href="/")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Report to TSEL", href="/report/report-tsel"),
                dbc.DropdownMenuItem("Report to EID", href="/report/report-eid"),
                dbc.DropdownMenuItem("Report Balancing", href="/report/report-balancing"),
                dbc.DropdownMenuItem("Report Balancing Teng", href="/report/report-balancing-teng"),
                dbc.DropdownMenuItem("Report QC", href="/report/report-qc"),
            ],
            nav=True,
            in_navbar=True,
            label="REPORT",
        ),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Monitoring Daily 4G", href="/monitoring/monitoring-daily4g"),
                dbc.DropdownMenuItem("Monitoring Daily 2G", href="/monitoring/monitoring-daily2g"),
                dbc.DropdownMenuItem("Monitoring Hourly 4G", href="/monitoring/monitoring-hourly4g"),
                dbc.DropdownMenuItem("Monitoring Hourly 2G", href="/monitoring/monitoring-hourly2g"),
            ],
            nav=True,
            in_navbar=True,
            label="MONITORING",
        ),
        dbc.NavItem(dbc.NavLink("MDT", href="/mdt")),
        dbc.NavItem(dbc.NavLink("TA", href="/ta")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Export to PDF", id="export-to-pdf"),
                dbc.DropdownMenuItem("Export to PPT", href="#"),
                dbc.DropdownMenuItem("Export to Excel", href="#"),
            ],
            nav=True,
            in_navbar=True,
            label="Export",
        ),
    ],
    color="primary",
    dark=True,
    sticky="top",
)

# Layout aplikasi Dash
app.layout = dbc.Container(
    [
        navbar,
        html.Div(id="page-content", children=dash.page_container),
        html.Div(id="export-message", style={"margin-top": "20px", "font-weight": "bold"}),
        dcc.Download(id="download-pdf"),
        dcc.Download(id="download-pdf-from-ta"),
        dcc.Download(id="download-pdf-from-balancing"),
        dcc.Location(id="url", refresh=False),
    ],
    fluid=True,
)


from pages.mdt import generate_pdf_mdt
@flask_server.route('/set_cookie')
def set_cookie():
    response = make_response("Cookie dengan SameSite=Strict telah diset!")
    response.set_cookie(
        "cookietest",
        "example_value",
        samesite="Strict",  # Atur nilai SameSite
        secure=True         # Tambahkan secure untuk keamanan
    )
    return response

# Route untuk get cookie
@flask_server.route('/get_cookie')
def get_cookie():
    cookie = request.cookies.get("cookietest")
    return f"Nilai cookie adalah: {cookie}" if cookie else "Cookie tidak ditemukan."


# Menjalankan aplikasi
if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
