#! /usr/bin/env python
# -*- coding:utf-8 -*-

from django.utils import timezone
from django.db.models import Count, Q
import time


def search_by(request, querysets, admin_form):
    search_str = request.GET.get("q")
    if search_str:
        q_objects = []
        for q_field in admin_form.search_fields:
            q_objects.append("Q(%s__contains='%s')" %(q_field, search_str))
        return querysets.filter(eval("|".join(q_objects)))
    return querysets


def get_orderby(request, model_objs, admin_form):
    order_by_field = request.GET.get("orderby")
    if order_by_field:
        order_by_field = order_by_field.strip()
        order_by_colum_index = admin_form.list_display.index(order_by_field.strip("-"))
        objs = model_objs.order_by(order_by_field)
        if order_by_field.startwith("-"):
            order_by_field = order_by_field.strip("-")
        else:
            order_by_field = "-%s" %order_by_field

        return [objs, order_by_field, order_by_colum_index]
    else:
        return [model_objs, order_by_field, None]


class TableHandler(object):
    """

    """
    def __init__(self, request, model_class, admin_class, query_sets, order_res):
        self.request = request
        self.model_class = model_class
        self.admin_class = admin_class

        self.model_verbose_name = self.model_class._meta.verbose_name
        self.model_name = self.model_class._meta.model_name
        self.actions = admin_class.actions
        self.list_editable = admin_class.list_editable
        self.query_sets = query_sets
        self.readonly_table = admin_class.readonly_table
        self.readonly_fields = admin_class.readonly_fields
        self.list_display = admin_class.list_display
        self.search_fields = admin_class.search_fields
        self.list_filter = self.get_list_filter(admin_class.list_filter) if hasattr(admin_class, 'list_filter') else ()

        self.order_by_field = order_res[1]
        self.order_by_colum_index = order_res[2]

        self.colored_fields = getattr(admin_class, 'colored_fields') if \
            hasattr(admin_class, 'colored_fields') else {}

        # for dynamic display
        self.dynamic_fk = getattr(admin_class, 'dynamic_fk') if \
            hasattr(admin_class, 'dynamic_fk') else None
        self.dynamic_list_display = getattr(admin_class, 'dynamic_list_display') if \
            hasattr(admin_class, 'dynamic_list_display') else ()
        self.dynamic_choice_fields = getattr(admin_class, 'dynamic_choice_fields') if \
            hasattr(admin_class, 'dynamic_choice_fields') else ()
        # for dynamic display
        self.dynamic_fk = getattr(admin_class, 'dynamic_fk') if \
            hasattr(admin_class, 'dynamic_fk') else None
        self.dynamic_list_display = getattr(admin_class, 'dynamic_list_display') if \
            hasattr(admin_class, 'dynamic_list_display') else ()
        self.dynamic_choice_fields = getattr(admin_class, 'dynamic_choice_fields') if \
            hasattr(admin_class, 'dynamic_choice_fields') else ()

    def get_list_filter(self, list_filter):
        """

        :param list_filter:
        :return:
        """
        filters = []
        for i in list_filter:
            filters_keys = i.split("__")
            if len(filters_keys) == 1:
                column_obj = self.model_class._meta.get_field(i)
                data = {
                    "verbose_name": column_obj.verbose_name,
                    "column_name": i,
                    "show_type": None,
                }
                if column_obj.deconstruct()[1] not in ('django.db.models.DateField', 'django.db.models.DateTimeField'):
                    try:
                        choices = column_obj.get_choices(limit_choices_to={
                            "id__in": (set(row[i] for row in column_obj.model.objects.values(i)))
                        })

                    except AttributeError as e:
                        choices_list = column_obj.model.objects.values(i).annotate(count=Count(i))
                        choices = [[obj[i], obj[i]] for obj in choices_list]
                        choices.insert(0, ["", "----------"])
                else:
                    today_obj = timezone.datetime.now()
                    choices = [
                        ("", '----------'),
                        (today_obj.strftime("%Y-%m-%d"), '今天'),
                        ((today_obj - timezone.timedelta(days=7)).strftime("%Y-%m-%d"), '过去七天'),
                        ((today_obj - timezone.timedelta(days=today_obj.day)).strftime("%Y-%m-%d"), '本月'),
                        ((today_obj - timezone.timedelta(days=90)).strftime("%Y-%m-%d"), '过去三个月'),
                        ((today_obj - timezone.timedelta(days=180)).strftime("%Y-%m-%d"), '过去六个月'),
                        ((today_obj - timezone.timedelta(days=365)).strftime("%Y-%m-%d"), '过去一年'),
                        ((today_obj - timezone.timedelta(seconds=time.time())).strftime("%Y-%m-%d"), 'ALL'),
                    ]
                    data["show_type"] = "date"
                data["choices"] = choices
            else:
                ref_filter_key_field_obj, ref_filter_key = get_fk_field_type(filter_keys, self.model_class)

                try:
                    choices = ref_filter_key_field_obj.get_choices()
                except AttributeError as e:
                    choices = [("", "__________"), ]
                    ref_objs = list(set(self.model_class.objects.values_list(i, i)))
                    if ref_objs:
                        if "datetime" in repr(type(ref_objs[0][0])):
                            today_obj = timezone.datetime.now()
                            choices += [
                                (today_obj.strftime("%Y-%m-%d"), '今天'),
                                ((today_obj - timezone.timedelta(days=7)).strftime("%Y-%m-%d"), '过去7天'),
                                ((today_obj - timezone.timedelta(days=today_obj.day)).strftime("%Y-%m-%d"), '本月'),
                                ((today_obj - timezone.timedelta(days=90)).strftime("%Y-%m-%d"), '过去3个月'),
                                ((today_obj - timezone.timedelta(days=180)).strftime("%Y-%m-%d"), '过去6个月'),
                                ((today_obj - timezone.timedelta(days=365)).strftime("%Y-%m-%d"), '过去1年'),
                                ('1900-01-01__gt', 'ALL'),
                            ]
                        else:
                            choices += ref_objs
                data = {
                    'verbose_name': ref_filter_key_field_obj.verbose_name,
                    'column_name': i,
                    'choices': choices,
                    'show_type': None
                }

            # handle selected data
            if self.request.GET.get(i):
                data['selected'] = self.request.GET.get(i)
            filters.append(data)

        return filters


