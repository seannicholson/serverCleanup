###############################################################################
# Import statements
# This script requires the following Python modules
# json, base64, requests, datetime, sys, argparse, pytz, iso8601, os, os.path
# use PIP import for these if you are encountering errors for pytz, requests,
# iso8601
#   > pip install requests, pytz, iso8601
#

import json, base64, requests, datetime, sys, argparse, pytz, iso8601
import os, os.path

from config import apiurl, move_deactivate_num_days, delete_deactivate_num_days, moveToGroupName, api_keys_path

###############################################################################

###############################################################################
# Define Methods

# Calls get_access_token and takes returned token value to Create
# request headers
def get_headers():
    # Create headers
    reply = get_access_token(api_request_url, "/oauth/access_token?grant_type=client_credentials",
                             {"Authorization": user_credential_b64})
    reply_clean = reply.encode('utf-8')
    headers = {"Content-type": "application/json", "Authorization": "Bearer " + reply_clean}
    #print headers
    return headers

# Request Bearer token and return access_token
def get_access_token(url, query_string, headers):
    reply = requests.post(url + query_string, headers=headers)
    return reply.json()["access_token"]

# Uses requests PUT command to send json to move group via API call
def move_group(host_id,group_id):
    data = { "server": {"group_id": group_id}}
    status_code = str("404")
    retry_loop_counter = 0
    moveurl = apiurl + "/v1/servers/" + host_id
    #print ("URL: %s") % moveurl
    #print ("Request Body: %s" % data)

    # Loop to attempt server move PUT request
    # will retry 4 times to move server if status_code not 204
    while (retry_loop_counter < 3):
        reply = requests.put( moveurl, data=json.dumps(data), headers=headers)
        status_code = str(reply.status_code)
        #print ("Result of group move: %s" % status_code)
        #Check for successful PUT, status_code == 204
        if status_code == "204":
            # Arbitrary number to exit loop
            retry_loop_counter = 5
            return True
        #Check for correct permissions on API Key (RW / Administrator)
        elif status_code == "403":
            print "API Key does not have correct permissions to perform operation"
            return False
        #Check bearer token expired, if expired (401) request new bearer token
        elif status_code == "401":
            headers = get_headers()
            retry_loop_counter += 1
        # After three retries return False
        elif retry_loop_counter == 2:
            script_errors += 1
            return False
        else:
            print "Failed to move server...Retry attempt %d" % retry_loop_counter
            retry_loop_counter += 1




# Get groupID from group name specified
def get_group_id(groupName):
    status_code = str("404")
    retry_loop_counter = 0
    groupID_found = 0
    groupurl = api_request_url + "/v1/groups"
    while (retry_loop_counter < 4):
        reply = requests.request("GET", groupurl, data=None, headers=headers)
        # Check for success status code for returning group list
        status_code = str(reply.status_code)
        if status_code == "200":
            retry_loop_counter = 5

        # check for expired bearer token, if expired (401) request new bearer
        # token then try again
        elif status_code == "401":
            print "Bearer token expired....requesting new token"
            get_headers()
            retry_loop_counter +=1
        #Check for correct permissions on API Key in scope (RW/RO)
        elif status_code == "403":
            print "API Key does not have correct scope to perform operation"
            return False
        # Anything but success or expired bearer token, then retry
        elif retry_loop_counter == 3:
            print "Request to match group name failed"
            print "Please check group name or API Key scope"
            print "Exiting..."
            return False

        else:
            print "Error retrieving group list...Retrying %d" % retry_loop_counter
            retry_loop_counter +=1
    # Parse list of groups looking for groupName match
    for group in reply.json()["groups"]:
        if group['name'] == groupName:
            newgroupID = group['id']
            groupID_found += 1

    # Sanity checks for group name matched only once
    if groupID_found == 1:
        return newgroupID
    elif groupID_found > 1:
        print "More than 1 group matched group name"
        print "Please specify unique group name"
        print "Exiting..."
        return False
    else:
        print "Group name match not found"
        print "Please check group name or API Key scope"
        print "Exiting..."
        script_errors += 1
        return False


