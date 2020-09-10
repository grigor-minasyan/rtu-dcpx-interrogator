# RTU DCPx Interrogator

This program is designed to run on a scheduled basis. It updates databases with polled data from arduino based remote telemetry units (RTU)

Here is a simple breakdown of what it does.

* Get a list of RTUs needed to monitor from an MySQL database.
* Send a polling request (DCPx packets via UDP) to all of the RTUs
* Listen to information sent back from the RTUs
* Process the sent information and put it back into the database

This is designed to ba cron job.
