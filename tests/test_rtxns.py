# from datetime import date
# from brightsidebudget import RTxn, rtxn_to_postings


# def test_rtxn_to_postings():
#     rtxn = RTxn(rtxn_id="Food", account="Food", amount=100,
#                 recurrence="DTSTART:2021-01-01 FREQ=DAILY;INTERVAL=1")
#     ps = rtxn_to_postings(rtxn, start_date=date(2021, 1, 1), end_date=date(2021, 1, 31))
#     assert len(ps) == 31
#     assert ps[0].account == "Food"
#     assert ps[0].amount == 100