def get_deactivated_server_list():
    status_code = str("404")
    retry_loop_counter = 0
    deactivatedServersURL = api_request_url + "/v1/servers?state=deactivated"
    while (retry_loop_counter < 3):

        reply = requests.request("GET", deactivatedServersURL, data=None, headers=headers)
        status_code = str(reply.status_code)
        # Check for success status code for returning deactivated server list
        if status_code == "200":
            return reply

        # check for expired bearer token, if expired (401) request new bearer
        # token then try again
        elif status_code == "401":
            get_headers()
            retry_loop_counter +=1
        #Check for correct permissions on API Key in scope (RW/RO)
        elif status_code == "403":
            print "API Key does not have correct scope to perform operation"
            return False
        # After third retry return False
        elif retry_loop_counter == 2:
            script_errors +=1
            return False
        # Anything but success or expired bearer token, then retry
        else:
            print "Error retrieving deactivated server list...Retrying %d" % retry_loop_counter
            retry_loop_counter +=1


def get_servers_to_delete_list():
    status_code = str("404")
    retry_loop_counter = 0
    deactivatedServersURL = api_request_url + "/v1/servers?state=deactivated&group_name=" + moveToGroupName
    while (retry_loop_counter < 5):
        reply = requests.request("GET", deactivatedServersURL, data=None, headers=headers)
        status_code = str(reply.status_code)
        # Check for success status code for returning deactivated server list
        if status_code == "200":
            return reply

        # check for expired bearer token, if expired (401) request new bearer
        # token then try again
        elif status_code == "401":
            get_headers()
            retry_loop_counter +=1
        #Check for correct permissions on API Key in scope (RW/RO)
        elif status_code == "403":
            print "API Key does not have correct scope to perform operation"
            return False
        # After third retry return False
        elif retry_loop_counter == 4:
            return False

        # Anything but success or expired bearer token, then retry
        else:
            print "Error retrieving deactivated server to delete list...Retrying %d" % retry_loop_counter
            retry_loop_counter +=1


# Uses requests PUT command to send json to move group via API call
def delete_server(host_id):
    status_code = str("404")
    retry_loop_counter = 0
    deleteurl = apiurl + "/v1/servers/" + host_id
    #print ("URL: %s") % moveurl
    #print ("Request Body: %s" % data)

    # Loop to attempt server move PUT request
    # will retry 4 times to move server if status_code not 204
    while (retry_loop_counter < 4):
        reply = requests.delete( deleteurl, headers=headers)
        status_code = str(reply.status_code)
        #print ("Result of group move: %s" % status_code)
        retry_loop_counter += 1
        if status_code == "204":
            # Arbitrary number to exit loop
            retry_loop_counter = 5
            return True
        # check for expired bearer token, if expired (401) request new bearer
        # token then try again
        elif status_code == "401":
            get_headers()
            retry_loop_counter +=1
        #Check for correct permissions on API Key (RW / Administrator)
        elif status_code == "403":
            print "API Key does not have correct permissions to perform operation"
            return False
        # After third retry return False
        elif retry_loop_counter == 3:
            print "Retry attempts exceeded...retries attempted %d" % retry_loop_counter
            return False
        else:
            print "Failed to delete server...Retry attempt %d" % retry_loop_counter
            retry_loop_counter +=1
            return False

