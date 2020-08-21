# flake8: noqa
# note: move this exmaple into the directory with the src filesfrom __future__ import print_function
import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from AuthenticatedClientFactory import AuthenticatedClientFactory

DATE_FORMAT = '%Y-%m-%d'


def get_usage_client(
        host='mysite.hosted.panopto.com',
        username='admin',
        password='yoursecrethere'):

    auth = AuthenticatedClientFactory(host, username, password)
        
    return auth.get_client('UsageReporting')


def show_report_status(usage_client, report_type='FolderUsage'):
    report_status = usage_client.call_service(
        'GetRecentReports',
        reportType=report_type)

    if report_status:
        for status in report_status:
            print('\t'.join([
                status['ReportId'],
                status['StartTime'].strftime(DATE_FORMAT),
                status['EndTime'].strftime(DATE_FORMAT),
                'Ready' if status['IsAvailable'] else 'Pending']))
    else:
        print('No recent reports')


def queue_report(
        usage_client,
        start,
        end,
        report_type='FolderUsage'):

    report_id = usage_client.call_service(
        'QueueReport',
        startTime=datetime.strptime(start, DATE_FORMAT),
        endTime=datetime.strptime(end, DATE_FORMAT),
        reportType=report_type)
    return report_id


def read_report(usage_client, report_id):
    raw_response = usage_client.call_service_raw(
        'GetReport',
        reportId=report_id)
    content_buffer = BytesIO(raw_response.content)
    zip_archive = zipfile.ZipFile(content_buffer)
    # there's just one report: the archive is for compression only
    report_file = zip_archive.namelist()[0]
    report_rows = zip_archive.open(report_file).readlines()
    # each report begins with a 3-character UTF-8 BOM; drop it
    report_rows[0] = report_rows[0][3:]
    return [row.decode('utf-8') for row in report_rows]
