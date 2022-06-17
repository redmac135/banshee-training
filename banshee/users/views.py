from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import View
from .forms import UserForm, SeniorForm

# Create your views here.
class SignupView(View):
    template_name = 'users/signup.html'
    user_form = UserForm
    senior_form = SeniorForm
        
    def get(self, request, *args, **kwargs):
        user_form = self.user_form()
        senior_form = self.senior_form()
        return render(request, self.template_name, {'user_form': user_form, 'senior_form': senior_form})

    def post(self, request, *args, **kwargs):
        user_form = self.user_form(request.POST)
        senior_form = self.senior_form(request.POST)
        if user_form.is_valid() and senior_form.is_valid():
            user_form.save()
            senior_form.save()
            messages.success(request, 'Signup Successful!')
            return redirect('login')
        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {'user_form': user_form, 'senior_form': senior_form})