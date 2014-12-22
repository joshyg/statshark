# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from posts.models import Post, Comment, PostPhoto, Choice, UserProfile
from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.http import Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.core.context_processors import csrf
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.files import File
import re

posts_per_page = 15 
num_posts = 0

def main(request, index=0):
  session_id = request.session.get('_auth_user_id', -1)
  if(session_id == -1):
    return HttpResponse("Must login to view this page")
  username = User.objects.get(pk=session_id)
  userprofile = UserProfile.objects.get(pk=session_id)
  ##posts per page/index settings
  num_posts = len(Post.objects.all())
  index = int(index)
  if(index+posts_per_page < num_posts):
    next_index = index  + posts_per_page
  else:
    next_index = -1
  if(index >= posts_per_page):
    previous_index = index  - posts_per_page
  else:
    previous_index = -1
  post_list = Post.objects.all().order_by('-pub_date')[index:index+posts_per_page]
  photo_list = PostPhoto.objects.all()
  next_post_id = num_posts + 1
  print next_post_id
  post_tuple_list = []
  for post_instance in post_list:
    num_choices = len(post_instance.choice_set.all())
    post_embed_list = split_post(post_instance.text)
    num_comments = len(post_instance.comment_set.all())
    if(len(userprofile.has_voted.filter(pk=post_instance.id)) == 1):
      post_tuple_list.append((num_choices, 1, post_instance, post_embed_list, num_comments))
    else:
      post_tuple_list.append((num_choices, 0, post_instance , post_embed_list, num_comments))
  csrf_request = {'post_tuple_list': post_tuple_list, 
                  'username': username, 
                  'userprofile': userprofile, 
                  'next_post_id': next_post_id,
                  'index': index,
                  'next_index': next_index,
                  'previous_index': previous_index}
  print "indexes:"+str(index)+" "+str(next_index)+" "+str(previous_index)
  csrf_request.update(csrf(request))
  if(username.is_active):
    return render_to_response('messageboard_main.html',  csrf_request, context_instance=RequestContext(request))
  else:
    return HttpResponse("Must login to view this page")

##The following function parses the post for youtube links
##If it finds any it converts them to embedded format.
##it returns a list of the posts elements.  If there were no embedded
##links the list will have one entry

def split_post(post_instance):
  post_link_tuple_list = []
  post_link_array = re.split(r'(\S*www.youtube.com/watch\S+)', post_instance)
  for text_block in post_link_array:
    link_suffix_re = re.search(r'\S*www.youtube.com/watch\?v=(\S+)\&*', text_block)
    if(link_suffix_re != None):
      link_suffix = link_suffix_re.groups(0)
      link = "http://www.youtube.com/embed/"+link_suffix[0];
      print link
      post_link_tuple_list.append((1, link))
    else:
      post_link_tuple_list.append((0, text_block))
  return post_link_tuple_list

def login_page(request):
  csrf_request = {}
  csrf_request.update(csrf(request))
  return render_to_response('messageboard_login.html', csrf_request,context_instance=RequestContext(request))


def authenticate_user(request):
    csrf_request = {}
    csrf_request.update(csrf(request))
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            # Redirect to a success page.
            return HttpResponseRedirect(reverse('posts.views.main'))
        else:
            # Return a 'disabled account' error message
            return HttpResponse("Account disabled, hit back on your browser to try again")
    else:
        # Return an 'invalid login' error message.
        return HttpResponse("Invalid Login, hit back on your browser to try again")

def logout_user(request):
  logout(request)
  return HttpResponseRedirect(reverse('posts.views.login_page'))
   
def add_post(request, post_id):
  print "in add_post"+str(post_id)
  session_id = request.session.get('_auth_user_id', -1)
  if(session_id == -1):
    return HttpResponse("Must login to view this page")
  username = User.objects.get(pk=session_id)
  #csrf: Cross Site Request Forgery protection
  csrf_request = {}
  csrf_request.update(csrf(request))
  p = Post(title=request.POST['new_post_title'], 
           text=request.POST['new_post_text'], 
           pub_date = timezone.now(),
           author = username,
           love = 0, hate = 0)
             
  p.save()
  #upload choices if poll
  localchoice_text = []
  localchoice = []
