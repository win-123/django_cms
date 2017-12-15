from django.shortcuts import render

# Create your views here.

import datetime
import re
import json
from django.core import serializers
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import PageNotAnInteger, Paginator, EmptyPage
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, redirect, HttpResponse, HttpResponseRedirect, Http404
from kingadmin.base_admin import site
from kingadmin import forms
from django.contrib import messages
from kingadmin import tables
from kingadmin.permissions import check_permission
from django.utils.safestring import mark_safe
from kingadmin import utils


@check_permission
@login_required(login_url="/kingadmin/login/")
def app_index(request):
    return render(request, "kingadmin/app_index.html", {'enabled_admins': site.enabled_admins})


@check_permission
@login_required(login_url="/kingadmin/login/")
def app_tables(request, app_name):
    enabled_admins = {app_name: site.enabled_admins[app_name]}
    return render(request, "kingadmin/app_index.html", {'enabled_admins': enabled_admins, 'current_app': app_name})


def acc_login(request):
    error_msg = {}
    today_str = datetime.date.today().strftime("%Y%m%d")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        _verify_code = request.POST.get("verify_code")
        _verify_code_key = request.POST.get("verify_code_key")
        if cache.get(_verify_code_key) == _verify_code:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                request.session.set_expiry(60 * 60)
                return HttpResponseRedirect(request.GET.get("next") if request.GET.get("next") else "/kingadmin/")
            else:
                error_msg["error"] = "Wrong username or password !"
        else:
            error_msg["error"] = "验证码错误"
    return render(request, "kingadmin/login.html", {"error": error_msg})


def acc_logout(request):
    logout(request)
    return HttpResponseRedirect("/kingadmin/login/")


@check_permission
@login_required(login_url="/kingadmin/login/")
def batch_update(request, editable_data, admin_class):
    errors = []
    for row_data in editable_data:
        obj_id = row_data.get("id")
        try:
            if obj_id:
                obj = admin_class.model.objects.get(id=obj_id)
                model_form = forms.create_form(admin_class.model, list(row_data.keys()),
                                               admin_class, request=request, partial_update=True)
                form_obj = model_form(instance=obj, data=row_data)
                if form_obj.is_valid():
                    log_data = [{"changed": {}}]
                    form_obj.save()
                    if form_obj.has_changed():
                        messages.add_message(
                            request,
                            messages.SUCCESS,
                            '''{model_name} "{obj}" 修改成功。'''.format(
                                model_name=admin_class.model._meta.verbose_name,
                                obj=form_obj.instance
                            ))
                else:
                    errors.append([form_obj.errors, obj])

        except ValueError as e:
            return False, [e, obj]
    if errors:
        return False, errors
    return True, []


@check_permission
@login_required(login_url="/kingadmin/login/")
def display_table_list(request, app_name, table_name, embed=False):
    """

    :param request:
    :param app_name:
    :param table_name:
    :param embed:
    :return:
    """
    errors = []
    if app_name in site.enabled_admins:
        if table_name in site.enabled_admins[app_name]:
            admin_class = site.enabled_admins[app_name][table_name]
            if request.method == "POST":
                editable_data = request.POST.get("editable_data")
                if editable_data:
                    editable_data = json.loads(editable_data)
                    res_state, errors = batch_update(request, editable_data, admin_class)

                else:
                    selected_ids = request.POST.get("selected_ids")
                    action = request.POST.get("admin_action")
                    if selected_ids:
                        selected_objs = admin_class.model.objects.filter(id__in=selected_ids.split(","))
                    else:
                        raise KeyError("No object selected")
                    if hasattr(admin_class, action):
                        action_func = getattr(admin_class, action)
                        request._admin_action = action
                        return action_func(request, selected_ids)

            querysets = tables.table_filter(request, admin_class, admin_class.model)
            searched_querysets = tables.search_by(request, querysets, admin_class)
            order_res = tables.get_orderby(request, searched_querysets, admin_class)

            paginator = Paginator(order_res[0], admin_class.list_per_page)
            page = request.GET.get("page")
            try:
                table_obj_list = paginator.page(page)
            except PageNotAnInteger:
                table_obj_list = paginator.page(1)
            except EmptyPage:
                table_obj_list = paginator.page(paginator.num_pages)
            table_obj = tables.TableHandler(request,
                                            admin_class.model,
                                            admin_class,
                                            table_obj_list,
                                            order_res
                                            )
            return_data = {
                "table_obj": table_obj,
                "app_name": app_name,
                "paginator": paginator,
                "errors": errors,
                "enabled_admins": site.enabled_admins,
            }
            if embed:
                return return_data
            else:
                return render(request, "kingadmin/model_obj_list.html", return_data)
    else:
        raise Http404("url %s/%s not found" % (app_name, table_name))


