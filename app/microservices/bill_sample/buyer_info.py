details = {
    "Vijay Laxmi Engineering": (
        "M/S: - Vijay Laxmi Engineering\n"
        "Address: - GRD, H996, H996, OPP INDIABULLS COMPLEX, KON, KON.PANVEL, Raigad,\n"
        "Maharashtra, 410207\n"
        "GSTIN: - 27ACBPG2352G2Z0\n"
        "State Name: - Maharashtra\n"
        "State Code : - 27"
    ),

    "Pearl Auto Springs": (
        "M/S: - Pearl Auto Springs\n"
        "Address: - Shop No- 36, Truck Terminal\n"
        "Near Libra Weight Bridge Kalamboli\n"
        "Navi Mumbai\n"
        "GSTIN: - 27ABFFP2282B1ZG\n"
        "State Name: - Maharashtra\n"
        "State Code : - 27"
    ),

    "Rajesh Cargo Movers(INDIA)Private Limited": (
        "M/S: - Rajesh Cargo Movers(INDIA)Private Limited\n"
        "Address: - Kalamboli.\n"
        "GSTIN: - 27AAGCR8316K1ZZ\n"
        "State Name: - Maharashtra\n"
        "State Code : - 27"
    ),

    "Shri Yash Roadways": (
        "M/S: - Shri Yash Roadways\n"
        "Address: - Steel Chembar A Wing,\n"
        "317, Kalamboli, PANVEL, Raigad,\n"
        "Maharashtra, 410207\n"
        "GSTIN: - 27AALPU0368C1ZL\n"
        "State Name: - Maharashtra\n"
        "State Code : - 27"
    )
}

def all_buyer_info(name):

    if name in details.keys():
        return details[name]
    else:
        return None


# print(all_buyer_info("Shri Yash Roadways"))