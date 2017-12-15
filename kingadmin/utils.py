#! /usr/bin/env python
# -*- coding:utf-8 -*-

from django.core import serializers
import json


def get_specified_data(obj, specified_fields):
    """

    :param obj:
    :param specified_fields:
    :return:
    """
    serialized_data = serializers.serialize("json", [obj])
    obj_data = json.loads(serialized_data)[0]
    filtered_data ={}
    for column in specified_fields:
        filtered_data[column] = obj_data["fields"][column]

    return filtered_data


def fetch_changed_data(old_data, fields):
    """

    :param old_data:
    :param fields:
    :return:
    """
    old_data = json.loads(old_data)
    changed_data_list = []
    for obj_data in old_data:
        changed_data = {}
        for column in fields:
            changed_data[column] = old_data["field"][column]
        changed_data_list.append(changed_data)
    return changed_data_list