def move_deactivated_servers():
    global newgroupID
    servers_moved = 0
    servers_ignored = 0
    servers_previously_moved = 0
    script_errors = 0
    # Check for defined groupID to move servers to
    #print "Move to Group ID: %s" % moveToGroupID
    #newgroupID = check_group_id()
    newgroupID = str(get_group_id(moveToGroupName))
    # How many days should a server be offline before being moved?
    #move_deactivate_num_days = move_deactivate_num_days

    # Get list of deactivated servers
    reply = get_deactivated_server_list()

    # Check for valid list of returned deactivated servers
    if (reply):
        # Loop through deactivated servers list
        # and move if move criteria met
        for server in reply.json()["servers"]:
            server_id = server['id']
            server_hostname = server['hostname']

            # Create aware datetime object for last time seen
            lastseen = iso8601.parse_date(server['last_state_change'])

            # Create aware datetime object for current time
            utc = pytz.timezone('UTC')
            utcnow = datetime.datetime.utcnow()
            utcnow_aware = utc.fromutc(utcnow)

            # Calculate time diff in days
            # After 1 day, last_state_change rounds off to days
            time_diff = utcnow_aware - lastseen
            diff_days = int(time_diff.days)

            # Don't move a server that's already in the desired deactivated group
            if server['group_name'] == moveToGroupName:
                print "Server %s already moved -- ignoring." % server_hostname
                servers_previously_moved += 1

            # If server older than move_deactivate_num_days days, move to newgroupID
            elif (diff_days > move_deactivate_num_days and server_id and newgroupID):
                #print server_id
                #print server_hostname
                #print newgroupID
                # Move Server to Deactivated group
                data  = move_group(server['id'],newgroupID)
                if data:
                    print "Server %s moved successfully" % server_hostname
                    servers_moved += 1
            else:
                print "Unable to move server."
                if not server_id:
                    print "Server: %s (id %s) does not exist.\n" % (server_hostname, server_id)
                elif diff_days <= move_deactivate_num_days:
                    print "Server %s has been offline for %s days.\n" % (server_hostname, diff_days)
                    servers_ignored += 1
                elif not newgroupID:
                    print "Request Error retrieving move to group ID"
                    script_errors += 1

        #Print summary of script actions
        print "\n******* Move Server Summary API Key #%d *******" % api_key_loop_counter
        if (api_key_description):
            print "API Key Descritpion: %s" % api_key_description
        if script_errors > 0:
            print "Script Errors: %d" % script_errors

        print "Servers moved: %d" % servers_moved
        print "Servers ignored, less than specified days deactivated: %d " % servers_ignored
        print "Servers already in deactivated group: %d" % servers_previously_moved
        current_date_time = datetime.datetime.utcnow()
        print "Script completed: %s UTC" % current_date_time
        print "**********************************************"
        return


    else:
        script_errors += 1
        print "\n****** Move Server Summary API Key #%d ********" % api_key_loop_counter
        if (api_key_description):
            print "API Key Descritpion: %s" % api_key_description
        print "Unable to retrieve Deactivated Servers List"
        print "Script completed: %s UTC" % current_date_time
        print "**********************************************"
        return
# Delete servers method
# Will delete servers in specified group (config.py -> moveToGroupName='')
def delete_deactivated_servers():
    servers_deleted = 0
    servers_ignored = 0
    script_errors = 0
    # How many days should a server be offline before being deleted?
    #delete_deactivate_num_days = delete_deactivate_num_days

    # Get list of deactivated servers
    reply = get_servers_to_delete_list()
    if (reply):
        # Loop through deactivated servers list
        # and delete if move criteria met
        for server in reply.json()["servers"]:
            server_id = server['id']
            server_hostname = server['hostname']


            # Create aware datetime object for last time seen
            lastseen = iso8601.parse_date(server['last_state_change'])

            # Create aware datetime object for current time
            utc = pytz.timezone('UTC')
            utcnow = datetime.datetime.utcnow()
            utcnow_aware = utc.fromutc(utcnow)

            # Calculate time diff in days
            # After 1 day, last_state_change rounds off to days
            time_diff = utcnow_aware - lastseen
            diff_days = int(time_diff.days)

            # Delete a server if in the desired deactivated server group and if
            # diff_days is greater than delete_deactivate_num_days
            if (server['group_name'] == moveToGroupName) and (diff_days > delete_deactivate_num_days) and server_id:
                print "Deleting server %s" % server_hostname
                data  = delete_server(server['id'])
                if data:
                    print "Server %s deleted successfully." % server_hostname
                    servers_deleted += 1
                else:
                    script_errors += 1
            else:
                print "Unable to delete server: %s" % server['hostname']
                if not server_id:
                    print "Server: %s (id %s) does not exist.\n" % (server_hostname, server_id)
                    script_errors += 1
                elif diff_days <= delete_deactivate_num_days:
                    print "Server %s not deleted, deactivated only for %s days.\n" % (server_hostname, diff_days)
                    servers_ignored += 1

        #Print summary of script actions
        print "\n****** Delete Server Summary API Key #%d ******" % api_key_loop_counter
        if (api_key_description):
            print "API Key Descritpion: %s" % api_key_description
        if script_errors > 0:
            print "Script Errors: %d" % script_errors
        print "Servers deleted: %d" % servers_deleted
        print "Servers ignored, less than specified days deactivated: %d " % servers_ignored
        current_date_time = datetime.datetime.utcnow()
        print "Script completed: %s UTC" % current_date_time
        print "**********************************************"


    else:
        script_errors += 1
        print "\n****** Delete Server Summary API Key #%d ******" % api_key_loop_counter
        if (api_key_description):
            print "API Key Descritpion: %s" % api_key_description
        print "Unable to retrieve Deactivated Servers List to delete"
        print "Script completed: %s UTC" % current_date_time
        print "**********************************************"
        return
