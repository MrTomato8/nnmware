import os
import Image
from datetime import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, SiteProfileNotAvailable

from django.contrib.auth.forms import PasswordResetForm, AuthenticationForm, \
    PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseForbidden, Http404
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson
from django.db.models import Q
from django.views.generic.base import View, TemplateView
from django.views.generic import FormView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from django.views.generic import YearArchiveView, MonthArchiveView, \
    DayArchiveView
from nnmware.apps.video.models import Video
from nnmware.core.http import redirect, handle_uploads, LazyEncoder
from nnmware.core.ajax import as_json
from nnmware.core.imgutil import resize_image, remove_thumbnails, remove_file
from nnmware.core.models import Tag, Follow, Action
from nnmware.core.views import AjaxFormMixin

from nnmware.apps.userprofile.models import Profile
from nnmware.apps.userprofile.forms import *
from nnmware.core.imgutil import fit


class UserList(ListView):
    model = User
    context_object_name = "object_list"
    template_name = "user/users_list.html"

    def get_queryset(self):
        return User.objects.order_by("-date_joined")


class UserMenList(UserList):
    def get_queryset(self):
        return User.objects.filter(profile__gender='M')


class UserWomenList(UserList):
    def get_queryset(self):
        return User.objects.filter(profile__gender='F')


class UserDateTemplate(object):
    template_name = 'user/users_list.html'
    model = User
    date_field = 'date_joined'
    context_object_name = "object_list"
    make_object_list = True
    allow_empty = True


class UserYearList(UserDateTemplate, YearArchiveView):
    pass


class UserMonthList(UserDateTemplate, MonthArchiveView):
    pass


class UserDayList(UserDateTemplate, DayArchiveView):
    pass


class UserDetail(DetailView):
    model = User
    slug_field = 'username'
    template_name = "user/user_detail.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(UserDetail,self).get_context_data(**kwargs)
        context['ctype'] = ContentType.objects.get_for_model(User)
        return context

class UserVideoLoved(DetailView):
    model = User
    slug_field = 'username'
    template_name = "user/loved_video.html"

    def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
        context = super(UserVideoLoved, self).get_context_data(**kwargs)
        context['added'] = Video.objects.filter(user=self.object).count()
        follow = self.object.follow_set.filter(content_type=ContentType.objects.get_for_model(Video)).values_list('object_id',flat=True)
        context['videos'] = Video.objects.filter(id__in=follow)
        context['ctype'] = ContentType.objects.get_for_model(User)
        context['tab'] = 'loved'
        context['tab_message'] = 'LOVED VIDEOS:'
        return context

class UserActivity(DetailView):
    model = User
    slug_field = 'username'
    template_name = "user/activity.html"

    def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
        context = super(UserActivity, self).get_context_data(**kwargs)
#        ctype = ContentType.objects.get_for_model(User)
        context['actions_list'] = Action.objects.filter(user=self.object) #actor_content_type=ctype, actor_object_id=self.object.id)
        context['tab'] = 'activity'
        context['tab_message'] = 'THIS USER ACTIVITY:'
        return context


class UserVideoAdded(DetailView):
    model = User
    slug_field = 'username'
    template_name = "user/added_video.html"

    def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
        context = super(UserVideoAdded, self).get_context_data(**kwargs)
        context['added'] = Video.objects.filter(user=self.object).count()
        context['user_video'] = Video.objects.filter(user=self.object).order_by('-publish_date')
        context['ctype'] = ContentType.objects.get_for_model(User)
        context['tab'] = 'added'
        context['tab_message'] = 'VIDEO ADDED THIS USER:'
        return context

class UserFollowTags(DetailView):
    model = User
    slug_field = 'username'
    template_name = "user/follow_tags.html"
    make_object_list = True


    def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
        context = super(UserFollowTags, self).get_context_data(**kwargs)
        context['added'] = Video.objects.filter(user=self.object).count()
        follow = self.object.follow_set.filter(content_type=ContentType.objects.get_for_model(Tag)).values_list('object_id',flat=True)
        context['tags_list'] = Tag.objects.filter(id__in=follow)
        context['ctype'] = ContentType.objects.get_for_model(User)
        context['tab'] = 'follow_tags'
        context['tab_message'] = 'USER FOLLOW THIS TAGS:'
        return context

class UserFollowUsers(DetailView):
    model = User
    slug_field = 'username'
    template_name = "user/follow_users.html"
    make_object_list = True

    def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
        context = super(UserFollowUsers, self).get_context_data(**kwargs)
        context['added'] = Video.objects.filter(user=self.object).count()
        follow = self.object.follow_set.filter(content_type=ContentType.objects.get_for_model(User)).values_list('object_id',flat=True)
        context['users'] = User.objects.filter(id__in=follow)
        context['ctype'] = ContentType.objects.get_for_model(User)
        context['tab'] = 'follow_users'
        context['tab_message'] = 'USER FOLLOW THIS USERS:'
        return context

