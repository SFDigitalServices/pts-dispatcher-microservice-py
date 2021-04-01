"""Process result file module"""
import os
import sys
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
    data_file_path = os.path.dirname(__file__) + '/../resources/data/exported_data/'
    template_file_path = os.path.dirname(__file__) + '/../resources/data/templates/'

    def on_get(self, req, resp):
        """ on get request """
        try:
            if req.params['token'] != os.environ.get('EXPORT_TOKEN') and req.params['token'] != os.environ.get('ACCESS_KEY'):
                raise ValueError(ERROR_ACCESS_401)

            #timezone = pytz.timezone('America/Los_Angeles')
            #current_time = datetime.datetime.now(timezone)
            #today_file_name = 'DBI_permits_' + str(current_time.year) + str(current_time.month) + str(current_time.day)
            #DBI_permits_YYYYMMDDHHMI_response.csv  where HH = 24 hour clock Mi  = minutes
            current_timestamp_file = open(self.data_file_path + 'current_file_name.txt', "r")  # reads file name
            #file_name = current_timestamp_file.read() + '_response.csv'
            file_name = 'DBI_permits_2021322147_response.csv'
            # dowloaded the result file from FTP
            #result = self.get_result_file(file_name)
            #if today_file_name in file_name and result:
            file_name = self.data_file_path + file_name
            self.process_file(file_name)

            resp.body = json.dumps(jsend.success({'message': file_name, 'responses':len(file_name + '.csv')}))
            resp.status = falcon.HTTP_200
        except Exception as exception: #pylint: disable=broad-except
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
            'temp_app_num': [],
            'error': [],
            'permit_type': [],
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
        # get exported submissions from file
        exported_submissions = self.get_exported_submissions()
        # create summary email to permit techs
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
                self.merge_failed_bluebeam(localfilepath)
            except Exception as exception: #pylint: disable=broad-except
                logging.exception("Exception: {0}".format(str(exception)))
                return None

        return file_name

    def get_exported_submissions(self, permit_type='applications'):
        """ get submissions in the current csv export """
        ret = {}
        try:
            formio_query = {
                'actionState': 'Export to PTS'
            }
            exported_submission = PermitApplication.get_applications_by_query(
                formio_query,
                submission_endpoint=permit_type)
            # use formio id as the key for the ['data'] object
            for item in exported_submission:
                if 'permitType' in item['data']:
                    item['data']['permitType'] = self.map_permit_type(item['data']['permitType'])
                ret[item['_id']] = item['data']
                ret[item['_id']]['date_created'] = item['created']
        except IOError as err:
            logging.exception("I/O error(%s): %s", err.errno, err.strerror)
        except Exception: #pylint: disable=broad-except
            logging.exception("Unexpected error: %s", format(sys.exc_info()[0]))
        return ret

    def create_tracker_file(self, tracker):
        """ create the tracker spreadsheet """
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

        file_content = ''
        if os.path.isfile(tracker_file):
            try:
                file1 = open(tracker_file, 'rb')
                file_content = file1.read()
                file1.close()
                #clean up tmp file
                os.remove(tracker_file)
            except IOError as err:
                logging.exception("I/O error(%s): %s", err.errno, err.strerror)
            except Exception: #pylint: disable=broad-except
                logging.exception("Unexpected error: %s", format(sys.exc_info()[0]))

        return file_content

    #pylint: disable=no-self-use, too-many-locals, R0915
    def create_email_content(self, file_name, tracker, exported_submissions):
        """ Create summary email for permit techs """
        ret = {}
        try:
            file_handle = open(file_name, 'r', encoding='utf-8-sig')
            content = ''
            # loop through the result file to create the summary table
            for line in file_handle:
                fields = line.split('|')
                #skip header
                if fields[0] == 'FORMIO':
                    continue
                formio_id = fields[0].lower()
                status = fields[2]
                temp_app_num = fields[1]
                error_msg = fields[3]
                if formio_id in exported_submissions:
                    tracker = self.create_tracker_content(
                        exported_submissions,
                        tracker,
                        formio_id,
                        status,
                        temp_app_num,
                        error_msg
                    )
                    content += self.create_content(
                        exported_submissions,
                        formio_id,
                        status,
                        temp_app_num,
                        error_msg
                    )
                    # if successfully loaded into PTS, update submission status
                    #if status == 'Success':
                        #PermitApplication.update_status(formio_id)
                        # send email to applicants with success email template?
                        #self.send_email_to_applicant(status, exported_submissions[formio_id])

            # merge addenda
            addenda = self.merge_addenda_resubmission(tracker, exported_submissions)
            content += addenda['content']
            with open(self.template_file_path + 'summary_email.html', 'r') as file_obj:
                template_content = file_obj.read()
                html_content = template_content.replace("{{ html_content }}", content)

            ret['email_body_content'] = html_content
            ret['tracker_content'] = addenda['tracker']
        except IOError as err:
            logging.exception("I/O error(%s): %s", err.errno, err.strerror)
        except Exception: #pylint: disable=broad-except
            logging.exception("Unexpected error: %s", sys.exc_info()[0])

        return ret

    def merge_addenda_resubmission(self, tracker, exported_submissions):
        """ merge addenda to summary email and tracker """
        #get addenda
        addenda = self.get_exported_submissions('addenda')
        #merge resubmissions
        for _id in exported_submissions:
            if exported_submissions[_id]['permitType'] == 'Resubmission':
                addenda.update({_id: exported_submissions[_id]})
        ret = {}
        status = 'NOT PROCESSED'
        temp_app_num = error_msg = ''
        content = ''
        for formio_id in addenda:
            addenda[formio_id]['permitType'] = addenda[formio_id].get('permitType', 'Addenda')
            tracker = self.create_tracker_content(
                addenda,
                tracker,
                formio_id,
                status,
                temp_app_num,
                error_msg
            )
            content += self.create_content(addenda, formio_id, status, temp_app_num, error_msg)
            # update status so that it doesn't get picked up again
            #PermitApplication.update_status(formio_id)
        ret['tracker'] = tracker
        ret['content'] = content
        return ret

    #pylint: disable=no-self-use, disable=too-many-arguments
    def create_tracker_content(self, exported_submissions, tracker, formio_id, status, temp_app_num, error_msg):
        """ create content for tracker file """
        tracker['formio id'].append(formio_id)
        tracker['status'].append(status)
        tracker['temp_app_num'].append(temp_app_num)
        tracker['error'].append(error_msg)
        tracker['permit_type'].append(exported_submissions[formio_id].get('permitType', ''))
        tracker['project_address'].append(exported_submissions[formio_id].get('projectAddress', ''))
        tracker['block'].append(exported_submissions[formio_id].get('projectAddressBlock', ''))
        tracker['lot'].append(exported_submissions[formio_id].get('projectAddressLot', ''))
        tracker['bb_project_id'].append(exported_submissions[formio_id].get('bluebeamId', ''))
        tracker['applicant_email'].append(exported_submissions[formio_id].get('applicantEmail', ''))
        applicant_name = exported_submissions[formio_id].get('applicantFirstName', '') + ' ' + exported_submissions[formio_id].get('applicantLastName', '')
        tracker['applicant_name'].append(applicant_name)
        tracker['applicant_phone'].append(exported_submissions[formio_id].get('applicantPhoneNumber', ''))
        date_created = exported_submissions[formio_id].get('date_created', '')
        if date_created:
            date_created = datetime.datetime.strptime(date_created, '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%Y/%m/%d %H:%M:%S")
        tracker['date_created'].append(date_created)
        #fill empty tracker columns with empty values
        tracker['staff_assignment'].append('')
        tracker['bpa#'].append('')
        tracker['last_remark_date'].append('')
        tracker['last_remarks'].append('')
        tracker['ppc_release_date'].append('')
        tracker['issued_closed_date'].append('')

        return tracker

    #pylint: disable=no-self-use, disable=too-many-arguments
    def create_content(self, exported_submissions, formio_id, status, temp_app_num, error_msg):
        """ create summary email table cell content"""
        content = ''

        date_created = exported_submissions[formio_id].get('date_created', '')
        if date_created:
            date_created = datetime.datetime.strptime(date_created, '%Y-%m-%dT%H:%M:%S.%fZ').strftime("%Y/%m/%d %H:%M:%S")

        content += '<tr>'
        content += '<td>' + status + '</td>'
        content += '<td>' + temp_app_num + '</td>'
        content += '<td>' + error_msg + '</td>'
        content += '<td>' + exported_submissions[formio_id].get('permitType', '') + '</td>'
        content += '<td>' + date_created + '</td>'
        content += '<td>' + exported_submissions[formio_id].get('bluebeamId', '') + '</td>'
        content += '<td>' + formio_id + '</td>'
        content += '<td>' + exported_submissions[formio_id].get('applicantEmail', '') + '</td>'
        content += '<td>' + exported_submissions[formio_id].get('applicantFirstName', '')
        content += ' ' + exported_submissions[formio_id].get('applicantLastName', '') + '</td>'
        content += '<td>' + exported_submissions[formio_id].get('projectAddress', '') + '</td>'
        content += '<td>' + exported_submissions[formio_id].get('projectAddressBlock', '') + '</td>'
        content += '<td>' + exported_submissions[formio_id].get('projectAddressLot', '') + '</td>'
        content += '<td>' + self.get_uploaded_file_names(exported_submissions[formio_id]) + '</td>'
        content += '</tr>'

        return content

    def get_uploaded_file_names(self, exported_submission):
        """ get all upload file names """
        aws_file_url = os.environ['AWS_FILE_URL']
        ds_file_url = os.environ['DS_FILE_URL']
        if exported_submission['permitType'] == "existingBuilding" or exported_submission['permitType'] == "permitRevision":
            uploads = exported_submission.get('optionalUploads', None)
        else:
            uploads = exported_submission.get('requiredUploads', None)

        _uploads = ''
        if uploads:
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

    def merge_failed_bluebeam(self, file_name):
        """ merge failed bluebeam submissions into result file"""
        try:
            result_file = open(file_name, 'r')
            result_file_content = result_file.read()
            result_file.close()

            bb_failed_file = open(self.data_file_path + 'bb_failed_records.txt', 'r')
            bb_failed_file_content = bb_failed_file.read()
            bb_failed_file.close()

            data = result_file_content + '\n' + bb_failed_file_content
            with open(file_name, 'w') as file_pointer:
                file_pointer.write(data)
                file_pointer.close()
        except IOError as err:
            logging.exception("I/O error(%s): %s", err.errno, err.strerror)
        except Exception: #pylint: disable=broad-except
            logging.exception("Unexpected error: %s", format(sys.exc_info()[0]))

    def map_permit_type(self, permit_type):
        """ map machine name to human readable name """
        permit_map = {
            'newConstruction': 'Form 1/2',
            'existingBuilding': 'Form 3/8',
            'permitRevision': 'Revision',
            'existingPermitApplication': 'Resubmission'
        }
        return permit_map[permit_type] if permit_type in permit_map else permit_type

    def send_email_to_applicant(self, status, exported_submission):
        """ sends an email to applicant after PTS integration """
        if 'applicantEmail' in exported_submission:
            applicant_email = exported_submission.get('applicantEmail', '')
            subject = 'Permit applicatioon successful submission'
            recipients = {
                'from_email': sendgrid.helpers.mail.Email(applicant_email),
                'to_emails': os.environ.get('SUMMARY_EMAIL_TO'),
                'cc_emails': os.environ.get('SUMMARY_EMAIL_CC', None),
                'bcc_emails': os.environ.get('SUMMARY_EMAIL_BCC', None)
            }
            email_body = ''
            Export().email(recipients, subject, email_body)