###############################################################################
# end of function definitions, begin inline code



###############################################################################
# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--moveservers", help="Move all deactivated servers to group specified in config.py (moveToGroupName) file that have been deactivated for more than days specified in move_deactivate_num_days", action="store_true")
parser.add_argument("--deleteservers", help="Delete all deactivated servers in group specified in config.py (moveToGroupName) file that have been deactivated for more than days specified in delete_deactivate_num_days", action="store_true")
args = parser.parse_args()

###############################################################################
# Variables
# Please edit these values in the config.auth.  You can find these information
# from HALO "[Site Administration] -> [API Keys]" page

# Set in config.py
api_request_url = apiurl
move_deactivate_num_days = move_deactivate_num_days
delete_deactivate_num_days = delete_deactivate_num_days
moveToGroupName = moveToGroupName
PATH = api_keys_path

# Set variable types
user_credential_b64 = ''
headers = {}
api_key_description = ''

# Set counters and sanity checkers
script_errors = 0
script_actions = 0
api_key_loop_counter = 0
###############################################################################

###############################################################################
# Validate script arguments are set and config.py variable values set

# Check for script arguments
if args.moveservers:
    script_actions += 1
if args.deleteservers:
    script_actions +=1

# If no arguments passed then exit with message
if script_actions == 0:
    print "No arguments passed to script, please specify script actions"
    print "See README.md or run serverCleanup.py --help"
    print "Nothing to do...Exiting...."
    sys.exit(0)

# Check moveToGroupName set in config.py
if not (moveToGroupName):
    print "NO GROUP TO MOVE TO CONFIGRED!"
    print "Please configure destination group in config.py"
    print "Exiting..."
    sys.exit(1)

###############################################################################

#---MAIN---------------------------------------------------------------------
# Reads in api_keys.txt file and loops through all available Keys
# and runs get_headers and methods passed from CLI arguments for each
# provided base64 keypair


# Check api_keys.txt exists and is readable
if os.path.isfile(PATH) and os.access(PATH, os.R_OK):
    print "api_keys.txt file exists and is readable"
    # Open file and read lines into list
    with open('api_keys.txt') as f:
        content = f.readlines()
        f.close()
        # Loop through list of API Keys and run CLI argument actions
        for apiKey in content:
            #print apiKey
            user_credential_b64 = "Basic " + base64.b64encode(apiKey[:41])
            api_key_description = apiKey[42:]
            #print user_credential_b64
            api_key_loop_counter += 1
            # Get headers for API calls
            headers=get_headers()
            if args.moveservers:
                move_deactivated_servers()
            if args.deleteservers:
                delete_deactivated_servers()
else:
    print "api_keys.txt file either file is missing or is not readable"
