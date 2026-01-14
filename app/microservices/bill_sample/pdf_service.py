from fastapi import FastAPI
import uvicorn  
from fpdf import FPDF, XPos, YPos
import os
import platform
import subprocess
from num2words import num2words
from app.microservices.bill_sample.bill_scema import BillSummary


class InvoicePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 20)
        self.cell(0, 15, "JAI BHAVANI TRADERS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

        y = self.get_y()  # current Y position for alignment

        # GSTIN on the left
        self.set_font("Helvetica", "B", 9)
        self.set_xy(10, y)
        self.cell(60, 6, "GSTIN :- 27AOMPM7988R1ZG", ln=0)

        # TAX INVOICE in the center
        self.set_font("Helvetica", "B", 17)
        invoice_text = "TAX INVOICE"
        invoice_x = (210 - self.get_string_width(invoice_text)) / 2
        self.set_xy(invoice_x, y)
        self.cell(self.get_string_width(invoice_text), 6, invoice_text, ln=0)

        # Original recipient on the right
        self.set_font("Helvetica", "", 9)
        recipient_text = "Original recipient"
        recipient_x = 210 - 10 - self.get_string_width(recipient_text)
        self.set_xy(recipient_x, y)
        self.cell(0, 6, recipient_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.ln(6)

    def add_company_address(self):
        self.set_font("Helvetica", "", 9)

        # Address text
        address_text = (
            "5TH FLOOR, FLAT NO.504, RIDDHI REGENCY, PLOT NO.61, Navade Phase 2, "
            "Navi Mumbai, Raigad, Maharashtra, 410208. State Name:-Maharashtra, "
            "State Code:-27. Mob:9224381321."
        )

        # Define box dimensions
        x = 10
        y = self.get_y()
        w = 190

        # Get height dynamically using multi_cell height estimation
        line_height = 5
        n_lines = len(self.multi_cell(w, line_height, address_text, split_only=True))
        h = n_lines * line_height

        # Draw box
        self.rect(x, y, w, h)

        # Insert the text inside the box
        self.set_xy(x, y)
        self.multi_cell(w, line_height, address_text)
        self.ln(4)

    # def buyer_info(self,name):
    #     self.set_font("Helvetica", "", 9)

    #     self.ln(3)

    #     # buyer details
    #     buyer_info = all_buyer_info(name)

    #     # define box dimensions
    #     x = 10
    #     y = self.get_y()
    #     w = 90
    #     line_height = 5

    #     # calculate height
    #     n_lines = len(self.multi_cell(w, line_height, buyer_info, split_only=True))
    #     h = n_lines * line_height

    #     # draw box
    #     self.rect(x, y, w, h)

    #     # insert text
    #     self.set_xy(x, y)
    #     self.multi_cell(w, line_height, buyer_info)

    #     # move cursor below box
    #     # self.set_x(x + w + 3)
    #     return y,h


    def buyer_info(self, name: str, address: str):
        self.set_font("Helvetica", "", 9)
        self.ln(3)

        buyer_info = (
            f"M/S: - {name}\n"
            f"{address}"
        )

        x = 10
        y = self.get_y()
        w = 90
        line_height = 5

        n_lines = len(self.multi_cell(w, line_height, buyer_info, split_only=True))
        h = n_lines * line_height

        self.rect(x, y, w, h)
        self.set_xy(x, y)
        self.multi_cell(w, line_height, buyer_info)

        return y, h


    def bill_details(
            self, 
            y_top, 
            h_equal,
            bill_no,
            challan_no,
            date,
            vehicle_no,
            place_of_delivery,
            ):
        self.set_font("Helvetica", "", 9)

        details = [
            ("Bill No.", f"{bill_no}"),
            ("Challan No.", f"{challan_no}"),
            ("Date", f"{date}"),
            ("Vehicle No.", f"{vehicle_no}"),
            ("Place of Delivery", f"{place_of_delivery}")
        ]

        x = 110
        w = 90
        padding_top = 1.2  # space from top edge
        padding_bottom = 1.2  # space from bottom edge of each row
        total_rows = len(details)

        # calculate adjusted line height per row based on total height
        line_height = (h_equal / total_rows)

        # draw outer box
        self.rect(x, y_top, w, h_equal)

        current_y = y_top
        for label, value in details:
            text_y = current_y + padding_top

            # draw row content
            self.set_xy(x + 2, text_y)
            self.cell(35, line_height - padding_top - padding_bottom, label, ln=0)
            self.cell(3, line_height - padding_top - padding_bottom, ":", ln=0)
            self.cell(w - 40, line_height - padding_top - padding_bottom, value, ln=0)

            # horizontal line (row separator)
            self.line(x, current_y + line_height, x + w, current_y + line_height)

            current_y += line_height

        # move cursor below the box
        self.set_y(y_top + h_equal + 2)



    # product rate and all totals
    def add_product_summary_table(self, products, loading_charge):

        t_amount = 0
        all_items = []
        
        for item in products:
            amount = float(item["quantity"]) * float(item["rate"])
            item_detials = {
                "description": item["description"], 
                "hsn": item["hsn"], 
                "quantity": item["quantity"],
                "rate": float(item["rate"]), 
                "per": item["per"],
                "amount": float(amount)
                }
            all_items.append(item_detials)
            t_amount += amount
        
        total_amount = t_amount + loading_charge

        GST_amount = total_amount * 0.18
        GST_amount = round(GST_amount,2)
        final_amount = t_amount + loading_charge + GST_amount

        # rounded_final_amount = round(final_amount)
        # round_off = round(rounded_final_amount - final_amount, 2)

        # Extract decimal part
        decimal_part = final_amount - int(final_amount)

        # Apply custom rounding
        if decimal_part > 0.50:
            rounded_final_amount = int(final_amount) + 1
        else:
            rounded_final_amount = int(final_amount)

        round_off = round(rounded_final_amount - final_amount, 2)





        
        # Build dynamic sign string
        round_sign = "+" if round_off > 0 else "-" if round_off < 0 else "±"
        round_off_str = f"({round_sign}){abs(round_off):.2f}"  # string for display

        # Charges dictionary with float + formatted round off
        all_charges = {
            "loading_charge": loading_charge,
            "CGST SALES @9%": round(GST_amount / 2, 2),
            "SGST SALES @9%": round(GST_amount / 2, 2),
            "Round Of": round_off_str
        }

        # half_GST =  ((GST_amount / 2)-round_off)
        half_GST =  ((GST_amount / 2))

        print(half_GST)

      

        self.set_font("Helvetica", "B", 9)

        self.ln(4)

        col_widths = [12, 50, 25, 22, 20, 15, 36]
        headers = ["SI NO.", "Description of Goods", "HSN/SAC", "Quantity", "Rate", "Per", "Amount"]
        line_height = 6
        amount_font_size = 9

        x_start = 10
        y_start = self.get_y()

        # === Header Row ===
        self.set_xy(x_start, y_start)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], line_height, header, border=1, align='C')
        self.ln(line_height)

        self.set_font("Helvetica", "", 9)

        # # === Product Rows (always at least 6) ===
        visible_rows = max(len(all_items), 6)
        for i in range(visible_rows):
            self.set_x(x_start)
            if i < len(all_items):
                prod = all_items[i]
                row = [
                    str(i + 1),
                    prod["description"],
                    prod["hsn"],
                    prod["quantity"],
                    prod["rate"],
                    prod["per"],
                    prod["amount"]
                ]
            else:
                row = [""] * 7  # empty row

            for j, item in enumerate(row):
                # Convert all items to string (format float if needed)
                if isinstance(item, float):
                    item = f"{item:.2f}"  # Format float to 2 decimal places
                else:
                    item = str(item)

                if j == 6 and item:  # Amount column, center vertically
                    box_x = self.get_x()
                    box_y = self.get_y()
                    box_w = col_widths[j]
                    box_h = line_height

                    text_width = self.get_string_width(item)
                    text_x = box_x + (box_w - text_width) / 2
                    text_y = box_y + (box_h - 4) / 2

                    self.cell(box_w, box_h, "", border=1)  # Draw cell box
                    self.set_xy(text_x, text_y)
                    self.cell(text_width, 4, item)
                    self.set_xy(box_x + box_w, box_y)  # Move to next cell position
                else:
                    align = "R" if j == 6 else "L"
                    self.cell(col_widths[j], line_height, item, border=1, align=align)

            self.ln(line_height)

        # === Loading Charge Row ===
        self.set_x(x_start)
        self.cell(col_widths[0], line_height, "", border="L")
        self.cell(col_widths[1], line_height, "Loading Charges", border="LR")
        for w in col_widths[2:-1]:
            self.cell(w, line_height, "", border="LR")
        text = f"{loading_charge:.2f}"
        self.cell(col_widths[-1], line_height, text, border="R", align="C")
        self.ln(line_height)

        # === Subtotal Row (Product total only) ===
        self.set_x(x_start)
        self.cell(sum(col_widths[:-1]), line_height, "Subtotal", border=1, align="R")
        text = f"{t_amount+loading_charge:.2f}"
        self.cell(col_widths[-1], line_height, text, border=1, align="C")

        self.ln(line_height)  # ✅ Add this line here

        # === GST + Round Off Rows ===
        for label in ["CGST SALES @9%", "SGST SALES @9%", "Round Of"]:
            self.set_x(x_start)
            self.cell(col_widths[0], line_height, "", border="L")
            self.cell(col_widths[1], line_height, label, border="LR")
            for w in col_widths[2:-1]:
                self.cell(w, line_height, "", border="LR")

            self.cell(col_widths[-1], line_height, "", border="R")
            
            # Get amount from dict
            amount = all_charges[label]
            if isinstance(amount, (int, float)):
                text = f"{amount:.2f}"
            else:
                text = str(amount)

            box_x = self.get_x() - col_widths[-1]
            box_y = self.get_y()
            box_w = col_widths[-1]
            text_width = self.get_string_width(text)
            text_x = box_x + (box_w - text_width) / 2
            text_y = box_y + (line_height - 4) / 2
            self.set_xy(text_x, text_y)
            self.cell(text_width, 4, text)
            self.set_xy(x_start, box_y + line_height)

        # === Grand Total Row ===
        self.set_font("Helvetica", "B", 9)
        self.set_x(x_start)
        self.cell(sum(col_widths[:-1]), line_height, "Total", border=1, align="R")
        text = f"{rounded_final_amount:.2f}"
        self.cell(col_widths[-1], line_height, text, border=1, align="C")


        self.ln(6)
        if round_sign=="+":
            GST_amount = round(GST_amount+round_off)
        if round_sign == "-":
            GST_amount = round(GST_amount-round_off)
        return BillSummary(total_amount=total_amount, final_amount=rounded_final_amount, GST_amount=GST_amount)


    def amount_in_word(self, amount):
        self.set_font("Helvetica", "B", 9)

        in_worlds = num2words(amount, to='cardinal', lang='en_IN').title()

        self.cell(
            0,
            15, 
            f"Invoice Amount in a word : {in_worlds} Only", 
            new_x=XPos.LMARGIN, 
            new_y=YPos.NEXT,
            align="L"
            )


    def add_tax_summary_table(self, total_amount, final_amount, GST_amount):

        tax_data = {
            "taxable_value": total_amount,
            "cgst_rate": "9%",
            "cgst_amount": GST_amount/2,
            "sgst_rate": "9%",
            "sgst_amount": GST_amount/2,
            "total_tax_amount": GST_amount
        }
        
        self.set_font("Helvetica", "B", 9)
        x = 10
        y = self.get_y()
        line_height = 6

        # Column widths
        w_hsn = 25
        w_taxable = 30
        w_rate = 15
        w_amt = 30
        w_total_tax = 35

        # First header row (merged titles for CGST and SGST)
        self.set_xy(x, y)
        self.cell(w_hsn, line_height * 2, "HSN/SAC", border=1, align="C")
        self.cell(w_taxable, line_height * 2, "Taxable Value", border=1, align="C")

        # Central Tax (merged over 2 columns)
        self.cell(w_rate + w_amt, line_height, "Central Tax", border=1, align="C")

        # State Tax (merged over 2 columns)
        self.cell(w_rate + w_amt, line_height, "State Tax", border=1, align="C")

        # Total Tax Amount (double height)
        self.cell(w_total_tax, line_height * 2, "Total Tax Amount", border=1, align="C")
        self.ln(line_height)

        # Second header row (Rate/Amount)
        self.set_x(x + w_hsn + w_taxable)
        self.cell(w_rate, line_height, "Rate", border=1, align="C")
        self.cell(w_amt, line_height, "Amount", border=1, align="C")
        self.cell(w_rate, line_height, "Rate", border=1, align="C")
        self.cell(w_amt, line_height, "Amount", border=1, align="C")
        self.ln(line_height)

        # Data row
        self.set_font("Helvetica", "", 9)
        self.set_x(x)
        self.cell(w_hsn, line_height, "Total", border=1, align="C")
        # self.cell(w_taxable, line_height, f"{tax_data['taxable_value']:.2f}", border=1, align="C")
        # self.cell(w_rate, line_height, f"{tax_data['cgst_amount']:.2f}", border=1, align="C")
        # self.cell(w_amt, line_height, tax_data["cgst_amount"], border=1, align="C")
        # self.cell(w_rate, line_height, tax_data["sgst_rate"], border=1, align="C")
        # self.cell(w_amt, line_height, tax_data["sgst_amount"], border=1, align="C")
        # self.cell(w_total_tax, line_height, tax_data["total_tax_amount"], border=1, align="C")
        self.cell(w_taxable, line_height, f"{tax_data['taxable_value']:.2f}", border=1, align="C")
        self.cell(w_rate, line_height, tax_data["cgst_rate"], border=1, align="C")
        self.cell(w_amt, line_height, f"{tax_data['cgst_amount']:.2f}", border=1, align="C")
        self.cell(w_rate, line_height, tax_data["sgst_rate"], border=1, align="C")
        self.cell(w_amt, line_height, f"{tax_data['sgst_amount']:.2f}", border=1, align="C")
        self.cell(w_total_tax, line_height, f"{tax_data['total_tax_amount']:.2f}", border=1, align="C")


        self.ln(8)


    def add_bank_details_table(self):
        bank_data = {
            "bank_name": "UCO Bank",
            "account_number": "25110210001042",
            "branch": "KAMOTHE",
            "ifsc": "UCBA0002511"
        }

        self.set_font("Helvetica", "", 9)

        self.ln(7)
        
        x = 10
        y_top = self.get_y() 
        col1_w = 40
        col2_w = 40
        row_h = 6

        # Bank info rows
        rows = [
            ["Bank name", bank_data["bank_name"]],
            ["Account number", bank_data["account_number"]],
            ["Branch", bank_data["branch"]],
            ["IFSC Code", bank_data["ifsc"]],
        ]

        for label, value in rows:
            self.set_x(x)
            self.cell(col1_w, row_h, label, border=1)
            self.cell(col2_w, row_h, value, border=1)
            self.ln(row_h)
    
        return y_top 


    def add_authorisation_block(self, y_top=None):
        self.set_font("Helvetica", "B", 10)

        if y_top is None:
            y_top = self.get_y()

        x = 120  # right side of the page (next to bank table)

        self.set_xy(x, y_top)
        self.cell(80, 31, "FOR JAI BHAVANI TRADERS", ln=True, align="L")

        self.set_xy(x, y_top + 32)
        self.set_font("Helvetica", "", 10)
        self.cell(80, 6, "Authorised Signature", ln=True, align="L")


