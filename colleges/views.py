from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import College, CampusImage
from .forms import CollegeProfileForm

# Custom shortcut to safely get college associated with logged-in user
def get_user_college_or_404(user):
    if not user.college:
        raise Http404("No college associated with your account.")
    return user.college

from django.http import Http404

class CollegeProfileDetailView(LoginRequiredMixin, View):
    template_name = 'colleges/profile_detail.html'

    def get(self, request, *args, **kwargs):
        college = get_user_college_or_404(request.user)
        # Fetch related campus images
        campus_images = college.campus_images.all()
        
        context = {
            'college': college,
            'campus_images': campus_images,
        }
        return render(request, self.template_name, context)


class CollegeProfileEditView(LoginRequiredMixin, View):
    form_class = CollegeProfileForm
    template_name = 'colleges/profile_edit.html'

    def get(self, request, *args, **kwargs):
        college = get_user_college_or_404(request.user)
        form = self.form_class(instance=college)
        return render(request, self.template_name, {'form': form, 'college': college})

    def post(self, request, *args, **kwargs):
        college = get_user_college_or_404(request.user)
        form = self.form_class(request.POST, request.FILES, instance=college)

        if form.is_valid():
            # Save the main college details (including logo)
            college = form.save()

            # Handle deletion of selected campus images
            delete_image_ids = form.cleaned_data.get('delete_images')
            if delete_image_ids:
                CampusImage.objects.filter(id__in=delete_image_ids, college=college).delete()

            # Handle creation/upload of new campus images
            new_files = request.FILES.getlist('campus_images')
            for f in new_files:
                CampusImage.objects.create(college=college, image=f)

            messages.success(request, "College profile updated successfully!")
            return redirect('colleges:profile_detail')

        return render(request, self.template_name, {'form': form, 'college': college})
