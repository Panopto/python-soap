# flake8: noqa
from panopto_api.AuthenticatedClientFactory import AuthenticatedClientFactory
from panopto_api.ClientWrapper import ClientWrapper
from datetime import datetime, timedelta
from time import sleep
from StringIO import StringIO
import zipfile

host = 'localhost'
username = 'admin'
password = '<insert local password>'

# create a client factory for making authenticated API requests
auth = AuthenticatedClientFactory(
    host, username, password, verify_ssl=host != 'localhost')

# create a client for calling the usage reporting endpoint
usage = auth.get_client('UsageReporting')

# let's see what reports are available
print 'so many reports to choose from!'
for reportType in usage.call_service('DescribeReportTypes'):
    print '\t', reportType

# maybe a SessionUsage report is for us. what does it contain?
print
print 'columns in the SessionUsage report:'
for column in usage.call_service('DescribeReportType', reportType='SessionUsage'):
    print '\t', column

# looks good -- any reports currently kicking around?
print
print 'current SessionUsage reports:'
for report in usage.call_service('GetRecentReports', reportType='SessionUsage'):
    print '\t{ReportId}: {StartTime} - {EndTime} '.format(**report) + \
                ('(available)' if report['IsAvailable'] else '(pending)')

# let's queue a new one for the past month
now = datetime.now()
last_month = now - timedelta(days=30)
report_id = usage.call_service(
    'QueueReport',
    reportType='SessionUsage',
    startTime=last_month,
    endTime=now)

# let's assume the report generator is running. we can wait a bit for the report to be generated.
isAvailable = False
for attempt in range(3):
    seconds = (attempt+1)*10
    print 'sleeping {} time{} for {} seconds...'.format(
        attempt + 1,
        's' if attempt else '', # grammar is critical
        seconds)
    sleep(seconds)

    isAvailable = [x['IsAvailable'] for x in \
                   usage.call_service('GetRecentReports', reportType='SessionUsage') \
                   if x['ReportId'] == report_id][0]
    if isAvailable:
        break

if not isAvailable:
    print 'the report engine is taking the day off it seems. try again later.'
else:
    # let's get the report! this bit is a little tricky since we want to download raw bytes.
    raw_response = usage.call_service_raw('GetReport', reportId=report_id)
    content_buffer = StringIO(raw_response.content)
    zip_archive = zipfile.ZipFile(content_buffer)
    # there's just one report, the archive is for compression only
    report_file = zip_archive.namelist()[0]
    report_rows = zip_archive.open(report_file).readlines()
    # the rows are comma-delimitted content (it's a CSV)
    if len(report_rows) == 1:
        print 'the report is empty! use more sessions'
    else:
        # the report alwasy leads with a 3-character UTF-8 BOM. strip it out.
        headers = report_rows[0][3:].split(',')
        rows = []
        for line in report_rows[1:]:
            # the first field, sessionName, might contain commas itself
            # in that case, it's wrapped in quotation marks. test that case.
            if line[0] == '"':
                splitz = line.split('"')
                rows.append([splitz[1]] + splitz[2].split(',')[1:])
            else:
                rows.append(line.split(','))

        print "{} rows in the report... let's peel out some stats!".format(len(rows))
        print

        session_name_index = headers.index('Session Name')
        average_rating_index = headers.index('Average Rating')
        views_index = headers.index('Views')
        # most-viewed session
        mvs = max(rows, key=lambda r: r[views_index])
        print 'most-viewed session: {} ({} views)'.format(mvs[session_name_index], mvs[views_index])
        # highest-rated session
        hrs = max(rows, key=lambda r: r[average_rating_index])
        print 'highest-rated session: {} (rated {} out of 5)'.format(
            hrs[session_name_index],
            hrs[average_rating_index])

        # tabulate presenter stats
        presenter_index = headers.index('Presenter')
        presenter_column_indices = { c: headers.index(c) for c in \
                                     ['Views', 'Unique Viewers', 'Minutes Delivered', 'Session Length'] }
        presenter_stats = { p:
                            { c: 0 for c in presenter_column_indices } \
                            for p in set([row[presenter_index] for row in rows]) }
        for row in rows:
            presenter_stat = presenter_stats[row[presenter_index]]
            for column,column_index in presenter_column_indices.items():
                presenter_stat[column] += float(row[column_index])

        # show the people
        for stat_name, stat_description, stat_formatter in [
                ('Views', 'most-viewed presenter by view count', lambda s: int(s)),
                ('Minutes Delivered', 'most-viewed presenter by minutes viewed', lambda s: s),
                ('Unique Viewers', 'most-viewed presenter by unique viewers', lambda s: int(s)),
                ('Session Length', 'most prolific presenter by minutes presented', lambda s: s)]:
            winner = max(presenter_stats.items(), key=lambda t:t[1][stat_name])
            print '{}: {} ({})'.format(stat_description, winner[0], stat_formatter(winner[1][stat_name]))

        print
        print 'are you not entertained?!'
