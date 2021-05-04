from datetime import datetime
from datetime import timedelta
from retrying import retry
import pysnow.exceptions

from lib.actions import BaseAction


class QuarantineServerRecord(BaseAction):
    @retry(wait_fixed=15000, stop_max_attempt_number=5)
    def run(self, table, name, email, days, dev=False):

        if self.config["environment"] != "lab" and dev:
            return (False, "ERROR: Dev can only be enabled in the Lab environment")

        default_payload = None

        try:
            self.get_client_with_default_payload(default_payload, dev)
        except Exception as err:
            return (False, err)

        connect = self.client
        query = {"fqdn": name}

        try:
            request = connect.query(table=table, query=query)
        except:
            return (False, "ERROR: Failed while querying ServiceNow for records for %s" % name)

        response = request.get_multiple()  # pylint: disable=no-member

        records = []
        try:
            for each_item in list(response):
                records.append(each_item)
        except pysnow.exceptions.NoResults:
            return (True, "Servicenow record for %s does not exist" % name)

        requester = email.split("@")[0]
        if len(records) > 0:
            for record in records:
                sys_id = record["sys_id"]
                if record["hardware_status"] != "retired":
                    query = {"sys_id": sys_id}
                    try:
                        req = connect.query(table=table, query=query)
                        decom_time_start = (datetime.now()).strftime('%m-%d-%Y %-I:%M:%S %p')
                        decom_time_end = (datetime.now() + timedelta(days=days)).strftime('%m-%d-%Y %-I:%M:%S %p')
                        payload = {"hardware_substatus": "In Quarantine",
                                   "u_quarantine_start": decom_time_start,
                                   "u_quarantine_end": decom_time_end,
                                   "u_lifecycle_comments": "Set to be in quarantine by %s (userID: %s email: %s) on %s and quarantine ends on %s" % (
                                       requester, requester, email, decom_time_start, decom_time_end),
                                   "short_description": "Set to be in quarantine by %s (userID: %s email: %s) on %s and quarantine ends on %s" % (
                                       requester, requester, email, decom_time_start, decom_time_end)}
                        req.update(payload)
                    except Exception as e:
                        return False, "ERROR: Failed to delete record with exception:\n%s" % e.message
                else:
                    print()
                    "%s status already set to retired" % sys_id
        else:
            return True, "No records found for %s" % name
