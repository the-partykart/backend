from fastapi import APIRouter, FastAPI
from fastapi.responses import StreamingResponse
import io
import uvicorn
from app.microservices.bill_sample.bill_scema import InvoiceRequest

from app.microservices.bill_sample.pdf_service import InvoicePDF



router = APIRouter(prefix="/bill", tags=["Bill"])

 
@router.post("/generate-invoice")
def generate_invoice(data: InvoiceRequest):

    pdf = InvoicePDF()
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # HEADER
    pdf.add_company_address()

    y, h = pdf.buyer_info(data.buyer_name)

    pdf.bill_details(
        y_top=y,
        h_equal=h,
        bill_no=data.bill_no,
        challan_no=data.challan_no,
        date=data.date,
        vehicle_no=data.vehicle_no,
        place_of_delivery=data.place_of_delivery
    )

    bill = pdf.add_product_summary_table(
        products=[p.dict() for p in data.products],
        loading_charge=data.loading_charge
    )

    pdf.amount_in_word(bill.final_amount)

    pdf.add_tax_summary_table(
        bill.total_amount,
        bill.final_amount,
        bill.GST_amount
    )

    y_bank = pdf.add_bank_details_table()
    pdf.add_authorisation_block(y_bank)

    # Convert PDF to bytes
    pdf_bytes = pdf.output(dest="S")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=invoice.pdf"
        }
    )


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=20000, reload=True)
