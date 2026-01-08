# from datetime import datetime
# import pandas as pd
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import sessionmaker, Session

# from app.db.models.db_base import Products




# def verify_sync_password(input_password: str):
#     EXPECTED_PASSWORD = "MARG_SYNC_123"  # move to env later

#     if not input_password or input_password != EXPECTED_PASSWORD:
#         raise PermissionError("Invalid sync password")

# def parse_int_price(value):
#     try:
#         if value is None or value == "":
#             return None
#         return int(float(str(value).replace(",", "")))
#     except Exception:
#         return None


# def parse_stock(value):
#     try:
#         return int(float(value))
#     except Exception:
#         return 0


# def sync_products_from_marg_excel(
#     db: Session,
#     file_path: str,
#     sync_password: str,
#     system_user_id: int = None
# ):
#     # ---------------------------
#     # 0. Password Check
#     # ---------------------------
#     verify_sync_password(sync_password)

#     now = datetime.utcnow()

#     # ---------------------------
#     # 1. Load Excel
#     # ---------------------------
#     df = pd.read_excel(file_path, skiprows=2)
#     df.columns = [c.strip() for c in df.columns]

#     required_cols = {
#         "Code",
#         "Product Name",
#         "Current Stock",
#         "Sales Price",
#         "M.R.P."
#     }

#     if not required_cols.issubset(df.columns):
#         raise RuntimeError("Invalid Marg Excel format")

#     df = df[df["Code"].notna()]

#     # ---------------------------
#     # 2. Preload products
#     # ---------------------------
#     products = db.query(Products).all()
#     product_map = {p.marg_product_code: p for p in products}
#     incoming_codes = set()

#     inserted = updated = disabled = 0

#     try:
#         # ---------------------------
#         # 3. Row processing
#         # ---------------------------
#         for _, row in df.iterrows():
#             code = str(row["Code"]).strip()
#             incoming_codes.add(code)

#             name = str(row["Product Name"]).strip()
#             stock = parse_stock(row["Current Stock"])
#             selling_price = parse_int_price(row["Sales Price"])
#             mrp = parse_int_price(row["M.R.P."])

#             if selling_price is None:
#                 continue  # skip invalid rows

#             if code in product_map:
#                 p = product_map[code]
#                 p.product_name = name
#                 p.stock = stock
#                 p.product_price = selling_price
#                 p.product_full_price = mrp
#                 p.is_active_in_marg = True
#                 p.is_deleted = False
#                 p.last_marg_sync_at = now
#                 p.updated_by = system_user_id
#                 updated += 1
#             else:
#                 p = Products(
#                     marg_product_code=code,
#                     product_name=name,
#                     stock=stock,
#                     product_price=selling_price,
#                     product_full_price=mrp,
#                     is_active_in_marg=True,
#                     is_deleted=False,
#                     last_marg_sync_at=now,
#                     created_by=system_user_id
#                 )
#                 db.add(p)
#                 inserted += 1

#         # ---------------------------
#         # 4. Disable missing products
#         # ---------------------------
#         for code, p in product_map.items():
#             if code not in incoming_codes and p.is_active_in_marg:
#                 p.is_active_in_marg = False
#                 p.stock = 0
#                 p.updated_by = system_user_id
#                 disabled += 1

#         db.commit()

#     except Exception as e:
#         db.rollback()
#         raise RuntimeError(f"Marg sync failed: {e}")

#     return {
#         "inserted": inserted,
#         "updated": updated,
#         "disabled": disabled,
#         "synced_at": now.isoformat()
#     }





from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from app.db.models.db_base import Products
from config.config import settings


# ---------------------------
# Password check (PLAIN)
# ---------------------------
def verify_sync_password(input_password: str):
    if input_password != "MARG_SYNC_123":
        raise PermissionError("Invalid sync password")


def parse_int(value):
    try:
        if value is None or value == "":
            return None
        return int(float(str(value).replace(",", "")))
    except Exception:
        return None


def parse_stock(value):
    try:
        return int(float(value))
    except Exception:
        return 0


# ---------------------------
# MAIN SYNC FUNCTION (SYNC)
# ---------------------------
def sync_products_from_marg_excel(
    db: Session,
    file_path: str,
    sync_password: str,
    system_user_id: int | None = None
):
    verify_sync_password(sync_password)

    now = datetime.utcnow()

    # ---------------------------
    # 1. Load Excel
    # ---------------------------
    df = pd.read_excel(file_path, skiprows=2)
    df.columns = [c.strip() for c in df.columns]

    required_cols = {
        "Code",
        "Product Name",
        "Current Stock",
        "Sales Price",
    }

    if not required_cols.issubset(df.columns):
        raise RuntimeError("Invalid Marg Excel format")

    df = df[df["Code"].notna()]

    # ---------------------------
    # 2. Preload existing products
    # ---------------------------
    products = db.query(Products).all()
    product_map = {p.marg_product_code: p for p in products}
    incoming_codes = set()

    inserted = updated = disabled = 0

    try:
        # ---------------------------
        # 3. Process rows
        # ---------------------------
        for _, row in df.iterrows():
            code = str(row["Code"]).strip()
            incoming_codes.add(code)

            name = str(row["Product Name"]).strip()
            stock = parse_stock(row["Current Stock"])
            selling_price = parse_int(row["Sales Price"])

            if selling_price is None:
                continue

            if code in product_map:
                # UPDATE
                p = product_map[code]
                p.product_name = name
                p.stock = stock
                p.product_price = selling_price
                p.is_active_in_marg = True
                p.is_deleted = False
                p.last_marg_sync_at = now
                p.updated_by = system_user_id
                updated += 1
            else:
                # INSERT
                p = Products(
                    marg_product_code=code,
                    product_name=name,
                    stock=stock,
                    product_price=selling_price,
                    is_active_in_marg=True,
                    is_deleted=False,
                    last_marg_sync_at=now,
                    created_by=system_user_id
                )
                db.add(p)
                inserted += 1

        # ---------------------------
        # 4. Disable missing products
        # ---------------------------
        for code, p in product_map.items():
            if code not in incoming_codes and p.is_active_in_marg:
                p.is_active_in_marg = False
                p.stock = 0
                p.updated_by = system_user_id
                disabled += 1

        db.commit()

    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Marg sync failed: {e}")

    return {
        "inserted": inserted,
        "updated": updated,
        "disabled": disabled,
        "synced_at": now.isoformat()
    }