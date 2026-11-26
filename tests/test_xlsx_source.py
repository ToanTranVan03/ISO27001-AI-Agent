from io import BytesIO
import pytest
from openpyxl import Workbook
from evidence_collectors.document_parser import extract_document_text


def test_xlsx_extracts_rows_and_does_not_execute_formula():
    book=Workbook();sheet=book.active;sheet.title='Account review';sheet.append(['employee_id','review_outcome','formula'])
    sheet.append(['EMP-001','Access review pending original owner verification','=1+1'])
    out=BytesIO();book.save(out)
    text=extract_document_text('review.xlsx',out.getvalue())
    assert 'EMP-001' in text and '[FORMULA_NOT_EXECUTED] =1+1' in text


def test_invalid_xlsx_is_rejected():
    with pytest.raises(ValueError):extract_document_text('bad.xlsx',b'not a workbook')