@check_permission
@login_required(login_url="/kingadmin/login/")
def table_change(request, app_name, table_name, obj_id, embed=False):
    """

    :param request:
    :param app_name:
    :param table_name:
    :param obj_id:
    :param embed:
    :return:
    """
    if app_name in site.enabled_admins:
        if table_name in site.enabled_admins[app_name]:
            admin_class = site.enabled_admins[app_name][table_name]
            obj = admin_class.model.objects.get(id=obj_id)
            fields = []
            for field_obj in admin_class.model._meta.fields:
                if field_obj.editable:
                    fields.append(field_obj.name)

            for field_obj in admin_class.model._meta.many_to_many:
                fields.append(field_obj.name)

            if admin_class.add_form is not None:
                custom_status = True

            else:
                custom_status = False

            model_form = forms.create_form(admin_class.model, fields, admin_class, request=request,
                                           custom_status=custom_status)

            if request.method == "GET":
                form_obj = model_form(instance=obj)

            elif request.method == "POST":
                old_data = serializers.serialize("json", [obj])
                form_obj = model_form(request.POST, instance=obj)
                if form_obj.is_valid():
                    form_obj.validate_unique()
                    if form_obj.is_valid():
                        log_data = [{"change": {}}]
                        form_obj.save()
                        messages.add_message(
                            request,
                            messages.SUCCESS,
                            mark_safe(
                                '''{model_name} <a href='{obj_change_link}'>{obj}</a> 修改成功。'''.format(
                                    model_name=admin_class.model._meta.verbose_name,
                                    obj=form_obj.instance,
                                    obj_change_link=request.path
                                )
                            )
                        )

                        new_object = form_obj.instance
                        field_data_before_change = utils.fetch_changed_data(old_data, form_obj.changed_data)
                        log_data[0]["changed"]["changed_to"] = utils.get_specified_data(new_object,
                                                                                        form_obj.changed_data)
                        log_data[0]["changed"]["old_data"] = field_data_before_change
                        admin_class.log_change(request, new_object, log_data)

            return_data = {
                "form_obj": form_obj,
                "model_verbose_name": admin_class.model._meta.verbose_name,
                "model_name": admin_class.model._meta.model_name,
                "app_name": app_name,
                "admin_class": admin_class,
                "enabled_admins": site.enabled_admins,
            }
            if embed:
                return return_data
            else:
                if request.method == "POST" and not form_obj.errors:
                    return redirect("/kingadmin/{app}/{table}/".format(app=app_name, table=table_name))
                return render(request, 'kingadmin/table_change.html', return_data)

    else:
        raise Http404("url %s/%s not found" % (app_name, table_name))


@check_permission
@login_required(login_url="/kingadmin/login/")
def table_del(request, app_name, table_name, obj_id, embed=False):
    """

    :param request:
    :param app_name:
    :param table_name:
    :param obj_id:
    :param embed:
    :return:
    """
    if app_name in site.enabled_admins:
        if table_name in site.enabled_admins[app_name]:
            admin_class = site.enabled_admins[app_name][table_name]
            objs = admin_class.model.objects.filter(id=obj_id)

            if request.method == "POST":
                obj_names = ",".join([repr(i) for i in objs])
                delete_tag = request.POST.get("_delete_confirm")
                if delete_tag == "yes":
                    admin_class.log_deletion(request, objs)
                    objs.delete()
                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        """{model_name} "{obj}" 删除成功。""".format(
                            model_name=admin_class.model._meta.verbose_name,
                            obj=obj_names)
                    )

                    if embed:
                        return redirect(request.path.replace("delete/%s/" % obj_id, ""))
                    return redirect("/kingadmin/%s/%s/" % (app_name, table_name))
            if admin_class.readonly_table is True:
                return render(request, "kingadmin/table_objs_delete.html")

            data = {
                'admin_class': admin_class,
                'model_verbose_name': admin_class.model._meta.verbose_name,
                'model_name': admin_class.model._meta.model_name,
                'model_db_table': admin_class.model._meta.db_table,
                'objs': objs,
                'app_name': app_name
            }
            if embed:
                return data
            else:
                return render(request, "kingadmin/table_objs_delete.html", data)


