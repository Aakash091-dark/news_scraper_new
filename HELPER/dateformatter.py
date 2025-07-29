from dateutil import parser

def standardize_pub_dates(pub_dates):
    standardized = []
    tzinfos = {"EDT": -4 * 3600}  # EDT is UTC-4 hours
    for date_str in pub_dates:
        try:
            if not date_str or len(date_str.strip()) < 6:
                raise ValueError("Too short to be a date")
            dt = parser.parse(date_str, tzinfos=tzinfos)
            formatted = dt.strftime("%d-%m-%Y")
            standardized.append(formatted)
        except Exception as e:
            standardized.append(f"Error parsing: {date_str} ({e})")
    return standardized[0]
