from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from .models import Post, Comment
from .forms import EmailPostForm,CommentForm, SearchForm
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count
from haystack.query import SearchQuerySet





def post_search(request):
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            cd = form.cleaned_data
            results = SearchQuerySet().models(Post).filter(content=cd['query']).load_all()
            total_results = results.count()
            context = {'form':form, 'cd':cd, 'results':results, 'total_results':total_results}
            return render (request, 'blog/post/search.html', context)
    else:
        form = SearchForm()
        context = {'form':form}
        return render (request, 'blog/post/search.html', context)
        # 
# def post_search(request):
#     results = []  # or None
#     total_results = 0  # or None
#     form = SearchForm(request.GET or None)
#     if 'query' in request.GET:

#         if form.is_valid():
#             cd = form.cleaned_data
#             results = SearchQuerySet().models(Post)\
#                 .filter(content=cd['query']).load_all()
#             # count total results
#             total_results = results.count()
#             template = 'blog/post/search.html'
#             context = {
#                'form': form,
#                'cd': cd,
#                'results': results,
#                'total_results': total_results}
#             return render(request, template, context)
#         else:
#         	return render(request, 'blog/post/search.html', {'form': form,})
#     else:
#        return render(request, 'blog/post/search.html', {'form': form,})	


def post_share(request, post_id):
	post = get_object_or_404(Post, id=post_id, status='published')
	sent = False
	if request.method == 'POST':
		form = EmailPostForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			post_url = request.build_absolute_uri(post.get_absolute_url())
			subject = '{} ({}) reccomends you reading "{}"'.format(cd['name'], cd['email'], post.title)
			message = 'Read "{}" at {}\n\n{}\'s comments: {}'.format(post.title, post_url, cd['name'], cd['comments'])
			send_mail(subject, message,'admin@myblog.com',[cd['to']])
			sent = True
	else:
	    form = EmailPostForm()
	return render(request, 'blog/post/share.html', {'post': post, 'form': form})    		

#using function based views...
def post_list(request, tag_slug=None):
	object_list = Post.published.all()
	tag = None

	if tag_slug:
		tag=get_object_or_404(Tag, slug=tag_slug)
		object_list=object_list.filter(tags__in=[tag])
	paginator = Paginator(object_list, 3)
	page = request.GET.get('page')
	try:
		posts = paginator.page(page)
	except PageNotAnInteger:
		posts = paginator.page(1)
	except EmptyPage:
		posts = paginator.page(paginator.num_pages)

	return render(request, 'blog/post/list.html', {'posts': posts, 'page': page, 'tag':tag})

# using class based views
# class PostListView(ListView):
# 	queryset = Post.published.all()
# 	context_object_name = 'posts'
# 	paginate_by = 3
# 	template_name = 'blog/post/list.html'

def post_detail(request,year,month,day,post):
	post = get_object_or_404(Post, slug=post, status='published', publish__year=year, publish__month=month, publish__day=day)
	comments = post.comments.filter(active=True)
	if request.method == 'POST':
		comment_form = CommentForm(data=request.POST)
		if comment_form.is_valid():
			new_comment = comment_form.save(commit=False)
			new_comment.post = post
			new_comment.save()
	else:
	    comment_form = CommentForm()

	post_tags_ids = post.tags.values_list('id', flat=True)
	similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
	similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]

	return render(request, 'blog/post/detail.html',{'post':post, 'comments': comments, 'comment_form': comment_form, 'similar_posts': similar_posts})

