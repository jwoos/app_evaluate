import logging

import pymysql
from flask import request
from flask.json import jsonify
from flask.views import MethodView

from src.db import connection
from src import errors, auth


logger = logging.getLogger(__name__)


class EvaluationView(MethodView):
    def get(self, evaluation_id=None):
        # authentication
        token = request.headers.get('Authorization')
        try:
            account = auth.check(token)
            if account['class'] != 'administrator':
                return jsonify({'error': errors.AUTHENTICATION_FORBIDDEN}), 403
        except errors.AuthenticationError:
            return jsonify({'error': errors.AUTHENTICATION_INVALID}), 401

        with connection.cursor() as cursor:
            if evaluation_id is None:
                cursor.execute('SELECT * FROM evaluations')
                return jsonify({'data': cursor.fetchall()}), 200
            else:
                cursor.execute('SELECT * FROM evaluations WHERE id=%(id)s', {'id': evaluation_id})
                return jsonify({'data': cursor.fetchone()}), 200

    def post(self):
        # authentication
        token = request.headers.get('Authorization')
        try:
            account = auth.check(token)
            if account['class'] != 'student':
                return jsonify({'error': errors.AUTHENTICATION_FORBIDDEN}), 403
        except errors.AuthenticationError:
            return jsonify({'error': errors.AUTHENTICATION_INVALID}), 401

        body = request.get_json()

        if not body:
            return jsonify({'error': DATA_EMPTY}), 422

        for k in ('enrollment_id', 'comments', 'rating'):
            if not body.get(k):
                return jsonify({'error': FIELD_EMPTY.format(k)}), 422

        try:
            with connection.cursor() as cursor:
                cursor.execute('INSERT INTO evaluations (enrollment_id, rating, comments) VALUES (%(enrollment_id)s, %(rating)s, %(comments)s)', body)

            connection.commit()
            return jsonify(None), 201

        except pymysql.err.IntegrityError as e:
            logger.error(e)
            return jsonify({'error': DATA_SAVE}), 500