def get_fk_field_type(condtion_key_list, model_class):
    """
     返回关联filter的目标字段的类型，以使后面的过滤条件确定如何处理这个字段的过滤请求
     :param condtion_key_list: like ['chpater','course','name']
     :param model_class:
     :return:
     """
    model_obj = model_class
    for key in condtion_key_list:
        field_obj = model_obj._meta.get_field(key)
        if field_obj.get_internal_type() in ('ForeignKey', 'OneToOneField'):
            model_obj = field_obj.rel.to

        else:
            return field_obj, key


def table_filter(request, model_admin, model_class):
    """

    :param request:
    :param model_admin:
    :param model_class:
    :return:
    """
    filter_conditions = {}
    if hasattr(model_class, "list_filter"):
        for condition in model_class.list_filter:
            if request.GET.get(condition):
                ref_conditions = condition.split("__")
                if len(ref_conditions) == 1:
                    field_type_name = model_class._meta.get_field(condition).get_internal_type()
                    if "ForeignKey" in field_type_name:
                        filter_conditions["%s_id" %condition] = request.GET.get(condition)
                    elif 'DateField' in field_type_name or 'DateTimeField' in field_type_name:
                        start_date, end_date = request.GET.get(condition).split(" - ")
                        if field_type_name == "DateTimeField":
                            end_date = "%s 23:59:59" % end_date
                        filter_conditions['%s__gte' % condition] = start_date
                        filter_conditions['%s__lte' % condition] = end_date
                    else:
                        filter_conditions[condition] = request.GET.get(condition)
                else:
                    ref_filter_key_field_obj, ref_filter_key = get_fk_field_type(ref_conditions, model_class)
                    if ref_filter_key_field_obj.get_internal_type() in ('DateField', 'DateTimeField'):
                        filter_conditions['%s__gte' % condition] = request.GET.get(condition)
                    else:
                        filter_conditions[condition] = request.GET.get(condition)

    if model_admin.prefetch_queryset_func:
        prefetched_queryset = getattr(model_admin, model_admin.prefetch_queryset_func)()
        return prefetched_queryset.filter(**filter_conditions).order_by('-pk')
    else:
        return model_class.objects.filter(**filter_conditions).order_by('-pk')