class UserFollowerUsers(DetailView):
    model = User
    slug_field = 'username'
    template_name = "user/follower_users.html"
    make_object_list = True

    def get_context_data(self, **kwargs):
    # Call the base implementation first to get a context
        context = super(UserFollowerUsers, self).get_context_data(**kwargs)
        context['added'] = Video.objects.filter(user=self.object).count()
        context['ctype'] = ContentType.objects.get_for_model(User)
        followers = Follow.objects.filter(object_id=self.object.id, content_type=ContentType.objects.get_for_model(User)).values_list('user',flat=True)
        context['users'] = User.objects.filter(id__in=followers)
        context['tab'] = 'follower_users'
        context['tab_message'] = 'USERS FOLLOW ON THIS USER:'
        return context


class ProfileEdit(AjaxFormMixin, UpdateView):
    form_class = ProfileForm
    template_name = "user/profile_edit.html"

    def get_object(self, queryset=None):
        return self.request.user.get_profile()

    def get_success_url(self):
        return reverse('user_detail', args=[self.request.user.username])

class AvatarEdit(UpdateView):
    model = Profile
    form_class = AvatarForm
    template_name = "user/settings.html"
    success_url = reverse_lazy('user_settings')

    def form_valid(self, form):
        avatar_path = self.object.avatar.url
        remove_thumbnails(avatar_path)
        remove_file(avatar_path)
        self.object = form.save(commit=False)
        self.object.avatar_complete = False
        self.object.save()
        resize_image(self.object.avatar.url)
        return super(AvatarEdit, self).form_valid(form)

    def get_object(self, queryset=None):
        return self.request.user.get_profile()


class AvatarCrop(UpdateView):
    form_class = AvatarCropForm
    template_name = "user/settings.html"
    success_url = reverse_lazy('user_settings')

    def get_object(self, queryset=None):
        return self.request.user.get_profile()

    def form_valid(self, form):
        top = int(form.cleaned_data.get('top'))
        left = int(form.cleaned_data.get('left'))
        right = int(form.cleaned_data.get('right'))
        bottom = int(form.cleaned_data.get('bottom'))
        image = Image.open(self.object.avatar.path)
        box = [left, top, right, bottom]
        image = image.crop(box)
        if image.mode not in ('L', 'RGB'):
            image = image.convert('RGB')
        image = fit(image, 120)
        image.save(self.object.avatar.path)
        self.object.avatar_complete = True
        self.object.save()
        return super(AvatarCrop, self).form_valid(form)


class UserSettings(UpdateView):
    form_class = UserSettingsForm
    template_name = "user/settings.html"

    def get_object(self, queryset=None):
        return self.request.user.get_profile()

    def get_success_url(self):
        return reverse('user_detail', args=[self.request.user.username])



class UserSearch(ListView):
    model = User
    template_name = "user/users_list.html"

    def get_queryset(self):
        query = self.request.GET.get('q')
        return User.objects.filter(username__icontains=query)


class RegisterView(AjaxFormMixin, FormView):
    form_class = RegistrationForm
    template_name = 'user/registration.html'
    success_url = "/users"
    status = _("YOU GOT ON E-MAIL IS CONFIRMATION. CHECK EMAIL")


    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        email = form.cleaned_data.get('email')
        newuser = User.objects.create_user(username=username, email=email, password=password)
        newuser.is_active = False
        EmailValidation.objects.add(user=newuser, email=newuser.email)
        newuser.save()
        return super(RegisterView, self).form_valid(form)

class SignupView(AjaxFormMixin, FormView):
    form_class = SignupForm
    template_name = 'user/registration.html'
    success_url = "/"
    status = _("YOU GOT ON E-MAIL IS CONFIRMATION. CHECK EMAIL")

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        email = form.cleaned_data.get('email')
        newuser = User.objects.create_user(username=username, email=email, password=password)
        newuser.is_active = True
        EmailValidation.objects.add(user=newuser, email=newuser.email)
        newuser.save()
        return super(SignupView, self).form_valid(form)


class LoginView(AjaxFormMixin, FormView):
    form_class = LoginForm
    template_name = 'user/login.html'
    success_url = "/users"

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return super(LoginView, self).form_valid(form)

class SigninView(AjaxFormMixin, FormView):
    form_class = SigninForm
    template_name = 'user/login.html'
    success_url = "/"
    status = _("YOU SUCCESSFULLY SIGN IN")


    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        user = authenticate(username=email, password=password)
        login(self.request, user)
        return super(SigninView, self).form_valid(form)


class ChangePasswordView(AjaxFormMixin, FormView):
    form_class = PassChangeForm
    template_name = 'user/pwd_change.html'
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        self.request.user.set_password(form.cleaned_data.get('new_password2'))
        self.request.user.save()
        return super(ChangePasswordView, self).form_valid(form)


class LogoutView(TemplateView):
    template_name = 'user/logged_out.html'

    def get(self, request, *args, **kwargs):
        logout(self.request)
        return super(LogoutView, self).get(request, *args, **kwargs)


#@render_to("profile/userprofile/email_validation_done.html")
def email_validation_process(request, key):
    """
     Verify key and change email
     """
    if EmailValidation.objects.verify(key=key):
        successful = True
    else:
        successful = False
    return {'successful': successful}


@login_required
def avatardelete(request, avatar_id=False):
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        try:
            Avatar.objects.get(user=request.user, valid=True).delete()
            return HttpResponse(simplejson.dumps({'success': True}))
        except:
            return HttpResponse(simplejson.dumps({'success': False}))
    else:
        raise Http404()