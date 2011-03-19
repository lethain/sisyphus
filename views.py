"Views for blog application."
from django.shortcuts import render_to_response

def frontpage(request):
    "Render frontpage."
    
    return render_to_response('sisyphus/front.html', {})
