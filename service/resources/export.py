"""Welcome export module"""
import os
import json
import datetime
import base64
import logging
import re
import pytz
import falcon
import jsend
import sendgrid
import sentry_sdk
from ..modules.permit_applications import PermitApplication
from ..transforms.export_submissions import ExportSubmissionsTransform

ERROR_EXPORT_GENERIC = "Bad Request"
ERROR_EXPORT_401 = "Unauthorized"

class Export():
    """Export class"""
    def on_get(self, req, resp):
        #pylint: disable=no-self-use,too-many-locals
        """
        on get request
        return export message and response if successful
        """
        try:
            if req.params['token'] != os.environ.get('EXPORT_TOKEN') and req.params['token'] != os.environ.get('ACCESS_KEY'):
                raise ValueError(ERROR_EXPORT_401)

            timezone = pytz.timezone('America/Los_Angeles')

            yesterday = datetime.datetime.now(timezone) - datetime.timedelta(days=1)
            start_datetime_obj = datetime.datetime.combine(
                yesterday, datetime.datetime.min.time())


            # subject name
            subject_name = "Export"
            if 'name' in req.params:
                subject_name = req.params['name'] + ' ' + subject_name

            formio_query = {
                'actionState': 'Export to PTS'
            }

            with sentry_sdk.configure_scope() as scope:
                scope.set_extra('formio_query', formio_query)

            responses = PermitApplication.get_applications_by_query(formio_query)
            
            file1 = open('responses.txt', 'w')
            file1.write(json.dumps(responses))
            file1.close()

            send_email = bool(req.params['send_email']) if 'send_email' in req.params else False
            sftp_upload = bool(req.params['sftp_upload']) if 'sftp_upload' in req.params else False
            submissions_csv = None
            sep = ','
            if len(responses) > 0:
                if sftp_upload:
                    sep = '|'
                submissions_csv = ExportSubmissionsTransform().transform(responses, sep)
            
            file2 = open('submission.txt', 'w')
            file2.write(submissions_csv)
            file2.close()
            
            msg = subject_name
            msg += " with export to PTS status, "
            msg += str(len(responses)) + " Submissions"

            file_name = re.sub("[^0-9a-zA-Z-_]+", "-", subject_name)
            file_name += "-"+str(start_datetime_obj.date())+".csv"

            if len(responses) > 0 and send_email:
                subject = subject_name+" "+str(start_datetime_obj.date())

                self.email(
                    subject,
                    content=msg,
                    file_name=file_name,
                    file_content=submissions_csv)

            resp.body = json.dumps(jsend.success({'message': msg, 'responses':len(responses)}))
            resp.status = falcon.HTTP_200

            sentry_sdk.capture_message('PTS Dispatch Export', 'info')

        #pylint: disable=broad-except
        except Exception as exception:
            logging.exception('Export.on_get Exception')
            resp.status = falcon.HTTP_500

            msg_error = ERROR_EXPORT_GENERIC
            if exception.__class__.__name__ == 'ValueError':
                msg_error = "{0}".format(exception)

            resp.body = json.dumps(jsend.error(msg_error))

    def email(self, subject, content="Hi", file_name=None, file_content=None):
        """ Email CSV """
        #pylint: disable=too-many-locals

        with sentry_sdk.configure_scope() as scope:
            scope.set_extra('email.subject', subject)

        from_email = sendgrid.helpers.mail.Email(os.environ.get('EXPORT_EMAIL_FROM'))
        to_emails = os.environ.get('EXPORT_EMAIL_TO')
        cc_emails = os.environ.get('EXPORT_EMAIL_CC', None)
        bcc_emails = os.environ.get('EXPORT_EMAIL_BCC', None)

        content = sendgrid.helpers.mail.Content("text/plain", content)

        mail = sendgrid.helpers.mail.Mail(
            from_email=from_email,
            subject=subject,
            plain_text_content=content)

        personalization = sendgrid.helpers.mail.Personalization()

        for _idx, val in enumerate(to_emails.split(',')):
            personalization.add_to(sendgrid.helpers.mail.Email(val))

        if cc_emails:
            for _idx, val in enumerate(cc_emails.split(',')):
                personalization.add_cc(sendgrid.helpers.mail.Email(val))
        if bcc_emails:
            for _idx, val in enumerate(bcc_emails.split(',')):
                personalization.add_bcc(sendgrid.helpers.mail.Email(val))

        mail.add_personalization(personalization)

        if file_content:
            encoded = base64.b64encode(file_content.encode("utf-8")).decode()
            attachment = sendgrid.helpers.mail.Attachment()
            attachment.file_content = sendgrid.helpers.mail.FileContent(encoded)
            attachment.file_type = sendgrid.helpers.mail.FileType('text/csv')
            attachment.file_name = sendgrid.helpers.mail.FileName(file_name)
            attachment.disposition = sendgrid.helpers.mail.Disposition('attachment')
            attachment.content_id = sendgrid.helpers.mail.ContentId(file_name+' Content ID')
            mail.attachment = attachment

        response = self.send_email(mail.get())
        print(response.status_code)
        print(response.body)
        print(response.headers)

    @staticmethod
    def send_email(data):
        """
        Send email via sendgrid
        """
        sg_api = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        return sg_api.client.mail.send.post(request_body=data)
