from django.contrib import admin

# Register your models here.

from django.shortcuts import render, redirect
from django.utils.encoding import force_text
import json
from django.contrib import messages
from kingadmin.models import (AdminLog, ADDITION, CHANGE, DELETION)


def get_content_type_for_model(obj):
    from django.contrib.contenttypes.models import ContentType
    return ContentType.objects.get_for_model(obj, for_concrete_model=False)


class BaseKingAdmin(object):
    base_app_url = None
    list_display = []
    list_filter = []
    search_fields = []
    fieldsets = []
    list_per_page = 60
    ordering = None
    filter_horizontal = []
    list_editable = []
    readonly_fields = []
    actions = ["delete_selscted_objs", ]
    readonly_able = False
    modelform_exclude_fields = []
    add_form = None
    model_display_name = None
    object_add_link = None
    object_del_link = None
    back_link = None
    prefetch_queryset_func = None
    registration_key = None
    instance = None
    model = None

    def delete_selected_objs(self, request, querysets):
        app_name = self.model._meta.app_label
        model_name = self.model._meta.model_name
        if self.readonly_able:
            errors = {"readonly_table": "This table is readonly ,cannot be deleted or modified!"}
        else:
            errors = {}
        if request.POST.get("_delete_confirm") == "yes":
            if not self.readonly_able:
                self.log_deletion(request, querysets)
                obj_names = ",".join([repr(i) for i in querysets])
                querysets.delete()
                messages.add_message(request, messages.SUCCESS,
                                     '''{model_name} "{obj}" 删除成功。'''.format(
                                         model_name=self.model._meta.verbose_name,
                                         obj=obj_names)
                                     )
            return redirect("/kingadmin/%s/%s" %(app_name, model_name))
        selected_ids = ",".join([str(i.id) for i in querysets])
        return render(request, "kingadmin/table_objs_delete.html", {
            "objs": querysets,
            "admin_class": self,
            "app_name": app_name,
            "model_name": model_name,
            "model_verbose_name": self.model._meta.verbose_name,
            "selected_ids": selected_ids,
            "admin_action": request._admin_action,
            "errors": errors

        })

    def default_form_validation(self):
        """
        用户可以自己自定义表单验证， 相当于Django form的clean方法
        :return:
        """
        pass

    def log_addition(self, request, object, message):
        """

        :param request:
        :param object:
        :param message:
        :return:
        """

        return AdminLog.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            action_flag=ADDITION,
            change_message=json.dumps(message)
        )

    def log_change(self, request, object, message):
        """

        :param request:
        :param object:
        :param message:
        :return:
        """
        return AdminLog.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            action_flag=CHANGE,
            change_message=json.dumps(message)
        )

    def log_deletion(self, request, objects):
        """

        :param request:
        :param objects:
        :return:
        """
        content_type_obj = get_content_type_for_model(objects[0])
        obj_del_list = [(repr(o), o.pk) for o in objects]

        msg = [{'delete': {'deleted_objs': obj_del_list}}]
        return AdminLog.objects.log_action(
            user_id=request.user.pk,
            content_type_id=content_type_obj.pk,
            object_id=objects[0].pk,
            object_repr='',
            change_message=json.dumps(msg),
            action_flag=DELETION,
        )


class AdminAlreadyRegistered(Exception):
    def __init__(self, msg):
        self.message = msg


class AdminSite(object):
    def __init__(self, name="management"):
        self.enabled_admins = {}

    def register(self, model_class, admin_class=None, indeppendent=False):
        """

        :param model_class:
        :param admin_class:
        :param indeppendent:
        :return:
        """
        if model_class._meta.app_label not in self.enabled_admins:
            self.enabled_admins[model_class._meta.app_label] = {}

        if not indeppendent:
            if not admin_class:
                admin_class = BaseKingAdmin()
            else:
                admin_class = admin_class()
            self.enabled_admins[model_class._meta.app_label][model_class._meta.model_name] = admin_class

        else:  # 单独添加一个key
            if not admin_class:
                raise ValueError("independent admin must has customized admin class , cannot use default BaseAdmin")
            if not admin_class.registration_key:
                raise ValueError("registration_key must be specified when use independent admin! ")

            self.enabled_admins[model_class._meta.app_label][admin_class.registration_key] = admin_class()

        admin_class.model = model_class  # 绑定model 对象和admin 类


site = AdminSite()

