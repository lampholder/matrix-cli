import json
import urllib
import logging
import requests
from matrix_client.client import MatrixClient

class MatrixStreamLogger(logging.StreamHandler):

    def __init__(self, matrix_client, log_room):
        super().__init__()
        self._client = matrix_client
        self._log_room = self._client.join_room(log_room)

    def emit(self, record):
        self._log_room.send_html('<pre><code>%s</code></pre>' % self.format(record))

class MatrixAdminAPI:

    @staticmethod
    def delete_room_listing(access_token, room_id,
                                   homeserver='https://matrix.org'):
        escaped_room_id = urllib.parse.quote_plus(room_id)
        uri = '%s/_matrix/client/r0/directory/list/room/%s' % (
            homeserver, escaped_room_id
        )

        headers = {
            'Authorization': 'Bearer %s' % access_token
        }
        return requests.delete(uri, headers=headers)

    @staticmethod
    def get_alias(access_token, alias, homeserver='https://matrix.org'):
        escaped_alias = urllib.parse.quote_plus(alias)
        uri = '%s/_matrix/client/r0/directory/room/%s' % (homeserver, escaped_alias)
        params = {
            'access_token': access_token
        }
        return requests.get(uri)

    @staticmethod
    def delete_alias(access_token, alias, homeserver='https://matrix.org'):
        escaped_alias = urllib.parse.quote_plus(alias)
        uri = '%s/_matrix/client/r0/directory/room/%s' % (homeserver, escaped_alias)
        params = {
            'access_token': access_token
        }
        return requests.delete(uri, params=params)

    @staticmethod
    def put_alias(access_token, alias, room_id, homeserver='https://matrix.org'):
        escaped_alias = urllib.parse.quote_plus(alias)
        uri = '%s/_matrix/client/r0/directory/room/%s' % (homeserver, escaped_alias)
        params = {
            'access_token': access_token
        }
        data = {
            'room_id': room_id
        }
        return requests.put(uri, data=json.dumps(data), params=params)

    @staticmethod
    def shutdown_room(access_token, user_id, room_id, message,
                      new_room_name='Room unavailable',
                      homeserver='https://matrix.org'):
        escaped_room_id = urllib.parse.quote_plus(room_id)
        uri = '%s/_matrix/client/r0/admin/shutdown_room/%s' % (homeserver, 
                                                               escaped_room_id)
        data = {
            'new_room_user_id': user_id,
            'message': message,
            'room_name': new_room_name
        }
        params = {
            'access_token': access_token
        }
        return requests.post(uri, data=json.dumps(data), params=params)

    @staticmethod
    def quarantine_media(access_token, room_id, homeserver='https://matrix.org'):
        escaped_room_id = urllib.parse.quote_plus(room_id)
        uri = '%s/_matrix/client/r0/admin/quarantine_media/%s' % (homeserver,
                                                                  escaped_room_id)
        params = {
            'access_token': access_token
        }
        return requests.post(uri, params=params)

    @staticmethod
    def deactivate_user(access_token, user_id, homeserver='https://matrix.org'):
        escaped_user_id = urllib.parse.quote_plus(user_id)
        uri = '%s/_matrix/client/r0/admin/deactivate/%s' % (homeserver,
                                                            escaped_user_id)
        headers = {
            'Authorization': 'Bearer %s' % access_token
        }
        return requests.post(uri, headers=headers)


