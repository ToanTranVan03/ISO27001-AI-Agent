from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_loads_vietnamese_login_without_invented_metrics() -> None:
    path = Path(__file__).resolve().parents[1] / "ui" / "streamlit_app.py"
    app = AppTest.from_file(path).run()
    assert not app.exception
    assert app.title[0].value == "Đánh giá an toàn thông tin"
    assert {field.label for field in app.text_input} == {"Tên đăng nhập", "Mật khẩu"}
    assert not app.metric