####old approach, works for a fixed amount of choices
  print request.POST
  print "id = "+post_id
  i = 1
  choice_i_exists = True
  while(choice_i_exists == True):
    localchoice_text.append(request.POST.get('choice_%d' % (i), -1))
    if(localchoice_text[i-1] == -1):
      choice_i_exists = False
    elif(localchoice_text[i-1] != ''):
      #the following failed when we deleted posts
      #localchoice.append(Choice(parent_post = get_object_or_404(Post, pk=post_id),
      localchoice.append(Choice(parent_post = p,
                         text = localchoice_text[i-1], 
                         votes = 0))
      localchoice[i-1].save()
    i+=1
    
  #upload photo
  post_photo = request.POST.get('post_photo', -1)
  if(post_photo != ''):
    photo_file = File(request.FILES['post_photo'])
    #the following failed when we deleted posts
    #post_photo = PostPhoto(parent_post =get_object_or_404(Post, pk=post_id),
    #                       image = photo_file)
    post_photo = PostPhoto(parent_post = p,
                           image = photo_file)
    post_photo.save()
    photo_file.close()
    
    #photo_object = PostPhoto
  return HttpResponseRedirect(reverse('posts.views.main'))
  #return HttpResponseRedirect('http://127.0.0.1:8000/')
  #return HttpResponse('Thank you:')
  
  
def view_comments(request, post_id):
  session_id = request.session.get('_auth_user_id', -1)
  if(session_id == -1):
    return HttpResponse("Must login to view this page")
  username = User.objects.get(pk=session_id)
  current_post = get_object_or_404(Post, pk=post_id)
  post_embed_list = split_post(current_post.text)
  comment_list = current_post.comment_set.all()
  return render_to_response('view_comments.html', {
    'current_post': current_post,
    'post_embed_list': post_embed_list,
    'comment_list': comment_list,
    'username' : username,
  }, context_instance=RequestContext(request))

def add_comment(request, post_id):
  session_id = request.session.get('_auth_user_id', -1)
  if(session_id == -1):
    return HttpResponse("Must login to view this page")
  username = User.objects.get(pk=session_id)
  csrf_request = {}
  csrf_request.update(csrf(request))
  new_comment = Comment(
           post = get_object_or_404(Post, pk=post_id),
           text=request.POST['new_comment_text'],
           pub_date = timezone.now(),
           author = username,
           love = 0, hate = 0)
  new_comment.save()
  return HttpResponseRedirect(reverse('posts.views.view_comments', args=(post_id,)))

def vote(request, post_id):
  session_id = request.session.get('_auth_user_id', -1)
  if(session_id == -1):
    return HttpResponse("Must login to view this page")
  csrf_request = {}
  csrf_request.update(csrf(request))
  username = User.objects.get(pk=session_id)
  userprofile = UserProfile.objects.get(pk=session_id)
  post = get_object_or_404(Post, pk=post_id)

  choice_list = post.choice_set.all()
  selected_choice_index = int(request.POST.get('selected_choice', 1))
  selected_choice = choice_list[selected_choice_index - 1]
  selected_choice.votes += 1
  selected_choice.save()
  userprofile.has_voted.add(post)
  post.save()
  userprofile.save()
  #return HttpResponseRedirect(reverse('posts.views.main'))
  #didnt work after posts deleted
  #num_posts = len(Post.objects.all())-int(post_id)
  num_posts = int(request.GET['post_index']) - 1
  index = int(num_posts/posts_per_page) * posts_per_page
  bookmark = num_posts%posts_per_page 
  print "num_posts: "+str(num_posts)+"post id: "+str(post_id)
  return HttpResponseRedirect('/home/%d/#%d' % (index, bookmark))
	  
def account_settings(request, username):
  session_id = request.session.get('_auth_user_id', -1)
  username = User.objects.get(pk=session_id)
  email = username.email
  settings_list = [('username', username), ('email', email)]
  if(session_id == -1):
    return HttpResponse("Must login to view this page")
  csrf_request = {'settings_list': settings_list, 'username': username 
		  }
  csrf_request.update(csrf(request))
  return render_to_response('posts/account_settings.html',  csrf_request, context_instance=RequestContext(request))

def edit_settings(request, setting):
  print "changing %s" %(setting)
  session_id = request.session.get('_auth_user_id', -1)
  username = User.objects.get(pk=session_id)
  email = username.email
  if(session_id == -1):
    return HttpResponse("Must login to view this page")
  if(setting == 'username'):
    username.username = request.POST.get('username')
    username.save()
  elif(setting == 'email'):
    username.email = request.POST.get('email')
    username.save()
  elif(setting == 'password'):
    username.set_password(request.POST.get('password'))
    username.save()
    email = username.email
  ##settings_list = [('username', username), ('email', email)]
  ##csrf_request = {'settings_list': settings_list, 'username': username }
  ##return render_to_response('posts/account_settings.html',  csrf_request, context_instance=RequestContext(request))
  return HttpResponseRedirect(reverse('posts.views.account_settings',args=(username.username,)))
