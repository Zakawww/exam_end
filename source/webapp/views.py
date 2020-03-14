from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.http import urlencode
from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from django.views.generic.base import View

from webapp.forms import SearchForm, FullCreateFile, AnonymousCreateFile
from webapp.models import File


class HomeView(ListView):
    template_name = 'home.html'
    model = File
    ordering = '-created_at'
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        self.form = self.get_search_form()
        self.search_value = self.get_search_value()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=None, **kwargs)
        context['form'] = self.form
        if self.search_value:
            context['query'] = urlencode({'search': self.search_value})
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.search_value:
            query = Q(name__icontains=self.search_value) & Q(access='free')
            queryset = queryset.filter(query)
        else:
            queryset = queryset.filter(access='free')
        return queryset

    def get_search_form(self):
        return SearchForm(self.request.GET)

    def get_search_value(self):
        if self.form.is_valid():
            return self.form.cleaned_data['search']
        return None


class FileDetailView(UserPassesTestMixin, DetailView):
    template_name = 'file_detail.html'
    model = File

    def test_func(self):
        file = self.get_object()
        return file.access != 'private' or self.request.user == file.author or self.request.user in file.private.all()


class FileCreateView(CreateView):
    template_name = 'file_create.html'
    model = File

    def get_form_class(self):
        if self.request.user.id:
            return FullCreateFile
        else:
            return AnonymousCreateFile

    def form_valid(self, form):
        if self.request.user.id:
            form.instance.author = self.request.user
        return super().form_valid(form)


class FileUpdateView(UserPassesTestMixin, UpdateView):
    model = File
    fields = ['name', 'file', 'access']
    template_name = 'file_edit.html'

    def test_func(self):
        file = self.get_object()
        return self.request.user.is_authenticated or file.author == self.request.user or self.request.user.has_perm('webapp.change_file')


class FileDeleteView(UserPassesTestMixin, DeleteView):
    model = File
    template_name = 'file_delete.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        file = self.get_object()
        return self.request.user.is_authenticated or file.author == self.request.user or self.request.user.has_perm('webapp.delete_file')


class UserDetailView(DetailView):
    model = User
    template_name = 'user_detail.html'
    context_object_name = 'user_obj'


class SearchUserView(View):
    def get(self, request):
        search_user = request.GET.get('search_user').strip()
        file_id = request.GET.get('file_id')
        context = {}
        try:
            user = User.objects.get(username=search_user)

            file = File.objects.get(pk=file_id)
            if user not in file.private.all():
                file.private.add(user)
                context['user'] = user.username
                context['user_id'] = user.id
        except:
            context['error'] = 'Пользователя не существует'

        return JsonResponse(context)


class DeleteUser(View):
    def get(self, request):
        file = File.objects.get(pk=int(request.GET['file_id']))
        user = User.objects.get(id=int(request.GET['user_id']))
        file.private.remove(user)
        return JsonResponse({'status': '200'})
