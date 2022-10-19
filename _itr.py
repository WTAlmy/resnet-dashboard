"""Get tickets from ServiceNow."""
from datetime import datetime
import json
import operator

import requests

from auth.auth import user, password

# url for getting incidents (tickets)
url = "https://ucsc.service-now.com/api/now/table/incident?"
# url for journals (comments/tech notes on tickets)
journal_url = "https://ucsc.service-now.com/api/now/table/sys_journal_field?"
# required headers
headers = {"Content-Type": "application/json", "Accept": "application/json"}

# various filters for ITR
filters = {'all': ('sysparm_query=assignment_group=55e7ddcd0a0a3d280047abc06e'
                   'd844c8^incident_state=1^ORincident_state=2^ORincident_sta'
                   'te=3^ORincident_state=4^ORincident_state=5^incident_state'
                   '=6^ORincident_state!=7'),
           'client_updated': ('sysparm_query=assignment_group=55e7ddcd0a0'
                              'a3d280047abc06ed844c8^incident_state=1^ORi'
                              'ncident_state=2^ORincident_state=3^ORincid'
                              'ent_state=4^ORincident_state=5^incident_st'
                              'ate!=6^ORincident_state!=7^sys_updated_byS'
                              'AMEAScaller_id.user_name'),
           'unassigned': ('sysparm_query=active=true^assignment_group='
                          '55e7ddcd0a0a3d280047abc06ed844c8^assigned_t'
                          'oISEMPTY'),
            'stale': ('sysparm_query=assignment_group=55e7ddcd0a0a3d280047abc06ed844c8^incident_state=1^ORincident_state=2^ORincident_state=4^ORincident_state=5^ORincident_state=3^incident_state!=6^ORincident_state!=7^sys_updated_on<javascript:gs.daysAgo(3)^caller_id!=67c139b309641440fa07e749fee81bd7^caller_id!=c5c2b5f309641440fa07e749fee81b40')}


def get_tickets(filter_str):
    """Return all the tickets from ITR given a filter."""
    filter_url = url + filter_str
    resp = requests.get(filter_url, auth=(user, password), headers=headers)
    tickets = None
    if(resp.status_code != 200):  # response is not OK, throw error
        raise ConnectionError('Problem with get_tickets')
    else:
        # filter tickets to just be the incident number and title as a string
        # {big scary json with lots of info} -> ['INC3029103 Computer BROKE']
        tickets = []
        for elem in resp.json()['result']:
            tickets.append('{} {}'.format(elem['number'],
                                          elem['short_description']))
    return tickets


def get_tickets_raw(filter_str):
    """Return all the tickets from ITR given a filter, as raw JSON."""
    filter_url = url + filter_str
    resp = requests.get(filter_url, auth=(user, password), headers=headers)
    if(resp.status_code != 200):  # response is not OK, throw error
        raise ConnectionError('Problem with get_tickets_raw')
    return resp.json()['result']


def get_tickets_meta():
  """Find oldest tickets in queue with other useful info"""
  tickets = get_tickets_raw(filters['all'])

  oldest_cr = None
  for ticket in tickets:
    dt_obj = datetime.strptime(ticket['sys_created_on'], '%Y-%m-%d %H:%M:%S')
    if oldest_cr is None:
      oldest_cr = dt_obj
    else:
      oldest_cr = min(oldest_cr, dt_obj)

  oldest_up = None
  for ticket in tickets:
    dt_obj = datetime.strptime(ticket['sys_updated_on'], '%Y-%m-%d %H:%M:%S')
    if oldest_up is None:
      oldest_up = dt_obj
    else:
      oldest_up = min(oldest_up, dt_obj)

  now = datetime.now()
  delta_cr = (now-oldest_cr).days + 1
  delta_up = (now-oldest_up).days + 1

  result = dict()
  result['oldest-cr-date'] = str(oldest_cr);
  result['oldest-up-date'] = str(oldest_up);
  result['oldest-cr-rel'] = str(delta_cr);
  result['oldest-up-rel'] = str(delta_up);
  return result


def high_priority():
    """Return all the high priority tickets in the queue."""
    unassigned = get_tickets(filters['unassigned'])
    unassigned = [(ticket, 0) for ticket in unassigned]
    client_updated = get_tickets(filters['client_updated'])
    client_updated = [(ticket, 1) for ticket in client_updated]
    stale = get_tickets(filters['stale'])
    stale = [(ticket, 2) for ticket in stale]

    all_tickets = list(set(unassigned + client_updated + stale))
    ticket_no_dupes = {}
    for ticket in all_tickets:
      if ticket[0] in ticket_no_dupes:
        if ticket[1] < ticket_no_dupes[ticket[0]]:
          ticket_no_dupes[ticket[0]] = ticket[1]
      else: 
        ticket_no_dupes[ticket[0]] = ticket[1]

    tickets_out = dict()
    tickets_out['tickets'] = []
    for key, val in sorted(ticket_no_dupes.items(), key=lambda x: x[1]):
        tickets_out['tickets'].append({'ticket_name': str(key),
                                       'priority': str(val)})
    return tickets_out


if __name__ == "__main__":
  print(get_tickets_meta())
