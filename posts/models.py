from django.db import models
import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save



# Create your models here.

class Post(models.Model):
  title = models.CharField(max_length=200)
  text = models.CharField(max_length=2500)
  pub_date = models.DateTimeField('posted on')
  author = models.ForeignKey(User)
  love = models.IntegerField()
  hate = models.IntegerField()
  #has_voted = models.ManyToManyField(UserProfile)

class Comment(models.Model):
  post = models.ForeignKey(Post)
  author = models.ForeignKey(User)
  text = models.CharField(max_length=2500)
  pub_date = models.DateTimeField('posted on')
  love = models.IntegerField()
  hate = models.IntegerField()
  #caused prob lems in deployment (though not in dev, even with mysql
  #I can see why, so im removing
  #parent_comment = models.ForeignKey('self')

class Choice(models.Model):
  parent_post = models.ForeignKey(Post)
  text = models.CharField(max_length=2500)
  votes = models.IntegerField()
  
class PostPhoto(models.Model):
  parent_post = models.ForeignKey(Post)
  image = models.ImageField(upload_to='posts/media/postphotos')

class CommentPhoto(models.Model):
  parent_post = models.ForeignKey(Comment)
  image = models.ImageField(upload_to='posts/media/commentphotos')

class UserProfile(models.Model):
  user = models.OneToOneField(User)
  has_voted = models.ManyToManyField(Post)

def create_user_profile(sender, instance, created, **kwargs):
    """Create the UserProfile when a new User is saved"""
    if created:
        profile = UserProfile()
        profile.user = instance
        post_list = Post.objects.all()
        profile.save()

##def set_votes_for_new_poll(sender, instance, created, **kwargs):
##  if created:
##    user_list = UserProfile.objects.all()
##    post_instance = instance;
##    for user_instance in user_list:
##      user_post_instance = UserProfile.has_voted.get(pk = (post_instance_id, user_instance_id) ) 
##      user_post_instance.has_voted = 0          
##      user_post_instance.save()
       
            

post_save.connect(create_user_profile, sender=User)
#post_save.connect(set_votes_for_new_poll, sender=Post)

