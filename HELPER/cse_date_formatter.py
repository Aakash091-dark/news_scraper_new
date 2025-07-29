import re
from datetime import datetime

def extract_date_and_description(snippet):
    if snippet == None:
        return {"date": None, "description": None}
    # Extract date using regex
    date_match = re.search(r'([A-Za-z]{3}) (\d{1,2}), (\d{4})', snippet)
    
    if date_match:
        month_str, day, year = date_match.groups()
        # Convert to datetime object
        date_obj = datetime.strptime(f"{day} {month_str} {year}", "%d %b %Y")
        formatted_date = date_obj.strftime("%d-%m-%Y")
    else:
        formatted_date = None

    # Remove the date portion from the snippet to get description
    description = re.sub(r'^.*?\.\.\. ', '', snippet).strip('\xa0...')

    return {
        "date": formatted_date,
        "description": description
    }


