def format_results(data):
    """
    Parses results from book_spot, release_spot, show_bookings, and book_free actions.
    """
    body = ''
    match data['action']:
        case 'book_spot':
            r = data['result']
            match r['status']:
                case 'success':
                    body += f"Spot {r['spot']} in {r['zone']} was booked for {r['for_date']}."
                case _:
                    body += f"Couldn't book {data['request']['spot_name']} for {data['request']['for_date']}!"

        case 'release_spot':
            req = data['request']
            body += f"Spot for {req['for_date']} was released."

        case 'show_bookings':
            body += "Retrieved the following bookings:\n\n"
            for reservation in data['result']['bookings']:
                parking_spot = reservation['my_booking']['name'] if reservation['my_booking'] else ""
                body += f"{reservation['day'].ljust(8)} | {parking_spot.rjust(8)} |\n"

        case 'show_spots':
            r = data['result']
            body += f"Retrieved the following spots in {r['zone']} for {r['for_date']}:\n\n"
            for s in r['spots']:
                state = 'free' if s['free'] else ""
                body += f"{s['name'].ljust(8)} | {state.rjust(8)} |\n"

        case 'book_free':
            body += f"I was looking for free spots from {data['request']['look-from']} and tried to book spots {data['request']['spot_name']}.\n\n"
            attempts = data['result']
            if attempts:
                body += "Bookings:\n"
                for a in attempts:
                    r = a['result']
                    booked = r['spot'] if r['status'] == 'success' else "FAILED"
                    body += f"{r['for_date'].ljust(8)} | {booked.rjust(8)} |\n"
            else:
                body += "No free spots found."
            body += "\n\n"
        case _:
            body += f"Parkanizer Bot notification: Unknown action type: {data['action']}"

    return body
