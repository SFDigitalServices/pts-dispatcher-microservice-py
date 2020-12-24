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
from ..transforms.transform import TransformBase

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
        tracker = {
            'formio id': [],
            'status': [],
            'error': [],
            'bb_project_id': [],
            'project_address': [],
            'block': [],
            'lot': [],
            'date_created': [],
            'applicant_name': [],
            'applicant_phone': [],
            'applicant_email': [],
            'staff_assignment': [],
            'bpa#': [],
            'last_remark_date': [],
            'last_remarks': [],
            'ppc_release_date': [],
            'issued_closed_date': [],
        }

        #exported_submissions = self.get_exported_submissions()
        data_file = open(self.data_file_path + 'exported_submissions.txt', 'r')
        data_string = data_file.read()
        exported_submissions = ast.literal_eval(data_string)
        data_file.close()

        summary_email_content = self.create_email_content(file_name, tracker, exported_submissions)
        # create tracker XLS
        tracker_file_content = self.create_tracker_file(summary_email_content['tracker_content'])

        subject = 'CSV export summary'
        recipients = {
            'from_email': sendgrid.helpers.mail.Email(os.environ.get('EXPORT_EMAIL_FROM')),
            'to_emails': os.environ.get('SUMMARY_EMAIL_TO'),
            'cc_emails': os.environ.get('SUMMARY_EMAIL_CC', None),
            'bcc_emails': os.environ.get('SUMMARY_EMAIL_BCC', None)
        }
        Export().email(recipients, subject, summary_email_content['email_body_content'], 'Tracker.xlsx', tracker_file_content)
        return summary_email_content

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
            ret[item['_id']]['date_created'] = item['created']
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

        # update column names
        data_frame.rename(columns=TransformBase.pretty_string, inplace=True)
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

    #pylint: disable=no-self-use, too-many-locals, R0915
    def create_email_content(self, file_name, tracker, exported_submissions):
        """ Create summary email for permit techs """
        ret = {}
        file_handle = open(file_name, 'r')
        content = '<table><tr><th>Integration Status</th><th>Error</th><th>Date Created</th><th>BB Project ID</th><th>Formio ID</th>'
        content += '<th>Email</th><th>Name</th><th>Project Address</th><th>Block</th><th>Lot</th><th>Uploaded Files</th></tr>'
        # loop through the result file to create the summary table
        file2 = open('tracker.txt', 'w')
        for line in file_handle:
            fields = line.split('|')
            #skip header
            if fields[0] == 'FORMIO':
                continue
            formio_id = fields[0]
            status = fields[1]
            uploaded_files = bb_project_id = date_created = applicant_first_name = applicant_last_name = block = lot = project_address = applicant_email =  ''
            if formio_id in exported_submissions:
                tracker['formio id'].append(formio_id)
                tracker['status'].append(status)
                tracker['error'].append(fields[2])
                #file2.write(str(exported_submissions[formio_id]))
                project_address = exported_submissions[formio_id].get('projectAddress', '')
                tracker['project_address'].append(project_address)
                block = exported_submissions[formio_id].get('projectAddressBlock', '')
                tracker['block'].append(block)
                lot = exported_submissions[formio_id].get('projectAddressLot', '')
                tracker['lot'].append(lot)
                bb_project_id = exported_submissions[formio_id].get('bluebeamId', '')
                tracker['bb_project_id'].append(bb_project_id)
                applicant_email = exported_submissions[formio_id].get('applicantEmail', '')
                tracker['applicant_email'].append(applicant_email)
                applicant_first_name = exported_submissions[formio_id].get('applicantFirstName', '')
                applicant_last_name = exported_submissions[formio_id].get('applicantLastName', '')
                tracker['applicant_name'].append(applicant_first_name + ' ' + applicant_last_name)
                applicant_phone = exported_submissions[formio_id].get('applicantPhoneNumber', '')
                tracker['applicant_phone'].append(applicant_phone)
                date_created = exported_submissions[formio_id].get('date_created', '')
                if date_created:
                    date_created = datetime.datetime.strptime(date_created, '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%Y/%m/%d %H:%M:%S")
                tracker['date_created'].append(date_created)
                uploaded_files = self.get_uploaded_file_names(exported_submissions[formio_id])
                #fill empty tracker columns with empty values
                tracker['staff_assignment'].append('')
                tracker['bpa#'].append('')
                tracker['last_remark_date'].append('')
                tracker['last_remarks'].append('')
                tracker['ppc_release_date'].append('')
                tracker['issued_closed_date'].append('')
            # if successfully loaded into PTS, update submission status
            #if status == 'Success':
                #PermitApplication.update_status(formio_id)
                # send email to applicants with success email template?

            content += '<tr>'
            content += '<td>' + status + '</td>'
            content += '<td>' + fields[2] + '</td>'
            content += '<td>' + date_created + '</td>'
            content += '<td>' + bb_project_id + '</td>'
            content += '<td>' + formio_id + '</td>'
            content += '<td>' + applicant_email + '</td>'
            content += '<td>' + applicant_first_name + ' ' + applicant_last_name + '</td>'
            content += '<td>' + project_address + '</td>'
            content += '<td>' + block + '</td>'
            content += '<td>' + lot + '</td>'
            content += '<td>' + uploaded_files + '</td>'
            content += '</tr>'

        file_handle.close()
        file2.write(str(tracker))
        file2.close()
        content += '</table>'
        ret['email_body_content'] = content
        ret['tracker_content'] = tracker
        return ret

    def get_uploaded_file_names(self, exported_submission):
        """ get all upload file names """
        aws_file_url = os.environ['AWS_FILE_URL']
        ds_file_url = os.environ['DS_FILE_URL']
        if exported_submission['permitType'] == "existingBuilding" or exported_submission['permitType'] == "revisionToAnIssuedPermit":
            uploads = exported_submission.get('optionalUploads', None)
        else:
            uploads = exported_submission.get('requiredUploads', None)

        _uploads = ''
        for upload in uploads:
            href = ''
            if 'url' in upload and 'originalName' in upload:
                href = upload['url'].replace(aws_file_url, ds_file_url)
                _uploads += '<li><a href="' + href + '"</a>' + upload['originalName'] + '</li>'

        confirm_uploads = ''
        if 'confirmationUploads' in exported_submission:
            for upload in exported_submission['confirmationUploads']:
                href = ''
                if 'url' in upload and 'originalName' in upload:
                    href = upload['url'].replace(aws_file_url, ds_file_url)
                    confirm_uploads += '<li><a href="' + href + '"</a>' + upload['originalName'] + '</li>'

        return '<ul>' + _uploads + confirm_uploads + '</ul>'
