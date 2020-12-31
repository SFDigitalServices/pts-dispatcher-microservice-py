"""Process result file module"""
import os
import json
import datetime
import logging
import ast
import jsend
import falcon
import pytz
import pysftp
import sendgrid
import sentry_sdk
import pandas as pd
from .permit_applications import PermitApplication
from ..resources.export import Export

ERROR_GENERIC = "Bad Request"
ERROR_ACCESS_401 = "Unauthorized"

class ProcessResultFile():
    """ Class for processing result file """
    data_file_path = os.path.dirname(__file__) + '/exported_data/'

    def on_get(self, req, resp):
        """ on get request """
        try:
            if req.params['token'] != os.environ.get('EXPORT_TOKEN') and req.params['token'] != os.environ.get('ACCESS_KEY'):
                raise ValueError(ERROR_ACCESS_401)

            timezone = pytz.timezone('America/Los_Angeles')
            current_time = datetime.datetime.now(timezone)
            file_name = 'DBI_permits_' + str(current_time.year) + str(current_time.month) + str(current_time.day)
            #DBI_permits_YYYYMMDDHHMI_response.csv  where HH = 24 hour clock Mi  = minutes
            file_name = 'PTS_Export_09_26.csv'
            result = self.get_result_file(file_name)

            if result == file_name:
                # dowloaded the result file
                self.process_file(self.data_file_path + file_name)

                resp.body = json.dumps(jsend.success({'message': file_name, 'responses':len(file_name)}))
                resp.status = falcon.HTTP_200
        #pylint: disable=broad-except
        except Exception as exception:
            logging.exception('ProcessResultFile.on_get Exception')
            resp.status = falcon.HTTP_500

            msg_error = ERROR_GENERIC
            if exception.__class__.__name__ == 'ValueError':
                msg_error = "{0}".format(exception)

            resp.body = json.dumps(jsend.error(msg_error))

    #pylint: disable=no-self-use,too-many-locals
    def process_file(self, file_name):
        """ process the result file """
        recipients = ''
        subject = 'CSV export summary'
        content = '<table><tr><th>Integration Status</th><th>ErrorD</th><th>Formio ID</th><th>Street #</th><th>Street Name</th><th>SFX</th><th>BB Project ID</th></tr>'

        file_handle = open(file_name, 'r')
        #exported_submissions = self.get_exported_submissions()
        data_file = open(self.data_file_path + 'exported_submissions.txt', 'r')
        data_string = data_file.read()
        exported_submissions = ast.literal_eval(data_string)
        data_file.close()
        tracker = {
            'formio id': [],
            'status': [],
            'error': [],
            'street_num': [],
            'street_name': [],
            'sfx': [],
            'bb_project_id': []
        }
        # loop through the result file to create the summary table
        #file2 = open('tracker.txt', 'w')
        for line in file_handle:
            fields = line.split('|')
            #skip header
            if fields[0] == 'FORMIO':
                continue
            formio_id = fields[0]
            status = fields[1]
            street_num = street_name = bb_project_id = sfx = ''
            if formio_id in exported_submissions:
                tracker['formio id'].append(formio_id)
                tracker['status'].append(status)
                tracker['error'].append(fields[2])
                #file2.write(str(exported_submissions[formio_id]))
                street_num = exported_submissions[formio_id]['projectAddressNumber'] if 'projectAddressNumber' in exported_submissions[formio_id] else ''
                tracker['street_num'].append(street_num)
                street_name = exported_submissions[formio_id]['projectAddressStreetName'] if 'projectAddressStreetName' in exported_submissions[formio_id] else ''
                tracker['street_name'].append(street_name)
                sfx = exported_submissions[formio_id]['projectAddressNumberSuffix'] if 'projectAddressNumberSuffix' in exported_submissions[formio_id] else ''
                tracker['sfx'].append(sfx)
                bb_project_id = exported_submissions[formio_id]['bluebeamId'] if 'bluebeamId' in exported_submissions[formio_id] else ''
                tracker['bb_project_id'].append(bb_project_id)
            # if successfully loaded into PTS, update submission status
            if status == 'Success':
                PermitApplication.update_status(formio_id)
                # send email to applicants with success email template?
            #else:
                # send email to applicants with failed email template?

            content += '<tr>'
            content += '<td>' + status + '</td>'
            content += '<td>' + fields[2] + '</td>'
            content += '<td>' + formio_id + '</td>'
            content += '<td>' + street_num + '</td>'
            content += '<td>' + street_name + '</td>'
            content += '<td>' + sfx + '</td>'
            content += '<td>' + bb_project_id + '</td>'
            content += '</tr>'

        file_handle.close()
        #file2.close()
        content += '</table>'
        # create tracker XLS
        tracker_file_content = self.create_tracker_file(tracker)
        recipients = {
            'from_email': sendgrid.helpers.mail.Email(os.environ.get('EXPORT_EMAIL_FROM')),
            'to_emails': os.environ.get('SUMMARY_EMAIL_TO'),
            'cc_emails': os.environ.get('SUMMARY_EMAIL_CC', None),
            'bcc_emails': os.environ.get('SUMMARY_EMAIL_BCC', None)
        }
        Export().email(recipients, subject, content, 'Tracker.xlsx', tracker_file_content)
        return content

    #pylint: disable=no-self-use,too-many-locals
    def get_result_file(self, file_name):
        """ get result fild from sftp folder """

        host = os.environ.get('SFTP_HOSTNAME')
        user = os.environ.get('SFTP_USERNAME')
        pass_ = os.environ.get('SFTP_PASSWORD')
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        with pysftp.Connection(host=host, username=user, password=pass_, cnopts=cnopts) as sftp:
            localfilepath = self.data_file_path + file_name
            try:
                sftp.get(file_name, localfilepath)
            #pylint: disable=broad-except
            except Exception as exception:
                print("Exception: {0}".format(str(exception)))
                return ''

        return file_name

    def get_exported_submissions(self):
        """ get submissions in the current csv export """
        formio_query = {
            'actionState': 'Export to PTS'
        }

        with sentry_sdk.configure_scope() as scope:
            scope.set_extra('formio_query', formio_query)

        responses = PermitApplication.get_applications_by_query(formio_query)

        ret = {}
        # use formio id as the key for the ['data'] object
        for item in responses:
            ret[item['_id']] = item['data']
        #file1 = open("exported_submissions.txt", "w")  # write mode
        #file1.write(str(ret))
        #file1.close()
        return ret

    def create_tracker_file(self, tracker):
        """ create the tracker spreadsheet """
        file_content = ''
        # Create a Pandas dataframe from tracker data.
        tracker_file = self.data_file_path + 'tracker_tmp.xlsx'
        # Create a Pandas dataframe from some data.
        data_frame = pd.DataFrame(tracker)

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        #pylint: disable=abstract-class-instantiated
        writer = pd.ExcelWriter(tracker_file, engine='xlsxwriter')

        # Convert the dataframe to an XlsxWriter Excel object.
        data_frame.to_excel(writer, sheet_name='New Submittals', index=False)

        # Close the Pandas Excel writer and output the Excel file.
        writer.save()

        if os.path.isfile(tracker_file):
            file1 = open(tracker_file, 'rb')
            file_content = file1.read()
            file1.close()
            #clean up tmp file
            os.remove(tracker_file)
        return file_content