class MatrixAdmin:

    def __init__(self, username, password, homeserver='https://matrix.org'):
        self._homeserver = homeserver
        self._client = MatrixClient(homeserver)
        self._client.login(username,
                           password,
                           sync=False)

    def deactivate_user(self, user_id, reason):
        access_token = self._client.token

        deactivate = MatrixAdminAPI.deactivate_user(access_token, user_id)
        logging.info('Deactivating account \'%s\': %s\nReason: %s' % (
            user_id,
            'SUCCESS' if deactivate.status_code == 200 else 'FAILURE',
            reason
        ))
        if deactivate.status_code != 200:
            logging.error(deactivate.text)

    def park_alias(self, alias, reason, parking_room_id='!GrRRLYVADFUBjqnEwX:matrix.org'):
        access_token = self._client.token

        room_id = MatrixAdminAPI.get_alias(access_token, alias).json().get('room_id')
        delete_alias = MatrixAdminAPI.delete_alias(access_token, alias)
        logging.info('Removing alias \'%s\' from \'%s\': %s\nReason: %s' % (
            alias,
            room_id,
            'SUCCESS' if delete_alias.status_code == 200 else 'FAILURE',
            reason
        ))
        if delete_alias.status_code != 200:
            logging.error(delete_alias.text)

        create_alias = MatrixAdminAPI.put_alias(access_token, alias, parking_room_id)
        logging.info('Parking alias \'%s\' (parking spot: \'%s\'): %s\nReason: %s' % (
            alias,
            parking_room_id,
            'SUCCESS' if create_alias.status_code == 200 else 'FAILURE',
            reason
        ))
        if create_alias.status_code != 200:
            logging.error(create_alias.text)

    def assign_alias(self, room_id, alias, reason):
        access_token = self._client.token

        assign_alias = MatrixAdminAPI.put_alias(access_token,
                                                alias,
                                                room_id)
        logging.info('Assigning alias \'%s\' to \'%s\': %s\nReason: %s' % (
            alias,
            room_id,
            'SUCCESS' if assign_alias.status_code == 200 else 'FAILURE',
            reason
        ))
        if assign_alias.status_code != 200:
            logging.error(assign_alias.text)

    def delete_alias(self, alias, reason):
        access_token = self._client.token

        room_id = self.resolve_alias(alias)

        delete_alias = MatrixAdminAPI.delete_alias(access_token, alias)
        logging.info('Deleting alias \'%s\' from \'%s\': %s\nReason: %s' % (
            alias,
            room_id,
            'SUCCESS' if delete_alias.status_code == 200 else 'FAILURE',
            reason
        ))
        if delete_alias.status_code != 200:
            logging.error(delete_alias.text)

    def resolve_alias(self, alias):
        access_token = self._client.token

        return MatrixAdminAPI.get_alias(access_token, alias).json().get('room_id')

    def delist_room(self, room_id, reason):
        access_token = self._client.token

        delist_room = MatrixAdminAPI.delete_room_listing(access_token, room_id)
        logging.info('Delisting room \'%s\': %s\nReason: %s' % (
            room_id,
            'SUCCESS' if delist_room.status_code == 200 else 'FAILURE',
            reason
        ))
        if delist_room.status_code != 200:
            logging.error(delist_room.text)

    def shutdown_room_and_quarantine_media(self, room_id, reason,
                                           message=None,
                                           new_room_name='Room unavailable'):
        if message is None:
            message = ('This room has been removed from the matrix.org ' +
                       'homeserver due to violating the terms of use.')

        access_token = self._client.token
        user_id = self._client.user_id

        shutdown = MatrixAdminAPI.shutdown_room(access_token, user_id, room_id,
                                                message, new_room_name)
        log_string = ('Shutting down room \'%s\' ' +
                '(new room name \'%s\'; message: \'%s\'): %s\nReason: %s')
        logging.info(log_string % (
            room_id,
            new_room_name,
            message,
            'SUCCESS' if shutdown.status_code == 200 else 'FAILURE',
            reason
        ))
        if shutdown.status_code != 200:
            logging.error(shutdown.text)

        quarantine = MatrixAdminAPI.quarantine_media(access_token, room_id)
        logging.info('Quarantining media in \'%s\'; quarantining %s items: %s\nReason: %s' % (
            room_id,
            quarantine.json().get('num_quarantined', 0),
            'SUCCESS' if quarantine.status_code == 200 else 'FAILURE',
            reason
        ))
        if quarantine.status_code != 200:
            logging.error(quarantine.text)