@check_permission
@login_required(login_url="/kingadmin/login/")
def table_add(request, app_name, table_name, embed=False):
    """

    :param request:
    :param app_name:
    :param table_name:
    :param embed:
    :return:
    """
    if app_name in site.enabled_admins:
        if table_name in site.enabled_admins[app_name]:
            admin_class = site.enabled_admins[app_name][table_name]

            template_file = "kingadmin/table_add.html"
            fields = []
            for field_obj in admin_class.model._meta.fields:
                if field_obj.editable:
                    fields.append(field_obj.name)
            for field_obj in admin_class.model._meta.many_to_many:
                fields.append(field_obj.name)
            if admin_class.add_form is not None:
                custom_status = True
            else:
                custom_status = False

            model_form = forms.create_form(
                admin_class.model,
                fields,
                admin_class,
                form_creata=True,
                request=request,
                custom_status=custom_status
            )
            if request.method == "GET":
                if "_popup=4" in request.get_full_path():
                    template_file = "kingadmin/table_add_popup.html"
                fk_id = request.get("fk_id")
                field_name = request.GET.get("field_name")
                model_name = request.GET.get("model_name")
                if fk_id and field_name:
                    if field_name == "content_type" and model_name:
                        content_type = ContentType.objects.get(model=model_name).id
                        form_obj = model_form(initial={"content_type": content_type, "object_id": fk_id})
                    else:

                        form_obj = model_form(initial={field_name: fk_id, })

                else:
                    form_obj = model_form()

            elif request.method == "POST":
                form_obj = model_form(request.POST)
                if form_obj.is_valid():
                    form_obj.validate_unique()
                    if form_obj.is_valid():
                        new_object = form_obj.save()
                        log_data = [{"added": {}}]
                        admin_class.log_addition(request, new_object, log_data)
                        messages.add_message(
                            request,
                            messages.SUCCESS,

                            mark_safe(
                                '''{model_name} <a href='{obj_change_link}'>{obj}</a> 添加成功。'''.format(
                                    model_name=admin_class.model._meta.verbose_name,
                                    obj=form_obj.instance,
                                    obj_change_link="/kingadmin/%s/%s/change/%s/" % (
                                        app_name, table_name, form_obj.instance.pk)

                                )
                            )
                        )
                        # 定制的批量操作， （路飞学城优惠券批量生成）
                        method_name = "bulk_create_%s" % table_name
                        if hasattr(admin_class, method_name):
                            getattr(admin_class, method_name)(new_object)

                        if request.POST.get("_continue") is not None:
                            redirect_url = '%s/%s/' % (re.sub("add/$", "change", request.path), form_obj.instance.id)
                            return redirect(redirect_url)
                        elif request.POST.get("_add_another") is not None:

                            fk_id = request.GET.get("fk_id")
                            field_name = request.GET.get("field_name")
                            model_name = request.GET.get("model_name")
                            if fk_id and field_name:
                                if field_name == "content_type" and model_name:
                                    content_type = ContentType.objects.get(model=model_name).id
                                    form_obj = model_form(initial={"content_type": content_type, "object_id": fk_id})
                                else:
                                    form_obj = model_form(initial={field_name: fk_id, })
                            else:
                                form_obj = model_form()

                            return redirect(request.get_full_path() or admin_class.object_add_link)

                        else:  # return to table list page
                            if "_popup=4" not in request.get_full_path():
                                redirect_url = re.sub("add/$", "", request.path)
                                return redirect(redirect_url)
                            else:
                                template_file = 'kingadmin/table_add_popup.html'

            return_data = {
                'form_obj': form_obj,
                'model_name': admin_class.model._meta.model_name,
                'model_verbose_name': admin_class.model._meta.verbose_name,
                'model_db_table': admin_class.model._meta.db_table,
                'admin_class': admin_class,
                'app_name': app_name,
                'enabled_admins': site.enabled_admins,
                'cid': request.GET.get('cid'),
                'chapter_num': request.GET.get('chapter_num')
            }

            if embed:
                return return_data
            else:
                if request.method == "POST" and not form_obj.errors and "_popup=4" not in request.get_full_path():
                    return redirect("/kingadmin/{app}/{table}/".format(app=app_name, table=table_name))

                return render(request, template_file, return_data)

    else:
        raise Http404("url %s/%s not found" % (app_name, table_name))


@check_permission
@login_required(login_url="/kingadmin/login/")
def personal_password_reset(request):
    app_name = request.user._meta.app_label
    model_name = request.user._meta.model_name

    if request.method == "GET":
        change_form = site.enabled_admins[app_name][model_name].add_form(instance=request.user)
    else:
        change_form = site.enabled_admins[app_name][model_name].add_form(request.POST, instance=request.user)
        if change_form.is_valid():
            change_form.save()
            url = "/%s/" % request.path.strip("/password/")
            return redirect(url)

    return render(request, 'kingadmin/password_change.html', {'user_obj': request.user, 'form': change_form})


@check_permission
@login_required(login_url="/kingadmin/login/")
def password_reset_form(request, app_name, table_db_name, user_id, embed=False):
    user_obj = request.user._meta.model.objects.get(id=user_id)
    can_change_user_password = False
    if request.user.is_superuser or request.user.id == user_obj.id:
        can_change_user_password = True

    if can_change_user_password:
        if request.method == "GET":
            change_form = site.enabled_admins[app_name][table_db_name].add_form(instance=user_obj)
        else:
            change_form = site.enabled_admins[app_name][table_db_name].add_form(request.POST, instance=user_obj)
            if change_form.is_valid():
                change_form.save()
                url = "/%s/" % request.path.strip("/password/")
                return redirect(url)
        data = {"user_obj": user_obj, "form": change_form}

        if embed:
            return data
        else:
            return render(request, "kingadmin/password_change.html", data)
    else:
        return HttpResponse("Only admin has permission to change password")



